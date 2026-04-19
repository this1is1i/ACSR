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
    kg_vector: Optional[np.ndarray] = None       # 知识图谱特征（预留）
    community_vector: Optional[np.ndarray] = None  # 社区行为特征（预留）
    research_topics: List[str] = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)


class FeatureBuilder:
    """
    特征构建器 —— 将用户画像转换为 RL 状态向量。

    当前实现使用随机 embedding，预留以下真实数据接入口：
      - AMiner 学术知识图谱 embedding
      - 用户行为日志（点击、收藏、阅读时长）
      - 知识图谱 GNN 编码
      - 社区协同过滤特征
    """

    def __init__(self, state_dim: int = 64, seed: int = 42):
        self.state_dim = state_dim
        self.half = state_dim // 2
        self.rng = np.random.default_rng(seed)

    # ── 主接口 ────────────────────────────────────────────────────

    def build_state(self, features: UserFeatures) -> np.ndarray:
        """
        将用户特征拼接为 RL 状态向量。

        state = concat(interest[:half], history[:half])  → (state_dim,)

        知识图谱 / 社区特征插入点已标注，启用时调整 state_dim。
        """
        interest = features.interest_vector[:self.half]
        history  = features.history_vector[:self.half]
        parts = [interest, history]

        # ── 知识图谱特征（预留）──────────────────────────────────
        # if features.kg_vector is not None:
        #     parts.append(features.kg_vector[:KG_DIM])

        # ── 社区行为特征（预留）──────────────────────────────────
        # if features.community_vector is not None:
        #     parts.append(features.community_vector[:COMM_DIM])

        state = np.concatenate(parts).astype(np.float32)
        norm = np.linalg.norm(state) + 1e-8
        return state / norm

    def build_item_vector(self, item_meta: Dict[str, Any]) -> np.ndarray:
        """
        构建科研内容（论文）的特征向量。

        生产环境接入：
          - 论文 BERT/SciBERT 摘要 embedding
          - 引用网络 Graph embedding
          - 知识图谱节点 embedding
        """
        # 当前使用 item_id 哈希作为伪 embedding，保证同一论文向量一致
        seed = hash(str(item_meta.get("item_id", "unknown"))) % (2**31)
        rng = np.random.default_rng(seed)
        v = rng.standard_normal(self.state_dim).astype(np.float32)
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
        # 使用 user_id 哈希生成确定性伪 embedding
        seed = hash(user_id) % (2**31)
        rng = np.random.default_rng(seed)

        interest = rng.standard_normal(self.state_dim).astype(np.float32)
        interest /= np.linalg.norm(interest) + 1e-8

        history_vec = np.zeros(self.state_dim, dtype=np.float32)
        if history:
            # 历史论文 embedding 均值池化
            vecs = [self.build_item_vector({"item_id": h}) for h in history]
            history_vec = np.mean(vecs, axis=0).astype(np.float32)

        return UserFeatures(
            user_id=user_id,
            interest_vector=interest,
            history_vector=history_vec,
            research_topics=["NLP", "Graph Learning"],  # 生产环境从数据库读取
        )

    # ── AMiner 接入预留 ───────────────────────────────────────────

    def load_aminer_embedding(self, scholar_id: str) -> Optional[np.ndarray]:
        """
        从 AMiner 数据集加载学者 embedding（预留接口）。

        接入方式：
          1. 下载 AMiner 公开数据集（https://www.aminer.org/data）
          2. 使用 TransE / GAT 训练知识图谱 embedding
          3. 按 scholar_id 索引返回向量
        """
        raise NotImplementedError("AMiner embedding 接口待实现")

    def load_kg_embedding(self, entity_id: str) -> Optional[np.ndarray]:
        """知识图谱实体 embedding 加载接口（预留）。"""
        raise NotImplementedError("知识图谱 embedding 接口待实现")
