# models/actor.py
# Actor 网络：输出动作概率分布

from __future__ import annotations
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional


class Actor(nn.Module):
    """
    Actor 网络（策略网络）π(a|s; θ)

    输入：状态向量 s ∈ R^{state_dim}
    输出：在 N 个候选动作上的概率分布 p ∈ Δ^N

    网络结构：
        Linear(state_dim → hidden) → ReLU → LayerNorm
        Linear(hidden → hidden)    → ReLU → LayerNorm
        Linear(hidden → action_num) → Softmax
    """

    def __init__(
        self,
        state_dim: int,
        action_num: int,
        hidden_dim: int = 128,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.state_dim = state_dim
        self.action_num = action_num

        self.net = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.LayerNorm(hidden_dim),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.LayerNorm(hidden_dim),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, action_num),
        )

        self._init_weights()

    def _init_weights(self) -> None:
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.orthogonal_(m.weight, gain=0.01)
                nn.init.zeros_(m.bias)

    def forward(self, state: torch.Tensor) -> torch.Tensor:
        """
        Args:
            state: (batch, state_dim) 或 (state_dim,)

        Returns:
            probs: (batch, action_num) 动作概率分布
        """
        logits = self.net(state)
        return F.softmax(logits, dim=-1)

    # ── Top-K 推荐接口 ────────────────────────────────────────────

    def top_k_actions(
        self,
        state: torch.Tensor,
        k: int,
        mask: Optional[torch.Tensor] = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """
        返回概率最高的 Top-K 动作及其概率。

        Args:
            state: (state_dim,) 当前状态
            k:     返回数量
            mask:  (action_num,) 可选掩码，屏蔽已推荐过的动作

        Returns:
            top_k_indices: (k,)   动作索引
            top_k_probs:   (k,)   对应概率
        """
        with torch.no_grad():
            logits = self.net(state.unsqueeze(0)).squeeze(0)  # (action_num,)
            if mask is not None:
                logits = logits.masked_fill(mask.bool(), float("-inf"))
            probs = F.softmax(logits, dim=-1)
            top_k_probs, top_k_indices = torch.topk(probs, k)
        return top_k_indices, top_k_probs

    # ── 知识图谱 embedding 融合接口（预留）───────────────────────

    def forward_with_kg(
        self,
        state: torch.Tensor,
        kg_embedding: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        将知识图谱 embedding 拼接到状态后再推断（预留接口）。
        使用时需同步调整 state_dim。
        """
        if kg_embedding is not None:
            state = torch.cat([state, kg_embedding], dim=-1)
        return self.forward(state)
