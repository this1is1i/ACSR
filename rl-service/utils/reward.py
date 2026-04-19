# utils/reward.py
# 奖励函数模块 —— 支持插拔式扩展

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional
import math


@dataclass
class InteractionSignal:
    """
    用户与推荐内容的一次交互信号。
    所有字段均为归一化后的浮点数 [0, 1]，便于奖励函数统一处理。
    """
    click: float = 0.0           # 是否点击 (0 or 1)
    favorite: float = 0.0        # 是否收藏 (0 or 1)
    read_time: float = 0.0       # 归一化阅读时长 (0~1)
    topic_match: float = 0.0     # 研究方向匹配度 (0~1)
    long_term_value: float = 0.0 # 长期科研价值估计 (0~1)，可由外部模型填充

    # ── 预留扩展字段 ─────────────────────────────────────────────
    citation_potential: float = 0.0   # 论文引用潜力（预留）
    collaboration_score: float = 0.0  # 科研合作匹配度（预留）


class BaseRewardFunction:
    """
    奖励函数基类。
    子类可重写 compute() 方法，实现自定义奖励策略（如多目标 RL）。
    """

    def compute(self, signal: InteractionSignal) -> float:
        raise NotImplementedError


class WeightedRewardFunction(BaseRewardFunction):
    """
    加权线性奖励函数：
        r = α·click + β·favorite + γ·read_time
          + δ·topic_match + η·long_term_value

    权重通过 weights 字典传入，便于在配置文件中统一管理。
    """

    def __init__(self, weights: Dict[str, float]):
        self.alpha = weights.get("alpha", 1.0)
        self.beta  = weights.get("beta",  2.0)
        self.gamma = weights.get("gamma", 0.5)
        self.delta = weights.get("delta", 3.0)
        self.eta   = weights.get("eta",   1.5)

    def compute(self, signal: InteractionSignal) -> float:
        r = (
            self.alpha * signal.click
            + self.beta  * signal.favorite
            + self.gamma * signal.read_time
            + self.delta * signal.topic_match
            + self.eta   * signal.long_term_value
        )
        return float(r)


class CuriosityAugmentedReward(BaseRewardFunction):
    """
    好奇心增强奖励（预留接口）。
    用于奖励探索行为，防止推荐系统陷入信息茧房。
    实现时可接入 ICM（Intrinsic Curiosity Module）。
    """

    def __init__(self, base_fn: BaseRewardFunction, curiosity_weight: float = 0.3):
        self.base_fn = base_fn
        self.curiosity_weight = curiosity_weight

    def compute(self, signal: InteractionSignal, curiosity_bonus: float = 0.0) -> float:  # type: ignore[override]
        base_r = self.base_fn.compute(signal)
        return base_r + self.curiosity_weight * curiosity_bonus


class LongTermValueEstimator:
    """
    长期科研价值估计器接口（预留）。
    可对接知识图谱、引用网络、用户职业发展轨迹等外部模型。
    """

    def estimate(self, user_embedding, item_embedding) -> float:
        """
        子类实现具体的长期价值估计逻辑。
        当前返回 0.0 作为占位。
        """
        return 0.0
