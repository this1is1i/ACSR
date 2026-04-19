# utils/logger.py
# 训练日志记录模块

from __future__ import annotations
import os
import json
import time
import logging
from typing import Dict, Any, Optional
from collections import defaultdict


class TrainingLogger:
    """
    训练过程记录器，支持：
    - 控制台输出
    - JSON 文件持久化
    - 预留 TensorBoard / WandB 接口
    """

    def __init__(self, log_dir: str = "logs/", experiment_name: str = "ac_recommender"):
        os.makedirs(log_dir, exist_ok=True)
        self.log_dir = log_dir
        self.experiment_name = experiment_name
        self.history: Dict[str, list] = defaultdict(list)
        self.start_time = time.time()

        # 配置 Python logging
        log_path = os.path.join(log_dir, f"{experiment_name}.log")
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[
                logging.FileHandler(log_path),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger(experiment_name)
        self.logger.info(f"实验 [{experiment_name}] 开始，日志保存至 {log_path}")

    # ── 核心记录接口 ──────────────────────────────────────────────

    def log_episode(self, episode: int, metrics: Dict[str, Any]) -> None:
        """记录每个 episode 的训练指标。"""
        for k, v in metrics.items():
            self.history[k].append(v)
        elapsed = time.time() - self.start_time
        msg = f"Episode {episode:>4d} | " + " | ".join(
            f"{k}: {v:.4f}" if isinstance(v, float) else f"{k}: {v}"
            for k, v in metrics.items()
        ) + f" | 耗时: {elapsed:.1f}s"
        self.logger.info(msg)

    def log_step(self, step: int, info: Dict[str, Any]) -> None:
        """记录单步交互信息（调试用）。"""
        self.logger.debug(f"  Step {step:>3d} | " + str(info))

    def save_history(self) -> None:
        """将训练历史保存为 JSON 文件。"""
        path = os.path.join(self.log_dir, f"{self.experiment_name}_history.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)
        self.logger.info(f"训练历史已保存至 {path}")

    # ── 预留扩展接口 ──────────────────────────────────────────────

    def log_recommendation(self, user_id: str, recommended_items: list,
                           explanation: Optional[str] = None) -> None:
        """
        推荐结果日志接口（预留）。
        可对接推荐理由生成模块与前端展示系统。
        """
        record = {
            "user_id": user_id,
            "items": recommended_items,
            "explanation": explanation,
            "timestamp": time.time(),
        }
        self.logger.info(f"推荐记录: {json.dumps(record, ensure_ascii=False)}")

    def init_tensorboard(self) -> None:
        """预留 TensorBoard 接口。"""
        try:
            from torch.utils.tensorboard import SummaryWriter
            tb_path = os.path.join(self.log_dir, "tensorboard", self.experiment_name)
            self.tb_writer = SummaryWriter(tb_path)
            self.logger.info(f"TensorBoard 已启动，路径: {tb_path}")
        except ImportError:
            self.logger.warning("未安装 TensorBoard，跳过初始化。")

    def init_wandb(self, project: str = "rl-recommender") -> None:
        """预留 Weights & Biases 接口。"""
        try:
            import wandb
            wandb.init(project=project, name=self.experiment_name)
            self.logger.info("WandB 已初始化。")
        except ImportError:
            self.logger.warning("未安装 wandb，跳过初始化。")
