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
    topic_vector: np.ndarray        # 研究方向 embedding（维度与 state_dim 一致）
    citation_count: int = 0
    year: int = 2024
    # 预留知识图谱节点 ID
    kg_node_id: Optional[str] = None


@dataclass
class UserProfile:
    """用户科研画像"""
    user_id: str
    interest_vector: np.ndarray     # 用户兴趣 embedding
    history_vector: np.ndarray      # 历史行为 embedding（近期交互的平均池化）
    research_topics: List[str] = field(default_factory=list)
    # 预留知识图谱特征
    kg_feature: Optional[np.ndarray] = None
    # 预留社区行为特征
    community_feature: Optional[np.ndarray] = None


class MockDataGenerator:
    """
    模拟数据生成器。
    生产环境中替换为：
      - MySQL / PostgreSQL 查询
      - Spring Boot REST API 调用
      - 用户行为日志解析
    """

    def __init__(self, state_dim: int = 64, action_num: int = 20, seed: int = 42):
        self.state_dim = state_dim
        self.action_num = action_num
        self.rng = np.random.default_rng(seed)

    # ── 用户数据 ──────────────────────────────────────────────────

    def generate_user(self, user_id: str = "user_001") -> UserProfile:
        """生成一个随机用户科研画像。"""
        return UserProfile(
            user_id=user_id,
            interest_vector=self._rand_vec(),
            history_vector=self._rand_vec(),
            research_topics=["NLP", "Graph Learning"],
            kg_feature=None,       # 接知识图谱时填充
            community_feature=None,
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
                kg_node_id=f"kg_node_{i}",
            )
            for i in range(n)
        ]

    # ── 状态构建 ──────────────────────────────────────────────────

    def build_state(
        self,
        user: UserProfile,
        kg_feature: Optional[np.ndarray] = None,
        community_feature: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """
        将用户特征拼接为状态向量。
        state = concat(interest_vector, history_vector) -> state_dim
        知识图谱 / 社区特征预留插入接口。
        """
        half = self.state_dim // 2
        interest = user.interest_vector[:half]
        history  = user.history_vector[:half]

        state = np.concatenate([interest, history]).astype(np.float32)

        # ── 知识图谱特征插入接口（预留）─────────────────────────
        # if kg_feature is not None:
        #     state = np.concatenate([state, kg_feature])

        # ── 社区行为特征插入接口（预留）─────────────────────────
        # if community_feature is not None:
        #     state = np.concatenate([state, community_feature])

        return state

    # ── 辅助方法 ──────────────────────────────────────────────────

    def _rand_vec(self) -> np.ndarray:
        v = self.rng.standard_normal(self.state_dim).astype(np.float32)
        return v / (np.linalg.norm(v) + 1e-8)


# ── 数据库适配器接口（预留）─────────────────────────────────────────

class DatabaseAdapter:
    """
    真实数据库适配器基类。
    实现此接口后可无缝替换 MockDataGenerator。
    示例：MySQLAdapter(DatabaseAdapter)
    """

    def fetch_user(self, user_id: str) -> UserProfile:
        raise NotImplementedError

    def fetch_candidates(self, user_id: str, limit: int = 20) -> List[ResearchItem]:
        raise NotImplementedError

    def log_interaction(self, user_id: str, item_id: str, signal: Dict[str, Any]) -> None:
        raise NotImplementedError
