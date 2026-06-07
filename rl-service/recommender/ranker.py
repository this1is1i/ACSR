# recommender/ranker.py
# 强化学习排序模块 —— 使用 Actor-Critic Agent 对候选集进行逐论文打分排序
#
# 排序流程:
#   1. 为每篇候选论文计算三项原始得分（Actor 策略分 / 语义相似度 / KG 拓扑分）
#   2. 质量门控: 滤除三项得分均低于阈值的论文（防止归一化"救活"垃圾论文）
#   3. 对通过门控的论文，逐项做 min-max 归一化，消除量级差异
#   4. 加权求和 → 降序排列 → 返回 Top-K
#
# 为什么需要归一化: Actor softmax 输出被压缩在 ~0.02(均值) 附近，而余弦相似度
# 可达 0.7~0.8，原始量级差距让 Actor 实际影响力不足 10%。
# 归一化后三项在 [0,1] 区间公平竞争，名义权重 = 实际影响力。

from __future__ import annotations
import logging
import numpy as np
import torch
from typing import List, Tuple, Optional
from dataclasses import dataclass

from recommender.candidate_generator import CandidateItem

logger = logging.getLogger(__name__)


@dataclass
class RankedItem:
    """排序结果条目。"""
    item: CandidateItem
    score: float
    rank: int


class RLRanker:
    """
    基于 Actor-Critic 的候选集排序器。

    Actor 逐论文打分 → 质量门控 → 三项 min-max 归一化 → 加权求和。

    综合分 = 0.5 × norm(Actor) + 0.3 × norm(cos_sim) + 0.2 × norm(kg_score)
    （无 KG 时: 0.6 × norm(Actor) + 0.4 × norm(cos_sim)）
    """

    def __init__(self, agent, config, kg_embedder=None):
        self.agent = agent
        self.config = config
        self.kg_embedder = kg_embedder
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # ── 辅助: min-max 归一化 ──────────────────────────────────────

    @staticmethod
    def _minmax_normalize(values: np.ndarray) -> np.ndarray:
        """将数组归一化到 [0, 1]。若全等则返回 0.5（中性分）。"""
        vmin, vmax = values.min(), values.max()
        if vmax - vmin < 1e-12:
            return np.full_like(values, 0.5, dtype=np.float32)
        return (values - vmin) / (vmax - vmin)

    # ── 主排序接口 ────────────────────────────────────────────────

    def rank(
        self,
        user_state: np.ndarray,
        candidates: List[CandidateItem],
        k: Optional[int] = None,
        user_history: Optional[List[str]] = None,
    ) -> List[RankedItem]:
        """
        对候选集进行 Actor-Critic + KG 排序（含质量门控 + 归一化）。

        Args:
            user_state:   用户 RL 状态向量 (state_dim,)
            candidates:   候选科研内容列表
            k:            返回数量
            user_history: 用户历史论文 ID（用于 KG 相关度计算）
        """
        k = k or self.config.top_k
        k = min(k, len(candidates))
        N = len(candidates)

        if N == 0:
            return []

        self.agent.actor.eval()

        # ── 第一步: 计算三项原始得分 ─────────────────────────────
        base_state = user_state[:self.config.base_state_dim]

        # 构建论文特征矩阵
        paper_dim = self.config.paper_feature_dim
        candidate_features = np.zeros((N, paper_dim), dtype=np.float32)
        for i, item in enumerate(candidates):
            if item.topic_vector is not None:
                candidate_features[i] = item.topic_vector[:paper_dim]

        # 余弦相似度 (N,)
        topic_matrix = np.array([
            item.topic_vector if item.topic_vector is not None
            else np.zeros(self.config.base_state_dim, dtype=np.float32)
            for item in candidates
        ])
        cos_sims = np.clip(np.dot(topic_matrix, base_state), 0.0, None)

        # KG 用户向量
        user_kg = None
        if self.kg_embedder is not None and user_history:
            user_kg = self.kg_embedder.get_user_kg_embedding(user_history)

        # Actor 概率 + KG 分数
        kg_scores = np.zeros(N, dtype=np.float32)
        with torch.no_grad():
            state_t = torch.FloatTensor(user_state).to(self.device)
            feat_t = torch.FloatTensor(candidate_features).to(self.device)
            actor_probs = self.agent.actor.score_candidates(state_t, feat_t)

        actor_scores = actor_probs.cpu().numpy().astype(np.float32)

        for i, item in enumerate(candidates):
            if user_kg is not None:
                paper_emb = self.kg_embedder.get_paper_embedding(item.kg_node_id)
                if paper_emb is not None:
                    kg_scores[i] = float(np.clip(np.dot(user_kg, paper_emb), 0.0, 1.0))

        self.agent.actor.train()

        # ── 第二步: 质量门控 ─────────────────────────────────────
        min_cos = getattr(self.config, "min_cos_similarity", 0.05)
        min_act = getattr(self.config, "min_actor_score", 0.001)

        use_kg = self.kg_embedder is not None
        passed_mask = (cos_sims >= min_cos) | (actor_scores >= min_act)
        if use_kg:
            min_kg = getattr(self.config, "min_kg_score", 0.0)
            passed_mask = passed_mask | (kg_scores >= min_kg)

        passed_indices = np.where(passed_mask)[0]

        if len(passed_indices) == 0:
            logger.warning(
                f"质量门控后无候选通过 (N={N}, "
                f"cos_max={cos_sims.max():.3f}, actor_max={actor_scores.max():.4f})，"
                f"回退全量归一化"
            )
            passed_indices = np.arange(N)
        elif len(passed_indices) < N:
            logger.debug(
                f"质量门控: {len(passed_indices)}/{N} 篇通过 "
                f"(cos≥{min_cos} or actor≥{min_act})"
            )

        # ── 第三步: 逐项 min-max 归一化 ──────────────────────────
        actor_norm = self._minmax_normalize(actor_scores[passed_indices])
        cos_norm   = self._minmax_normalize(cos_sims[passed_indices])
        kg_norm    = self._minmax_normalize(kg_scores[passed_indices]) if use_kg else None

        # ── 第四步: 加权求和 ─────────────────────────────────────
        if use_kg:
            final_scores = 0.5 * actor_norm + 0.3 * cos_norm + 0.2 * kg_norm
        else:
            final_scores = 0.6 * actor_norm + 0.4 * cos_norm

        # ── 第五步: 排序返回 Top-K ───────────────────────────────
        order = np.argsort(-final_scores)  # 降序
        top_k_order = order[:k]

        return [
            RankedItem(
                item=candidates[passed_indices[idx]],
                score=float(final_scores[idx]),
                rank=rank + 1,
            )
            for rank, idx in enumerate(top_k_order)
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
