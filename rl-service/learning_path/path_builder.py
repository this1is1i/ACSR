# learning_path/path_builder.py
# 学习路径生成模块 —— 基于知识图谱构建用户科研学习轨迹

from __future__ import annotations
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

from knowledge_graph.kg_builder import KnowledgeGraph
from knowledge_graph.graph_query import GraphQuery

logger = logging.getLogger(__name__)


@dataclass
class PathNode:
    """学习路径中的一个知识点节点。"""
    node_id: str
    label: str                      # 知识点名称（关键词 / 论文标题）
    node_type: str                  # "keyword" | "paper"
    mastery: float = 0.0            # 掌握度 [0, 1]
    depth: int = 0                  # 在路径中的深度
    prerequisite_ids: List[str] = field(default_factory=list)
    year: Optional[int] = None
    properties: Dict = field(default_factory=dict)


@dataclass
class LearningPath:
    """完整学习路径。"""
    user_id: str
    nodes: List[PathNode]           # 有序的学习节点序列
    edges: List[Tuple[str, str, float]]  # (src_id, dst_id, weight)
    topic: str = ""                 # 学习主题
    estimated_hours: float = 0.0    # 预估学习时长（小时）
    coverage: float = 0.0           # 领域覆盖率


class PathBuilder:
    """
    科研学习路径生成器。

    算法：
        1. 从用户历史阅读中识别已掌握知识点
        2. 在知识图谱中查找前置知识 → 目标知识的路径
        3. 按论文发表年份 / 引用关系确定学习顺序
        4. 融合强化学习推荐分数调整路径优先级

    生成的路径用于：
        - 三维学习路径可视化（前端 Three.js）
        - 推荐系统解释：「为了理解此论文，建议先阅读...」
        - 用户科研进度追踪
    """

    def __init__(self, kg: KnowledgeGraph, query: Optional[GraphQuery] = None):
        self.kg = kg
        self.query = query or GraphQuery(kg)

    # ── 主接口 ────────────────────────────────────────────────────

    def build_path(
        self,
        user_id: str,
        user_history: List[str],       # 用户已读论文 paper_id 列表
        target_topic: str,             # 目标研究方向（关键词）
        max_nodes: int = 20,
        include_papers: bool = True,   # 是否在路径中包含论文节点
    ) -> LearningPath:
        """
        为用户生成从当前知识状态到目标主题的学习路径。

        Args:
            user_id:       用户 ID
            user_history:  已读论文 ID 列表
            target_topic:  目标研究方向关键词
            max_nodes:     路径最大节点数
            include_papers: 是否包含具体论文节点

        Returns:
            LearningPath 对象
        """
        # 1. 识别用户已掌握的关键词（来自历史阅读）
        known_keywords = self._extract_known_keywords(user_history)
        logger.info(f"用户 [{user_id}] 已知关键词：{len(known_keywords)} 个")

        # 2. 获取目标主题的关键词簇
        target_cluster = self.query.get_keyword_cluster(target_topic, k=max_nodes)
        target_papers  = [p["paper_id"] for p in target_cluster["papers"]]
        related_kws    = [r["keyword_id"] for r in target_cluster["related_keywords"]]

        # 3. 构建路径节点序列（按层级深度排列）
        path_nodes = self._build_path_nodes(
            known_keywords=known_keywords,
            target_kw=f"kw_{target_topic.strip().lower().replace(' ', '_')}",
            related_kws=related_kws,
            target_papers=target_papers,
            include_papers=include_papers,
            max_nodes=max_nodes,
        )

        # 4. 构建路径边
        path_edges = self._build_path_edges(path_nodes)

        # 5. 估算学习时长（每篇论文约 2 小时）
        paper_count = sum(1 for n in path_nodes if n.node_type == "paper")
        estimated_hours = paper_count * 2.0

        # 6. 计算领域覆盖率
        coverage = min(len(known_keywords) / max(len(related_kws) + 1, 1), 1.0)

        path = LearningPath(
            user_id=user_id,
            nodes=path_nodes,
            edges=path_edges,
            topic=target_topic,
            estimated_hours=estimated_hours,
            coverage=coverage,
        )
        logger.info(
            f"学习路径生成完成：{len(path_nodes)} 个节点，"
            f"预估学习时长 {estimated_hours:.1f} 小时"
        )
        return path

    def build_prerequisite_chain(
        self,
        target_paper_id: str,
        depth: int = 3,
    ) -> List[PathNode]:
        """
        为目标论文生成前置知识链（从基础到高级）。

        例如：Machine Learning → Deep Learning → Transformer → BERT

        Args:
            target_paper_id: 目标论文 ID
            depth:           向前追溯的层数

        Returns:
            有序 PathNode 列表（前置优先）
        """
        visited: set = set()
        chain: List[PathNode] = []
        self._dfs_prerequisites(target_paper_id, 0, depth, visited, chain)
        chain.reverse()  # 翻转为「基础 → 目标」顺序
        return chain

    # ── 内部方法 ──────────────────────────────────────────────────

    def _extract_known_keywords(self, history: List[str]) -> Dict[str, float]:
        """
        从历史阅读中提取已掌握的关键词及掌握度。

        掌握度 = 该关键词出现次数 / 历史论文总数（归一化）
        """
        kw_count: Dict[str, int] = defaultdict(int)
        total = len(history)
        if total == 0:
            return {}

        for paper_id in history:
            node = self.kg.nodes.get(paper_id)
            if not node:
                continue
            for kw_id in node.properties.get("keywords", []):
                raw = kw_id.strip().lower().replace(' ', '_')
                kw_node_id = raw if raw.startswith("kw_") else f"kw_{raw}"
                if kw_node_id in self.kg.nodes:
                    kw_count[kw_node_id] += 1

        return {kw: cnt / total for kw, cnt in kw_count.items()}

    def _build_path_nodes(
        self,
        known_keywords: Dict[str, float],
        target_kw: str,
        related_kws: List[str],
        target_papers: List[str],
        include_papers: bool,
        max_nodes: int,
    ) -> List[PathNode]:
        """构建有序路径节点列表。"""
        nodes: List[PathNode] = []
        seen: set = set()

        # 已掌握关键词（depth=0）
        for kw_id, mastery in list(known_keywords.items())[:5]:
            if kw_id in self.kg.nodes and kw_id not in seen:
                node = self.kg.nodes[kw_id]
                nodes.append(PathNode(
                    node_id=kw_id, label=node.label,
                    node_type="keyword", mastery=mastery, depth=0,
                ))
                seen.add(kw_id)

        # 相关关键词（depth=1）
        for kw_id in related_kws:
            if kw_id in self.kg.nodes and kw_id not in seen:
                node = self.kg.nodes[kw_id]
                mastery = known_keywords.get(kw_id, 0.0)
                nodes.append(PathNode(
                    node_id=kw_id, label=node.label,
                    node_type="keyword", mastery=mastery, depth=1,
                ))
                seen.add(kw_id)

        # 目标关键词（depth=2）
        if target_kw in self.kg.nodes and target_kw not in seen:
            node = self.kg.nodes[target_kw]
            nodes.append(PathNode(
                node_id=target_kw, label=node.label,
                node_type="keyword", mastery=known_keywords.get(target_kw, 0.0),
                depth=2,
            ))
            seen.add(target_kw)

        # 目标论文（depth=3）
        if include_papers:
            for pid in target_papers:
                if pid in self.kg.nodes and pid not in seen and len(nodes) < max_nodes:
                    node = self.kg.nodes[pid]
                    nodes.append(PathNode(
                        node_id=pid, label=node.label,
                        node_type="paper", mastery=0.0, depth=3,
                        year=node.properties.get("year"),
                    ))
                    seen.add(pid)

        return nodes[:max_nodes]

    def _build_path_edges(
        self, nodes: List[PathNode]
    ) -> List[Tuple[str, str, float]]:
        """基于节点顺序和深度构建路径边（depth → depth+1）。"""
        edges = []
        node_map = {n.node_id: n for n in nodes}
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                ni, nj = nodes[i], nodes[j]
                if nj.depth == ni.depth + 1:
                    weight = 1.0 / (abs(i - j) + 1)
                    edges.append((ni.node_id, nj.node_id, weight))
                    if len(edges) > 50:  # 防止边过多
                        break
        return edges

    def _dfs_prerequisites(
        self,
        paper_id: str,
        cur_depth: int,
        max_depth: int,
        visited: set,
        chain: List[PathNode],
    ) -> None:
        """DFS 递归追溯前置论文。"""
        if cur_depth >= max_depth or paper_id in visited:
            return
        visited.add(paper_id)
        node = self.kg.nodes.get(paper_id)
        if not node:
            return
        chain.append(PathNode(
            node_id=paper_id, label=node.label,
            node_type="paper", mastery=0.0, depth=cur_depth,
            year=node.properties.get("year"),
        ))
        # 递归到被引用的论文（前置知识）
        for edge in self.kg._adj.get(paper_id, []):
            if edge.relation == "cite":
                self._dfs_prerequisites(
                    edge.dst_id, cur_depth + 1, max_depth, visited, chain
                )

    def to_dict(self, path: LearningPath) -> dict:
        """序列化学习路径为 JSON 格式（供前端三维可视化使用）。"""
        return {
            "user_id": path.user_id,
            "topic": path.topic,
            "estimated_hours": path.estimated_hours,
            "coverage": round(path.coverage, 4),
            "nodes": [
                {
                    "node_id":   n.node_id,
                    "label":     n.label,
                    "node_type": n.node_type,
                    "mastery":   round(n.mastery, 4),
                    "depth":     n.depth,
                    "year":      n.year,
                }
                for n in path.nodes
            ],
            "edges": [
                {"src": e[0], "dst": e[1], "weight": round(e[2], 4)}
                for e in path.edges
            ],
        }
