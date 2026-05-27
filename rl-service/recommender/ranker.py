# recommender/ranker.py
# 强化学习排序模块 —— 使用 Actor-Critic Agent 对候选集进行逐论文打分排序

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

    Actor 逐论文打分：对每篇候选论文，拼接 [user_state | paper_features]，
    输出单篇 logit，softmax 后得到每篇论文的概率。

    综合分 = Actor 策略分 * 0.5 + 语义相似度 * 0.3 + KG 拓扑分 * 0.2

    当 KG 未启用时，退化为 Actor * 0.6 + 语义 * 0.4。
    """

    def __init__(self, agent, config, kg_embedder=None):
        self.agent = agent
        self.config = config
        self.kg_embedder = kg_embedder
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # ── 主排序接口 ────────────────────────────────────────────────

    def rank(
        self,
        user_state: np.ndarray,
        candidates: List[CandidateItem],
        k: Optional[int] = None,
        user_history: Optional[List[str]] = None,
    ) -> List[RankedItem]:
        """
        对候选集进行 Actor-Critic + KG 排序。

        Args:
            user_state:   用户 RL 状态向量 (state_dim,)
            candidates:   候选科研内容列表
            k:            返回数量
            user_history: 用户历史论文 ID（用于 KG 相关度计算）
        """
        k = k or self.config.top_k
        k = min(k, len(candidates))

        self.agent.actor.eval()
        scored: List[Tuple[float, CandidateItem]] = []

        # 用 base_state_dim 部分计算语义相似度
        base_state = user_state[:self.config.base_state_dim]

        N = len(candidates)

        # ── 构建候选论文特征矩阵 ──────────────────────────────────
        paper_dim = self.config.paper_feature_dim
        candidate_features = np.zeros((N, paper_dim), dtype=np.float32)
        for i, item in enumerate(candidates):
            if item.topic_vector is not None:
                candidate_features[i] = item.topic_vector[:paper_dim]

        # ── 余弦相似度向量化（一次矩阵点积替代逐论文循环）────────
        topic_matrix = np.array([
            item.topic_vector if item.topic_vector is not None
            else np.zeros(self.config.base_state_dim, dtype=np.float32)
            for item in candidates
        ])
        cos_sims = np.clip(np.dot(topic_matrix, base_state), 0.0, None)  # (N,)

        # ── KG 用户向量只算一次（之前循环内重复计算）──────────────
        user_kg = None
        if self.kg_embedder is not None and user_history:
            user_kg = self.kg_embedder.get_user_kg_embedding(user_history)

        with torch.no_grad():
            state_t = torch.FloatTensor(user_state).to(self.device)
            feat_t = torch.FloatTensor(candidate_features).to(self.device)

            # Actor 逐论文打分 → (N,) 概率分布
            actor_probs = self.agent.actor.score_candidates(state_t, feat_t)

            for i, item in enumerate(candidates):
                # 语义相似度（已向量化）
                cos_sim = float(cos_sims[i])

                # Actor 策略分 — 该论文的独立概率
                actor_score = float(actor_probs[i].item())

                # KG 拓扑分
                kg_score = 0.0
                if user_kg is not None:
                    paper_emb = self.kg_embedder.get_paper_embedding(item.kg_node_id)
                    if paper_emb is not None:
                        kg_score = float(np.clip(np.dot(user_kg, paper_emb), 0.0, 1.0))

                # 综合分
                if self.kg_embedder is not None:
                    final_score = 0.5 * actor_score + 0.3 * cos_sim + 0.2 * kg_score
                else:
                    final_score = 0.6 * actor_score + 0.4 * cos_sim

                scored.append((final_score, item))

        self.agent.actor.train()

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
        user_history: Optional[List[str]] = None,
    ) -> List[RankedItem]:
        """对外暴露的 Top-K 推荐接口。"""
        return self.rank(user_state, candidates, k, user_history)
