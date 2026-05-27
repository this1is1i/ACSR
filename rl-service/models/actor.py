# models/actor.py
# Actor 网络：逐论文打分（pairwise scoring）

from __future__ import annotations
import torch
import torch.nn as nn
import torch.nn.functional as F


class Actor(nn.Module):
    """
    Actor 网络（策略网络）π(a|s, p; θ)

    输入：用户状态 s ∈ R^{state_dim} + 论文特征 p ∈ R^{paper_feature_dim}
    输出：单篇论文的 logit，对 N 篇候选 softmax 后得到概率分布

    网络结构：
        Linear(state_dim + paper_feature_dim → hidden) → ReLU → LayerNorm
        Linear(hidden → hidden)                      → ReLU → LayerNorm
        Linear(hidden → 1)
    """

    def __init__(
        self,
        state_dim: int,
        paper_feature_dim: int,
        hidden_dim: int = 128,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.state_dim = state_dim
        self.paper_feature_dim = paper_feature_dim
        input_dim = state_dim + paper_feature_dim

        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.LayerNorm(hidden_dim),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.LayerNorm(hidden_dim),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
        )

        self._init_weights()

    def _init_weights(self) -> None:
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.orthogonal_(m.weight, gain=0.01)
                nn.init.zeros_(m.bias)

    def forward(self, state: torch.Tensor, paper_features: torch.Tensor) -> torch.Tensor:
        """
        Args:
            state:           (batch, state_dim)
            paper_features:  (batch, paper_feature_dim)

        Returns:
            logits: (batch, 1) 每篇论文的原始分数
        """
        x = torch.cat([state, paper_features], dim=-1)
        return self.net(x)

    def score_candidates(
        self,
        state: torch.Tensor,
        candidate_features: torch.Tensor,
    ) -> torch.Tensor:
        """
        对候选论文批量打分，返回概率分布。

        Args:
            state:              (state_dim,) 用户状态
            candidate_features: (N, paper_feature_dim) N 篇候选论文的特征

        Returns:
            probs: (N,) 归一化概率分布
        """
        N = candidate_features.shape[0]
        state_batch = state.unsqueeze(0).expand(N, -1)
        logits = self.forward(state_batch, candidate_features).squeeze(-1)
        return F.softmax(logits, dim=-1)
