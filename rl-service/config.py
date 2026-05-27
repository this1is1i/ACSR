# config.py
# 系统全局配置文件

import os
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class Config:
    # ── 基础维度 ──────────────────────────────────────────────────
    base_state_dim: int = 64     # 基础状态维度 = interest(32) + history(32)
    paper_feature_dim: int = 32  # 论文特征维度（用于 Actor 逐论文打分）
    action_num: int = 50         # 最大候选数量（训练/推理时动态调整）
    top_k: int = 10              # Top-K 推荐默认值（由请求参数 k 覆盖）

    # ── 知识图谱 ──────────────────────────────────────────────────
    kg_embedding_dim: int = 32   # 知识图谱 embedding 维度
    use_kg: bool = True          # 启用知识图谱特征
    graph_backend: str = field(default_factory=lambda: os.getenv("REC_GRAPH_BACKEND", "neo4j"))  # json | pickle | neo4j
    neo4j_uri: str = field(default_factory=lambda: os.getenv("GRAPH_NEO4J_URI", "bolt://localhost:7687"))
    neo4j_user: str = field(default_factory=lambda: os.getenv("GRAPH_NEO4J_USERNAME", "neo4j"))
    neo4j_password: str = field(default_factory=lambda: os.getenv("GRAPH_NEO4J_PASSWORD", ""))
    neo4j_database: str = field(default_factory=lambda: os.getenv("GRAPH_NEO4J_DATABASE", "neo4j"))
    neo4j_batch_size: int = field(default_factory=lambda: int(os.getenv("GRAPH_NEO4J_BATCH_SIZE", "500")))

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
        "zeta":  2.0,   # 知识图谱拓扑相关度权重
    })

    # ── MySQL 数据源 ──────────────────────────────────────────────
    mysql_host: str = field(default_factory=lambda: os.getenv("MYSQL_HOST", "localhost"))
    mysql_port: int = field(default_factory=lambda: int(os.getenv("MYSQL_PORT", "3306")))
    mysql_user: str = field(default_factory=lambda: os.getenv("MYSQL_USER", "root"))
    mysql_password: str = field(default_factory=lambda: os.getenv("MYSQL_PASSWORD", "qwer1234"))
    mysql_db: str = field(default_factory=lambda: os.getenv("MYSQL_DB", "research_db"))

    # ── 持久化 ────────────────────────────────────────────────────
    model_save_path: str = "checkpoints/ac_model.pth"
    log_dir: str = "logs/"

    def __post_init__(self):
        """state_dim 根据是否启用 KG 动态计算。"""
        self.state_dim: int = self.base_state_dim + (
            self.kg_embedding_dim if self.use_kg else 0
        )


# 全局默认配置实例
default_config = Config()
