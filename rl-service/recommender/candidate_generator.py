# recommender/candidate_generator.py
# 候选集生成模块 —— 为强化学习排序提供候选科研内容

from __future__ import annotations
import numpy as np
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from dataset.aminer_loader import Paper


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

    生产环境替换接入点：
      - MySQL 全文检索
      - Elasticsearch 向量检索
      - Faiss / Milvus 向量数据库
      - Spring Boot API 召回服务
    """

    def __init__(
        self,
        pool_size: int = 500,
        state_dim: int = 64,
        paper_pool: Optional[List[CandidateItem]] = None,
        seed: int = 42,
    ):
        self.pool_size = pool_size
        self.state_dim = state_dim
        self.rng = np.random.default_rng(seed)

        # 模拟全量论文库（生产环境替换为数据库）
        self._paper_pool = paper_pool if paper_pool is not None else self._build_mock_pool()

    @classmethod
    def from_papers(
        cls,
        papers: List["Paper"],
        state_dim: int = 64,
        seed: int = 42,
    ) -> "CandidateGenerator":
        generator = cls(
            pool_size=max(len(papers), 1),
            state_dim=state_dim,
            paper_pool=[],
            seed=seed,
        )
        generator._paper_pool = generator._build_pool_from_papers(papers)
        return generator

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

    # ── 数据库适配器接口（预留）──────────────────────────────────

    def fetch_from_mysql(
        self, user_id: str, limit: int = 20
    ) -> List[CandidateItem]:
        """
        从 MySQL 数据库获取候选集（预留接口）。

        接入步骤：
          1. 配置 JDBC 连接（host/port/db/user/pass）
          2. 执行 SELECT + 向量相似度函数
          3. 映射结果到 CandidateItem 列表
        """
        raise NotImplementedError("MySQL 候选集接口待实现")

    def fetch_from_elasticsearch(
        self, query_text: str, limit: int = 20
    ) -> List[CandidateItem]:
        """从 Elasticsearch 全文检索候选集（预留接口）。"""
        raise NotImplementedError("Elasticsearch 接口待实现")

    def fetch_from_vector_db(
        self, user_embedding: np.ndarray, limit: int = 20
    ) -> List[CandidateItem]:
        """从向量数据库（Milvus/Faiss）检索候选集（预留接口）。"""
        raise NotImplementedError("向量数据库接口待实现")

    # ── Mock 数据 ─────────────────────────────────────────────────

    def _build_mock_pool(self) -> List[CandidateItem]:
        """构建模拟论文库（生产环境替换为数据库查询）。"""
        topics_pool = [
            "Reinforcement Learning", "Natural Language Processing",
            "Graph Neural Networks", "Computer Vision", "Knowledge Graphs",
            "Recommender Systems", "Meta-Learning", "Transformers",
            "Federated Learning", "Causal Inference",
        ]
        items = []
        for i in range(self.pool_size):
            topic = topics_pool[i % len(topics_pool)]
            vec = self._build_vector(f"paper_{i:04d}", topic)

            items.append(CandidateItem(
                item_id=f"paper_{i:04d}",
                title=f"Advances in {topic}: A Study #{i}",
                abstract=f"This paper presents novel methods for {topic.lower()}...",
                authors=[f"Author_{i % 30}", f"Author_{(i+1) % 30}"],
                year=2018 + (i % 7),
                citation_count=int(self.rng.integers(0, 800)),
                topics=[topic],
                topic_vector=vec,
                kg_node_id=f"kg_node_{i:04d}",
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
                topic_vector=self._build_vector(paper.paper_id, paper.text_for_embedding()),
                kg_node_id=paper.paper_id,
            ))
        return items

    def _build_vector(self, key: str, text: str) -> np.ndarray:
        seed = hash(f"{key}:{text}") % (2**31)
        rng = np.random.default_rng(seed)
        vec = rng.standard_normal(self.state_dim).astype(np.float32)
        return vec / (np.linalg.norm(vec) + 1e-8)
