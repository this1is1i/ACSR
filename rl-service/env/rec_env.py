# env/rec_env.py
# 科研推荐强化学习环境

from __future__ import annotations
import numpy as np
from typing import Tuple, Dict, Any, Optional, List

from config import Config, default_config
from data.mock_data import MockDataGenerator, UserProfile, ResearchItem
from utils.reward import WeightedRewardFunction, InteractionSignal, BaseRewardFunction


class ResearchRecEnv:
    """
    科研推荐强化学习环境。

    遵循 OpenAI Gym 风格接口：
        state, info = env.reset()
        next_state, reward, done, info = env.step(action)

    生产环境替换：
        将 MockDataGenerator 替换为 DatabaseAdapter 子类即可，
        其余 RL 逻辑无需修改。
    """

    def __init__(
        self,
        config: Config = default_config,
        reward_fn: Optional[BaseRewardFunction] = None,
        data_generator: Optional[MockDataGenerator] = None,
    ):
        self.config = config
        self.reward_fn = reward_fn or WeightedRewardFunction(config.reward_weights)
        self.data_gen = data_generator or MockDataGenerator(
            state_dim=config.state_dim,
            action_num=config.action_num,
        )

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
        生产环境：从数据库随机抽取一个用户及其候选集。
        """
        self._user = self.data_gen.generate_user(
            user_id=f"user_{np.random.randint(1000):04d}"
        )
        self._candidates = self.data_gen.generate_candidate_items()
        self._current_state = self.data_gen.build_state(self._user)
        self._step_count = 0
        self._episode_reward = 0.0

        info = {
            "user_id": self._user.user_id,
            "num_candidates": len(self._candidates),
        }
        return self._current_state.copy(), info

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict[str, Any]]:
        """
        执行推荐动作，返回 (next_state, reward, done, info)。

        Args:
            action: 选中的候选内容索引（离散动作）

        Returns:
            next_state: 下一时刻状态向量
            reward:     即时奖励
            done:       是否终止
            info:       调试信息字典
        """
        assert 0 <= action < self.config.action_num, f"非法 action: {action}"
        assert self._current_state is not None, "请先调用 reset()"

        selected_item = self._candidates[action]

        # ── 模拟用户交互信号 ──────────────────────────────────────
        signal = self._simulate_interaction(selected_item)

        # ── 计算奖励 ──────────────────────────────────────────────
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

    # ── 知识图谱特征插入接口（预留）──────────────────────────────

    def inject_kg_features(self, kg_embeddings: np.ndarray) -> None:
        """
        向当前状态注入知识图谱 embedding（预留接口）。
        调用时机：reset() 之后、第一次 step() 之前。

        Args:
            kg_embeddings: shape (action_num, kg_embedding_dim)
        """
        # TODO: 将 kg_embeddings 拼接到候选项的 topic_vector 中
        raise NotImplementedError("知识图谱特征注入接口待实现")

    # ── 推荐理由生成接口（预留）──────────────────────────────────

    def generate_explanation(self, action: int) -> str:
        """
        为推荐结果生成自然语言解释（预留接口）。
        可对接 LLM（GPT / ChatGLM）或模板引擎。
        """
        if not self._candidates:
            return "暂无推荐理由"
        item = self._candidates[action]
        return (
            f"推荐《{item.title}》的原因：该论文与您的研究方向高度相关，"
            f"发表于 {item.year} 年，被引 {item.citation_count} 次，"
            f"知识图谱节点 ID: {item.kg_node_id}。"
        )

    # ── 内部辅助方法 ──────────────────────────────────────────────

    def _simulate_interaction(self, item: ResearchItem) -> InteractionSignal:
        """
        模拟用户与推荐内容的交互（生产环境替换为真实行为日志）。
        """
        assert self._user is not None
        # 计算用户兴趣与内容的余弦相似度作为基础匹配分
        cos_sim = float(np.dot(self._user.interest_vector, item.topic_vector))
        cos_sim = max(0.0, cos_sim)  # 截断负值

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
        状态转移：用选中内容的 topic_vector 轻微更新用户历史向量。
        模拟用户兴趣随交互逐渐漂移的过程。
        """
        assert self._current_state is not None
        half = self.config.state_dim // 2
        new_state = self._current_state.copy()
        # 历史向量（后半段）= 0.9 * 原历史 + 0.1 * 交互内容
        new_state[half:] = (
            0.9 * new_state[half:] + 0.1 * item.topic_vector[:half]
        )
        # 归一化
        norm = np.linalg.norm(new_state) + 1e-8
        return (new_state / norm).astype(np.float32)
