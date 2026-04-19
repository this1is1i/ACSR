# dataset/data_importer.py
# 数据导入模块 —— 将 AMiner 数据写入 SQLite / MySQL 数据库

from __future__ import annotations
import os
import json
import sqlite3
import logging
from typing import List, Optional
from contextlib import contextmanager

from dataset.aminer_loader import Paper, Author, Citation

logger = logging.getLogger(__name__)

# ── DDL 建表语句 ──────────────────────────────────────────────────

DDL_SQLITE = """
CREATE TABLE IF NOT EXISTS paper (
    paper_id    TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    abstract    TEXT,
    venue       TEXT,
    year        INTEGER,
    keywords    TEXT,   -- JSON 字符串
    embedding   TEXT    -- JSON 字符串（float 列表）
);

CREATE TABLE IF NOT EXISTS author (
    author_id   TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    org         TEXT,
    interests   TEXT    -- JSON 字符串
);

CREATE TABLE IF NOT EXISTS paper_author (
    paper_id    TEXT,
    author_id   TEXT,
    PRIMARY KEY (paper_id, author_id)
);

CREATE TABLE IF NOT EXISTS citation (
    citing_paper_id TEXT,
    cited_paper_id  TEXT,
    PRIMARY KEY (citing_paper_id, cited_paper_id)
);

CREATE INDEX IF NOT EXISTS idx_paper_year     ON paper(year);
CREATE INDEX IF NOT EXISTS idx_citation_cited ON citation(cited_paper_id);
"""


