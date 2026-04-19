# models/critic.py
# Critic 网络：估计状态价值函数 V(s)

from __future__ import annotations
import torch
import torch.nn as nn


class Critic(nn.Module):
    """
    Critic 网络（价值网络）V(s; w)

    输入：状态向量 s ∈ R^{state_dim}
    输出：标量状态价值 V(s) ∈ R

    网络结构：
        Linear(state_dim → hidden) → ReLU → LayerNorm
        Linear(hidden → hidden)    → ReLU → LayerNorm
        Linear(hidden → 1)
    """

    def __init__(
        self,
        state_dim: int,
        hidden_dim: int = 128,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.state_dim = state_dim

        self.net = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
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
                nn.init.orthogonal_(m.weight)
                nn.init.zeros_(m.bias)

    def forward(self, state: torch.Tensor) -> torch.Tensor:
        """
        Args:
            state: (batch, state_dim) 或 (state_dim,)

        Returns:
            value: (batch, 1) 或 (1,) 状态价值估计
        """
        return self.net(state)
