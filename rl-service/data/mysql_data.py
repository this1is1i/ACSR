# data/mysql_data.py
# MySQL 数据访问层 —— 从 research_db 读取用户行为与论文数据，替代 mock 随机向量

from __future__ import annotations
import json
import logging
import pymysql
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MySQLDataSource:
    """从 MySQL research_db 读取真实用户行为数据和论文元数据。"""

    def __init__(self, config):
        self.config = config
        self._conn: Optional[pymysql.Connection] = None

    # ── 连接管理 ──────────────────────────────────────────────────

    @property
    def conn(self) -> pymysql.Connection:
        if self._conn is None or not self._conn.open:
            self._conn = pymysql.connect(
                host=self.config.mysql_host,
                port=self.config.mysql_port,
                user=self.config.mysql_user,
                password=self.config.mysql_password,
                database=self.config.mysql_db,
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True,
            )
        return self._conn

    def close(self) -> None:
        if self._conn and self._conn.open:
            self._conn.close()
            self._conn = None

    # ── 用户行为查询 ──────────────────────────────────────────────

    def get_user_behaviors(
        self, user_id: int, days: int = 90, limit: int = 200
    ) -> List[dict]:
        """获取用户近期行为日志 (click / favorite / read)。"""
        sql = """
            SELECT paper_id, action, duration, source, timestamp
            FROM behavior_log
            WHERE user_id = %s
              AND timestamp >= %s
            ORDER BY timestamp DESC
            LIMIT %s
        """
        cutoff = datetime.now() - timedelta(days=days)
        with self.conn.cursor() as cursor:
            cursor.execute(sql, (user_id, cutoff, limit))
            return cursor.fetchall()

    def get_user_interest_tags(self, user_id: int) -> List[dict]:
        """获取用户兴趣标签及权重（从 user_interest_history）。"""
        sql = """
            SELECT interest_tag, weight, source, record_date
            FROM user_interest_history
            WHERE user_id = %s
            ORDER BY record_date DESC, weight DESC
        """
        with self.conn.cursor() as cursor:
            cursor.execute(sql, (user_id,))
            return cursor.fetchall()

    # ── 论文数据查询 ──────────────────────────────────────────────

    def get_papers_by_ids(self, paper_ids: List[int]) -> List[dict]:
        """根据本地 paper.id 列表批量获取论文。"""
        if not paper_ids:
            return []
        placeholders = ",".join(["%s"] * len(paper_ids))
        sql = f"""
            SELECT id, aminer_id, title, keywords, authors, citation_count, year
            FROM paper
            WHERE id IN ({placeholders}) AND deleted = 0
        """
        with self.conn.cursor() as cursor:
            cursor.execute(sql, paper_ids)
            return cursor.fetchall()

    # ── 特征快照缓存 ──────────────────────────────────────────────

    def get_cached_feature(
        self, user_id: int, feature_type: str
    ) -> Optional[np.ndarray]:
        """读取已缓存的用户特征向量。"""
        sql = """
            SELECT feature_vector, feature_dim
            FROM user_feature_snapshot
            WHERE user_id = %s AND feature_type = %s
              AND updated_at >= %s
        """
        cutoff = datetime.now() - timedelta(hours=6)
        with self.conn.cursor() as cursor:
            cursor.execute(sql, (user_id, feature_type, cutoff))
            row = cursor.fetchone()
            if row:
                vec = json.loads(row["feature_vector"])
                return np.array(vec, dtype=np.float32)
        return None

    def cache_feature(
        self, user_id: int, feature_type: str, vector: np.ndarray, source: str = "computed"
    ) -> None:
        """缓存用户特征向量到 MySQL。"""
        vec_list = vector.tolist()
        sql = """
            INSERT INTO user_feature_snapshot (user_id, feature_type, feature_vector, feature_dim, source)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                feature_vector = VALUES(feature_vector),
                feature_dim = VALUES(feature_dim),
                source = VALUES(source),
                updated_at = CURRENT_TIMESTAMP
        """
        with self.conn.cursor() as cursor:
            cursor.execute(sql, (user_id, feature_type, json.dumps(vec_list), len(vec_list), source))

    # ── 全局统计 ──────────────────────────────────────────────────

    def get_all_user_ids(self) -> List[int]:
        """获取所有有行为记录的用户 ID（用于训练时采样）。"""
        sql = """
            SELECT DISTINCT user_id FROM behavior_log
            UNION
            SELECT DISTINCT user_id FROM user_interest_history
        """
        with self.conn.cursor() as cursor:
            cursor.execute(sql)
            return [int(row["user_id"]) for row in cursor.fetchall()]

    def get_global_keyword_freq(self) -> Dict[str, int]:
        """获取全局关键词频率分布（用于新用户冷启动）。"""
        sql = """
            SELECT interest_tag, SUM(weight) AS total_weight
            FROM user_interest_history
            GROUP BY interest_tag
            ORDER BY total_weight DESC
            LIMIT 100
        """
        with self.conn.cursor() as cursor:
            cursor.execute(sql)
            return {row["interest_tag"]: int(row["total_weight"]) for row in cursor.fetchall()}
