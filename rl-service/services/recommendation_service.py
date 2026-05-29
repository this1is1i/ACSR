# services/recommendation_service.py
# 统一推荐服务层 —— 编排完整推荐流程

from __future__ import annotations
import time
import logging
import os
import sys
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

# 将项目根目录加入路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, default_config
from agent import ActorCriticAgent
from dataset.aminer_loader import Paper as SourcePaper
from features.feature_builder import FeatureBuilder, UserFeatures
from knowledge_graph.graph_query import GraphQuery
from knowledge_graph.kg_embedder import KGEmbedder, create_kg_embedder
from recommender.candidate_generator import CandidateGenerator, CandidateItem
from recommender.ranker import RLRanker, RankedItem

logger = logging.getLogger(__name__)


@dataclass
class RecommendationItem:
    """单条推荐结果（对外暴露的标准格式）。"""
    paper_id: str
    title: str
    authors: List[str]
    year: int
    score: float
    rank: int
    reason: str
    reason_details: List[str]
    similarity_score: float
    topics: List[str]
    citation_count: int
    confidence: float


@dataclass
class RecommendationResponse:
    """推荐接口返回体。"""
    user_id: str
    k: int
    recommendations: List[RecommendationItem]
    latency_ms: float
    model_version: str
    timestamp: float = field(default_factory=time.time)


