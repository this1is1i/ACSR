# train.py
# 主训练脚本 —— 支持真实数据（MySQL + KG）和模拟数据回退

from __future__ import annotations
import sys
import os
import signal

# 将项目根目录加入 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import torch
import logging
from typing import Optional

from config import Config, default_config
from agent import ActorCriticAgent
from env.rec_env import ResearchRecEnv
from utils.logger import TrainingLogger
from utils.reward import WeightedRewardFunction
from knowledge_graph.kg_embedder import create_kg_embedder

logger = logging.getLogger(__name__)


class GracefulStopController:
    def __init__(self):
        self._stop_requested = False
        self.reason: Optional[str] = None
        self._signal_count = 0

    @property
    def stop_requested(self) -> bool:
        return self._stop_requested

    def request_stop(self, reason: str = "stop requested") -> None:
        self._stop_requested = True
        self.reason = reason

    def install_signal_handlers(self):
        previous_handlers = {}

        def handler(signum, _frame):
            self._signal_count += 1
            if self._signal_count == 1:
                self.request_stop(f"received signal {signum}")
                print("\n[Train] 收到停止信号，将在当前安全点保存模型并退出。再次按 Ctrl+C 将立即中断。")
                return
            raise KeyboardInterrupt

        for signame in ("SIGINT", "SIGTERM"):
            sig = getattr(signal, signame, None)
            if sig is not None:
                previous_handlers[sig] = signal.getsignal(sig)
                signal.signal(sig, handler)
        return previous_handlers

    @staticmethod
    def restore_signal_handlers(previous_handlers) -> None:
        for sig, handler in (previous_handlers or {}).items():
            signal.signal(sig, handler)


def _init_real_data_sources(config: Config):
    """
    初始化真实数据源：MySQL → FeatureBuilder → CandidateGenerator → user_ids。

    Returns:
        (feature_builder, candidate_gen, user_ids, paper_catalog)
        任一为 None 表示该环节不可用。
    """
    feature_builder = None
    candidate_gen = None
    user_ids = []
    paper_catalog = []
    kg = None

    # ── 1. MySQL 连接 ──────────────────────────────────────────
    mysql_source = None
    try:
        from data.mysql_data import MySQLDataSource
        mysql_source = MySQLDataSource(config)
        _ = mysql_source.conn
        logger.info("MySQL 数据源连接成功")
    except Exception as e:
        logger.warning(f"MySQL 不可用: {e}")

    # ── 2. 知识图谱 / 论文池 ──────────────────────────────────
    if config.use_kg:
        kg_embedder, kg = create_kg_embedder(config)
        if kg is not None:
            paper_catalog = _extract_papers_from_kg(kg)
            logger.info(f"KG 论文池加载完成: {len(paper_catalog)} 篇")
        else:
            logger.warning("KG 加载失败，论文池不可用")

    # ── 3. FeatureBuilder ─────────────────────────────────────
    if mysql_source is not None:
        kg_dim = config.kg_embedding_dim if config.use_kg else 0
        try:
            from features.feature_builder import FeatureBuilder
            feature_builder = FeatureBuilder(
                base_state_dim=config.base_state_dim,
                kg_dim=kg_dim,
                kg_embedder=kg_embedder if config.use_kg else None,
                mysql_source=mysql_source,
            )
            logger.info("FeatureBuilder 初始化完成")
        except Exception as e:
            logger.warning(f"FeatureBuilder 初始化失败: {e}")

    # ── 4. CandidateGenerator ────────────────────────────────
    if paper_catalog:
        try:
            from recommender.candidate_generator import CandidateGenerator
            candidate_gen = CandidateGenerator.from_papers(paper_catalog, state_dim=config.base_state_dim)
            logger.info(f"CandidateGenerator 初始化完成: {len(paper_catalog)} 篇论文")
        except Exception as e:
            logger.warning(f"CandidateGenerator 初始化失败: {e}")

    # ── 5. 用户 ID 列表 ──────────────────────────────────────
    if mysql_source is not None:
        try:
            user_ids = mysql_source.get_all_user_ids()
            logger.info(f"训练用户池: {len(user_ids)} 人")
        except Exception as e:
            logger.warning(f"获取用户列表失败: {e}")

    return feature_builder, candidate_gen, user_ids


