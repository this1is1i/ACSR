# recommender/ranker.py
# 强化学习排序模块 —— 使用 Actor-Critic Agent 对候选集进行打分排序

from __future__ import annotations
import numpy as np
import torch
from typing import List, Tuple, Optional
from dataclasses import dataclass

from recommender.candidate_generator import CandidateItem


@dataclass
class RankedItem:
    """排序结果条目。"""
    item: CandidateItem
    score: float
    rank: int


class RLRanker:
    """
    基于 Actor-Critic 的候选集排序器。

    设计思路：
      1. 将每个候选论文的 topic_vector 与当前用户状态拼接
      2. 调用 Actor 网络输出每个候选的推荐概率
      3. 按概率降序排列，取 Top-K

    此模块与 Agent 解耦：Agent 负责训练，Ranker 负责推理服务。
    """

    def __init__(self, agent, config):
        """
        Args:
            agent:  ActorCriticAgent 实例（已加载权重）
            config: Config 实例
        """
        self.agent = agent
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # ── 主排序接口 ────────────────────────────────────────────────

    def rank(
        self,
        user_state: np.ndarray,
        candidates: List[CandidateItem],
        k: Optional[int] = None,
    ) -> List[RankedItem]:
        """
        对候选集进行 Actor-Critic 排序。

        原理：
          对每个候选项，构造「用户状态 + 候选项特征」的拼接向量，
          计算 Actor 对该动作的评分（log 概率），降序排列后取 Top-K。

        Args:
            user_state: 用户 RL 状态向量 (state_dim,)
            candidates: 候选科研内容列表
            k:          返回数量（默认 config.top_k）

        Returns:
            按推荐分降序排列的 RankedItem 列表
        """
        k = k or self.config.top_k
        k = min(k, len(candidates))

        self.agent.actor.eval()
        scored: List[Tuple[float, CandidateItem]] = []

        with torch.no_grad():
            state_t = torch.FloatTensor(user_state).to(self.device)

            for item in candidates:
                # 计算用户兴趣与论文方向的余弦相似度作为 RL 分数
                if item.topic_vector is not None:
                    cos_sim = float(np.dot(user_state, item.topic_vector))
                    cos_sim = max(0.0, cos_sim)
                else:
                    cos_sim = 0.0

                # Actor 网络输出当前状态下各动作的概率
                probs = self.agent.actor(state_t)     # (action_num,)
                # 使用候选项索引对应的动作概率（若候选数 > action_num 则取余）
                action_idx = hash(item.item_id) % self.config.action_num
                actor_score = float(probs[action_idx].item())

                # 综合分 = Actor 分 * 0.6 + 语义相似度 * 0.4
                final_score = 0.6 * actor_score + 0.4 * cos_sim
                scored.append((final_score, item))

        self.agent.actor.train()

        # 降序排列，取 Top-K
        scored.sort(key=lambda x: -x[0])
        return [
            RankedItem(item=item, score=score, rank=rank + 1)
            for rank, (score, item) in enumerate(scored[:k])
        ]

    def recommend_top_k(
        self,
        user_state: np.ndarray,
        candidates: List[CandidateItem],
        k: int = 10,
    ) -> List[RankedItem]:
        """对外暴露的 Top-K 推荐接口（与 Agent 接口对称）。"""
        return self.rank(user_state, candidates, k)
