# knowledge_graph/graph_storage.py
# 知识图谱持久化存储模块 —— JSON / NetworkX / Neo4j（预留）

from __future__ import annotations
import os
import json
import logging
import pickle
from typing import Optional

from knowledge_graph.kg_builder import KnowledgeGraph, KGNode, KGEdge

logger = logging.getLogger(__name__)


class GraphStorage:
    """
    知识图谱存储管理器。

    支持后端：
      - JSON 文件（默认，轻量级，适合开发）
      - Pickle（二进制，加载更快）
      - NetworkX（图算法分析）
      - Neo4j（预留，生产环境图数据库）
    """

    def __init__(self, storage_dir: str = "data/kg"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        self.json_path   = os.path.join(storage_dir, "knowledge_graph.json")
        self.pickle_path = os.path.join(storage_dir, "knowledge_graph.pkl")

    # ── JSON 存储 ──────────────────────────────────────────────────

    def save_json(self, kg: KnowledgeGraph) -> None:
        """将知识图谱序列化为 JSON 文件。"""
        data = {
            "stats": kg.stats,
            "nodes": [
                {
                    "node_id":   n.node_id,
                    "node_type": n.node_type,
                    "label":     n.label,
                    "properties": n.properties,
                }
                for n in kg.nodes.values()
            ],
            "edges": [
                {
                    "src_id":   e.src_id,
                    "dst_id":   e.dst_id,
                    "relation": e.relation,
                    "weight":   e.weight,
                }
                for e in kg.edges
            ],
        }
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"知识图谱已保存 JSON：{self.json_path}（{os.path.getsize(self.json_path)//1024}KB）")

    def load_json(self) -> KnowledgeGraph:
        """从 JSON 文件加载知识图谱。"""
        with open(self.json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        kg = KnowledgeGraph()
        for n in data["nodes"]:
            kg.add_node(KGNode(
                node_id=n["node_id"], node_type=n["node_type"],
                label=n["label"], properties=n.get("properties", {}),
            ))
        for e in data["edges"]:
            kg.add_edge(KGEdge(
                src_id=e["src_id"], dst_id=e["dst_id"],
                relation=e["relation"], weight=e.get("weight", 1.0),
            ))
        logger.info(f"知识图谱已加载：{kg.stats}")
        return kg

    # ── Pickle 存储（快速序列化）─────────────────────────────────

    def save_pickle(self, kg: KnowledgeGraph) -> None:
        with open(self.pickle_path, "wb") as f:
            pickle.dump(kg, f)
        logger.info(f"知识图谱已保存 Pickle：{self.pickle_path}")

    def load_pickle(self) -> KnowledgeGraph:
        with open(self.pickle_path, "rb") as f:
            kg = pickle.load(f)
        logger.info(f"知识图谱已从 Pickle 加载：{kg.stats}")
        return kg

    # ── NetworkX 导出（用于图算法分析）──────────────────────────

    def to_networkx(self, kg: KnowledgeGraph, relation_filter: Optional[str] = None):
        """
        将知识图谱转换为 NetworkX DiGraph。

        Args:
            relation_filter: 仅保留特定关系类型的边（None 保留全部）

        Returns:
            nx.DiGraph 对象，可用于 PageRank、社区发现等算法
        """
        try:
            import networkx as nx
        except ImportError:
            raise ImportError("请安装 networkx：pip install networkx")

        G = nx.DiGraph()
        for node in kg.nodes.values():
            G.add_node(node.node_id, node_type=node.node_type, label=node.label)
        for edge in kg.edges:
            if relation_filter is None or edge.relation == relation_filter:
                G.add_edge(edge.src_id, edge.dst_id,
                           relation=edge.relation, weight=edge.weight)
        logger.info(f"NetworkX 图创建完成：{G.number_of_nodes()} 节点，{G.number_of_edges()} 边")
        return G

    # ── Neo4j 接入接口（预留）─────────────────────────────────────

    def save_to_neo4j(self, kg: KnowledgeGraph, uri: str, user: str, password: str) -> None:
        """
        将知识图谱导入 Neo4j 图数据库（预留接口）。

        接入步骤：
          1. 安装 Neo4j Desktop：https://neo4j.com/download/
          2. 安装驱动：pip install neo4j
          3. 创建图谱实例，配置 uri/user/password
          4. 取消注释并运行本方法

        Cypher 示例：
            CREATE (p:Paper {paper_id: $id, title: $title})
            CREATE (a:Author {author_id: $id, name: $name})
            MATCH (a:Author {author_id: $aid}), (p:Paper {paper_id: $pid})
            CREATE (a)-[:AUTHOR_OF]->(p)
        """
        raise NotImplementedError("Neo4j 导入接口待实现")

    def load_from_neo4j(self, uri: str, user: str, password: str) -> KnowledgeGraph:
        """从 Neo4j 加载知识图谱（预留）。"""
        raise NotImplementedError("Neo4j 加载接口待实现")

    # ── 便捷方法 ──────────────────────────────────────────────────

    def save(self, kg: KnowledgeGraph, format: str = "both") -> None:
        """保存知识图谱（默认同时保存 JSON 和 Pickle）。"""
        if format in ("json", "both"):
            self.save_json(kg)
        if format in ("pickle", "both"):
            self.save_pickle(kg)

    def load(self, prefer: str = "pickle") -> KnowledgeGraph:
        """加载知识图谱（优先 Pickle，其次 JSON）。"""
        if prefer == "pickle" and os.path.exists(self.pickle_path):
            return self.load_pickle()
        elif os.path.exists(self.json_path):
            return self.load_json()
        raise FileNotFoundError(f"未找到知识图谱文件于 {self.storage_dir}")

    def exists(self) -> bool:
        """检查是否已有保存的知识图谱。"""
        return os.path.exists(self.pickle_path) or os.path.exists(self.json_path)
