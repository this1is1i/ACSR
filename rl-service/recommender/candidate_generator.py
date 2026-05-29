# recommender/candidate_generator.py
# 候选集生成模块 —— 为强化学习排序提供候选科研内容

from __future__ import annotations
import json
import logging
import os
import numpy as np
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from dataset.aminer_loader import Paper

logger = logging.getLogger(__name__)

# 投影矩阵缓存文件路径
_PROJECTION_NPZ = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "checkpoints", "projection.npz")


@dataclass
class CandidateItem:
    """候选科研内容条目。"""
    item_id: str
    title: str
    abstract: str = ""
    authors: List[str] = field(default_factory=list)
    year: int = 2024
    citation_count: int = 0
    topics: List[str] = field(default_factory=list)
    topic_vector: Optional[np.ndarray] = None   # 语义 embedding
    kg_node_id: Optional[str] = None            # 知识图谱节点（预留）
    score: float = 0.0                          # 排序后填入


class CandidateGenerator:
    """
    候选集生成器。

    生成策略（可叠加）：
      - 召回：基于用户兴趣向量的余弦相似度检索
      - 热门：高被引论文召回
      - 探索：随机抽样保证多样性

    论文向量来源（优先级从高到低）：
      1. paper.embedding 预存向量（离线脚本写入，主流路径）
      2. KGEmbedder 实时计算（回退，与离线脚本同逻辑）
      3. 元数据近似特征（最差回退，仍基于数据库真实字段）
      4. 确定性哈希随机向量（紧急回退，仅在所有数据源不可用时触发）
    """

    def __init__(
        self,
        pool_size: int = 500,
        state_dim: int = 64,
        paper_pool: Optional[List[CandidateItem]] = None,
        seed: int = 42,
        kg_embedder: Any = None,
    ):
        self.pool_size = pool_size
        self.state_dim = state_dim
        self.rng = np.random.default_rng(seed)
        self._kg_embedder = kg_embedder

        # 加载投影矩阵（若存在）
        self._projection_P: Optional[np.ndarray] = None
        self._projection_mean: Optional[np.ndarray] = None
        self._projection_std: Optional[np.ndarray] = None
        self._load_projection_artifacts()

        # 模拟全量论文库（生产环境替换为数据库）
        self._paper_pool = paper_pool if paper_pool is not None else self._build_mock_pool()

    @classmethod
    def from_papers(
        cls,
        papers: List["Paper"],
        state_dim: int = 64,
        seed: int = 42,
        kg_embedder: Any = None,
    ) -> "CandidateGenerator":
        generator = cls(
            pool_size=max(len(papers), 1),
            state_dim=state_dim,
            paper_pool=[],
            seed=seed,
            kg_embedder=kg_embedder,
        )
        generator._paper_pool = generator._build_pool_from_papers(papers)
        return generator

    # ── 投影矩阵加载 ────────────────────────────────────────────────

    def _load_projection_artifacts(self) -> None:
        """从 checkpoints/projection.npz 加载投影矩阵和归一化参数。"""
        if os.path.exists(_PROJECTION_NPZ):
            try:
                data = np.load(_PROJECTION_NPZ)
                self._projection_P = data["P"]
                self._projection_mean = data["mean"]
                self._projection_std = data["std"]
                logger.info(f"已加载投影矩阵: {_PROJECTION_NPZ}")
            except Exception as e:
                logger.warning(f"加载投影矩阵失败: {e}，元数据回退将使用随机投影")
        elif self._kg_embedder is not None:
            # 从 KGEmbedder 复制投影参数
            try:
                self._projection_P = self._kg_embedder.get_projection_matrix()
                self._projection_mean, self._projection_std = self._kg_embedder.get_feature_stats()
            except Exception:
                pass

    # ── 主接口 ────────────────────────────────────────────────────

    def generate(
        self,
        user_id: str,
        user_embedding: np.ndarray,
        history: Optional[List[str]] = None,
        limit: int = 20,
        strategy: str = "hybrid",
    ) -> List[CandidateItem]:
        """
        生成用户候选集。

        Args:
            user_id:        用户 ID
            user_embedding: 用户兴趣向量
            history:        历史交互论文 ID 列表（用于过滤已读）
            limit:          候选集大小
            strategy:       召回策略 ("similarity" | "popular" | "hybrid")

        Returns:
            候选科研内容列表，已按初步相关性排序
        """
        history_set = set(history or [])

        # 过滤已读论文
        pool = [p for p in self._paper_pool if p.item_id not in history_set]

        if strategy == "similarity":
            candidates = self._retrieve_by_similarity(user_embedding, pool, limit)
        elif strategy == "popular":
            candidates = self._retrieve_by_popularity(pool, limit)
        else:  # hybrid
            sim_cnt = int(limit * 0.7)
            pop_cnt = limit - sim_cnt
            sim_items = self._retrieve_by_similarity(user_embedding, pool, sim_cnt)
            pop_items = self._retrieve_by_popularity(pool, pop_cnt * 3)
            # 去重合并
            seen = {p.item_id for p in sim_items}
            pop_items = [p for p in pop_items if p.item_id not in seen][:pop_cnt]
            candidates = sim_items + pop_items

        return candidates[:limit]

    # ── 检索策略 ──────────────────────────────────────────────────

    def _retrieve_by_similarity(
        self, user_vec: np.ndarray, pool: List[CandidateItem], k: int
    ) -> List[CandidateItem]:
        """余弦相似度检索（生产环境替换为 Faiss ANN 搜索）。"""
        scores = []
        for item in pool:
            if item.topic_vector is not None:
                sim = float(np.dot(user_vec, item.topic_vector))
            else:
                sim = 0.0
            scores.append((sim, item))
        scores.sort(key=lambda x: -x[0])
        return [item for _, item in scores[:k]]

    def _retrieve_by_popularity(
        self, pool: List[CandidateItem], k: int
    ) -> List[CandidateItem]:
        """按被引量检索热门论文。"""
        return sorted(pool, key=lambda p: -p.citation_count)[:k]

    # ── 论文向量加载 ──────────────────────────────────────────────

    def _load_paper_embedding(self, paper) -> np.ndarray:
        """从 paper 对象加载预存向量，不回退到随机哈希。

        优先级:
          1. paper.embedding 预存向量（主流路径，32-dim → pad to state_dim）
          2. KGEmbedder 实时计算（KG 中的论文但无预存时）
          3. 元数据近似特征（最差回退，仍基于数据库字段）
        """
        # 优先级 1: 预存向量
        if hasattr(paper, 'embedding') and paper.embedding:
            vec = self._parse_embedding_json(paper.embedding)
            if vec is not None:
                return self._pad_to_state_dim(vec)

        # 优先级 2: KGEmbedder 实时计算
        if self._kg_embedder is not None:
            pid = getattr(paper, 'paper_id', None) or getattr(paper, 'aminer_id', None)
            if pid:
                emb = self._kg_embedder.get_paper_embedding(pid)
                if emb is not None:
                    return self._pad_to_state_dim(emb)

        # 优先级 3: 元数据近似特征
        return self._build_from_metadata(
            citation_count=getattr(paper, 'citation_count', 0) or 0,
            year=getattr(paper, 'year', 2024) or 2024,
            keywords=getattr(paper, 'keywords', []),
            authors=getattr(paper, 'authors', []),
        )

    def _build_from_metadata(
        self,
        citation_count: int,
        year: int,
        keywords: list,
        authors: list,
    ) -> np.ndarray:
        """基于论文元数据构建 32 维向量（使用投影矩阵，若无则用固定种子随机投影）。"""
        kw_list = keywords if isinstance(keywords, list) else []
        au_list = authors if isinstance(authors, list) else []

        raw_10d = np.array([
            float(citation_count) / max(1.0, float(citation_count) + 1.0),  # [0] cite_in 归一化
            0.0,                                                              # [1] cite_out (需KG)
            min(float(len(kw_list)) / 10.0, 1.0),                            # [2] keyword_count
            0.0,                                                              # [3] keyword_reach (需KG)
            float(len(au_list)),                                              # [4] author_count
            0.0,                                                              # [5] author_productivity (需KG)
            0.0,                                                              # [6] venue_popularity (需KG)
            0.0,                                                              # [7] co_author_density (需KG)
            0.0,                                                              # [8] topo_depth (需KG)
            (float(year) - 2010.0) / 15.0,                                    # [9] recency
        ], dtype=np.float32)

        # Z-score + 投影
        if self._projection_P is not None and self._projection_mean is not None:
            normalized = (raw_10d - self._projection_mean) / self._projection_std
            projected = normalized @ self._projection_P
        else:
            # 无投影矩阵时使用固定种子随机投影（保持可复现但不理想）
            rng = np.random.default_rng(42)
            P = rng.standard_normal((10, 32)).astype(np.float32) / np.sqrt(10)
            projected = raw_10d @ P

        norm = np.linalg.norm(projected) + 1e-8
        vec_32d = (projected / norm).astype(np.float32)

        return self._pad_to_state_dim(vec_32d)

    def _pad_to_state_dim(self, vec: np.ndarray) -> np.ndarray:
        """将 32 维向量 pad 到 state_dim 维（后补零）。"""
        if len(vec) >= self.state_dim:
            return vec[:self.state_dim].astype(np.float32)
        padded = np.zeros(self.state_dim, dtype=np.float32)
        padded[:len(vec)] = vec
        return padded

    @staticmethod
    def _parse_embedding_json(embedding) -> Optional[np.ndarray]:
        """解析 embedding 字段：JSON 字符串 / Python 列表 / 已为 np.ndarray。"""
        if embedding is None:
            return None
        if isinstance(embedding, np.ndarray):
            return embedding.astype(np.float32)
        if isinstance(embedding, list):
            return np.array(embedding, dtype=np.float32)
        if isinstance(embedding, str):
            try:
                parsed = json.loads(embedding)
                if isinstance(parsed, list):
                    return np.array(parsed, dtype=np.float32)
            except (json.JSONDecodeError, TypeError):
                pass
        return None

    # ── Mock 数据（当无真实论文池时使用）───────────────────────────

    def _build_mock_pool(self) -> List[CandidateItem]:
        """构建模拟论文库（每个 mock 论文的向量基于其元数据，非随机哈希）。"""
        topics_pool = [
            "Reinforcement Learning", "Natural Language Processing",
            "Graph Neural Networks", "Computer Vision", "Knowledge Graphs",
            "Recommender Systems", "Meta-Learning", "Transformers",
            "Federated Learning", "Causal Inference",
        ]
        items = []
        for i in range(self.pool_size):
            topic = topics_pool[i % len(topics_pool)]
            year = 2018 + (i % 7)
            citation_count = int(self.rng.integers(0, 800))
            vec = self._build_from_metadata(
                citation_count=citation_count,
                year=year,
                keywords=[topic],
                authors=[f"Author_{i % 30}", f"Author_{(i+1) % 30}"],
            )

            items.append(CandidateItem(
                item_id=f"paper_{i:04d}",
                title=f"Advances in {topic}: A Study #{i}",
                abstract=f"This paper presents novel methods for {topic.lower()}...",
                authors=[f"Author_{i % 30}", f"Author_{(i+1) % 30}"],
                year=year,
                citation_count=citation_count,
                topics=[topic],
                topic_vector=vec,
                kg_node_id=f"aminer_{i:06d}",
            ))
        return items

    def _build_pool_from_papers(self, papers: List["Paper"]) -> List[CandidateItem]:
        items: List[CandidateItem] = []
        for paper in papers:
            topics = paper.keywords[:5] if paper.keywords else ([paper.venue] if paper.venue else [])
            items.append(CandidateItem(
                item_id=paper.paper_id,
                title=paper.title,
                abstract=paper.abstract,
                authors=paper.authors,
                year=paper.year or 2024,
                citation_count=paper.citation_count,
                topics=topics,
                topic_vector=self._load_paper_embedding(paper),
                kg_node_id=paper.paper_id,
            ))
        return items

    def _build_vector(self, key: str, text: str) -> np.ndarray:
        """紧急回退：确定性哈希随机向量。仅在所有数据源不可用时使用。"""
        logger.warning(f"_build_vector fallback triggered for key={key[:50]} — paper embedding unavailable")
        seed = hash(f"{key}:{text}") % (2**31)
        rng = np.random.default_rng(seed)
        vec = rng.standard_normal(self.state_dim).astype(np.float32)
        return vec / (np.linalg.norm(vec) + 1e-8)
