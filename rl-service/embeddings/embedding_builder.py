# embeddings/embedding_builder.py
# Embedding 构建模块 —— 论文/关键词/作者向量化，升级 RL 状态空间

from __future__ import annotations
import os
import json
import logging
import numpy as np
from typing import List, Dict, Optional, Tuple

from dataset.aminer_loader import Paper, Author
from knowledge_graph.kg_builder import KnowledgeGraph

logger = logging.getLogger(__name__)


class EmbeddingBuilder:
    """
    多模态 Embedding 构建器。

    构建三类 Embedding：
        1. Paper Embedding     —— 论文语义向量（用于推荐相似度计算 / RL 状态输入）
        2. Keyword Embedding   —— 关键词语义向量（用于知识图谱 GNN 特征）
        3. Author Embedding    —— 作者研究兴趣向量（用于合作者推荐 / 社区特征）

    并将这三类 Embedding 融合为升级版 RL 状态向量。

    升级前 state_dim = 64：
        [兴趣向量(32) | 历史行为向量(32)]

    升级后 state_dim = 128：
        [兴趣向量(32) | 历史行为向量(32) | KG嵌入向量(32) | 社区行为向量(32)]
    """

    def __init__(
        self,
        embedding_dim: int = 64,
        output_dir: str = "data/embeddings",
    ):
        self.embedding_dim = embedding_dim
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # 已构建的 embedding 缓存
        self._paper_embs:   Optional[np.ndarray] = None
        self._keyword_embs: Optional[np.ndarray] = None
        self._author_embs:  Optional[np.ndarray] = None
        self._paper_id_map:   Dict[str, int] = {}
        self._keyword_id_map: Dict[str, int] = {}
        self._author_id_map:  Dict[str, int] = {}

    # ── 1. 论文 Embedding ────────────────────────────────────────

    def build_paper_embeddings(
        self,
        papers: List[Paper],
        precomputed: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """
        构建论文 Embedding 矩阵。

        Args:
            papers:      论文列表
            precomputed: 预计算的 embedding（由 preprocess.py 生成）

        Returns:
            embeddings: (n_papers, embedding_dim) float32
        """
        self._paper_id_map = {p.paper_id: i for i, p in enumerate(papers)}

        if precomputed is not None and precomputed.shape[0] == len(papers):
            logger.info(f"使用预计算论文 embedding，shape={precomputed.shape}")
            embs = precomputed
        elif any(p.embedding is not None for p in papers):
            # 从 paper.embedding 字段还原
            embs = np.array([
                p.embedding if p.embedding is not None
                else np.zeros(self.embedding_dim)
                for p in papers
            ], dtype=np.float32)
        else:
            # 回退：哈希 embedding
            logger.warning("未找到预计算 embedding，使用哈希方法")
            embs = self._hash_embeddings(
                [p.text_for_embedding() for p in papers]
            )

        # 降维 / 升维到目标维度
        if embs.shape[1] != self.embedding_dim:
            embs = self._resize_embeddings(embs, self.embedding_dim)

        self._paper_embs = embs
        self._save_embeddings(embs, self._paper_id_map, "paper")
        return embs

    # ── 2. 关键词 Embedding ──────────────────────────────────────

    def build_keyword_embeddings(self, kg: KnowledgeGraph) -> np.ndarray:
        """
        构建关键词 Embedding（基于论文共现关系）。

        方法：关键词 embedding = 包含该关键词的论文 embedding 的均值池化。
        若 self._paper_embs 未构建，则使用哈希 embedding。
        """
        kw_nodes = [(nid, node) for nid, node in kg.nodes.items()
                    if node.node_type == "keyword"]
        self._keyword_id_map = {nid: i for i, (nid, _) in enumerate(kw_nodes)}

        # 构建关键词 → 论文 embedding 的均值池化
        embs = np.zeros((len(kw_nodes), self.embedding_dim), dtype=np.float32)

        for i, (kw_id, kw_node) in enumerate(kw_nodes):
            # 找到包含该关键词的论文
            paper_ids = []
            for edge in kg._rev_adj.get(kw_id, []):
                if edge.relation == "has_keyword":
                    paper_ids.append(edge.src_id)

            if self._paper_embs is not None and paper_ids:
                indices = [
                    self._paper_id_map[pid]
                    for pid in paper_ids
                    if pid in self._paper_id_map
                ]
                if indices:
                    embs[i] = self._paper_embs[indices].mean(axis=0)
                    continue

            # 回退：关键词文本哈希 embedding
            h_vec = self._hash_single(kw_node.label)
            embs[i] = h_vec

        # L2 归一化
        norms = np.linalg.norm(embs, axis=1, keepdims=True) + 1e-8
        embs = embs / norms

        self._keyword_embs = embs
        self._save_embeddings(embs, self._keyword_id_map, "keyword")
        logger.info(f"关键词 embedding 构建完成：{embs.shape}")
        return embs

    # ── 3. 作者 Embedding ────────────────────────────────────────

    def build_author_embeddings(
        self,
        authors: List[Author],
        kg: KnowledgeGraph,
    ) -> np.ndarray:
        """
        构建作者 Embedding（基于其发表论文的均值池化）。

        作者向量 = 该作者所有论文 embedding 的加权平均，
        体现作者的研究兴趣分布。
        """
        self._author_id_map = {a.author_id: i for i, a in enumerate(authors)}
        embs = np.zeros((len(authors), self.embedding_dim), dtype=np.float32)

        for i, author in enumerate(authors):
            paper_ids = []
            for edge in kg._adj.get(author.author_id, []):
                if edge.relation == "author_of":
                    paper_ids.append(edge.dst_id)

            if self._paper_embs is not None and paper_ids:
                indices = [
                    self._paper_id_map[pid]
                    for pid in paper_ids
                    if pid in self._paper_id_map
                ]
                if indices:
                    embs[i] = self._paper_embs[indices].mean(axis=0)
                    continue

            # 回退：兴趣词哈希均值
            if author.interests:
                vecs = [self._hash_single(interest) for interest in author.interests]
                embs[i] = np.mean(vecs, axis=0)

        norms = np.linalg.norm(embs, axis=1, keepdims=True) + 1e-8
        embs = embs / norms

        self._author_embs = embs
        self._save_embeddings(embs, self._author_id_map, "author")
        logger.info(f"作者 embedding 构建完成：{embs.shape}")
        return embs

    # ── 4. 升级版 RL 状态构建 ─────────────────────────────────────

    def build_rl_state(
        self,
        user_interest_vec: np.ndarray,        # (dim,) 用户兴趣向量
        user_history_vec: np.ndarray,          # (dim,) 历史行为均值
        user_history_papers: Optional[List[str]] = None,  # 历史论文 ID
        user_id: Optional[str] = None,         # 用于查找作者 embedding
    ) -> np.ndarray:
        """
        构建升级版 RL 状态向量（state_dim=128）。

        state = concat(
            interest_vec(32),          # 用户长期兴趣
            history_vec(32),           # 近期行为
            kg_embedding(32),          # 知识图谱特征（论文 embedding 均值）
            community_vec(32),         # 社区特征（作者 embedding 代理）
        )

        若 KG embedding 未构建，则用零向量占位。
        """
        half = self.embedding_dim // 2
        interest = user_interest_vec[:half]
        history  = user_history_vec[:half]

        # KG embedding（历史论文 embedding 均值）
        kg_vec = np.zeros(half, dtype=np.float32)
        if self._paper_embs is not None and user_history_papers:
            indices = [
                self._paper_id_map[pid]
                for pid in user_history_papers
                if pid in self._paper_id_map
            ]
            if indices:
                kg_vec = self._paper_embs[indices].mean(axis=0)[:half]

        # 社区向量（作者 embedding 代理，预留）
        community_vec = np.zeros(half, dtype=np.float32)
        if self._author_embs is not None and user_id and user_id in self._author_id_map:
            idx = self._author_id_map[user_id]
            community_vec = self._author_embs[idx][:half]

        state = np.concatenate([interest, history, kg_vec, community_vec]).astype(np.float32)
        norm = np.linalg.norm(state) + 1e-8
        return state / norm

    # ── 工具方法 ──────────────────────────────────────────────────

    def get_paper_embedding(self, paper_id: str) -> Optional[np.ndarray]:
        """按 paper_id 获取论文 embedding 向量。"""
        if self._paper_embs is None:
            return None
        idx = self._paper_id_map.get(paper_id)
        return self._paper_embs[idx] if idx is not None else None

    def get_similar_papers(
        self,
        query_vec: np.ndarray,
        k: int = 10,
    ) -> List[Tuple[str, float]]:
        """
        基于余弦相似度检索最相近的论文（用于向量召回）。

        Returns:
            [(paper_id, similarity_score), ...]
        """
        if self._paper_embs is None:
            return []
        sims = self._paper_embs @ query_vec
        top_indices = np.argsort(sims)[::-1][:k]
        id_reverse = {v: k for k, v in self._paper_id_map.items()}
        return [(id_reverse[i], float(sims[i])) for i in top_indices if i in id_reverse]

    def _hash_embeddings(self, texts: List[str]) -> np.ndarray:
        """批量哈希 embedding。"""
        embs = np.zeros((len(texts), self.embedding_dim), dtype=np.float32)
        for i, text in enumerate(texts):
            embs[i] = self._hash_single(text)
        return embs

    def _hash_single(self, text: str) -> np.ndarray:
        """单文本哈希 embedding（确定性，无需模型）。"""
        vec = np.zeros(self.embedding_dim, dtype=np.float32)
        for word in text.lower().split():
            h = hash(word) % self.embedding_dim
            vec[h] += 1.0
        norm = np.linalg.norm(vec) + 1e-8
        return vec / norm

    def _resize_embeddings(
        self, embs: np.ndarray, target_dim: int
    ) -> np.ndarray:
        """调整 embedding 维度（PCA 降维或零填充升维）。"""
        current_dim = embs.shape[1]
        if current_dim > target_dim:
            try:
                from sklearn.decomposition import PCA
                pca = PCA(n_components=target_dim, random_state=42)
                return pca.fit_transform(embs).astype(np.float32)
            except ImportError:
                return embs[:, :target_dim].astype(np.float32)
        else:
            pad = np.zeros((embs.shape[0], target_dim - current_dim), dtype=np.float32)
            return np.concatenate([embs, pad], axis=1)

    def _save_embeddings(
        self, embs: np.ndarray, id_map: Dict[str, int], name: str
    ) -> None:
        """保存 embedding 矩阵和 ID 映射。"""
        np.save(os.path.join(self.output_dir, f"{name}_embeddings.npy"), embs)
        with open(os.path.join(self.output_dir, f"{name}_id_map.json"), "w") as f:
            json.dump(id_map, f)
        logger.info(f"{name} embedding 已保存：{embs.shape}")

    def load_all(self) -> None:
        """加载所有已保存的 embedding。"""
        for name, attr in [
            ("paper",   "_paper_embs"),
            ("keyword", "_keyword_embs"),
            ("author",  "_author_embs"),
        ]:
            emb_path = os.path.join(self.output_dir, f"{name}_embeddings.npy")
            map_path = os.path.join(self.output_dir, f"{name}_id_map.json")
            if os.path.exists(emb_path) and os.path.exists(map_path):
                setattr(self, attr, np.load(emb_path))
                with open(map_path) as f:
                    setattr(self, f"_{name}_id_map", json.load(f))
                logger.info(f"已加载 {name} embedding")
