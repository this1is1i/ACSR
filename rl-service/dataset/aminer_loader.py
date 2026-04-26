# dataset/aminer_loader.py
# AMiner 数据集解析模块 —— 支持论文、作者、引用关系加载

from __future__ import annotations
import json
import os
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Iterator, Any

logger = logging.getLogger(__name__)


# ── 数据模型 ──────────────────────────────────────────────────────

@dataclass
class Paper:
    """论文实体。"""
    paper_id: str
    title: str
    abstract: str = ""
    authors: List[str] = field(default_factory=list)   # author_id 列表
    keywords: List[str] = field(default_factory=list)
    venue: str = ""
    year: int = 0
    citation_count: int = 0
    references: List[str] = field(default_factory=list)  # 被引 paper_id 列表
    # 预留 embedding 接口
    embedding: Optional[List[float]] = None

    def text_for_embedding(self) -> str:
        """拼接用于 embedding 的文本。"""
        kw = " ".join(self.keywords)
        return f"{self.title}. {self.abstract} {kw}".strip()


@dataclass
class Author:
    """作者实体。"""
    author_id: str
    name: str
    org: str = ""
    interests: List[str] = field(default_factory=list)
    paper_ids: List[str] = field(default_factory=list)


@dataclass
class Citation:
    """引用关系。"""
    citing_paper_id: str    # 施引论文
    cited_paper_id: str     # 被引论文


# ── 数据集加载器 ──────────────────────────────────────────────────

