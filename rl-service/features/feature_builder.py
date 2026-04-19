# features/feature_builder.py
# 特征构建模块 —— 将用户原始数据转换为强化学习状态向量

from __future__ import annotations
import numpy as np
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class UserFeatures:
    """用户特征容器，统一封装所有特征来源。"""
    user_id: str
    interest_vector: np.ndarray          # 科研兴趣 embedding
    history_vector: np.ndarray           # 历史行为 embedding
    kg_vector: Optional[np.ndarray] = None       # 知识图谱结构特征
    community_vector: Optional[np.ndarray] = None  # 社区行为特征（预留）
    research_topics: List[str] = field(default_factory=list)
    history_paper_ids: List[str] = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)


class FeatureBuilder:
    """
    特征构建器 —— 将用户画像转换为 RL 状态向量。

    状态结构（use_kg=True 时）：
        state = concat(interest[:half], history[:half], kg_vector[:kg_dim])
              = (32 + 32 + 32) = 96 维

    状态结构（use_kg=False 时）：
        state = concat(interest[:half], history[:half])
              = (32 + 32) = 64 维
    """

    def __init__(
        self,
        base_state_dim: int = 64,
        kg_dim: int = 0,
        kg_embedder: Any = None,
        seed: int = 42,
    ):
        self.base_state_dim = base_state_dim
        self.half = base_state_dim // 2   # interest / history 各占一半
        self.kg_dim = kg_dim
        self.kg_embedder = kg_embedder
        self.state_dim = base_state_dim + kg_dim
        self.rng = np.random.default_rng(seed)

    # ── 主接口 ────────────────────────────────────────────────────

    def build_state(self, features: UserFeatures) -> np.ndarray:
        """
        将用户特征拼接为 RL 状态向量。

        state = concat(interest[:half], history[:half], [kg_vector])
        """
        interest = features.interest_vector[:self.half]
        history  = features.history_vector[:self.half]
        parts = [interest, history]

        # ── 知识图谱特征 ──────────────────────────────────────────
        if self.kg_dim > 0:
            if features.kg_vector is not None:
                parts.append(features.kg_vector[:self.kg_dim])
            else:
                parts.append(np.zeros(self.kg_dim, dtype=np.float32))

        state = np.concatenate(parts).astype(np.float32)
        norm = np.linalg.norm(state) + 1e-8
        return state / norm

    def build_item_vector(self, item_meta: Dict[str, Any]) -> np.ndarray:
        """
        构建科研内容（论文）的特征向量（base_state_dim 维）。

        注意：item 向量维度固定为 base_state_dim，不包含 KG 部分。
        KG 信息通过 state 中的 kg_vector 段传入 Actor/Critic。
        """
        seed = hash(str(item_meta.get("item_id", "unknown"))) % (2**31)
        rng = np.random.default_rng(seed)
        v = rng.standard_normal(self.base_state_dim).astype(np.float32)
        return v / (np.linalg.norm(v) + 1e-8)

    # ── 用户特征获取 ──────────────────────────────────────────────

    def get_user_features(
        self,
        user_id: str,
        history: Optional[List[str]] = None,
    ) -> UserFeatures:
        """
        获取并构建用户特征。

        生产环境替换：
          - 从 MySQL 查询用户画像
          - 从 Redis 获取近期行为序列
          - 调用 AMiner API 获取学者主页信息
        """
        seed = hash(user_id) % (2**31)
        rng = np.random.default_rng(seed)

        interest = rng.standard_normal(self.base_state_dim).astype(np.float32)
        interest /= np.linalg.norm(interest) + 1e-8

        history_vec = np.zeros(self.base_state_dim, dtype=np.float32)
        if history:
            vecs = [self.build_item_vector({"item_id": h}) for h in history]
            history_vec = np.mean(vecs, axis=0).astype(np.float32)

        return UserFeatures(
            user_id=user_id,
            interest_vector=interest,
            history_vector=history_vec,
            kg_vector=self._compute_kg_vector(history),
            research_topics=["NLP", "Graph Learning"],
            history_paper_ids=list(history or []),
        )

    def _compute_kg_vector(self, history: Optional[List[str]]) -> Optional[np.ndarray]:
        """利用 KG Embedder 计算用户的知识图谱特征向量。"""
        if self.kg_embedder is None or self.kg_dim == 0:
            return None
        if not history:
            return np.zeros(self.kg_dim, dtype=np.float32)
        return self.kg_embedder.get_user_kg_embedding(history)
