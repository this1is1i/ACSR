# knowledge_graph/graph_storage.py
# 知识图谱持久化存储模块 —— JSON / NetworkX / Neo4j（预留）

from __future__ import annotations
import os
import json
import logging
import pickle
from typing import Any, Dict, Optional

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
    # ── Neo4j 接入接口 ──────────────────────────────────────────────

    def save_to_neo4j(
        self,
        kg: KnowledgeGraph,
        uri: str,
        user: str,
        password: str,
        database: str = "neo4j",
        clear_existing: bool = False,
        batch_size: int = 500,
    ) -> None:
        """将知识图谱导入 Neo4j 图数据库。"""
        try:
            from neo4j import GraphDatabase
        except ImportError:
            raise ImportError("请安装 neo4j 驱动：pip install neo4j")

        driver = GraphDatabase.driver(uri, auth=(user, password))
        try:
            with driver.session(database=database) as session:
                session.run(
                    "CREATE CONSTRAINT graph_node_id IF NOT EXISTS "
                    "FOR (n:GraphNode) REQUIRE n.node_id IS UNIQUE"
                )
                if clear_existing:
                    session.run("MATCH (n:GraphNode) DETACH DELETE n")

                grouped_nodes: Dict[str, list] = {}
                for node in kg.nodes.values():
                    grouped_nodes.setdefault(node.node_type, []).append({
                        "node_id": node.node_id,
                        "node_type": node.node_type,
                        "label": node.label,
                        "flat_properties": self._to_neo4j_properties(node.properties),
                        "embedding": node.embedding,
                        "properties_json": json.dumps(node.properties, ensure_ascii=False),
                    })

                for node_type, rows in grouped_nodes.items():
                    label = self._neo4j_label(node_type)
                    query = f"""
                    UNWIND $rows AS row
                    MERGE (n:GraphNode:{label} {{node_id: row.node_id}})
                    SET n.node_type = row.node_type,
                        n.label = row.label,
                        n.properties_json = row.properties_json
                    SET n += row.flat_properties
                    FOREACH (_ IN CASE WHEN row.embedding IS NULL THEN [] ELSE [1] END |
                        SET n.embedding = row.embedding)
                    """
                    for chunk in self._chunks(rows, batch_size):
                        session.run(query, rows=chunk)

                grouped_edges: Dict[str, list] = {}
                for edge in kg.edges:
                    grouped_edges.setdefault(edge.relation, []).append({
                        "src_id": edge.src_id,
                        "dst_id": edge.dst_id,
                        "relation": edge.relation,
                        "weight": edge.weight,
                        "properties_json": json.dumps(edge.properties, ensure_ascii=False),
                    })

                for relation, rows in grouped_edges.items():
                    rel_type = self._neo4j_rel_type(relation)
                    query = f"""
                    UNWIND $rows AS row
                    MATCH (src:GraphNode {{node_id: row.src_id}})
                    MATCH (dst:GraphNode {{node_id: row.dst_id}})
                    MERGE (src)-[r:{rel_type} {{src_id: row.src_id, dst_id: row.dst_id}}]->(dst)
                    SET r.relation = row.relation,
                        r.weight = row.weight,
                        r.properties_json = row.properties_json
                    """
                    for chunk in self._chunks(rows, batch_size):
                        session.run(query, rows=chunk)
        finally:
            driver.close()

    def load_from_neo4j(
        self,
        uri: str,
        user: str,
        password: str,
        database: str = "neo4j",
    ) -> KnowledgeGraph:
        """从 Neo4j 加载知识图谱。"""
        try:
            from neo4j import GraphDatabase
        except ImportError:
            raise ImportError("请安装 neo4j 驱动：pip install neo4j")

        driver = GraphDatabase.driver(uri, auth=(user, password))
        try:
            kg = KnowledgeGraph()
            with driver.session(database=database) as session:
                node_rows = session.run("MATCH (n:GraphNode) RETURN n").data()
                for row in node_rows:
                    node = row["n"]
                    reserved = {"node_id", "node_type", "label", "embedding", "properties_json"}
                    properties = {
                        key: value for key, value in dict(node).items()
                        if key not in reserved
                    }
                    if node.get("properties_json"):
                        try:
                            properties.update(json.loads(node["properties_json"]))
                        except json.JSONDecodeError:
                            pass
                    kg.add_node(KGNode(
                        node_id=node["node_id"],
                        node_type=node.get("node_type", "unknown"),
                        label=node.get("label", node["node_id"]),
                        properties=properties,
                        embedding=node.get("embedding"),
                    ))

                edge_rows = session.run("""
                    MATCH (src:GraphNode)-[r]->(dst:GraphNode)
                    RETURN src.node_id AS src_id,
                           dst.node_id AS dst_id,
                           type(r) AS rel_type,
                           properties(r) AS rel_props
                """).data()
                for row in edge_rows:
                    kg.add_edge(self._edge_from_row(row))
            return kg
        finally:
            driver.close()

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

    @staticmethod
    def _neo4j_label(node_type: str) -> str:
        mapping = {
            "paper": "Paper",
            "author": "Author",
            "keyword": "Keyword",
            "venue": "Venue",
        }
        return mapping.get(node_type, "GraphNode")

    @staticmethod
    def _neo4j_rel_type(relation: str) -> str:
        cleaned = "".join(ch if ch.isalnum() else "_" for ch in relation.upper())
        return cleaned or "RELATED_TO"

    @staticmethod
    def _to_neo4j_properties(properties: Dict[str, Any]) -> Dict[str, Any]:
        flattened: Dict[str, Any] = {}
        for key, value in properties.items():
            if value is None:
                continue
            if isinstance(value, (str, int, float, bool)):
                flattened[key] = value
            elif isinstance(value, list) and all(isinstance(item, (str, int, float, bool)) for item in value):
                flattened[key] = value
        return flattened

    @staticmethod
    def _chunks(rows: list, batch_size: int):
        for idx in range(0, len(rows), batch_size):
            yield rows[idx: idx + batch_size]

    @staticmethod
    def _edge_from_row(row: Dict[str, Any]) -> KGEdge:
        rel_props = row.get("rel_props") or {}
        relation = rel_props.get("relation") or row.get("rel_type") or "RELATED_TO"
        weight = rel_props.get("weight", 1.0)
        # Normalize: HAS_KEYWORD → has_keyword, CITE → cite, etc.
        norm_relation = str(relation).lower().replace("-", "_")
        return KGEdge(
            src_id=row["src_id"],
            dst_id=row["dst_id"],
            relation=norm_relation,
            weight=float(weight if weight is not None else 1.0),
        )
