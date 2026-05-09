# data/mock_data.py
# 模拟数据生成模块 —— 可替换为真实数据库查询

from __future__ import annotations
import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class ResearchItem:
    """科研内容条目（论文 / 项目 / 合作者）"""
    item_id: str
    title: str
    topic_vector: np.ndarray        # 研究方向 embedding（维度与 base_state_dim 一致）
    citation_count: int = 0
    year: int = 2024
    kg_node_id: Optional[str] = None


@dataclass
class UserProfile:
    """用户科研画像"""
    user_id: str
    interest_vector: np.ndarray     # 用户兴趣 embedding
    history_vector: np.ndarray      # 历史行为 embedding（近期交互的平均池化）
    research_topics: List[str] = field(default_factory=list)
    kg_feature: Optional[np.ndarray] = None
    community_feature: Optional[np.ndarray] = None
    history_paper_ids: List[str] = field(default_factory=list)


class MockDataGenerator:
    """
    模拟数据生成器。
    生产环境中替换为：
      - MySQL / PostgreSQL 查询
      - Spring Boot REST API 调用
      - 用户行为日志解析
    """

    def __init__(
        self,
        base_state_dim: int = 64,
        action_num: int = 20,
        kg_dim: int = 0,
        seed: int = 42,
    ):
        self.base_state_dim = base_state_dim
        self.action_num = action_num
        self.kg_dim = kg_dim
        self.rng = np.random.default_rng(seed)

    # ── 用户数据 ──────────────────────────────────────────────────

    def generate_user(self, user_id: str = "user_001") -> UserProfile:
        """生成一个随机用户科研画像。"""
        # 模拟用户阅读过的论文 ID（用于 KG embedding 计算）
        num_history = self.rng.integers(3, 15)
        history_ids = [f"aminer_{self.rng.integers(0, 500):06d}" for _ in range(num_history)]

        return UserProfile(
            user_id=user_id,
            interest_vector=self._rand_vec(),
            history_vector=self._rand_vec(),
            research_topics=["NLP", "Graph Learning"],
            kg_feature=None,  # 由环境注入
            community_feature=None,
            history_paper_ids=history_ids,
        )

    # ── 候选科研内容 ──────────────────────────────────────────────

    def generate_candidate_items(self, n: Optional[int] = None) -> List[ResearchItem]:
        """生成候选科研内容列表。"""
        n = n or self.action_num
        topics = ["NLP", "CV", "RL", "Graph NN", "Bioinformatics",
                  "Systems", "Security", "HCI", "Robotics", "Theory"]
        return [
            ResearchItem(
                item_id=f"paper_{i:04d}",
                title=f"Research on {topics[i % len(topics)]} #{i}",
                topic_vector=self._rand_vec(),
                citation_count=int(self.rng.integers(0, 500)),
                year=int(self.rng.integers(2018, 2025)),
                kg_node_id=f"aminer_{i:06d}",
            )
            for i in range(n)
        ]

    # ── 状态构建 ──────────────────────────────────────────────────

    def build_state(
        self,
        user: UserProfile,
        kg_feature: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """
        将用户特征拼接为状态向量。

        state = concat(interest[:half], history[:half], [kg_feature])
        """
        half = self.base_state_dim // 2
        interest = user.interest_vector[:half]
        history  = user.history_vector[:half]

        parts = [interest, history]

        # ── 知识图谱特征 ─────────────────────────────────────────
        if self.kg_dim > 0:
            if kg_feature is not None:
                parts.append(kg_feature[:self.kg_dim])
            elif user.kg_feature is not None:
                parts.append(user.kg_feature[:self.kg_dim])
            else:
                parts.append(np.zeros(self.kg_dim, dtype=np.float32))

        state = np.concatenate(parts).astype(np.float32)
        return state

    # ── 辅助方法 ──────────────────────────────────────────────────

    def _rand_vec(self) -> np.ndarray:
        v = self.rng.standard_normal(self.base_state_dim).astype(np.float32)
        return v / (np.linalg.norm(v) + 1e-8)