class AMinerLoader:
    """
    AMiner 数据集加载器。

    支持格式：
      - AMiner 官方 JSON 格式（papers.json / authors.json / citations.json）
      - AMiner V14 学术网络格式
      - 自定义 JSONL 格式（每行一个 JSON 对象）

    本地测试：
        若无真实数据，调用 generate_mock_data() 生成符合同等格式的 mock 数据。
    """

    def __init__(self, data_dir: str = "data/A+9+Miner"):
        self.data_dir = data_dir
        self.papers_path   = os.path.join(data_dir, "papers.json")
        self.authors_path  = os.path.join(data_dir, "authors.json")
        self.citations_path = os.path.join(data_dir, "citations.json")

    # ── 主加载接口 ────────────────────────────────────────────────

    def load_papers(self, limit: Optional[int] = None) -> List[Paper]:
        """
        加载论文数据。

        Args:
            limit: 最多加载条数（None 表示全量，大数据集建议设置上限）

        Returns:
            Paper 对象列表
        """
        if not os.path.exists(self.papers_path):
            logger.warning(f"未找到 {self.papers_path}，使用 mock 数据")
            return self._mock_papers(limit or 500)

        papers: List[Paper] = []
        for i, record in enumerate(self._iter_json(self.papers_path)):
            if limit and i >= limit:
                break
            paper = self._parse_paper(record)
            if paper:
                papers.append(paper)

        logger.info(f"加载论文 {len(papers)} 篇（来源：{self.papers_path}）")
        return papers

    def load_authors(self, limit: Optional[int] = None) -> List[Author]:
        """加载作者数据。"""
        if not os.path.exists(self.authors_path):
            logger.warning(f"未找到 {self.authors_path}，使用 mock 数据")
            return self._mock_authors(limit or 200)

        authors: List[Author] = []
        for i, record in enumerate(self._iter_json(self.authors_path)):
            if limit and i >= limit:
                break
            author = self._parse_author(record)
            if author:
                authors.append(author)

        logger.info(f"加载作者 {len(authors)} 人")
        return authors

    def load_citations(self, papers: List[Paper]) -> List[Citation]:
        """
        从论文的 references 字段提取引用关系。
        若存在独立 citations.json 则优先使用。
        """
        if os.path.exists(self.citations_path):
            return self._load_citations_file()

        # 从 paper.references 字段提取
        paper_ids = {p.paper_id for p in papers}
        citations: List[Citation] = []
        for paper in papers:
            for ref_id in paper.references:
                if ref_id in paper_ids:  # 只保留数据集内部的引用
                    citations.append(Citation(
                        citing_paper_id=paper.paper_id,
                        cited_paper_id=ref_id,
                    ))

        logger.info(f"提取引用关系 {len(citations)} 条")
        return citations

    # ── AMiner 格式解析 ───────────────────────────────────────────

    def _parse_paper(self, record: Dict[str, Any]) -> Optional[Paper]:
        """解析 AMiner 论文记录（兼容多版本字段命名）。"""
        pid = (record.get("id") or record.get("_id") or
               record.get("paper_id") or "")
        if not pid:
            return None

        title = record.get("title") or record.get("name") or ""
        if not title.strip():
            return None

        # AMiner V14 作者字段为 authors 列表（每项含 id, name, org）
        raw_authors = record.get("authors") or []
        author_ids = []
        for a in raw_authors:
            if isinstance(a, dict):
                author_ids.append(a.get("id") or a.get("name") or "")
            elif isinstance(a, str):
                author_ids.append(a)

        # 关键词提取：优先 keywords，其次 fos（Fields of Study）
        keywords = (
            record.get("keywords") or
            [f.get("name", "") for f in record.get("fos", []) if isinstance(f, dict)] or
            []
        )
        keywords = [str(k).strip() for k in keywords if str(k).strip()][:10]

        references = record.get("references") or []
        references = [str(r) for r in references]

        return Paper(
            paper_id  = str(pid),
            title     = title.strip(),
            abstract  = (record.get("abstract") or "").strip(),
            authors   = [str(a) for a in author_ids if a],
            keywords  = keywords,
            venue     = str(record.get("venue") or record.get("journal") or ""),
            year      = int(record.get("year") or 0),
            citation_count = int(record.get("n_citation") or record.get("citation_count") or 0),
            references= references,
        )

    def _parse_author(self, record: Dict[str, Any]) -> Optional[Author]:
        """解析 AMiner 作者记录。"""
        aid = record.get("id") or record.get("author_id") or ""
        name = record.get("name") or ""
        if not (aid and name):
            return None
        return Author(
            author_id = str(aid),
            name      = str(name).strip(),
            org       = str(record.get("org") or ""),
            interests = list(record.get("interests") or []),
            paper_ids = [str(p) for p in (record.get("papers") or [])],
        )

    def _load_citations_file(self) -> List[Citation]:
        """从 citations.json 加载引用关系。"""
        citations = []
        for record in self._iter_json(self.citations_path):
            citing = record.get("citing") or record.get("citing_id") or ""
            cited  = record.get("cited")  or record.get("cited_id")  or ""
            if citing and cited:
                citations.append(Citation(str(citing), str(cited)))
        return citations

    # ── 流式 JSON 解析 ────────────────────────────────────────────

    @staticmethod
    def _iter_json(path: str) -> Iterator[Dict]:
        """
        流式解析 JSON 文件（支持 JSON Array 和 JSONL 两种格式）。
        避免将大文件一次性加载到内存。
        """
        with open(path, "r", encoding="utf-8") as f:
            first_char = f.read(1)
            f.seek(0)
            if first_char == "[":
                # JSON Array 格式
                data = json.load(f)
                yield from data
            else:
                # JSONL 格式（每行一个 JSON 对象）
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            yield json.loads(line)
                        except json.JSONDecodeError:
                            continue

    # ── Mock 数据（真实数据不存在时使用）────────────────────────

    def _mock_papers(self, n: int = 500) -> List[Paper]:
        """生成符合 AMiner 格式的 mock 论文数据，用于开发测试。"""
        import random
        random.seed(42)
        topics = [
            ("Reinforcement Learning", ["RL", "MDP", "policy gradient", "Q-learning"]),
            ("Natural Language Processing", ["NLP", "BERT", "transformer", "text classification"]),
            ("Graph Neural Networks", ["GNN", "graph embedding", "node classification", "link prediction"]),
            ("Knowledge Graphs", ["KG", "entity embedding", "relation extraction", "TransE"]),
            ("Recommender Systems", ["collaborative filtering", "matrix factorization", "deep learning"]),
            ("Computer Vision", ["CNN", "object detection", "image segmentation", "ResNet"]),
            ("Federated Learning", ["privacy", "distributed learning", "aggregation"]),
            ("Meta-Learning", ["few-shot", "MAML", "transfer learning"]),
        ]
        venues = ["ICML", "NeurIPS", "ICLR", "ACL", "KDD", "WWW", "SIGIR", "AAAI"]
        papers = []
        for i in range(n):
            topic, kws = topics[i % len(topics)]
            selected_kws = random.sample(kws, min(3, len(kws)))
            paper_id = f"aminer_{i:06d}"
            refs = [f"aminer_{random.randint(0, max(0, i-1)):06d}"
                    for _ in range(random.randint(0, 8)) if i > 0]
            papers.append(Paper(
                paper_id  = paper_id,
                title     = f"Advances in {topic}: Method and Application #{i}",
                abstract  = (
                    f"In this paper, we propose a novel approach to {topic.lower()}. "
                    f"Our method leverages {', '.join(selected_kws)} to achieve "
                    f"state-of-the-art performance on benchmark datasets."
                ),
                authors   = [f"author_{(i*3+j) % 50:03d}" for j in range(random.randint(1, 4))],
                keywords  = selected_kws + [topic],
                venue     = random.choice(venues),
                year      = random.randint(2015, 2024),
                citation_count = random.randint(10, 5000),
                references= refs,
            ))
        logger.info(f"生成 mock 论文 {len(papers)} 篇")
        return papers

    def _mock_authors(self, n: int = 200) -> List[Author]:
        """生成 mock 作者数据。"""
        orgs = ["MIT", "Stanford", "CMU", "Peking University", "Tsinghua", "Google", "DeepMind"]
        import random
        random.seed(42)
        return [
            Author(
                author_id = f"author_{i:03d}",
                name      = f"Researcher_{i}",
                org       = random.choice(orgs),
                interests = random.sample(
                    ["RL", "NLP", "CV", "GNN", "KG", "RecSys"], k=random.randint(1, 3)
                ),
            )
            for i in range(n)
        ]

    # ── 数据集写入（用于生成标准格式测试文件）───────────────────

    def save_mock_data(self, output_dir: str = "data/aminer") -> None:
        """将 mock 数据保存为标准 JSON 格式，便于流程测试。"""
        os.makedirs(output_dir, exist_ok=True)
        papers  = self._mock_papers(500)
        authors = self._mock_authors(50)

        def paper_to_dict(p: Paper) -> dict:
            return {
                "id": p.paper_id, "title": p.title,
                "abstract": p.abstract, "authors": p.authors,
                "keywords": p.keywords, "venue": p.venue,
                "year": p.year, "citation_count": p.citation_count, "references": p.references,
            }

        def author_to_dict(a: Author) -> dict:
            return {
                "id": a.author_id, "name": a.name,
                "org": a.org, "interests": a.interests,
            }

        with open(os.path.join(output_dir, "papers.json"), "w") as f:
            json.dump([paper_to_dict(p) for p in papers], f, indent=2)
        with open(os.path.join(output_dir, "authors.json"), "w") as f:
            json.dump([author_to_dict(a) for a in authors], f, indent=2)

        logger.info(f"Mock 数据已保存至 {output_dir}")
