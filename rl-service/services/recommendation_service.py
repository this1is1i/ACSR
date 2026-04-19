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
from features.feature_builder import FeatureBuilder, UserFeatures
from recommender.candidate_generator import CandidateGenerator, CandidateItem
from recommender.ranker import RLRanker, RankedItem
from recommender.explain import ExplanationGenerator, ExplanationResult

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
        1. 获取用户特征（FeatureBuilder）
        2. 生成候选集（CandidateGenerator）
        3. 强化学习排序（RLRanker + ActorCriticAgent）
        4. 生成推荐解释（ExplanationGenerator）
        5. 组装并返回结果

    设计原则：
        - 每个子模块可独立替换（接口不变）
        - 所有 IO 操作（数据库、模型加载）在此层统一管理
        - 对 REST API 层（FastAPI）透明暴露
    """

    MODEL_VERSION = "v1.0.0-actor-critic"

    def __init__(self, config: Config = default_config):
        self.config = config
        self._agent: Optional[ActorCriticAgent] = None
        self._ranker: Optional[RLRanker] = None

        # 初始化各子模块
        self.feature_builder    = FeatureBuilder(state_dim=config.state_dim)
        self.candidate_gen      = CandidateGenerator(state_dim=config.state_dim)
        self.explain_gen        = ExplanationGenerator()

        self._load_agent()
        logger.info(f"RecommendationService 初始化完成，模型版本: {self.MODEL_VERSION}")

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
            user_id:  用户唯一标识
            k:        推荐数量
            history:  已交互论文 ID 列表（用于过滤）
            strategy: 候选集召回策略（"similarity" | "popular" | "hybrid"）

        Returns:
            RecommendationResponse 标准推荐结果
        """
        t0 = time.time()

        # ── Step 1: 获取用户特征 ──────────────────────────────────
        user_features = self.feature_builder.get_user_features(user_id, history)
        user_state    = self.feature_builder.build_state(user_features)
        logger.debug(f"[{user_id}] Step1 特征构建完成")

        # ── Step 2: 生成候选集 ────────────────────────────────────
        candidates = self.candidate_gen.generate(
            user_id=user_id,
            user_embedding=user_features.interest_vector,
            history=history,
            limit=min(self.config.action_num * 2, 50),
            strategy=strategy,
        )
        logger.debug(f"[{user_id}] Step2 候选集生成: {len(candidates)} 篇")

        # ── Step 3: 强化学习排序 ──────────────────────────────────
        ranked_items = self._ranker.recommend_top_k(user_state, candidates, k=k)
        logger.debug(f"[{user_id}] Step3 RL排序完成: Top-{len(ranked_items)}")

        # ── Step 4: 生成推荐解释 ──────────────────────────────────
        item_list = [r.item for r in ranked_items]
        explanations = self.explain_gen.batch_explain(user_features, item_list)
        exp_map = {e.paper_id: e for e in explanations}

        # ── Step 5: 组装结果 ──────────────────────────────────────
        result_items = []
        for ranked in ranked_items:
            exp = exp_map.get(ranked.item.item_id)
            result_items.append(RecommendationItem(
                paper_id       = ranked.item.item_id,
                title          = ranked.item.title,
                authors        = ranked.item.authors,
                year           = ranked.item.year,
                score          = round(ranked.score, 6),
                rank           = ranked.rank,
                reason         = exp.reason if exp else "相关推荐",
                reason_details = exp.reason_details if exp else [],
                similarity_score = exp.similarity_score if exp else 0.0,
                topics         = ranked.item.topics,
                citation_count = ranked.item.citation_count,
                confidence     = exp.confidence if exp else 0.5,
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
            "model_version":  self.MODEL_VERSION,
            "train_step":     agent.train_step if agent else 0,
            "episode_count":  agent.episode_count if agent else 0,
            "model_path":     self.config.model_save_path,
            "state_dim":      self.config.state_dim,
            "action_num":     self.config.action_num,
            "top_k":          self.config.top_k,
            "device":         str(next(agent.actor.parameters()).device) if agent else "cpu",
        }

    def reload_model(self) -> None:
        """热重载模型权重（训练完成后无需重启服务）。"""
        self._load_agent()
        self._ranker = RLRanker(self._agent, self.config)
        logger.info("模型已热重载")

    # ── 内部方法 ──────────────────────────────────────────────────

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
        self._ranker = RLRanker(self._agent, self.config)
