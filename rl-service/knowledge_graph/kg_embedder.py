# knowledge_graph/kg_embedder.py
# 知识图谱结构化 Embedding 模块 —— 将图拓扑特征编码为固定维度向量

from __future__ import annotations
import numpy as np
import logging
from typing import Dict, List, Optional
from collections import defaultdict

from knowledge_graph.kg_builder import KnowledgeGraph

logger = logging.getLogger(__name__)


class KGEmbedder:
    """
    知识图谱结构化 Embedding 生成器。

    为每个论文节点计算一个固定维度的向量，编码以下图结构特征：
      - 引用入度 / 出度（学术影响力）
      - 关键词连通度（研究领域广度）
      - 作者合著网络特征（学术协作密度）
      - 拓扑深度（在引用 DAG 中的位置）
      - 发表场所影响力（Venue 关联论文数量）
      - 时间特征（论文新旧程度）

    用户级 KG Embedding 通过对其历史论文的 Embedding 进行平均池化得到，
    表示用户在知识图谱中的「位置」和「偏好结构」。
    """

    # 原始结构特征的维度
    RAW_FEATURE_DIM = 10

    def __init__(
        self,
        kg: KnowledgeGraph,
        embed_dim: int = 32,
        seed: int = 42,
    ):
        self.kg = kg
        self.embed_dim = embed_dim
        self._rng = np.random.default_rng(seed)
        self._embeddings: Dict[str, np.ndarray] = {}

        # 随机投影矩阵（用于降维）
        self._projection = self._rng.standard_normal(
            (self.RAW_FEATURE_DIM, embed_dim)
        ).astype(np.float32) / np.sqrt(self.RAW_FEATURE_DIM)

        self._compute_all_embeddings()
        logger.info(
            f"KGEmbedder 初始化完成：{len(self._embeddings)} 篇论文生成 {embed_dim} 维 embedding"
        )

    # ── 公共接口 ──────────────────────────────────────────────────

    def get_paper_embedding(self, paper_id: str) -> Optional[np.ndarray]:
        """获取单篇论文的 KG embedding。"""
        return self._embeddings.get(paper_id)

    def get_user_kg_embedding(self, history_paper_ids: List[str]) -> np.ndarray:
        """
        计算用户的 KG embedding（基于历史论文平均池化）。

        反映用户在知识图谱中的活跃区域：
        - 常读高被引论文 → KG embedding 偏向高影响力区域
        - 常读特定关键词 → KG embedding 偏向该主题子图
        """
        vecs = [
            self._embeddings[pid]
            for pid in history_paper_ids
            if pid in self._embeddings
        ]
        if vecs:
            return np.mean(vecs, axis=0).astype(np.float32)
        return np.zeros(self.embed_dim, dtype=np.float32)

    def get_kg_similarity(self, paper_id_a: str, paper_id_b: str) -> float:
        """计算两篇论文在 KG 空间的余弦相似度。"""
        ea = self._embeddings.get(paper_id_a)
        eb = self._embeddings.get(paper_id_b)
        if ea is None or eb is None:
            return 0.0
        norm_a = np.linalg.norm(ea) + 1e-8
        norm_b = np.linalg.norm(eb) + 1e-8
        return float(np.dot(ea, eb) / (norm_a * norm_b))

    # ── 内部实现 ──────────────────────────────────────────────────

    def _compute_all_embeddings(self) -> None:
        """为所有 paper 节点计算结构化 embedding。"""
        raw_features: Dict[str, np.ndarray] = {}
        for node_id, node in self.kg.nodes.items():
            if node.node_type == "paper":
                raw_features[node_id] = self._extract_structural_features(node_id)

        if not raw_features:
            return

        # Z-score 标准化
        all_feats = np.array(list(raw_features.values()))
        mean = all_feats.mean(axis=0)
        std = all_feats.std(axis=0) + 1e-8

        for nid, raw in raw_features.items():
            normalized = (raw - mean) / std
            projected = normalized @ self._projection
            # L2 归一化
            norm = np.linalg.norm(projected) + 1e-8
            self._embeddings[nid] = (projected / norm).astype(np.float32)

    def _extract_structural_features(self, paper_id: str) -> np.ndarray:
        """
        提取论文节点的 10 维原始结构特征向量。

        维度含义：
          [0] cite_in_degree     被引次数（学术影响力）
          [1] cite_out_degree    引用次数（知识广度）
          [2] keyword_count      关键词数量
          [3] keyword_reach      关键词关联论文总数（主题连通度）
          [4] author_count       作者数量
          [5] author_productivity 作者平均产出（合著者活跃度）
          [6] venue_popularity   发表场所关联论文数（场所影响力）
          [7] co_author_density  合著网络密度（学术协作密度）
          [8] topo_depth         引用链深度（知识传播距离）
          [9] recency            时间新旧度（归一化年份）
        """
        adj = self.kg._adj.get(paper_id, [])
        rev_adj = self.kg._rev_adj.get(paper_id, [])

        # 引用特征
        cite_out = sum(1 for e in adj if e.relation == "cite")
        cite_in = sum(1 for e in rev_adj if e.relation == "cite")

        # 关键词特征
        kw_edges = [e for e in adj if e.relation == "has_keyword"]
        kw_count = len(kw_edges)
        kw_reach = sum(
            len(self.kg._rev_adj.get(e.dst_id, []))
            for e in kw_edges
        )

        # 作者特征
        author_edges = [e for e in rev_adj if e.relation == "author_of"]
        author_count = len(author_edges)
        author_productivity = (
            sum(len(self.kg._adj.get(e.src_id, [])) for e in author_edges)
            / max(author_count, 1)
        )

        # 合著网络密度：该论文作者之间的合著边数 / 可能合著边数
        author_ids = [e.src_id for e in author_edges]
        co_author_edges = 0
        for aid in author_ids:
            for e in self.kg._adj.get(aid, []):
                if e.relation == "co_author" and e.dst_id in author_ids:
                    co_author_edges += 1
        possible_pairs = max(author_count * (author_count - 1) / 2, 1)
        co_author_density = co_author_edges / possible_pairs

        # Venue 影响力
        venue_edges = [e for e in adj if e.relation == "publish_in"]
        venue_popularity = sum(
            len(self.kg._rev_adj.get(e.dst_id, []))
            for e in venue_edges
        )

        # 拓扑深度（沿引用链向前追溯的最大深度，限制 BFS 防止耗时）
        topo_depth = self._compute_topo_depth(paper_id, max_depth=5)

        # 时间特征
        node = self.kg.nodes[paper_id]
        year = node.properties.get("year", 2020)
        recency = (year - 2010) / 15.0  # 归一化到 ~[0, 1]

        return np.array([
            cite_in, cite_out, kw_count, kw_reach,
            author_count, author_productivity, venue_popularity,
            co_author_density, topo_depth, recency,
        ], dtype=np.float32)

    def _compute_topo_depth(self, paper_id: str, max_depth: int = 5) -> float:
        """BFS 计算论文在引用 DAG 中的最大引用链深度。"""
        from collections import deque
        visited = {paper_id}
        queue = deque([(paper_id, 0)])
        max_d = 0
        while queue:
            nid, d = queue.popleft()
            if d >= max_depth:
                continue
            for edge in self.kg._adj.get(nid, []):
                if edge.relation == "cite" and edge.dst_id not in visited:
                    visited.add(edge.dst_id)
                    next_d = d + 1
                    max_d = max(max_d, next_d)
                    queue.append((edge.dst_id, next_d))
        return float(max_d)


def create_kg_embedder(config) -> "tuple[Optional[KGEmbedder], Optional[Any]]":
    """从 AMiner 数据文件构建 KG 并返回 (KGEmbedder, KnowledgeGraph)。

    供 train.py 和 RecommendationService 共用，消除重复 KG 构建代码。
    若 config.use_kg=False 或构建失败则返回 (None, None)。
    """
    if not config.use_kg:
        return None, None
    try:
        from dataset.aminer_loader import AMinerLoader
        from knowledge_graph.kg_builder import KGBuilder

        loader = AMinerLoader()
        papers = loader.load_papers(limit=500)
        authors = loader.load_authors(limit=200)
        citations = loader.load_citations(papers)

        kg = KGBuilder(min_keyword_freq=1).build(papers, authors, citations)
        embedder = KGEmbedder(kg, embed_dim=config.kg_embedding_dim)
        logger.info(f"KG Embedder 构建完成：{len(papers)} 篇论文")
        return embedder, kg
    except Exception as e:
        logger.warning(f"KG Embedder 构建失败，回退为无 KG 模式: {e}")
        return None, None
