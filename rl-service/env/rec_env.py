# env/rec_env.py
# 科研推荐强化学习环境

from __future__ import annotations
import numpy as np
import logging
from typing import Tuple, Dict, Any, Optional, List

from config import Config, default_config
from data.mock_data import MockDataGenerator, UserProfile, ResearchItem
from utils.reward import WeightedRewardFunction, InteractionSignal, BaseRewardFunction

logger = logging.getLogger(__name__)


class ResearchRecEnv:
    """
    科研推荐强化学习环境。

    遵循 OpenAI Gym 风格接口：
        state, info = env.reset()
        next_state, reward, done, info = env.step(action)

    知识图谱集成：
        当 config.use_kg=True 时，状态向量包含 KG 结构特征段，
        反映用户在学术知识网络中的位置、引用拓扑和主题连通性。
    """

    def __init__(
        self,
        config: Config = default_config,
        reward_fn: Optional[BaseRewardFunction] = None,
        data_generator: Optional[MockDataGenerator] = None,
        kg_embedder=None,
    ):
        self.config = config
        self.reward_fn = reward_fn or WeightedRewardFunction(config.reward_weights)
        self.data_gen = data_generator or MockDataGenerator(
            base_state_dim=config.base_state_dim,
            action_num=config.action_num,
            kg_dim=config.kg_embedding_dim if config.use_kg else 0,
        )
        self.kg_embedder = kg_embedder

        # 环境内部状态
        self._user: Optional[UserProfile] = None
        self._candidates: List[ResearchItem] = []
        self._current_state: Optional[np.ndarray] = None
        self._step_count: int = 0
        self._episode_reward: float = 0.0

    # ── 核心接口 ──────────────────────────────────────────────────

    def reset(self) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        重置环境，返回初始状态。
        若启用 KG，状态包含知识图谱结构特征段。
        """
        self._user = self.data_gen.generate_user(
            user_id=f"user_{np.random.randint(1000):04d}"
        )
        self._candidates = self.data_gen.generate_candidate_items()

        # 计算 KG 特征并注入状态
        kg_feature = self._compute_user_kg_feature(self._user)
        self._current_state = self.data_gen.build_state(self._user, kg_feature=kg_feature)
        self._step_count = 0
        self._episode_reward = 0.0

        info = {
            "user_id": self._user.user_id,
            "num_candidates": len(self._candidates),
            "kg_enabled": self.config.use_kg,
        }
        return self._current_state.copy(), info

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict[str, Any]]:
        """
        执行推荐动作，返回 (next_state, reward, done, info)。
        """
        assert 0 <= action < self.config.action_num, f"非法 action: {action}"
        assert self._current_state is not None, "请先调用 reset()"

        selected_item = self._candidates[action]

        # ── 模拟用户交互信号 ──────────────────────────────────────
        signal = self._simulate_interaction(selected_item)

        # ── 计算奖励（含 KG 拓扑相关度）──────────────────────────
        if self.config.use_kg and self.kg_embedder is not None:
            kg_bonus = self._compute_kg_reward(selected_item)
            signal = InteractionSignal(
                click=signal.click,
                favorite=signal.favorite,
                read_time=signal.read_time,
                topic_match=signal.topic_match,
                long_term_value=signal.long_term_value,
                kg_topology_score=kg_bonus,
            )

        reward = self.reward_fn.compute(signal)
        self._episode_reward += reward

        # ── 状态转移 ──────────────────────────────────────────────
        next_state = self._transition(selected_item)
        self._current_state = next_state

        # ── 终止条件 ──────────────────────────────────────────────
        self._step_count += 1
        done = self._step_count >= self.config.max_steps

        info = {
            "step": self._step_count,
            "action": action,
            "item_id": selected_item.item_id,
            "signal": signal,
            "episode_reward": self._episode_reward,
        }
        return next_state.copy(), float(reward), done, info

    # ── 知识图谱集成 ──────────────────────────────────────────────

    def _compute_user_kg_feature(self, user: UserProfile) -> Optional[np.ndarray]:
        """基于用户历史论文计算 KG embedding。"""
        if not self.config.use_kg or self.kg_embedder is None:
            return None
        return self.kg_embedder.get_user_kg_embedding(user.history_paper_ids)

    def _compute_kg_reward(self, item: ResearchItem) -> float:
        """
        计算选中论文与用户 KG 上下文的拓扑相关度奖励。

        考量因素：
        - 与用户历史论文在引用网络上的接近度
        - 与用户偏好关键词群落的重叠度
        """
        if self.kg_embedder is None or self._user is None:
            return 0.0
        paper_emb = self.kg_embedder.get_paper_embedding(item.kg_node_id)
        if paper_emb is None:
            return 0.0
        user_kg = self.kg_embedder.get_user_kg_embedding(self._user.history_paper_ids)
        sim = float(np.dot(user_kg, paper_emb))
        return float(np.clip(sim, 0.0, 1.0))

    # ── 内部辅助方法 ──────────────────────────────────────────────

    def _simulate_interaction(self, item: ResearchItem) -> InteractionSignal:
        """模拟用户与推荐内容的交互。"""
        assert self._user is not None
        cos_sim = float(np.dot(self._user.interest_vector, item.topic_vector))
        cos_sim = max(0.0, cos_sim)

        rng = np.random
        return InteractionSignal(
            click=float(rng.random() < 0.3 + 0.5 * cos_sim),
            favorite=float(rng.random() < 0.1 + 0.3 * cos_sim),
            read_time=float(np.clip(rng.normal(cos_sim, 0.1), 0, 1)),
            topic_match=cos_sim,
            long_term_value=float(np.clip(
                item.citation_count / 500.0 * cos_sim, 0, 1
            )),
        )

    def _transition(self, item: ResearchItem) -> np.ndarray:
        """
        状态转移：
        - interest 部分（前 half）保持不变
        - history 部分（half:base_state_dim）平滑更新
        - KG 部分（base_state_dim:）基于选中论文的 KG 邻域更新
        """
        assert self._current_state is not None
        half = self.config.base_state_dim // 2
        new_state = self._current_state.copy()

        # 历史向量平滑更新
        new_state[half:half * 2] = (
            0.9 * new_state[half:half * 2] + 0.1 * item.topic_vector[:half]
        )

        # KG 部分：向选中论文的 KG embedding 漂移
        if self.config.use_kg and self.kg_embedder is not None:
            paper_emb = self.kg_embedder.get_paper_embedding(item.kg_node_id)
            if paper_emb is not None:
                kg_start = self.config.base_state_dim
                kg_end = kg_start + self.config.kg_embedding_dim
                new_state[kg_start:kg_end] = (
                    0.8 * new_state[kg_start:kg_end] + 0.2 * paper_emb
                )

        # 归一化
        norm = np.linalg.norm(new_state) + 1e-8
        return (new_state / norm).astype(np.float32)
