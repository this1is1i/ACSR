# agent.py
# Actor–Critic 智能体核心实现

from __future__ import annotations
import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.distributions import Categorical
from typing import Tuple, List, Optional, Dict, Any
import numpy as np

from config import Config, default_config
from models.actor import Actor
from models.critic import Critic


class ActorCriticAgent:
    """
    Actor–Critic 强化学习智能体。

    算法核心：
        TD 误差：  δ_t = r_t + γ·V(s_{t+1}) − V(s_t)
        Critic 损失：L_c = δ_t²
        Actor 损失：L_a = −log π(a_t|s_t) · δ_t − β·H(π)

    其中 H(π) 为策略熵，用于鼓励探索，防止推荐系统陷入信息茧房。
    """

    def __init__(self, config: Config = default_config):
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # 初始化网络
        self.actor = Actor(
            state_dim=config.state_dim,
            action_num=config.action_num,
            hidden_dim=config.actor_hidden,
        ).to(self.device)

        self.critic = Critic(
            state_dim=config.state_dim,
            hidden_dim=config.critic_hidden,
        ).to(self.device)

        # 优化器
        self.actor_optimizer  = optim.Adam(self.actor.parameters(),  lr=config.actor_lr)
        self.critic_optimizer = optim.Adam(self.critic.parameters(), lr=config.critic_lr)

        # 训练统计
        self.train_step: int = 0
        self.episode_count: int = 0

    # ── 核心接口 ──────────────────────────────────────────────────

    def select_action(
        self,
        state: np.ndarray,
        deterministic: bool = False,
    ) -> Tuple[int, torch.Tensor]:
        """
        根据当前策略选择动作。

        Args:
            state:         当前状态向量 (state_dim,)
            deterministic: 推理阶段置 True，返回概率最大的动作

        Returns:
            action:     选中动作的索引
            log_prob:   log π(a|s)，用于 Actor 损失计算
        """
        state_t = torch.FloatTensor(state).to(self.device)
        probs = self.actor(state_t)                  # (action_num,)
        dist  = Categorical(probs)

        if deterministic:
            action = torch.argmax(probs).item()
            log_prob = dist.log_prob(torch.tensor(action).to(self.device))
        else:
            action   = dist.sample()
            log_prob = dist.log_prob(action)
            action   = action.item()

        return int(action), log_prob

    def update(
        self,
        state:      np.ndarray,
        action:     int,
        reward:     float,
        next_state: np.ndarray,
        done:       bool,
        log_prob:   torch.Tensor,
    ) -> Dict[str, float]:
        """
        单步 Actor–Critic 更新。

        标准 TD(0) 更新规则：
            δ = r + γ·V(s') − V(s)
            L_critic = δ²
            L_actor  = −log π(a|s) · δ.detach() − α·H(π)

        Args:
            state:      当前状态
            action:     执行的动作
            reward:     即时奖励
            next_state: 下一状态
            done:       是否终止
            log_prob:   select_action 返回的 log_prob

        Returns:
            losses: 包含 actor_loss / critic_loss / td_error 的字典
        """
        s  = torch.FloatTensor(state).to(self.device)
        s_ = torch.FloatTensor(next_state).to(self.device)
        r  = torch.FloatTensor([reward]).to(self.device)
        mask = torch.FloatTensor([0.0 if done else 1.0]).to(self.device)

        # ── 计算 TD 误差 ──────────────────────────────────────────
        v_s  = self.critic(s).squeeze()
        with torch.no_grad():
            v_s_ = self.critic(s_).squeeze()
        td_target = r + self.config.gamma * v_s_ * mask
        td_error  = td_target - v_s            # δ

        # ── Critic 更新：最小化 δ² ────────────────────────────────
        critic_loss = td_error.pow(2)
        self.critic_optimizer.zero_grad()
        critic_loss.backward()
        nn.utils.clip_grad_norm_(self.critic.parameters(), max_norm=1.0)
        self.critic_optimizer.step()

        # ── Actor 更新：最大化 log π(a|s) · δ + 熵正则 ──────────
        # 重新计算当前策略的 log_prob 和熵（保留计算图）
        probs    = self.actor(s)
        dist     = Categorical(probs)
        log_prob_new = dist.log_prob(torch.tensor(action).to(self.device))
        entropy  = dist.entropy()

        actor_loss = -(log_prob_new * td_error.detach()
                       + self.config.entropy_coeff * entropy)
        self.actor_optimizer.zero_grad()
        actor_loss.backward()
        nn.utils.clip_grad_norm_(self.actor.parameters(), max_norm=1.0)
        self.actor_optimizer.step()

        self.train_step += 1
        return {
            "actor_loss":  float(actor_loss.item()),
            "critic_loss": float(critic_loss.item()),
            "td_error":    float(td_error.item()),
            "entropy":     float(entropy.item()),
            "v_s":         float(v_s.item()),
        }

    # ── Top-K 推荐 ────────────────────────────────────────────────

    def recommend_top_k(
        self,
        state: np.ndarray,
        k: Optional[int] = None,
        mask: Optional[np.ndarray] = None,
    ) -> Tuple[List[int], List[float]]:
        """
        返回 Top-K 推荐结果（推理接口，可对接 REST API）。

        Args:
            state: 当前用户状态
            k:     推荐数量，默认使用 config.top_k
            mask:  已推荐内容的掩码（可选），shape (action_num,)

        Returns:
            indices: Top-K 动作索引列表
            probs:   对应概率列表
        """
        k = k or self.config.top_k
        self.actor.eval()
        state_t = torch.FloatTensor(state).to(self.device)
        mask_t = (
            torch.BoolTensor(mask).to(self.device) if mask is not None else None
        )
        with torch.no_grad():
            indices, probs = self.actor.top_k_actions(state_t, k, mask_t)
        self.actor.train()
        return indices.cpu().tolist(), probs.cpu().tolist()

    # ── 模型持久化 ────────────────────────────────────────────────

    def save_model(self, path: Optional[str] = None) -> None:
        """保存 Actor 和 Critic 权重。"""
        path = path or self.config.model_save_path
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        torch.save(
            {
                "actor_state_dict":  self.actor.state_dict(),
                "critic_state_dict": self.critic.state_dict(),
                "train_step":        self.train_step,
                "episode_count":     self.episode_count,
                "config":            self.config,
            },
            path,
        )
        print(f"[Agent] 模型已保存至 {path}")

    def load_model(self, path: Optional[str] = None) -> None:
        """加载已保存的模型权重。"""
        path = path or self.config.model_save_path
        checkpoint = torch.load(path, map_location=self.device)
        self.actor.load_state_dict(checkpoint["actor_state_dict"])
        self.critic.load_state_dict(checkpoint["critic_state_dict"])
        self.train_step    = checkpoint.get("train_step", 0)
        self.episode_count = checkpoint.get("episode_count", 0)
        print(f"[Agent] 模型已从 {path} 加载，训练步数: {self.train_step}")

    # ── REST API 预测接口（预留）──────────────────────────────────

    def predict_for_api(self, user_state_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        为 Spring Boot REST API 提供预测接口（预留）。

        Args:
            user_state_dict: 包含 interest_vector / history_vector 的字典
                             （由后端序列化后传入）

        Returns:
            推荐结果字典，包含 item_indices / scores / explanation
        """
        # 从字典构建状态向量
        interest = np.array(user_state_dict.get("interest_vector", [0.0] * (self.config.state_dim // 2)))
        history  = np.array(user_state_dict.get("history_vector",  [0.0] * (self.config.state_dim // 2)))
        state = np.concatenate([interest, history]).astype(np.float32)

        indices, probs = self.recommend_top_k(state)
        return {
            "item_indices": indices,
            "scores":       probs,
            "explanation":  f"基于 Actor-Critic 算法，为您推荐 Top-{self.config.top_k} 科研内容",
        }

    # ── PPO 升级预留接口 ──────────────────────────────────────────

    def update_ppo(self, *args, **kwargs):
        """
        PPO（Proximal Policy Optimization）更新接口（预留）。
        未来替换 update() 方法时实现此函数。
        """
        raise NotImplementedError("PPO 更新接口待实现，当前使用 Actor-Critic")