class DataImporter:
    """
    AMiner 数据库导入器。

    支持：
      - SQLite（开发 / 本地测试，零配置）
      - MySQL（生产环境，需安装 pymysql）

    切换数据库只需修改初始化参数，导入逻辑完全复用。
    """

    def __init__(
        self,
        db_type: str = "sqlite",
        sqlite_path: str = "data/research.db",
        mysql_config: Optional[dict] = None,
        batch_size: int = 500,
    ):
        """
        Args:
            db_type:      "sqlite" 或 "mysql"
            sqlite_path:  SQLite 文件路径（db_type="sqlite" 时使用）
            mysql_config: MySQL 连接参数（db_type="mysql" 时使用）
                          {"host":"localhost","port":3306,"db":"research",
                           "user":"root","password":"xxx"}
            batch_size:   批量插入大小
        """
        self.db_type    = db_type
        self.sqlite_path = sqlite_path
        self.mysql_config = mysql_config or {}
        self.batch_size  = batch_size

        if db_type == "sqlite":
            os.makedirs(os.path.dirname(sqlite_path) if os.path.dirname(sqlite_path) else ".", exist_ok=True)
            self._init_sqlite()
        elif db_type == "mysql":
            self._init_mysql()
        else:
            raise ValueError(f"不支持的数据库类型: {db_type}")

    # ── 初始化 ────────────────────────────────────────────────────

    def _init_sqlite(self) -> None:
        """初始化 SQLite 数据库，创建表结构。"""
        with self._get_conn() as conn:
            conn.executescript(DDL_SQLITE)
            conn.commit()
        logger.info(f"SQLite 数据库初始化完成：{self.sqlite_path}")

    def _init_mysql(self) -> None:
        """初始化 MySQL 数据库（需要预先创建数据库）。"""
        try:
            import pymysql
            # MySQL DDL 略有差异（TEXT → LONGTEXT，PRIMARY KEY 语法相同）
            mysql_ddl = DDL_SQLITE.replace(
                "TEXT PRIMARY KEY", "VARCHAR(64) PRIMARY KEY"
            ).replace(
                "PRIMARY KEY (paper_id, author_id)",
                "PRIMARY KEY (paper_id, author_id)"
            )
            with self._get_conn() as conn:
                cursor = conn.cursor()
                for stmt in mysql_ddl.split(";"):
                    stmt = stmt.strip()
                    if stmt:
                        cursor.execute(stmt)
                conn.commit()
            logger.info("MySQL 数据库初始化完成")
        except ImportError:
            raise ImportError("请安装 MySQL 驱动：pip install pymysql")

    # ── 批量导入 ──────────────────────────────────────────────────

    def import_papers(self, papers: List[Paper]) -> int:
        """
        批量导入论文数据。

        Returns:
            成功导入条数
        """
        inserted = 0
        with self._get_conn() as conn:
            for i in range(0, len(papers), self.batch_size):
                batch = papers[i: i + self.batch_size]
                rows = [
                    (
                        p.paper_id,
                        p.title,
                        p.abstract,
                        p.venue,
                        p.year if p.year else None,
                        json.dumps(p.keywords),
                        json.dumps(p.embedding) if p.embedding else None,
                    )
                    for p in batch
                ]
                sql = """
                    INSERT OR REPLACE INTO paper
                    (paper_id, title, abstract, venue, year, keywords, embedding)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """ if self.db_type == "sqlite" else """
                    INSERT INTO paper
                    (paper_id, title, abstract, venue, year, keywords, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE title=VALUES(title)
                """
                conn.executemany(sql, rows)

                # 导入论文-作者关系
                author_rows = []
                for p in batch:
                    for aid in p.authors:
                        author_rows.append((p.paper_id, aid))
                if author_rows:
                    pa_sql = (
                        "INSERT OR IGNORE INTO paper_author (paper_id, author_id) VALUES (?, ?)"
                        if self.db_type == "sqlite"
                        else "INSERT IGNORE INTO paper_author (paper_id, author_id) VALUES (%s, %s)"
                    )
                    conn.executemany(pa_sql, author_rows)

                conn.commit()
                inserted += len(batch)
                logger.debug(f"导入论文进度：{inserted}/{len(papers)}")

        logger.info(f"论文导入完成：{inserted} 篇")
        return inserted

    def import_authors(self, authors: List[Author]) -> int:
        """批量导入作者数据。"""
        inserted = 0
        sql = (
            "INSERT OR REPLACE INTO author (author_id, name, org, interests) VALUES (?, ?, ?, ?)"
            if self.db_type == "sqlite"
            else "INSERT INTO author (author_id, name, org, interests) VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE name=VALUES(name)"
        )
        with self._get_conn() as conn:
            for i in range(0, len(authors), self.batch_size):
                batch = authors[i: i + self.batch_size]
                rows = [(a.author_id, a.name, a.org, json.dumps(a.interests)) for a in batch]
                conn.executemany(sql, rows)
                conn.commit()
                inserted += len(batch)
        logger.info(f"作者导入完成：{inserted} 人")
        return inserted

    def import_citations(self, citations: List[Citation]) -> int:
        """批量导入引用关系。"""
        inserted = 0
        sql = (
            "INSERT OR IGNORE INTO citation (citing_paper_id, cited_paper_id) VALUES (?, ?)"
            if self.db_type == "sqlite"
            else "INSERT IGNORE INTO citation (citing_paper_id, cited_paper_id) VALUES (%s, %s)"
        )
        with self._get_conn() as conn:
            for i in range(0, len(citations), self.batch_size):
                batch = citations[i: i + self.batch_size]
                rows = [(c.citing_paper_id, c.cited_paper_id) for c in batch]
                conn.executemany(sql, rows)
                conn.commit()
                inserted += len(batch)
        logger.info(f"引用关系导入完成：{inserted} 条")
        return inserted

    def import_all(
        self,
        papers: List[Paper],
        authors: List[Author],
        citations: List[Citation],
    ) -> dict:
        """一键导入全部数据。"""
        return {
            "papers":    self.import_papers(papers),
            "authors":   self.import_authors(authors),
            "citations": self.import_citations(citations),
        }

    # ── 查询接口 ──────────────────────────────────────────────────

    def get_paper(self, paper_id: str) -> Optional[dict]:
        """按 ID 查询单篇论文。"""
        with self._get_conn() as conn:
            ph = "?" if self.db_type == "sqlite" else "%s"
            row = conn.execute(
                f"SELECT * FROM paper WHERE paper_id = {ph}", (paper_id,)
            ).fetchone()
            if row:
                return dict(zip(
                    ["paper_id", "title", "abstract", "venue", "year", "keywords", "embedding"],
                    row,
                ))
        return None

    def get_stats(self) -> dict:
        """返回数据库统计信息。"""
        with self._get_conn() as conn:
            return {
                "papers":    conn.execute("SELECT COUNT(*) FROM paper").fetchone()[0],
                "authors":   conn.execute("SELECT COUNT(*) FROM author").fetchone()[0],
                "citations": conn.execute("SELECT COUNT(*) FROM citation").fetchone()[0],
            }

    # ── 连接管理 ──────────────────────────────────────────────────

    @contextmanager
    def _get_conn(self):
        """获取数据库连接（上下文管理器）。"""
        if self.db_type == "sqlite":
            conn = sqlite3.connect(self.sqlite_path)
            try:
                yield conn
            finally:
                conn.close()
        else:
            import pymysql
            conn = pymysql.connect(**self.mysql_config, charset="utf8mb4")
            try:
                yield conn
            finally:
                conn.close()
