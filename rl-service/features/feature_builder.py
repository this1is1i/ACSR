# features/feature_builder.py
# 特征构建模块 —— 将用户原始数据转换为强化学习状态向量

from __future__ import annotations
import json
import logging
import numpy as np
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class UserFeatures:
    """用户特征容器，统一封装所有特征来源。"""
    user_id: str
    interest_vector: np.ndarray          # 科研兴趣 embedding
    history_vector: np.ndarray           # 历史行为 embedding
    kg_vector: Optional[np.ndarray] = None       # 知识图谱结构特征
    community_vector: Optional[np.ndarray] = None  # 社区行为特征（预留）
    research_topics: List[str] = field(default_factory=list)
    history_paper_ids: List[str] = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)


class FeatureBuilder:
    """
    特征构建器 —— 将用户画像转换为 RL 状态向量。

    状态结构（use_kg=True 时）：
        state = concat(interest[:half], history[:half], kg_vector[:kg_dim])
              = (32 + 32 + 32) = 96 维

    状态结构（use_kg=False 时）：
        state = concat(interest[:half], history[:half])
              = (32 + 32) = 64 维

    数据来源优先级：
        1. MySQL user_feature_snapshot 缓存（6 小时内有效）
        2. MySQL behavior_log + user_interest_history 实时构建
        3. 随机向量回退（仅用于无 MySQL 连接的训练环境）
    """

    def __init__(
        self,
        base_state_dim: int = 64,
        kg_dim: int = 0,
        kg_embedder: Any = None,
        mysql_source: Any = None,    # Optional[MySQLDataSource]
        seed: int = 42,
    ):
        self.base_state_dim = base_state_dim
        self.half = base_state_dim // 2   # interest / history 各占一半
        self.kg_dim = kg_dim
        self.kg_embedder = kg_embedder
        self.mysql = mysql_source
        self.state_dim = base_state_dim + kg_dim
        self.rng = np.random.default_rng(seed)

    # ── 主接口 ────────────────────────────────────────────────────

    def build_state(self, features: UserFeatures) -> np.ndarray:
        """
        将用户特征拼接为 RL 状态向量。

        state = concat(interest[:half], history[:half], [kg_vector])
        """
        interest = features.interest_vector[:self.half]
        history  = features.history_vector[:self.half]
        parts = [interest, history]

        if self.kg_dim > 0:
            if features.kg_vector is not None:
                parts.append(features.kg_vector[:self.kg_dim])
            else:
                parts.append(np.zeros(self.kg_dim, dtype=np.float32))

        state = np.concatenate(parts).astype(np.float32)
        norm = np.linalg.norm(state) + 1e-8
        return state / norm

    def build_item_vector(self, item_meta: Dict[str, Any]) -> np.ndarray:
        """
        构建科研内容（论文）的特征向量（base_state_dim 维）。

        注意：item 向量维度固定为 base_state_dim，不包含 KG 部分。
        KG 信息通过 state 中的 kg_vector 段传入 Actor/Critic。
        """
        seed = hash(str(item_meta.get("item_id", "unknown"))) % (2**31)
        rng = np.random.default_rng(seed)
        v = rng.standard_normal(self.base_state_dim).astype(np.float32)
        return v / (np.linalg.norm(v) + 1e-8)

    # ── 用户特征获取 ──────────────────────────────────────────────

    def get_user_features(
        self,
        user_id: str,
        history: Optional[List[str]] = None,
    ) -> UserFeatures:
        """
        获取并构建用户特征。

        数据来源优先级：
        1. MySQL 真实数据（behavior_log + user_interest_history）
        2. 随机向量回退（训练环境 / MySQL 不可用）
        """
        # ── 尝试从 MySQL 获取真实特征 ──────────────────────────
        if self.mysql is not None:
            try:
                numeric_id = int(user_id)
                return self._build_features_from_mysql(numeric_id, user_id, history)
            except (ValueError, Exception) as e:
                logger.debug(f"无法从 MySQL 获取用户 {user_id} 的特征: {e}，回退随机向量")

        # ── 回退：随机向量（训练环境） ─────────────────────────
        return self._build_features_random(user_id, history)

    # ── MySQL 真实特征构建 ───────────────────────────────────────

    def _build_features_from_mysql(
        self,
        numeric_id: int,
        user_id: str,
        history: Optional[List[str]] = None,
    ) -> UserFeatures:
        # 尝试读取缓存
        cached_interest = self.mysql.get_cached_feature(numeric_id, "interest")
        cached_history = self.mysql.get_cached_feature(numeric_id, "history")

        if cached_interest is not None and cached_history is not None:
            logger.debug(f"[{user_id}] 使用缓存特征向量")
            kg_vec = self._compute_kg_vector(history)
            return UserFeatures(
                user_id=user_id,
                interest_vector=cached_interest,
                history_vector=cached_history,
                kg_vector=kg_vec,
                research_topics=[],
                history_paper_ids=list(history or []),
            )

        # ── 从 MySQL 实时构建 ──────────────────────────────────
        interest_vec = self._build_interest_from_mysql(numeric_id)
        history_vec = self._build_history_from_mysql(numeric_id)
        research_topics = self._get_topics_from_mysql(numeric_id)
        history_paper_ids = self._get_history_paper_ids_from_mysql(numeric_id)

        # 写入缓存
        try:
            self.mysql.cache_feature(numeric_id, "interest", interest_vec, "computed")
            self.mysql.cache_feature(numeric_id, "history", history_vec, "computed")
        except Exception:
            pass

        kg_vec = self._compute_kg_vector(
            history if history is not None else history_paper_ids
        )
        return UserFeatures(
            user_id=user_id,
            interest_vector=interest_vec,
            history_vector=history_vec,
            kg_vector=kg_vec,
            research_topics=research_topics,
            history_paper_ids=list(history or history_paper_ids),
        )

    def _build_interest_from_mysql(self, numeric_id: int) -> np.ndarray:
        """从 user_interest_history 构建兴趣向量。"""
        tags = self.mysql.get_user_interest_tags(numeric_id)

        if not tags:
            # 冷启动：使用全局热门兴趣的均值
            global_kw = self.mysql.get_global_keyword_freq()
            if global_kw:
                tags = [{"interest_tag": k, "weight": float(v)}
                        for k, v in list(global_kw.items())[:10]]

        if not tags:
            return self._fallback_vec(numeric_id)

        vec = np.zeros(self.base_state_dim, dtype=np.float32)
        total_weight = 0.0
        for tag in tags:
            tag_vec = self._hash_tag(tag["interest_tag"], self.base_state_dim)
            w = float(tag.get("weight", 1.0))
            vec += tag_vec * w
            total_weight += w

        if total_weight > 0:
            vec /= total_weight
        norm = np.linalg.norm(vec) + 1e-8
        return (vec / norm).astype(np.float32)

    def _build_history_from_mysql(self, numeric_id: int) -> np.ndarray:
        """从 behavior_log 构建历史行为向量。"""
        behaviors = self.mysql.get_user_behaviors(numeric_id)

        if not behaviors:
            return self._fallback_vec(numeric_id)

        # 提取去重论文 ID
        paper_ids = list({b["paper_id"] for b in behaviors})
        papers = self.mysql.get_papers_by_ids(paper_ids)

        if not papers:
            return self._fallback_vec(numeric_id)

        # 先尝试 KG Embedder 的论文向量
        vecs = []
        for paper in papers:
            aminer_id = paper.get("aminer_id")
            if aminer_id and self.kg_embedder is not None:
                emb = self.kg_embedder.get_paper_embedding(aminer_id)
                if emb is not None:
                    # KG embedding 维度可能不同，取前 base_state_dim
                    padded = np.zeros(self.base_state_dim, dtype=np.float32)
                    copy_len = min(len(emb), self.base_state_dim)
                    padded[:copy_len] = emb[:copy_len]
                    vecs.append(padded)
                    continue

            # 回退：基于论文属性的 hash 向量
            vecs.append(self._paper_attr_vec(paper))

        if not vecs:
            return self._fallback_vec(numeric_id)

        # 平均池化
        history_vec = np.mean(vecs, axis=0).astype(np.float32)
        norm = np.linalg.norm(history_vec) + 1e-8
        return history_vec / norm

    def _get_topics_from_mysql(self, numeric_id: int) -> List[str]:
        tags = self.mysql.get_user_interest_tags(numeric_id)
        return [t["interest_tag"] for t in tags[:10]]

    def _get_history_paper_ids_from_mysql(self, numeric_id: int) -> List[str]:
        behaviors = self.mysql.get_user_behaviors(numeric_id)
        paper_ids = list({b["paper_id"] for b in behaviors})
        papers = self.mysql.get_papers_by_ids(paper_ids)
        return [p.get("aminer_id") or str(p["id"]) for p in papers if p.get("aminer_id")]

    # ── 随机向量回退 ──────────────────────────────────────────────

    def _build_features_random(
        self,
        user_id: str,
        history: Optional[List[str]] = None,
    ) -> UserFeatures:
        seed = hash(user_id) % (2**31)
        rng = np.random.default_rng(seed)

        interest = rng.standard_normal(self.base_state_dim).astype(np.float32)
        interest /= np.linalg.norm(interest) + 1e-8

        history_vec = np.zeros(self.base_state_dim, dtype=np.float32)
        if history:
            vecs = [self.build_item_vector({"item_id": h}) for h in history]
            history_vec = np.mean(vecs, axis=0).astype(np.float32)

        return UserFeatures(
            user_id=user_id,
            interest_vector=interest,
            history_vector=history_vec,
            kg_vector=self._compute_kg_vector(history),
            research_topics=["NLP", "Graph Learning"],
            history_paper_ids=list(history or []),
        )

    def _compute_kg_vector(self, history: Optional[List[str]]) -> Optional[np.ndarray]:
        """利用 KG Embedder 计算用户的知识图谱特征向量。"""
        if self.kg_embedder is None or self.kg_dim == 0:
            return None
        if not history:
            return np.zeros(self.kg_dim, dtype=np.float32)
        return self.kg_embedder.get_user_kg_embedding(history)

    # ── 辅助方法 ──────────────────────────────────────────────────

    @staticmethod
    def _hash_tag(tag: str, dim: int) -> np.ndarray:
        """将兴趣标签映射为确定性向量。"""
        seed = hash(tag.strip().lower()) % (2**31)
        rng = np.random.default_rng(seed)
        v = rng.standard_normal(dim).astype(np.float32)
        return v / (np.linalg.norm(v) + 1e-8)

    @staticmethod
    def _paper_attr_vec(paper: dict) -> np.ndarray:
        """基于论文关键词 + 标题构建哈希向量。"""
        dim = 64
        vec = np.zeros(dim, dtype=np.float32)
        text_parts = [paper.get("title", "")]

        keywords = paper.get("keywords")
        if isinstance(keywords, str):
            try:
                keywords = json.loads(keywords)
            except (json.JSONDecodeError, TypeError):
                keywords = [keywords]
        if isinstance(keywords, list):
            text_parts.extend(str(k) for k in keywords[:5])

        text = " ".join(text_parts).lower()
        for word in text.split():
            h = hash(word) % dim
            vec[h] += 1.0
        norm = np.linalg.norm(vec) + 1e-8
        return vec / norm

    def _fallback_vec(self, seed_int: int) -> np.ndarray:
        """生成确定性的占位向量。"""
        return self._hash_tag(str(seed_int), self.base_state_dim)
