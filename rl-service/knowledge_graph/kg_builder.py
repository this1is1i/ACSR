# knowledge_graph/kg_builder.py
# 科研知识图谱构建模块

from __future__ import annotations
import json
import os
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Any
from collections import defaultdict

from dataset.aminer_loader import Paper, Author, Citation

logger = logging.getLogger(__name__)


# ── 图数据结构 ────────────────────────────────────────────────────

@dataclass
class KGNode:
    """知识图谱节点。"""
    node_id: str
    node_type: str        # "paper" | "author" | "keyword" | "venue"
    label: str            # 显示名称
    properties: Dict[str, Any] = field(default_factory=dict)
    # 预留 embedding 接口（用于 GNN 训练）
    embedding: Optional[List[float]] = None


@dataclass
class KGEdge:
    """知识图谱边（关系）。"""
    src_id: str
    dst_id: str
    relation: str         # "author_of" | "cite" | "has_keyword" | "publish_in" | "co_author"
    weight: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgeGraph:
    """
    科研知识图谱容器。

    节点类型：
        Paper    → 论文节点
        Author   → 作者节点
        Keyword  → 关键词节点
        Venue    → 发表场所节点

    边类型：
        author_of    Author → Paper    作者撰写论文
        cite         Paper  → Paper    论文引用关系
        has_keyword  Paper  → Keyword  论文包含关键词
        publish_in   Paper  → Venue    论文发表在期刊/会议
        co_author    Author ↔ Author   合著关系（对称边）
    """
    nodes: Dict[str, KGNode] = field(default_factory=dict)
    edges: List[KGEdge] = field(default_factory=list)

    # 索引（加速查询）
    _adj: Dict[str, List[KGEdge]] = field(default_factory=lambda: defaultdict(list))
    _rev_adj: Dict[str, List[KGEdge]] = field(default_factory=lambda: defaultdict(list))

    def add_node(self, node: KGNode) -> None:
        self.nodes[node.node_id] = node

    def add_edge(self, edge: KGEdge) -> None:
        self.edges.append(edge)
        self._adj[edge.src_id].append(edge)
        self._rev_adj[edge.dst_id].append(edge)

    @property
    def stats(self) -> Dict[str, int]:
        """图统计信息。"""
        type_count = defaultdict(int)
        for node in self.nodes.values():
            type_count[node.node_type] += 1
        rel_count = defaultdict(int)
        for edge in self.edges:
            rel_count[edge.relation] += 1
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            **{f"node_{k}": v for k, v in type_count.items()},
            **{f"edge_{k}": v for k, v in rel_count.items()},
        }


# ── 图谱构建器 ────────────────────────────────────────────────────

