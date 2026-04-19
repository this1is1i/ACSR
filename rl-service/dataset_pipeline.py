# dataset_pipeline.py
# 数据层完整流水线入口

from __future__ import annotations
import os
import sys
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("pipeline")


def run_pipeline(
    data_dir: str = "data/aminer",
    use_real_data: bool = False,
    paper_limit: int = 500,
    use_sentence_transformer: bool = False,
):
    """
    完整数据处理流水线。

    阶段：
        1. AMiner 数据加载（或生成 Mock 数据）
        2. 数据预处理（去重、过滤、Embedding 构建）
        3. 数据库导入（SQLite）
        4. 知识图谱构建
        5. 知识图谱持久化
        6. Embedding 构建（论文/关键词/作者）
        7. 学习路径演示

    Args:
        use_real_data: True 时从 data_dir 读取真实 AMiner JSON 文件
        paper_limit:   最大加载论文数量
        use_sentence_transformer: 是否使用 SPECTER 学术论文 embedding
    """
    from dataset.aminer_loader import AMinerLoader
    from dataset.preprocess import DataPreprocessor
    from dataset.data_importer import DataImporter
    from knowledge_graph.kg_builder import KGBuilder
    from knowledge_graph.graph_storage import GraphStorage
    from knowledge_graph.graph_query import GraphQuery
    from learning_path.path_builder import PathBuilder
    from learning_path.propagation import KnowledgePropagation
    from embeddings.embedding_builder import EmbeddingBuilder

    print("=" * 65)
    print("  科研推荐系统 · 数据层流水线")
    print("=" * 65)

    # ── Step 1: 加载 AMiner 数据 ──────────────────────────────────
    print("\n[Step 1] 加载 AMiner 数据...")
    loader = AMinerLoader(data_dir=data_dir)

    if not use_real_data:
        # 生成 mock 数据文件（首次运行时创建）
        if not os.path.exists(os.path.join(data_dir, "papers.json")):
            logger.info("生成 Mock AMiner 数据...")
            loader.save_mock_data(data_dir)

    papers   = loader.load_papers(limit=paper_limit)
    authors  = loader.load_authors(limit=paper_limit // 2)
    citations = loader.load_citations(papers)
    print(f"  ✓ 论文: {len(papers)}, 作者: {len(authors)}, 引用关系: {len(citations)}")

    # ── Step 2: 数据预处理 ────────────────────────────────────────
    print("\n[Step 2] 数据预处理（去重/过滤/Embedding）...")
    preprocessor = DataPreprocessor(
        embedding_dim=64,
        output_dir="data/processed",
        use_sentence_transformer=use_sentence_transformer,
    )
    papers, paper_embeddings = preprocessor.run(papers, authors)
    print(f"  ✓ 清洗后论文: {len(papers)}, Embedding shape: {paper_embeddings.shape}")

    # ── Step 3: 数据库导入 ────────────────────────────────────────
    print("\n[Step 3] 导入 SQLite 数据库...")
    importer = DataImporter(db_type="sqlite", sqlite_path="data/research.db")
    stats = importer.import_all(papers, authors, citations)
    print(f"  ✓ 导入统计: {stats}")

    # ── Step 4: 构建知识图谱 ──────────────────────────────────────
    print("\n[Step 4] 构建科研知识图谱...")
    builder = KGBuilder(min_keyword_freq=2, max_keyword_nodes=200)
    kg = builder.build(papers, authors, citations)
    builder.update_citation_counts(kg)
    print(f"  ✓ 图谱统计: {kg.stats}")

    # ── Step 5: 持久化知识图谱 ────────────────────────────────────
    print("\n[Step 5] 保存知识图谱...")
    storage = GraphStorage(storage_dir="data/kg")
    storage.save(kg, format="both")
    print(f"  ✓ 已保存至 data/kg/")

    # ── Step 6: 构建 Embedding ────────────────────────────────────
    print("\n[Step 6] 构建多模态 Embedding...")
    emb_builder = EmbeddingBuilder(embedding_dim=64, output_dir="data/embeddings")
    emb_builder.build_paper_embeddings(papers, precomputed=paper_embeddings)
    emb_builder.build_keyword_embeddings(kg)
    emb_builder.build_author_embeddings(authors, kg)
    print(f"  ✓ 论文/关键词/作者 Embedding 已保存至 data/embeddings/")

    # ── Step 7: 演示知识图谱查询 ─────────────────────────────────
    print("\n[Step 7] 知识图谱查询演示...")
    query = GraphQuery(kg)
    if papers:
        sample_id = papers[0].paper_id
        related = query.get_related_papers(sample_id, k=3)
        print(f"  论文 [{papers[0].title[:40]}...] 相关论文:")
        for r in related:
            print(f"    - {r['title'][:40]} (score={r['score']})")

    kw_cluster = query.get_keyword_cluster("reinforcement learning", k=3)
    print(f"  关键词 'reinforcement learning' 聚类：{kw_cluster['frequency']} 篇相关论文")

    # ── Step 8: 演示学习路径生成 ──────────────────────────────────
    print("\n[Step 8] 学习路径生成演示...")
    propagation = KnowledgePropagation(kg)
    history_ids = [p.paper_id for p in papers[:5]]
    propagation.batch_update(history_ids)

    path_builder = PathBuilder(kg, query)
    path = path_builder.build_path(
        user_id="demo_user",
        user_history=history_ids,
        target_topic="reinforcement learning",
        max_nodes=12,
    )
    path = propagation.apply_to_path(path)
    path_dict = path_builder.to_dict(path)
    print(f"  ✓ 生成学习路径：{len(path_dict['nodes'])} 个节点，"
          f"{len(path_dict['edges'])} 条边")
    print(f"  预估学习时长：{path_dict['estimated_hours']:.1f} 小时")

    # ── Step 9: 演示推荐解释增强 ──────────────────────────────────
    print("\n[Step 9] 推荐解释增强演示...")
    if len(papers) > 10:
        reasons = query.explain_recommendation(
            user_history=history_ids,
            recommended_paper_id=papers[10].paper_id,
        )
        print(f"  推荐《{papers[10].title[:40]}...》的原因:")
        for r in reasons:
            print(f"    ✦ {r}")

    print("\n" + "=" * 65)
    print("  数据层流水线完成！")
    print("  下一步：将 EmbeddingBuilder 接入 FeatureBuilder 升级 RL 状态")
    print("=" * 65)

    return {
        "papers": papers,
        "authors": authors,
        "citations": citations,
        "kg": kg,
        "emb_builder": emb_builder,
        "query": query,
        "path_builder": path_builder,
    }


if __name__ == "__main__":
    run_pipeline()
