# train.py
# 主训练脚本

from __future__ import annotations
import sys
import os

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

logger = logging.getLogger(__name__)


def _build_kg_embedder(config: Config):
    """构建知识图谱及 Embedder（可选）。"""
    if not config.use_kg:
        return None
    try:
        from dataset.aminer_loader import AMinerLoader
        from knowledge_graph.kg_builder import KGBuilder
        from knowledge_graph.kg_embedder import KGEmbedder

        loader = AMinerLoader()
        papers = loader.load_papers(limit=500)
        authors = loader.load_authors(limit=200)
        citations = loader.load_citations(papers)

        kg = KGBuilder(min_keyword_freq=1).build(papers, authors, citations)
        embedder = KGEmbedder(kg, embed_dim=config.kg_embedding_dim)
        logger.info(f"KG Embedder 构建完成：{len(papers)} 篇论文")
        return embedder
    except Exception as e:
        logger.warning(f"KG Embedder 构建失败，回退为无 KG 模式: {e}")
        return None


def train(config: Optional[Config] = None) -> ActorCriticAgent:
    """
    Actor–Critic 训练主循环。

    流程：
        for each episode:
            state = env.reset()
            for each step:
                action, log_prob = agent.select_action(state)
                next_state, reward, done = env.step(action)
                agent.update(...)
                state = next_state
    """
    config = config or default_config
    torch.manual_seed(42)
    np.random.seed(42)

    # ── 初始化组件 ────────────────────────────────────────────────
    kg_embedder = _build_kg_embedder(config)
    reward_fn = WeightedRewardFunction(config.reward_weights)
    env = ResearchRecEnv(config=config, reward_fn=reward_fn, kg_embedder=kg_embedder)
    agent = ActorCriticAgent(config=config)
    train_logger = TrainingLogger(log_dir=config.log_dir, experiment_name="ac_recommender")

    train_logger.logger.info(
        f"训练配置: state_dim={config.state_dim}, action_num={config.action_num}, "
        f"episodes={config.max_episodes}, steps={config.max_steps}, use_kg={config.use_kg}"
    )

    best_reward = float("-inf")

    # ── 主训练循环 ────────────────────────────────────────────────
    for episode in range(1, config.max_episodes + 1):
        state, info = env.reset()

        episode_reward   = 0.0
        episode_steps    = 0
        total_actor_loss = 0.0
        total_td_error   = 0.0

        for step in range(config.max_steps):
            action, log_prob = agent.select_action(state)
            next_state, reward, done, step_info = env.step(action)

            losses = agent.update(
                state=state,
                action=action,
                reward=reward,
                next_state=next_state,
                done=done,
                log_prob=log_prob,
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

        # ── Episode 统计 ──────────────────────────────────────────
        agent.episode_count += 1
        avg_actor_loss = total_actor_loss / episode_steps
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
    train_logger.save_history()
    train_logger.logger.info(f"训练完成！最优 Episode Reward: {best_reward:.3f}")
    return agent


def _demo_recommendation(
    agent: ActorCriticAgent,
    env: ResearchRecEnv,
    train_logger: TrainingLogger,
    config: Config,
) -> None:
    """展示当前策略的 Top-K 推荐结果（用于训练过程监控）。"""
    state, info = env.reset()
    indices, probs = agent.recommend_top_k(state, k=config.top_k)

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
    trained_agent = train(default_config)

    # ── 推理演示 ──────────────────────────────────────────────────
    print("\n[推理演示] 调用 REST API 接口格式：")
    dummy_request = {
        "interest_vector": np.random.randn(default_config.base_state_dim // 2).tolist(),
        "history_vector":  np.random.randn(default_config.base_state_dim // 2).tolist(),
    }
    result = trained_agent.predict_for_api(dummy_request)
    print(f"  推荐结果: {result}")