def _extract_papers_from_kg(kg) -> list:
    """从 KG 节点中提取论文列表。"""
    from dataset.aminer_loader import Paper as SourcePaper

    papers = []
    for node in kg.nodes.values():
        if node.node_type != "paper":
            continue

        props = node.properties
        authors = props.get("authors") or []
        keywords = props.get("keywords") or []
        if isinstance(authors, str):
            authors = [authors]
        if isinstance(keywords, str):
            keywords = [keywords]

        year = _safe_int(props.get("year"), 0)
        citation_count = _safe_int(props.get("citation_count"), 0)

        papers.append(SourcePaper(
            paper_id=props.get("aminer_id") or node.node_id,
            title=props.get("title") or node.label,
            abstract=props.get("abstract") or "",
            authors=[str(a) for a in authors],
            keywords=[str(k) for k in keywords],
            venue=str(props.get("venue") or ""),
            year=year,
            citation_count=citation_count,
            references=[],
        ))
    return papers


def _safe_int(value, default: int = 0) -> int:
    if value is None:
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, dict):
        return int(value.get("low", default))
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def train(
    config: Optional[Config] = None,
    stop_controller: Optional[GracefulStopController] = None,
) -> ActorCriticAgent:
    """
    Actor–Critic 训练主循环。

    流程：
        for each episode:
            state, info = env.reset()
            candidate_features = info["candidate_features"]
            for each step:
                action, log_prob = agent.select_action(state, candidate_features)
                next_state, reward, done, step_info = env.step(action)
                agent.update(state, action, reward, next_state, done, log_prob, candidate_features)
                state = next_state
    """
    import copy
    config = copy.copy(config or default_config)
    stop_controller = stop_controller or GracefulStopController()
    torch.manual_seed(42)
    np.random.seed(42)

    # ── 初始化数据源 ────────────────────────────────────────────
    feature_builder, candidate_gen, user_ids = _init_real_data_sources(config)

    # ── 初始化组件 ────────────────────────────────────────────────
    kg_embedder, _ = create_kg_embedder(config)
    reward_fn = WeightedRewardFunction(config.reward_weights)
    env = ResearchRecEnv(
        config=config,
        reward_fn=reward_fn,
        kg_embedder=kg_embedder,
        feature_builder=feature_builder,
        candidate_gen=candidate_gen,
        user_ids=user_ids,
    )
    agent = ActorCriticAgent(config=config)
    train_logger = TrainingLogger(log_dir=config.log_dir, experiment_name="ac_recommender")

    train_logger.logger.info(
        f"训练配置: state_dim={config.state_dim}, action_num={config.action_num}, "
        f"paper_feature_dim={config.paper_feature_dim}, "
        f"episodes={config.max_episodes}, steps={config.max_steps}, use_kg={config.use_kg}"
    )

    best_reward = float("-inf")
    final_avg_loss = 0.0
    total_episodes_run = 0
    stop_reason = None

    # ── 主训练循环 ────────────────────────────────────────────────
    for episode in range(1, config.max_episodes + 1):
        if stop_controller.stop_requested:
            stop_reason = stop_controller.reason or "stop requested before next episode"
            break

        state, info = env.reset()
        candidate_features = info["candidate_features"]

        episode_reward   = 0.0
        episode_steps    = 0
        total_actor_loss = 0.0
        total_td_error   = 0.0

        for step in range(config.max_steps):
            if stop_controller.stop_requested:
                stop_reason = stop_controller.reason or "stop requested during episode"
                break

            action, log_prob = agent.select_action(state, candidate_features)
            next_state, reward, done, step_info = env.step(action)

            losses = agent.update(
                state=state,
                action=action,
                reward=reward,
                next_state=next_state,
                done=done,
                log_prob=log_prob,
                candidate_features=candidate_features,
            )

            episode_reward   += reward
            total_actor_loss += losses["actor_loss"]
            total_td_error   += abs(losses["td_error"])
            episode_steps    += 1

            train_logger.log_step(step, {
                "action":      action,
                "reward":      f"{reward:.3f}",
                "td_error":    f"{losses['td_error']:.4f}",
                "entropy":     f"{losses['entropy']:.4f}",
            })

            state = next_state
            if done:
                break

        if episode_steps == 0 and stop_reason:
            break

        # ── Episode 统计 ──────────────────────────────────────────
        agent.episode_count += 1
        total_episodes_run = episode
        avg_actor_loss = total_actor_loss / episode_steps
        final_avg_loss = avg_actor_loss
        avg_td_error   = total_td_error   / episode_steps

        metrics = {
            "episode_reward": episode_reward,
            "steps":          episode_steps,
            "avg_actor_loss": avg_actor_loss,
            "avg_td_error":   avg_td_error,
        }
        train_logger.log_episode(episode, metrics)

        # ── 最优模型保存 ──────────────────────────────────────────
        if episode_reward > best_reward:
            best_reward = episode_reward
            agent.save_model()
            train_logger.logger.info(f"  ✓ 新最优模型已保存 (reward={best_reward:.3f})")

        # ── 每 50 轮打印 Top-K 推荐示例 ──────────────────────────
        if episode % 50 == 0:
            _demo_recommendation(agent, env, train_logger, config)

    # ── 训练结束 ──────────────────────────────────────────────────
    final_best = best_reward if best_reward > float("-inf") else 0.0
    model_ver = f"v{agent.train_step // 1000}.{agent.episode_count // 100}"
    try:
        if stop_reason:
            agent.save_model()
            train_logger.logger.info(f"训练已优雅停止：{stop_reason}")
        train_logger.save_history()
        train_logger.logger.info(f"训练完成！最优 Episode Reward: {final_best:.3f}")

        # 写入一条训练摘要到 rl_training_log
        try:
            from data.mysql_data import MySQLDataSource
            mysql_src = MySQLDataSource(config)
            mysql_src.insert_training_log(
                episode=total_episodes_run,
                reward=final_best,
                loss=final_avg_loss,
                model_version=model_ver,
            )
            train_logger.logger.info(
                f"训练记录已写入 rl_training_log: episodes={total_episodes_run}, "
                f"reward={final_best:.4f}, loss={final_avg_loss:.4f}"
            )
            mysql_src.close()
        except Exception as e:
            train_logger.logger.warning(f"写入 rl_training_log 失败: {e}")

        return agent, {
            "total_episodes": total_episodes_run,
            "best_reward": final_best,
            "final_avg_loss": final_avg_loss,
            "model_version": model_ver,
        }
    finally:
        train_logger.close()


