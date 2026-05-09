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
    long_term_value: float = 0.0 # 长期科研价值估计 (0~1)

    # ── 知识图谱维度 ─────────────────────────────────────────────
    kg_topology_score: float = 0.0    # KG 拓扑相关度（引用链接近度、主题连通度）

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
        self.zeta  = weights.get("zeta",  2.0)  # KG 拓扑相关度权重

    def compute(self, signal: InteractionSignal) -> float:
        r = (
            self.alpha * signal.click
            + self.beta  * signal.favorite
            + self.gamma * signal.read_time
            + self.delta * signal.topic_match
            + self.eta   * signal.long_term_value
            + self.zeta  * signal.kg_topology_score
        )
        return float(r)