class KGBuilder:
    """
    科研知识图谱构建器。

    构建流程：
        1. 添加 Paper 节点
        2. 添加 Author 节点
        3. 添加 Keyword 节点（合并同义词）
        4. 添加 Venue 节点
        5. 构建 author_of 边
        6. 构建 cite 边
        7. 构建 has_keyword 边
        8. 构建 publish_in 边
        9. 推导 co_author 边
    """

    def __init__(
        self,
        min_keyword_freq: int = 2,    # 关键词最小出现频次（过滤低频噪声词）
        max_keyword_nodes: int = 500, # 最多保留的关键词节点数
    ):
        self.min_keyword_freq = min_keyword_freq
        self.max_keyword_nodes = max_keyword_nodes

    def build(
        self,
        papers: List[Paper],
        authors: List[Author],
        citations: List[Citation],
    ) -> KnowledgeGraph:
        """
        构建完整科研知识图谱。

        Args:
            papers:    论文列表（已预处理）
            authors:   作者列表
            citations: 引用关系列表

        Returns:
            KnowledgeGraph 对象
        """
        kg = KnowledgeGraph()

        logger.info("开始构建知识图谱...")

        # 1. Paper 节点
        self._add_paper_nodes(kg, papers)
        logger.info(f"Paper 节点：{len(papers)}")

        # 2. Author 节点
        self._add_author_nodes(kg, authors)
        logger.info(f"Author 节点：{len(authors)}")

        # 3-4. Keyword & Venue 节点
        kw_count = self._add_keyword_venue_nodes(kg, papers)
        logger.info(f"Keyword 节点：{kw_count['keywords']}，Venue 节点：{kw_count['venues']}")

        # 5. author_of 边
        self._add_author_of_edges(kg, papers, authors)

        # 6. cite 边
        paper_ids = {p.paper_id for p in papers}
        for c in citations:
            if c.citing_paper_id in paper_ids and c.cited_paper_id in paper_ids:
                kg.add_edge(KGEdge(
                    src_id=c.citing_paper_id,
                    dst_id=c.cited_paper_id,
                    relation="cite",
                    weight=1.0,
                ))

        # 7-8. has_keyword & publish_in 边
        self._add_keyword_venue_edges(kg, papers)

        # 9. co_author 边（推导）
        self._add_co_author_edges(kg, papers)

        stats = kg.stats
        logger.info(f"知识图谱构建完成：{stats}")
        return kg

    # ── 节点添加 ──────────────────────────────────────────────────

    def _add_paper_nodes(self, kg: KnowledgeGraph, papers: List[Paper]) -> None:
        for p in papers:
            kg.add_node(KGNode(
                node_id=p.paper_id,
                node_type="paper",
                label=p.title[:60],
                properties={
                    "year": p.year,
                    "venue": p.venue,
                    "keywords": p.keywords,
                    "citation_count": p.citation_count,
                },
            ))

    def _add_author_nodes(self, kg: KnowledgeGraph, authors: List[Author]) -> None:
        author_map = {a.author_id: a for a in authors}
        for a in authors:
            kg.add_node(KGNode(
                node_id=a.author_id,
                node_type="author",
                label=a.name,
                properties={"org": a.org, "interests": a.interests},
            ))

    def _add_keyword_venue_nodes(
        self, kg: KnowledgeGraph, papers: List[Paper]
    ) -> Dict[str, int]:
        """添加关键词和 Venue 节点，按频次过滤低频关键词。"""
        from collections import Counter
        kw_freq: Counter = Counter()
        venues: Set[str] = set()

        for p in papers:
            for kw in p.keywords:
                kw_normalized = kw.strip().lower()
                if kw_normalized:
                    kw_freq[kw_normalized] += 1
            if p.venue and p.venue.strip():
                venues.add(p.venue.strip())

        # 过滤低频关键词，保留 Top-N
        top_kws = [
            kw for kw, cnt in kw_freq.most_common(self.max_keyword_nodes)
            if cnt >= self.min_keyword_freq
        ]
        for kw in top_kws:
            kg.add_node(KGNode(
                node_id=f"kw_{kw.replace(' ', '_')}",
                node_type="keyword",
                label=kw,
                properties={"frequency": kw_freq[kw]},
            ))

        for venue in venues:
            kg.add_node(KGNode(
                node_id=f"venue_{venue.replace(' ', '_')[:30]}",
                node_type="venue",
                label=venue,
            ))

        return {"keywords": len(top_kws), "venues": len(venues)}

    # ── 边添加 ────────────────────────────────────────────────────

    def _add_author_of_edges(
        self,
        kg: KnowledgeGraph,
        papers: List[Paper],
        authors: List[Author],
    ) -> None:
        author_ids = {a.author_id for a in authors}
        for p in papers:
            for aid in p.authors:
                if aid in author_ids and aid in kg.nodes:
                    kg.add_edge(KGEdge(
                        src_id=aid,
                        dst_id=p.paper_id,
                        relation="author_of",
                    ))

    def _add_keyword_venue_edges(
        self, kg: KnowledgeGraph, papers: List[Paper]
    ) -> None:
        for p in papers:
            for kw in p.keywords:
                kw_id = f"kw_{kw.strip().lower().replace(' ', '_')}"
                if kw_id in kg.nodes:
                    kg.add_edge(KGEdge(
                        src_id=p.paper_id,
                        dst_id=kw_id,
                        relation="has_keyword",
                    ))
            if p.venue:
                venue_id = f"venue_{p.venue.replace(' ', '_')[:30]}"
                if venue_id in kg.nodes:
                    kg.add_edge(KGEdge(
                        src_id=p.paper_id,
                        dst_id=venue_id,
                        relation="publish_in",
                    ))

    def _add_co_author_edges(
        self, kg: KnowledgeGraph, papers: List[Paper]
    ) -> None:
        """推导合著边：共同撰写同一论文的作者之间建立合著关系。"""
        co_pairs: Set[tuple] = set()
        for p in papers:
            authors_in_kg = [a for a in p.authors if a in kg.nodes]
            for i in range(len(authors_in_kg)):
                for j in range(i + 1, len(authors_in_kg)):
                    pair = tuple(sorted([authors_in_kg[i], authors_in_kg[j]]))
                    if pair not in co_pairs:
                        co_pairs.add(pair)
                        kg.add_edge(KGEdge(
                            src_id=pair[0],
                            dst_id=pair[1],
                            relation="co_author",
                            weight=1.0,
                        ))

    # ── 引用计数更新 ──────────────────────────────────────────────

    def update_citation_counts(self, kg: KnowledgeGraph) -> None:
        """统计每篇论文被引次数，更新 Paper 节点属性。"""
        from collections import Counter
        cited_count: Counter = Counter()
        for edge in kg.edges:
            if edge.relation == "cite":
                cited_count[edge.dst_id] += 1
        for node_id, count in cited_count.items():
            if node_id in kg.nodes:
                kg.nodes[node_id].properties["citation_count"] = count