def _demo_recommendation(
    agent: ActorCriticAgent,
    env: ResearchRecEnv,
    train_logger: TrainingLogger,
    config: Config,
) -> None:
    """展示当前策略的 Top-K 推荐结果（用于训练过程监控）。"""
    state, info = env.reset()
    candidate_features = info["candidate_features"]
    indices, probs = agent.recommend_top_k(state, candidate_features, k=config.top_k)

    train_logger.logger.info("── Top-K 推荐示例 ──────────────────────────")
    for rank, (idx, prob) in enumerate(zip(indices, probs), 1):
        train_logger.logger.info(f"  #{rank}: item_idx={idx:>2d} | prob={prob:.4f}")
    train_logger.logger.info("────────────────────────────────────────────")

    train_logger.log_recommendation(
        user_id=info["user_id"],
        recommended_items=indices,
        explanation=f"Top-{config.top_k} 推荐（策略概率排序）",
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("=" * 60)
    print("  Actor–Critic 科研推荐系统  开始训练")
    print("=" * 60)
    controller = GracefulStopController()
    previous_handlers = controller.install_signal_handlers()
    try:
        trained_agent, _ = train(default_config, stop_controller=controller)
    finally:
        controller.restore_signal_handlers(previous_handlers)

    # ── 推理演示 ──────────────────────────────────────────────────
    print("\n[推理演示] Top-K 推荐：")
    state = np.random.randn(default_config.state_dim).astype(np.float32)
    dummy_features = np.random.randn(default_config.action_num, default_config.paper_feature_dim).astype(np.float32)
    indices, probs = trained_agent.recommend_top_k(state, dummy_features, k=default_config.top_k)
    print(f"  Top-{default_config.top_k}: indices={indices}, probs={[round(p, 4) for p in probs]}")
