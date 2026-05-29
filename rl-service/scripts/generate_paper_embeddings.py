#!/usr/bin/env python
# scripts/generate_paper_embeddings.py
# 离线脚本：为全库论文生成预存向量并写入 MySQL + Neo4j
#
# 用法: python scripts/generate_paper_embeddings.py
#
# 流程:
#   1. 连接 MySQL，读取全部 paper 行
#   2. 尝试加载 Neo4j KG，创建 KGEmbedder
#   3. 收集全库统计量（均值、标准差，用于 Z-score 归一化）
#   4. 对每篇论文提取 10 维结构特征 → Z-score → project(10×32) → L2-norm
#   5. UPDATE paper SET embedding=JSON_ARRAY(32d), embedding_raw=JSON_ARRAY(10d)
#   6. 若 Neo4j 可用，同步更新 Paper 节点的 embedding / embedding_raw 属性

from __future__ import annotations
import json
import logging
import os
import sys
import numpy as np

# 将项目根目录加入路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import default_config
from knowledge_graph.kg_embedder import KGEmbedder

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("generate_embeddings")

# 投影矩阵种子（与 config.embedding_seed 一致）
EMBEDDING_SEED = 42
RAW_FEATURE_DIM = 10
EMBEDDING_DIM = 32


def connect_mysql(config):
    """连接 MySQL 并返回连接对象。"""
    try:
        import pymysql
        conn = pymysql.connect(
            host=config.mysql_host,
            port=config.mysql_port,
            user=config.mysql_user,
            password=config.mysql_password,
            database=config.mysql_db,
            charset="utf8mb4",
        )
        logger.info(f"MySQL 已连接: {config.mysql_host}:{config.mysql_port}/{config.mysql_db}")
        return conn
    except ImportError:
        logger.error("pymysql 未安装，请执行: pip install pymysql")
        raise
    except Exception as e:
        logger.error(f"MySQL 连接失败: {e}")
        raise


def load_kg_and_embedder(config):
    """尝试从 Neo4j 加载 KG 并创建 KGEmbedder。返回 (KGEmbedder, KnowledgeGraph) 或 (None, None)。"""
    if not config.use_kg or not config.neo4j_password:
        logger.info("KG 未配置，跳过 Neo4j 加载")
        return None, None
    try:
        from knowledge_graph.graph_storage import GraphStorage
        storage = GraphStorage()
        kg = storage.load_from_neo4j(
            uri=config.neo4j_uri,
            user=config.neo4j_user,
            password=config.neo4j_password,
            database=config.neo4j_database,
        )
        embedder = KGEmbedder(kg, embed_dim=config.kg_embedding_dim, seed=EMBEDDING_SEED)
        paper_count = sum(1 for n in kg.nodes.values() if n.node_type == "paper")
        logger.info(f"KG 已加载: {paper_count} 篇论文节点")
        return embedder, kg
    except Exception as e:
        logger.warning(f"Neo4j 加载失败: {e}")
        return None, None


def collect_global_stats(cursor):
    """收集全库论文的统计量：max_citation, max_keywords。"""
    cursor.execute("SELECT MAX(citation_count), MAX(year), MIN(year) FROM paper WHERE deleted = 0")
    row = cursor.fetchone()
    max_cite = max((row[0] or 0), 1)
    max_year = max((row[1] or 2024), 2024)
    min_year = min((row[2] or 2010), 2010)

    # 关键词数量需要解析 JSON 数组
    cursor.execute("SELECT keywords FROM paper WHERE deleted = 0 AND keywords IS NOT NULL")
    max_kw = 1
    for (kw_str,) in cursor:
        if kw_str:
            try:
                kw_list = json.loads(kw_str) if isinstance(kw_str, str) else kw_str
                if isinstance(kw_list, list):
                    max_kw = max(max_kw, len(kw_list))
            except (json.JSONDecodeError, TypeError):
                pass

    return {
        "max_citation": max_cite,
        "max_keywords": max_kw,
        "max_year": max_year,
        "min_year": min_year,
    }


def extract_10d_for_paper(paper_row, kg_embedder, global_stats):
    """对单篇论文提取 10 维原始结构特征。

    优先级: KG 节点特征 > MySQL 元数据近似特征
    """
    aminer_id = paper_row.get("aminer_id")
    if kg_embedder is not None and aminer_id:
        emb = kg_embedder.get_paper_embedding(aminer_id)
        if emb is not None:
            # KG 中已存在该论文：提取原始特征
            try:
                raw = kg_embedder._extract_structural_features(aminer_id)
                return raw
            except Exception:
                pass

    # 回退：从 MySQL 元数据提取
    return KGEmbedder.extract_features_from_metadata(paper_row, global_stats)


