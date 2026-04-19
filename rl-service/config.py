# config.py
# 系统全局配置文件

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class Config:
    # ── 状态 / 动作空间 ──────────────────────────────────────────
    state_dim: int = 64          # 状态向量维度
    action_num: int = 20         # 候选科研内容数量（离散动作空间大小）
    top_k: int = 5               # Top-K 推荐数量

    # ── 网络结构 ──────────────────────────────────────────────────
    actor_hidden: int = 128
    critic_hidden: int = 128

    # ── 训练超参数 ────────────────────────────────────────────────
    gamma: float = 0.99          # 折扣因子
    actor_lr: float = 1e-3
    critic_lr: float = 1e-3
    max_episodes: int = 500
    max_steps: int = 50          # 每轮最大交互步数
    entropy_coeff: float = 0.01  # 熵正则化系数（防止策略过早收敛）

    # ── 奖励函数权重 ──────────────────────────────────────────────
    reward_weights: Dict[str, float] = field(default_factory=lambda: {
        "alpha": 1.0,   # 点击权重
        "beta":  2.0,   # 收藏权重
        "gamma": 0.5,   # 阅读时长权重
        "delta": 3.0,   # 研究方向匹配度权重
        "eta":   1.5,   # 长期科研价值权重
    })

    # ── 持久化 ────────────────────────────────────────────────────
    model_save_path: str = "checkpoints/ac_model.pth"
    log_dir: str = "logs/"

    # ── 知识图谱预留 ──────────────────────────────────────────────
    kg_embedding_dim: int = 32   # 知识图谱 embedding 维度（预留）
    use_kg: bool = False         # 是否启用知识图谱特征


# 全局默认配置实例
default_config = Config()