class RecommendationService:
    """
    推荐服务层 —— 统一编排推荐全链路。

    流程：
        1. 获取用户特征（FeatureBuilder → MySQL / KG）
        2. 生成候选集（CandidateGenerator → Neo4j 论文池）
        3. 强化学习排序（RLRanker + ActorCriticAgent）
        4. 生成推荐解释（ExplanationGenerator）
        5. 组装并返回结果

    数据来源：
        - 用户特征：MySQL behavior_log + user_interest_history（FeatureBuilder）
        - 论文池：  Neo4j 知识图谱（通过 GraphStorage.load_from_neo4j）
        - KG 嵌入： KGEmbedder 运行时从图结构计算
        - 模型权重： checkpoints/ac_model.pth
    """

    MODEL_VERSION = "v2.0.0-mysql-neo4j"

    def __init__(self, config: Config = default_config):
        self.config = config
        self._agent: Optional[ActorCriticAgent] = None
        self._ranker: Optional[RLRanker] = None
        self._kg_embedder = None
        self._paper_catalog: List[SourcePaper] = []
        self._mysql = None
        self._graph_query = None

        # 初始化 MySQL 数据源
        self._init_mysql(config)

        # 初始化 KG（Neo4j 或本地构建）
        self._init_kg(config)

        # 初始化各子模块
        kg_dim = config.kg_embedding_dim if config.use_kg else 0
        self.feature_builder = FeatureBuilder(
            base_state_dim=config.base_state_dim,
            kg_dim=kg_dim,
            kg_embedder=self._kg_embedder,
            mysql_source=self._mysql,
        )
        self.candidate_gen = (
            CandidateGenerator.from_papers(
                self._paper_catalog, state_dim=config.base_state_dim,
                kg_embedder=self._kg_embedder,
            )
            if self._paper_catalog else
            CandidateGenerator(state_dim=config.base_state_dim, kg_embedder=self._kg_embedder)
        )

        self._load_agent()
        logger.info(
            f"RecommendationService 初始化完成，模型版本: {self.MODEL_VERSION}, "
            f"use_kg={config.use_kg}, papers={len(self._paper_catalog)}, "
            f"mysql={'enabled' if self._mysql else 'disabled'}"
        )

    # ── 主推荐接口 ────────────────────────────────────────────────

    def get_recommendations(
        self,
        user_id: str,
        k: int = 10,
        history: Optional[List[str]] = None,
        strategy: str = "hybrid",
    ) -> RecommendationResponse:
        """
        完整推荐流程入口。

        Args:
            user_id:  用户唯一标识（对应 MySQL user.id）
            k:        推荐数量
            history:  已交互论文 ID 列表（AMiner ID 格式，用于过滤）
            strategy: 候选集召回策略（"similarity" | "popular" | "hybrid"）

        Returns:
            RecommendationResponse 标准推荐结果
        """
        t0 = time.time()

        # ── Step 1: 获取用户特征 ──────────────────────────────────
        user_features = self.feature_builder.get_user_features(user_id, history)
        user_state    = self.feature_builder.build_state(user_features)
        logger.debug(f"[{user_id}] Step1 特征构建完成, state_dim={len(user_state)}")

        # ── Step 2: 生成候选集 ────────────────────────────────────
        candidates = self.candidate_gen.generate(
            user_id=user_id,
            user_embedding=user_features.interest_vector,
            history=history,
            limit=min(self.config.action_num, 50),
            strategy=strategy,
        )
        logger.debug(f"[{user_id}] Step2 候选集生成: {len(candidates)} 篇")

        # ── Step 3: 强化学习排序 ──────────────────────────────────
        user_history = user_features.history_paper_ids if hasattr(user_features, 'history_paper_ids') else None
        ranked_items = self._ranker.recommend_top_k(user_state, candidates, k=k, user_history=user_history)
        logger.debug(f"[{user_id}] Step3 RL排序完成: Top-{len(ranked_items)}")

        # ── Step 4: 生成推荐解释（KG 图结构增强版）──────────────
        history_for_explain = user_features.history_paper_ids
        logger.info(
            f"[{user_id}] Step4 解释准备: graph_query={'OK' if self._graph_query else 'MISSING'}, "
            f"history_ids={history_for_explain[:3] if history_for_explain else 'EMPTY'}"
        )

        # ── Step 5: 组装结果 ──────────────────────────────────────
        result_items = []
        for ranked in ranked_items:
            item = ranked.item
            paper_id = item.item_id

            # 基于 KG 图结构生成解释（引用链、共同作者、关键词共现）
            if self._graph_query is not None and history_for_explain:
                reasons = self._graph_query.explain_recommendation(
                    history_for_explain, paper_id
                )
            else:
                if self._graph_query is None:
                    logger.debug(f"[{user_id}] 无 GraphQuery，推荐理由回退模板文本")
                elif not history_for_explain:
                    logger.debug(f"[{user_id}] 无历史论文 ID，推荐理由回退模板文本")
                reasons = []

            reason = reasons[0] if reasons else "基于您的科研兴趣推荐"
            reason_details = reasons if reasons else ["基于强化学习算法推测您可能感兴趣的内容"]
            confidence = min(0.99, 0.5 + 0.12 * len(reasons))

            result_items.append(RecommendationItem(
                paper_id       = paper_id,
                title          = item.title,
                authors        = item.authors,
                year           = item.year,
                score          = round(ranked.score, 6),
                rank           = ranked.rank,
                reason         = reason,
                reason_details = reason_details,
                similarity_score = round(ranked.score, 4),
                topics         = item.topics,
                citation_count = item.citation_count,
                confidence     = round(confidence, 4),
            ))

        latency_ms = round((time.time() - t0) * 1000, 2)
        logger.info(f"[{user_id}] 推荐完成: Top-{k}，耗时 {latency_ms}ms")

        return RecommendationResponse(
            user_id=user_id,
            k=k,
            recommendations=result_items,
            latency_ms=latency_ms,
            model_version=self.MODEL_VERSION,
        )

    def to_dict(self, response: RecommendationResponse) -> Dict[str, Any]:
        """将推荐结果序列化为 JSON 兼容字典。"""
        return {
            "user_id":       response.user_id,
            "k":             response.k,
            "model_version": response.model_version,
            "latency_ms":    response.latency_ms,
            "timestamp":     response.timestamp,
            "recommendations": [
                {
                    "paper_id":        item.paper_id,
                    "title":           item.title,
                    "authors":         item.authors,
                    "year":            item.year,
                    "score":           item.score,
                    "rank":            item.rank,
                    "reason":          item.reason,
                    "reason_details":  item.reason_details,
                    "similarity_score": item.similarity_score,
                    "topics":          item.topics,
                    "citation_count":  item.citation_count,
                    "confidence":      item.confidence,
                }
                for item in response.recommendations
            ],
        }

    # ── 模型管理 ──────────────────────────────────────────────────

    def get_model_info(self) -> Dict[str, Any]:
        """返回当前模型状态信息（供 /model/info 接口使用）。"""
        agent = self._agent
        return {
            "model_version":    self.MODEL_VERSION,
            "train_step":       agent.train_step if agent else 0,
            "episode_count":    agent.episode_count if agent else 0,
            "model_path":       self.config.model_save_path,
            "state_dim":        self.config.state_dim,
            "base_state_dim":   self.config.base_state_dim,
            "action_num":       self.config.action_num,
            "top_k":            self.config.top_k,
            "use_kg":           self.config.use_kg,
            "kg_embedding_dim": self.config.kg_embedding_dim if self.config.use_kg else 0,
            "device":           str(next(agent.actor.parameters()).device) if agent else "cpu",
        }

    def reload_model(self) -> None:
        """热重载模型权重（训练完成后无需重启服务）。"""
        self._load_agent()
        logger.info("模型已热重载")

    # ── 内部方法 ──────────────────────────────────────────────────

    def _init_mysql(self, config: Config) -> None:
        """初始化 MySQL 数据源。"""
        try:
            from data.mysql_data import MySQLDataSource
            self._mysql = MySQLDataSource(config)
            # 快速连接测试
            _ = self._mysql.conn
            logger.info("MySQL 数据源连接成功")
        except Exception as e:
            logger.warning(f"MySQL 数据源不可用，用户特征将使用随机向量: {e}")
            self._mysql = None

    def _init_kg(self, config: Config) -> None:
        """初始化知识图谱及 Embedder。"""
        if not config.use_kg:
            logger.info("KG 未启用（use_kg=False）")
            return

        kg = None

        # 优先使用 Neo4j 图数据库
        if config.graph_backend == "neo4j":
            kg = self._load_kg_from_neo4j(config)

        # 回退：从 AMiner 数据文件或 JSON/Pickle 加载
        if kg is None:
            kg = self._load_kg_from_files(config)

        if kg is None:
            logger.warning("无法加载知识图谱，推荐将使用 mock 论文池")
            return

        # 提取论文目录
        self._paper_catalog = self._extract_papers_from_kg(kg)
        self._kg_embedder = KGEmbedder(kg, embed_dim=config.kg_embedding_dim)

        # 将 KG 设置为 GraphQuery 可用的属性
        self.kg = kg
        self._graph_query = GraphQuery(kg)

        # 保存投影矩阵，供离线脚本和 CandidateGenerator 回退使用
        self._save_projection_artifacts(config)

        logger.info(f"KG 初始化完成: {kg.stats}, paper_catalog={len(self._paper_catalog)}")

    def _save_projection_artifacts(self, config: Config) -> None:
        """保存投影矩阵和归一化参数到 checkpoints/projection.npz。"""
        if self._kg_embedder is None:
            return
        try:
            artifacts_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "checkpoints", "projection.npz",
            )
            os.makedirs(os.path.dirname(artifacts_path), exist_ok=True)
            if not os.path.exists(artifacts_path):
                P = self._kg_embedder.get_projection_matrix()
                mean, std = self._kg_embedder.get_feature_stats()
                np.savez(artifacts_path, P=P, mean=mean, std=std)
                logger.info(f"投影矩阵已保存: {artifacts_path}")
        except Exception as e:
            logger.warning(f"保存投影矩阵失败: {e}")

    def _load_kg_from_neo4j(self, config: Config) -> Optional[Any]:
        """从 Neo4j 加载知识图谱。"""
        if not config.neo4j_password or not config.neo4j_uri:
            logger.info("Neo4j 未配置（缺少 uri 或 password），跳过 Neo4j 加载")
            return None
        try:
            from knowledge_graph.graph_storage import GraphStorage
            storage = GraphStorage()
            kg = storage.load_from_neo4j(
                uri=config.neo4j_uri,
                user=config.neo4j_user,
                password=config.neo4j_password,
                database=config.neo4j_database,
            )
            paper_count = sum(1 for n in kg.nodes.values() if n.node_type == "paper")
            logger.info(f"KG 从 Neo4j 加载完成：{kg.stats}, paper nodes={paper_count}")
            return kg
        except Exception as e:
            logger.warning(f"Neo4j 加载失败: {e}，尝试其他 KG 后端")
            return None

    def _load_kg_from_files(self, config: Config) -> Optional[Any]:
        """从已持久化的 JSON/Pickle 或 AMiner 数据文件加载 KG。"""
        try:
            from knowledge_graph.graph_storage import GraphStorage

            storage = GraphStorage()
            if storage.exists():
                kg = storage.load(prefer="pickle")
                logger.info(f"KG 从本地文件加载完成：{kg.stats}")
                return kg

            # 回退：从 AMiner 构建（共享函数）
            _, kg = create_kg_embedder(config)
            if kg is not None:
                storage.save(kg, format="both")
            return kg
        except Exception as e:
            logger.warning(f"文件加载 KG 失败: {e}")
            return None

    @staticmethod
    def _extract_papers_from_kg(kg) -> List[SourcePaper]:
        """从 KG 节点中提取论文列表，供 CandidateGenerator 使用。"""
        from knowledge_graph.kg_builder import KnowledgeGraph
        papers: List[SourcePaper] = []
        for node in kg.nodes.values():
            if node.node_type != "paper":
                continue

            props = node.properties

            authors = props.get("authors") or []
            keywords = props.get("keywords") or []
            if isinstance(authors, str):
                authors = [authors]
            if isinstance(keywords, str):
                keywords = [keywords]

            # Neo4j 返回的整数可能是 dict{"low": n, "high": 0}，需要转换
            year = _safe_int(props.get("year"), 0)
            citation_count = _safe_int(props.get("citation_count"), 0)

            # 从 Neo4j 节点读取预存向量（embedding 在 reserved 集，存在 node.embedding）
            embedding_val = node.embedding or props.get("embedding")
            paper_embedding = _parse_json_prop(embedding_val)
            paper_embedding_raw = _parse_json_prop(props.get("embedding_raw"))

            papers.append(SourcePaper(
                paper_id=props.get("aminer_id") or node.node_id,
                title=props.get("title") or node.label,
                abstract=props.get("abstract") or "",
                authors=[str(a) for a in authors],
                keywords=[str(k) for k in keywords],
                venue=str(props.get("venue") or ""),
                year=year,
                citation_count=citation_count,
                references=[],
                embedding=paper_embedding,
                embedding_raw=paper_embedding_raw,
            ))
        return papers

    def _load_agent(self) -> None:
        """加载或初始化 Agent。"""
        self._agent = ActorCriticAgent(self.config)
        model_path = self.config.model_save_path
        if os.path.exists(model_path):
            try:
                self._agent.load_model(model_path)
                logger.info(f"已加载预训练模型: {model_path}")
            except Exception as e:
                logger.warning(f"模型加载失败，使用随机初始化权重: {e}")
        else:
            logger.info("未找到预训练模型，使用随机初始化权重（请先运行 train.py）")
        self._ranker = RLRanker(self._agent, self.config, kg_embedder=self._kg_embedder)


# ── 工具函数 ──────────────────────────────────────────────────────

def _safe_int(value, default: int = 0) -> int:
    """安全转换 Neo4j 整型（可能是 dict{"low": n} 或原生 int）。"""
    if value is None:
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, dict):
        return int(value.get("low", default))
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_json_prop(value) -> Optional[list]:
    """解析 Neo4j 节点属性中的 JSON 字符串或 list。"""
    if value is None:
        return None
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            import json
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else None
        except (json.JSONDecodeError, TypeError):
            pass
    return None