def main():
    config = default_config
    logger.info("=== 论文向量生成脚本开始 ===")

    # 1. 连接 MySQL
    conn = connect_mysql(config)
    cursor = conn.cursor()

    # 2. 加载 KG
    kg_embedder, kg = load_kg_and_embedder(config)

    # 3. 收集全库统计量
    global_stats = collect_global_stats(cursor)
    logger.info(f"全库统计: {global_stats}")

    # 4. 读取全部论文
    cursor.execute(
        "SELECT id, aminer_id, title, citation_count, year, keywords, authors "
        "FROM paper WHERE deleted = 0"
    )
    columns = [desc[0] for desc in cursor.description]
    papers = [dict(zip(columns, row)) for row in cursor.fetchall()]
    logger.info(f"读取 {len(papers)} 篇论文")

    if not papers:
        logger.warning("无论文数据，退出")
        cursor.close()
        conn.close()
        return

    # 5. 提取所有原始特征（用于计算全库 Z-score 参数）
    all_raw_10d = {}
    for paper in papers:
        raw = extract_10d_for_paper(paper, kg_embedder, global_stats)
        all_raw_10d[paper["id"]] = raw

    # 计算全库 Z-score 参数
    all_feats = np.array(list(all_raw_10d.values()))
    mean = all_feats.mean(axis=0).astype(np.float32)
    std = all_feats.std(axis=0).astype(np.float32) + 1e-8

    # 初始化投影矩阵 P (10×32)
    rng = np.random.default_rng(EMBEDDING_SEED)
    P = rng.standard_normal((RAW_FEATURE_DIM, EMBEDDING_DIM)).astype(np.float32) / np.sqrt(RAW_FEATURE_DIM)

    # 6. 对每篇论文：Z-score → 投影 → L2-norm → 写入
    updated_count = 0
    neo4j_updates: list[tuple[str, str, str]] = []  # (aminer_id, embedding_json, embedding_raw_json)

    for paper in papers:
        raw_10d = all_raw_10d[paper["id"]]
        normalized = (raw_10d - mean) / std
        projected = normalized @ P
        norm = np.linalg.norm(projected) + 1e-8
        vec_32d = projected / norm

        embedding_json = json.dumps([round(float(v), 6) for v in vec_32d])
        embedding_raw_json = json.dumps([round(float(v), 4) for v in raw_10d])

        cursor.execute(
            "UPDATE paper SET embedding = %s, embedding_raw = %s WHERE id = %s",
            (embedding_json, embedding_raw_json, paper["id"]),
        )
        updated_count += 1

        aminer_id = paper.get("aminer_id")
        if aminer_id:
            neo4j_updates.append((aminer_id, embedding_json, embedding_raw_json))

        if updated_count % 50 == 0:
            conn.commit()
            logger.info(f"  进度: {updated_count}/{len(papers)}")

    conn.commit()
    logger.info(f"MySQL 更新完成: {updated_count} 篇论文")

    # 7. 保存投影矩阵
    artifacts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "checkpoints")
    os.makedirs(artifacts_dir, exist_ok=True)
    np.savez(os.path.join(artifacts_dir, "projection.npz"), P=P, mean=mean, std=std)
    logger.info(f"投影矩阵已保存: {artifacts_dir}/projection.npz")

    # 8. 同步到 Neo4j
    if kg is not None and neo4j_updates:
        try:
            synced = _sync_to_neo4j(neo4j_updates, config)
            logger.info(f"Neo4j 同步完成: {synced} 个 Paper 节点")
        except Exception as e:
            logger.warning(f"Neo4j 同步失败（MySQL 数据已写入，可稍后重试）: {e}")

    cursor.close()
    conn.close()
    logger.info("=== 论文向量生成脚本完成 ===")


def _sync_to_neo4j(updates: list[tuple[str, str, str]], config) -> int:
    """将 embedding 和 embedding_raw 同步到 Neo4j Paper 节点。"""
    try:
        from neo4j import GraphDatabase
    except ImportError:
        raise ImportError("请安装 neo4j 驱动：pip install neo4j")

    driver = GraphDatabase.driver(
        config.neo4j_uri,
        auth=(config.neo4j_user, config.neo4j_password),
    )
    try:
        with driver.session(database=config.neo4j_database) as session:
            query = """
            UNWIND $rows AS row
            MATCH (n:GraphNode:Paper {node_id: row.aminer_id})
            SET n.embedding = row.embedding,
                n.embedding_raw = row.embedding_raw
            RETURN count(n) AS updated
            """
            rows = [
                {"aminer_id": aid, "embedding": emb, "embedding_raw": raw}
                for aid, emb, raw in updates
            ]
            total = 0
            batch_size = config.neo4j_batch_size
            for i in range(0, len(rows), batch_size):
                chunk = rows[i:i + batch_size]
                result = session.run(query, rows=chunk)
                for record in result:
                    total += record["updated"]
            return total
    finally:
        driver.close()


if __name__ == "__main__":
    main()
