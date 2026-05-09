# knowledge_graph/graph_query.py
# 知识图谱查询模块 —— 支持推荐解释、学习路径生成

from __future__ import annotations
import logging
from typing import List, Dict, Set, Optional, Tuple, Any
from collections import defaultdict, deque

from knowledge_graph.kg_builder import KnowledgeGraph, KGNode, KGEdge

logger = logging.getLogger(__name__)


class GraphQuery:
    """
    知识图谱查询引擎。

    提供：
      - 相关论文查询（基于引用 / 关键词 / 作者）
      - 作者邻居查询（合著网络）
      - 关键词聚类查询
      - 最短路径查询（学习路径生成基础）
      - 推荐解释生成（结合图结构）
    """

    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg
        # 预建索引
        self._paper_kw_idx:  Dict[str, List[str]] = defaultdict(list)  # paper_id → kw_ids
        self._kw_paper_idx:  Dict[str, List[str]] = defaultdict(list)  # kw_id → paper_ids
        self._cite_idx:      Dict[str, List[str]] = defaultdict(list)  # cited → citing (反向)
        self._author_idx:    Dict[str, List[str]] = defaultdict(list)  # paper_id → author_ids
        self._build_indices()

    def _build_indices(self) -> None:
        """构建查询加速索引（兼容大小写和驼峰变体）。"""
        relation_counts: dict = {}
        for edge in self.kg.edges:
            rel = edge.relation.lower().replace("_", "")
            relation_counts[rel] = relation_counts.get(rel, 0) + 1

            if rel in ("haskeyword",):
                self._paper_kw_idx[edge.src_id].append(edge.dst_id)
                self._kw_paper_idx[edge.dst_id].append(edge.src_id)
            elif rel in ("cite",):
                self._cite_idx[edge.dst_id].append(edge.src_id)
            elif rel in ("authorof",):
                self._author_idx[edge.dst_id].append(edge.src_id)

        sample_rels = list(set(r for r in relation_counts.keys()))[:8]
        logger.info("GraphQuery 索引: paper_kw=%d, kw_paper=%d, cite=%d, author=%d, total_edges=%d, sample_rels=%s",
                     len(self._paper_kw_idx), len(self._kw_paper_idx),
                     len(self._cite_idx), len(self._author_idx),
                     len(self.kg.edges), sample_rels)

    # ── 论文相关查询 ──────────────────────────────────────────────

    def get_related_papers(
        self,
        paper_id: str,
        k: int = 10,
        methods: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取与目标论文相关的论文列表。

        相关性来源（可组合）：
          - "cite_out":    该论文引用的论文
          - "cite_in":     引用该论文的论文
          - "keyword":     共享关键词的论文
          - "co_author":   同一作者的其他论文

        Returns:
            List of {"paper_id": ..., "source": ..., "score": ...}
        """
        methods = methods or ["cite_out", "cite_in", "keyword"]
        scores: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))

        # 1. 引出关系（该论文 → 引用）
        if "cite_out" in methods:
            for edge in self.kg._adj.get(paper_id, []):
                if edge.relation == "cite":
                    scores[edge.dst_id]["cite_out"] += 1.5

        # 2. 引入关系（施引 → 该论文）
        if "cite_in" in methods:
            for citing_id in self._cite_idx.get(paper_id, []):
                scores[citing_id]["cite_in"] += 1.2

        # 3. 关键词共现
        if "keyword" in methods:
            my_kws = set(self._paper_kw_idx.get(paper_id, []))
            for kw_id in my_kws:
                for pid in self._kw_paper_idx.get(kw_id, []):
                    if pid != paper_id:
                        scores[pid]["keyword"] += 1.0 / (len(my_kws) + 1)

        # 4. 同一作者
        if "co_author" in methods:
            my_authors = set(self._author_idx.get(paper_id, []))
            for author_id in my_authors:
                for edge in self.kg._adj.get(author_id, []):
                    if edge.relation == "author_of" and edge.dst_id != paper_id:
                        scores[edge.dst_id]["co_author"] += 0.8

        # 汇总并过滤不存在的节点
        results = []
        for pid, src_scores in scores.items():
            if pid not in self.kg.nodes:
                continue
            total = sum(src_scores.values())
            node = self.kg.nodes[pid]
            results.append({
                "paper_id": pid,
                "title": node.label,
                "score": round(total, 4),
                "sources": dict(src_scores),
            })

        results.sort(key=lambda x: -x["score"])
        return results[:k]

    def get_author_neighbors(
        self,
        author_id: str,
        hops: int = 1,
    ) -> List[Dict[str, Any]]:
        """
        获取作者的合著网络邻居。

        Args:
            author_id: 目标作者 ID
            hops:      跳数（1=直接合著者，2=二阶合著者）

        Returns:
            List of {"author_id": ..., "name": ..., "hop": ...}
        """
        visited: Dict[str, int] = {author_id: 0}
        queue = deque([(author_id, 0)])
        results = []

        while queue:
            cur_id, cur_hop = queue.popleft()
            if cur_hop >= hops:
                continue
            for edge in self.kg._adj.get(cur_id, []):
                if edge.relation == "co_author" and edge.dst_id not in visited:
                    visited[edge.dst_id] = cur_hop + 1
                    queue.append((edge.dst_id, cur_hop + 1))
            # 反向合著边
            for edge in self.kg._rev_adj.get(cur_id, []):
                if edge.relation == "co_author" and edge.src_id not in visited:
                    visited[edge.src_id] = cur_hop + 1
                    queue.append((edge.src_id, cur_hop + 1))

        for nid, hop in visited.items():
            if nid == author_id:
                continue
            node = self.kg.nodes.get(nid)
            if node and node.node_type == "author":
                results.append({
                    "author_id": nid,
                    "name": node.label,
                    "org": node.properties.get("org", ""),
                    "hop": hop,
                })
        return sorted(results, key=lambda x: x["hop"])

    def get_keyword_cluster(
        self,
        keyword: str,
        k: int = 5,
    ) -> Dict[str, Any]:
        """
        获取关键词聚类：包含该关键词的论文及相关关键词。

        Returns:
            {
                "keyword": ...,
                "papers": [...],
                "related_keywords": [...],
                "frequency": ...
            }
        """
        kw_id = f"kw_{keyword.strip().lower().replace(' ', '_')}"
        papers_with_kw = self._kw_paper_idx.get(kw_id, [])

        # 相关关键词（共现频次）
        co_kw_count: Dict[str, int] = defaultdict(int)
        for pid in papers_with_kw:
            for other_kw in self._paper_kw_idx.get(pid, []):
                if other_kw != kw_id:
                    co_kw_count[other_kw] += 1

        related_kws = [
            {"keyword_id": kid, "label": self.kg.nodes[kid].label if kid in self.kg.nodes else kid,
             "co_occurrence": cnt}
            for kid, cnt in sorted(co_kw_count.items(), key=lambda x: -x[1])[:k]
        ]

        papers = []
        for pid in papers_with_kw[:k]:
            node = self.kg.nodes.get(pid)
            if node:
                papers.append({
                    "paper_id": pid,
                    "title": node.label,
                    "year": node.properties.get("year"),
                    "citation_count": node.properties.get("citation_count", 0),
                })

        return {
            "keyword": keyword,
            "keyword_id": kw_id,
            "frequency": len(papers_with_kw),
            "papers": papers,
            "related_keywords": related_kws,
        }

    # ── 路径查询 ──────────────────────────────────────────────────

    def shortest_path(
        self,
        src_id: str,
        dst_id: str,
        max_hops: int = 4,
        relation_filter: Optional[List[str]] = None,
    ) -> Optional[List[str]]:
        """
        BFS 最短路径查询（用于学习路径生成）。

        Args:
            src_id:          起点节点 ID
            dst_id:          终点节点 ID
            max_hops:        最大跳数
            relation_filter: 仅沿特定关系类型边游走

        Returns:
            路径节点 ID 列表（含起终点），未找到返回 None
        """
        if src_id not in self.kg.nodes or dst_id not in self.kg.nodes:
            return None
        if src_id == dst_id:
            return [src_id]

        visited = {src_id: None}
        queue = deque([src_id])

        while queue:
            cur = queue.popleft()
            for edge in self.kg._adj.get(cur, []):
                if relation_filter and edge.relation not in relation_filter:
                    continue
                nxt = edge.dst_id
                if nxt not in visited:
                    visited[nxt] = cur
                    if nxt == dst_id:
                        # 回溯路径
                        path = []
                        node = nxt
                        while node is not None:
                            path.append(node)
                            node = visited[node]
                        return list(reversed(path))
                    if len(visited) <= max_hops * 1000:
                        queue.append(nxt)
        return None

    # ── 推荐解释增强 ──────────────────────────────────────────────

    def explain_recommendation(
        self,
        user_history: List[str],
        recommended_paper_id: str,
    ) -> List[str]:
        """
        基于图谱结构生成推荐解释（增强版）。

        Returns:
            解释字符串列表（多条理由）
        """
        reasons: List[str] = []
        rec_node = self.kg.nodes.get(recommended_paper_id)
        if not rec_node:
            return ["基于您的科研兴趣推荐"]

        rec_kws = set(self._paper_kw_idx.get(recommended_paper_id, []))
        rec_authors = set(self._author_idx.get(recommended_paper_id, []))

        for hist_id in user_history[-5:]:  # 取最近 5 篇历史
            hist_node = self.kg.nodes.get(hist_id)
            if not hist_node:
                continue
            hist_kws = set(self._paper_kw_idx.get(hist_id, []))

            # ① 关键词重叠
            overlap_kws = rec_kws & hist_kws
            if overlap_kws:
                kw_labels = [
                    self.kg.nodes[k].label for k in list(overlap_kws)[:2]
                    if k in self.kg.nodes
                ]
                if kw_labels:
                    reasons.append(
                        f"与您阅读的《{hist_node.label[:30]}》共享关键词：{', '.join(kw_labels)}"
                    )

            # ② 引用关系（兼容大小写）
            for edge in self.kg._adj.get(recommended_paper_id, []):
                if edge.relation.lower() in ("cite",) and edge.dst_id == hist_id:
                    reasons.append(
                        f"该论文引用了您读过的《{hist_node.label[:30]}》"
                    )
                    break

            # ③ 被历史论文引用
            if hist_id in self._cite_idx.get(recommended_paper_id, []):
                reasons.append(
                    f"您的历史阅读《{hist_node.label[:30]}》引用了该论文"
                )

            # ④ 同一作者
            hist_authors = set(self._author_idx.get(hist_id, []))
            common_authors = rec_authors & hist_authors
            if common_authors:
                for aid in list(common_authors)[:1]:
                    author_node = self.kg.nodes.get(aid)
                    if author_node:
                        reasons.append(
                            f"该论文与您阅读的论文来自同一作者：{author_node.label}"
                        )

        if not reasons:
            # 通用解释：基于关键词领域
            kw_labels = [
                self.kg.nodes[k].label for k in list(rec_kws)[:2]
                if k in self.kg.nodes
            ]
            if kw_labels:
                reasons.append(f"属于您感兴趣的研究领域：{', '.join(kw_labels)}")
            else:
                reasons.append("基于强化学习算法推测您可能感兴趣的内容")

        return list(dict.fromkeys(reasons))[:4]  # 去重，最多返回 4 条
