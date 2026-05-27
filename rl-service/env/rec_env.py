# env/rec_env.py
# 科研推荐强化学习环境 —— 支持真实数据 + 模拟回退

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

    数据来源优先级：
        训练：FeatureBuilder（MySQL 真实数据）→ MockDataGenerator（模拟回退）
        推理：由 RecommendationService 直接编排，不使用本环境

    知识图谱集成：
        当 config.use_kg=True 时，状态向量包含 KG 结构特征段。
    """

    def __init__(
        self,
        config: Config = default_config,
        reward_fn: Optional[BaseRewardFunction] = None,
        data_generator: Optional[MockDataGenerator] = None,
        kg_embedder=None,
        feature_builder=None,
        candidate_gen=None,
        user_ids: Optional[List[int]] = None,
    ):
        self.config = config
        self.reward_fn = reward_fn or WeightedRewardFunction(config.reward_weights)
        self.kg_embedder = kg_embedder
        self.feature_builder = feature_builder
        self.candidate_gen = candidate_gen
        self._user_ids = user_ids or []
        self._use_real_data = feature_builder is not None and candidate_gen is not None and len(self._user_ids) > 0

        # 模拟数据生成器（始终保留作为回退）
        self.data_gen = data_generator or MockDataGenerator(
            base_state_dim=config.base_state_dim,
            action_num=config.action_num,
            kg_dim=config.kg_embedding_dim if config.use_kg else 0,
        )

        if self._use_real_data:
            logger.info(
                f"训练环境使用真实数据: users={len(self._user_ids)}, "
                f"use_kg={config.use_kg}"
            )
        else:
            logger.info("训练环境使用模拟数据（MockDataGenerator）")

        # 环境内部状态
        self._user: Optional[UserProfile] = None
        self._candidates: List[ResearchItem] = []
        self._candidate_features: Optional[np.ndarray] = None  # (N, paper_feature_dim)
        self._current_state: Optional[np.ndarray] = None
        self._step_count: int = 0
        self._episode_reward: float = 0.0

    # ── 核心接口 ──────────────────────────────────────────────────

    def reset(self) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        重置环境，返回初始状态和候选论文特征。

        真实数据路径：从 MySQL 采样用户 → FeatureBuilder 构建状态 →
                     CandidateGenerator 生成候选 → 提取论文特征
        模拟数据路径：MockDataGenerator 生成随机用户和论文
        """
        if self._use_real_data:
            return self._reset_real()
        else:
            return self._reset_mock()

    def _reset_real(self) -> Tuple[np.ndarray, Dict[str, Any]]:
        """使用真实 MySQL 数据初始化 episode。"""
        # 随机采样一个真实用户
        user_id = str(int(np.random.choice(self._user_ids)))
        history: List[str] = []

        # 通过 FeatureBuilder 构建用户特征
        try:
            user_features = self.feature_builder.get_user_features(user_id, history)
            state = self.feature_builder.build_state(user_features)
            history = user_features.history_paper_ids
        except Exception as e:
            logger.warning(f"真实用户 {user_id} 特征构建失败: {e}，回退模拟")
            return self._reset_mock()

        # 通过 CandidateGenerator 生成候选集
        try:
            candidate_items = self.candidate_gen.generate(
                user_id=user_id,
                user_embedding=user_features.interest_vector,
                history=history,
                limit=min(self.config.action_num, 50),
                strategy="hybrid",
            )
        except Exception as e:
            logger.warning(f"候选生成失败: {e}，回退模拟")
            return self._reset_mock()

        if len(candidate_items) == 0:
            logger.warning("候选集为空，回退模拟")
            return self._reset_mock()

        # 转换为 ResearchItem（环境内部格式）
        self._candidates = [
            ResearchItem(
                item_id=item.item_id,
                title=item.title,
                topic_vector=item.topic_vector if item.topic_vector is not None
                else np.zeros(self.config.base_state_dim, dtype=np.float32),
                citation_count=item.citation_count,
                year=item.year,
                kg_node_id=item.kg_node_id,
            )
            for item in candidate_items
        ]

        # 构建候选论文特征矩阵
        paper_dim = self.config.paper_feature_dim
        self._candidate_features = np.array([
            item.topic_vector[:paper_dim] if item.topic_vector is not None
            else np.zeros(paper_dim, dtype=np.float32)
            for item in candidate_items
        ], dtype=np.float32)

        # 构建模拟 UserProfile（用于 _simulate_interaction 和 _transition）
        self._user = UserProfile(
            user_id=user_id,
            interest_vector=user_features.interest_vector,
            history_vector=user_features.history_vector,
            research_topics=user_features.research_topics,
            kg_feature=user_features.kg_vector,
            history_paper_ids=user_features.history_paper_ids,
        )

        self._current_state = state.astype(np.float32)
        self._step_count = 0
        self._episode_reward = 0.0

        return self._current_state.copy(), {
            "user_id": user_id,
            "num_candidates": len(self._candidates),
            "candidate_features": self._candidate_features,
            "kg_enabled": self.config.use_kg,
            "data_source": "mysql",
        }

    def _reset_mock(self) -> Tuple[np.ndarray, Dict[str, Any]]:
        """使用模拟数据初始化 episode（回退路径）。"""
        self._user = self.data_gen.generate_user(
            user_id=f"user_{np.random.randint(1000):04d}"
        )
        self._candidates = self.data_gen.generate_candidate_items()

        # 构建候选论文特征矩阵
        paper_dim = self.config.paper_feature_dim
        self._candidate_features = np.array([
            c.topic_vector[:paper_dim]
            for c in self._candidates
        ], dtype=np.float32)

        kg_feature = self._compute_user_kg_feature(self._user)
        self._current_state = self.data_gen.build_state(self._user, kg_feature=kg_feature)
        self._step_count = 0
        self._episode_reward = 0.0

        return self._current_state.copy(), {
            "user_id": self._user.user_id,
            "num_candidates": len(self._candidates),
            "candidate_features": self._candidate_features,
            "kg_enabled": self.config.use_kg,
            "data_source": "mock",
        }

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict[str, Any]]:
        """
        执行推荐动作，返回 (next_state, reward, done, info)。

        action 为候选列表索引（0 ~ N-1），N 为当前 episode 的候选数量。
        """
        N = len(self._candidates)
        assert 0 <= action < N, f"非法 action: {action}，候选数={N}"
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
        """计算选中论文与用户 KG 上下文的拓扑相关度奖励。"""
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
        """模拟用户与推荐内容的交互（训练时使用，推理时不经过此路径）。"""
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
