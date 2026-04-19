# dataset/preprocess.py
# 数据预处理模块 —— 去重、过滤、关键词提取、论文 embedding 构建

from __future__ import annotations
import os
import re
import logging
import numpy as np
from typing import List, Dict, Tuple, Optional
from collections import Counter

from dataset.aminer_loader import Paper, Author

logger = logging.getLogger(__name__)


class DataPreprocessor:
    """
    数据预处理流水线。

    流程：
        原始 AMiner 数据
            → 去重 & 过滤无效记录
            → 文本清洗
            → 关键词提取 / 增强
            → 论文 Embedding 构建（SentenceTransformer）
            → 保存 paper_embeddings.npy
    """

    def __init__(
        self,
        embedding_dim: int = 64,
        output_dir: str = "data/processed",
        use_sentence_transformer: bool = False,   # True 时需要安装 sentence-transformers
    ):
        self.embedding_dim = embedding_dim
        self.output_dir = output_dir
        self.use_sentence_transformer = use_sentence_transformer
        self._encoder = None
        os.makedirs(output_dir, exist_ok=True)

    # ── 主流水线 ──────────────────────────────────────────────────

    def run(
        self,
        papers: List[Paper],
        authors: Optional[List[Author]] = None,
    ) -> Tuple[List[Paper], np.ndarray]:
        """
        完整预处理流水线。

        Returns:
            (清洗后的论文列表, paper_embeddings array)
            paper_embeddings shape: (n_papers, embedding_dim)
        """
        logger.info(f"开始预处理，输入论文数：{len(papers)}")

        # 1. 去重
        papers = self._deduplicate(papers)
        logger.info(f"去重后：{len(papers)} 篇")

        # 2. 过滤无效记录
        papers = self._filter_invalid(papers)
        logger.info(f"过滤后：{len(papers)} 篇")

        # 3. 文本清洗
        papers = [self._clean_paper(p) for p in papers]

        # 4. 关键词增强（TF-IDF 提取补充关键词）
        papers = self._augment_keywords(papers)

        # 5. 构建 Embedding
        embeddings = self._build_embeddings(papers)

        # 6. 将 embedding 写回 paper 对象
        for i, paper in enumerate(papers):
            paper.embedding = embeddings[i].tolist()

        # 7. 保存
        self._save(papers, embeddings)

        logger.info(f"预处理完成，最终论文数：{len(papers)}")
        return papers, embeddings

    # ── 去重 ──────────────────────────────────────────────────────

    def _deduplicate(self, papers: List[Paper]) -> List[Paper]:
        """
        按 paper_id 去重；title 重复时保留字段更完整的版本。
        """
        seen_ids: Dict[str, Paper] = {}
        for p in papers:
            if p.paper_id not in seen_ids:
                seen_ids[p.paper_id] = p
            else:
                # 保留信息更丰富的版本
                existing = seen_ids[p.paper_id]
                if len(p.abstract) > len(existing.abstract):
                    seen_ids[p.paper_id] = p
        return list(seen_ids.values())

    # ── 过滤 ──────────────────────────────────────────────────────

    def _filter_invalid(self, papers: List[Paper]) -> List[Paper]:
        """
        过滤规则：
          - 标题为空或过短（< 5 字符）
          - 年份异常（< 1990 或 > 2026）
          - 摘要过短（< 20 字符）且无关键词
        """
        valid = []
        for p in papers:
            if len(p.title.strip()) < 5:
                continue
            if p.year and (p.year < 1990 or p.year > 2026):
                continue
            if len(p.abstract.strip()) < 20 and not p.keywords:
                continue
            valid.append(p)
        return valid

    # ── 文本清洗 ──────────────────────────────────────────────────

    def _clean_paper(self, paper: Paper) -> Paper:
        """清洗标题、摘要中的特殊字符和多余空白。"""
        paper.title    = self._clean_text(paper.title)
        paper.abstract = self._clean_text(paper.abstract)
        paper.keywords = [self._clean_text(k) for k in paper.keywords if k.strip()]
        return paper

    @staticmethod
    def _clean_text(text: str) -> str:
        """移除控制字符、多余空格，统一编码。"""
        text = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]", "", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    # ── 关键词增强 ────────────────────────────────────────────────

    def _augment_keywords(self, papers: List[Paper]) -> List[Paper]:
        """
        对关键词为空的论文，从标题+摘要中用简单 TF-IDF 提取关键词。

        生产环境替换：
          - KeyBERT / YAKE 关键词提取
          - 领域词典匹配（计算机科学主题词表）
        """
        # 构建全局词频（IDF 分母）
        doc_freq: Counter = Counter()
        for p in papers:
            words = set(self._tokenize(p.title + " " + p.abstract))
            doc_freq.update(words)
        total_docs = len(papers)

        for p in papers:
            if p.keywords:
                continue
            text = p.title + " " + p.abstract
            words = self._tokenize(text)
            if not words:
                continue
            # TF
            tf = Counter(words)
            # TF-IDF 打分
            scores = {
                w: tf[w] / len(words) / (doc_freq[w] / total_docs + 1e-9)
                for w in tf
                if len(w) > 3 and doc_freq[w] < total_docs * 0.5
            }
            top_keywords = [w for w, _ in
                            sorted(scores.items(), key=lambda x: -x[1])[:5]]
            p.keywords = top_keywords
        return papers

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """简单英文分词（生产环境替换为 NLTK / spaCy）。"""
        text = re.sub(r"[^a-zA-Z\s]", " ", text.lower())
        stop = {"the", "a", "an", "is", "are", "was", "were", "be", "been",
                "being", "have", "has", "had", "do", "does", "did", "will",
                "would", "could", "should", "may", "might", "shall", "can",
                "to", "of", "in", "for", "on", "with", "at", "by", "from",
                "as", "or", "and", "but", "not", "this", "that", "we", "our",
                "paper", "propose", "show", "present", "method", "approach"}
        return [w for w in text.split() if len(w) > 2 and w not in stop]

    # ── Embedding 构建 ─────────────────────────────────────────────

    def _build_embeddings(self, papers: List[Paper]) -> np.ndarray:
        """
        为每篇论文构建 embedding 向量。

        默认使用 TF-IDF 伪 embedding（无需 GPU，开发环境可直接运行）。
        SentenceTransformer 开关：设置 use_sentence_transformer=True。

        Args:
            papers: 论文列表

        Returns:
            embeddings: (n, embedding_dim) float32 array
        """
        if self.use_sentence_transformer:
            return self._sentence_transformer_embeddings(papers)
        else:
            return self._tfidf_hash_embeddings(papers)

    def _sentence_transformer_embeddings(self, papers: List[Paper]) -> np.ndarray:
        """
        使用 SentenceTransformer 构建语义 embedding。

        安装：pip install sentence-transformers
        推荐模型：allenai-specter（专为学术论文设计）
          - model_name = "allenai-specter"
          - embedding_dim = 768，可通过 PCA 降维到 64/128

        使用：
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer("allenai-specter")
            texts = [p.text_for_embedding() for p in papers]
            embeddings = model.encode(texts, batch_size=64, show_progress_bar=True)
        """
        try:
            from sentence_transformers import SentenceTransformer
            if self._encoder is None:
                model_name = "allenai-specter"
                logger.info(f"加载 SentenceTransformer 模型：{model_name}")
                self._encoder = SentenceTransformer(model_name)

            texts = [p.text_for_embedding() for p in papers]
            logger.info(f"开始编码 {len(texts)} 篇论文...")
            embs = self._encoder.encode(
                texts,
                batch_size=64,
                show_progress_bar=True,
                convert_to_numpy=True,
            )

            # PCA 降维到目标维度
            if embs.shape[1] != self.embedding_dim:
                embs = self._pca_reduce(embs, self.embedding_dim)

            return embs.astype(np.float32)

        except ImportError:
            logger.warning("sentence-transformers 未安装，回退到 hash embedding")
            return self._tfidf_hash_embeddings(papers)

    def _tfidf_hash_embeddings(self, papers: List[Paper]) -> np.ndarray:
        """
        基于 TF-IDF 词袋的 hash embedding（无依赖，可直接运行）。
        每个词映射到向量空间的固定维度并叠加，形成文档向量。
        """
        embeddings = np.zeros((len(papers), self.embedding_dim), dtype=np.float32)
        for i, paper in enumerate(papers):
            words = self._tokenize(paper.text_for_embedding())
            for word in words:
                # 哈希映射到 embedding 维度（模拟随机投影）
                h = hash(word) % self.embedding_dim
                embeddings[i, h] += 1.0
            # L2 归一化
            norm = np.linalg.norm(embeddings[i]) + 1e-8
            embeddings[i] /= norm
        return embeddings

    @staticmethod
    def _pca_reduce(embs: np.ndarray, target_dim: int) -> np.ndarray:
        """PCA 降维（用于将 768-dim SPECTER 降至目标维度）。"""
        from sklearn.decomposition import PCA
        pca = PCA(n_components=target_dim, random_state=42)
        reduced = pca.fit_transform(embs)
        explained = pca.explained_variance_ratio_.sum()
        logger.info(f"PCA 降维 {embs.shape[1]}→{target_dim}，信息保留率: {explained:.2%}")
        return reduced

    # ── 保存 ──────────────────────────────────────────────────────

    def _save(self, papers: List[Paper], embeddings: np.ndarray) -> None:
        """保存 embedding 和论文 ID 映射文件。"""
        emb_path = os.path.join(self.output_dir, "paper_embeddings.npy")
        np.save(emb_path, embeddings)
        logger.info(f"Embedding 已保存：{emb_path}，shape={embeddings.shape}")

        # 保存 paper_id → index 映射
        import json
        id_map = {p.paper_id: i for i, p in enumerate(papers)}
        with open(os.path.join(self.output_dir, "paper_id_map.json"), "w") as f:
            json.dump(id_map, f)
        logger.info(f"论文 ID 映射已保存，共 {len(id_map)} 篇")

    def load_embeddings(self) -> Tuple[np.ndarray, Dict[str, int]]:
        """加载已保存的 embedding 和 ID 映射。"""
        import json
        emb_path = os.path.join(self.output_dir, "paper_embeddings.npy")
        map_path = os.path.join(self.output_dir, "paper_id_map.json")
        embeddings = np.load(emb_path)
        with open(map_path, "r") as f:
            id_map = json.load(f)
        return embeddings, id_map
