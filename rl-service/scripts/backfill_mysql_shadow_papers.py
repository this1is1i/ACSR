from __future__ import annotations

import argparse
import json
import os


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="将 Neo4j Paper 节点回填到 MySQL paper 影子表")
    parser.add_argument("--neo4j-uri", default=os.getenv("GRAPH_NEO4J_URI", "bolt://localhost:7687"))
    parser.add_argument("--neo4j-user", default=os.getenv("GRAPH_NEO4J_USERNAME", "neo4j"))
    parser.add_argument("--neo4j-password", default=os.getenv("GRAPH_NEO4J_PASSWORD", ""))
    parser.add_argument("--neo4j-database", default=os.getenv("GRAPH_NEO4J_DATABASE", "neo4j"))
    parser.add_argument("--mysql-host", default=os.getenv("MYSQL_HOST", "localhost"))
    parser.add_argument("--mysql-port", type=int, default=int(os.getenv("MYSQL_PORT", "3306")))
    parser.add_argument("--mysql-db", default=os.getenv("MYSQL_DB", "research_db"))
    parser.add_argument("--mysql-user", default=os.getenv("MYSQL_USER", "root"))
    parser.add_argument("--mysql-password", default=os.getenv("MYSQL_PASSWORD", ""))
    parser.add_argument("--batch-size", type=int, default=500)
    return parser.parse_args()


def build_paper_fetch_query() -> str:
    return """
        MATCH (p:Paper)
        RETURN p.aminer_id AS aminer_id,
               p.title AS title,
               p.abstract AS abstract,
               p.keywords AS keywords,
               p.authors AS authors,
               p.venue AS venue,
               p.year AS year,
               coalesce(p.citation_count, 0) AS citation_count,
               p['embedding'] AS embedding
    """


def main() -> None:
    args = parse_args()

    from neo4j import GraphDatabase
    import pymysql

    driver = GraphDatabase.driver(args.neo4j_uri, auth=(args.neo4j_user, args.neo4j_password))
    mysql = pymysql.connect(
        host=args.mysql_host,
        port=args.mysql_port,
        user=args.mysql_user,
        password=args.mysql_password,
        database=args.mysql_db,
        charset="utf8mb4",
        autocommit=False,
    )

    try:
        with driver.session(database=args.neo4j_database) as session:
            records = session.run(build_paper_fetch_query()).data()

        sql = """
            INSERT INTO paper (aminer_id, title, abstract, keywords, authors, venue, year, citation_count, embedding)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                title = VALUES(title),
                abstract = VALUES(abstract),
                keywords = VALUES(keywords),
                authors = VALUES(authors),
                venue = VALUES(venue),
                year = VALUES(year),
                citation_count = VALUES(citation_count),
                embedding = VALUES(embedding)
        """

        with mysql.cursor() as cursor:
            for idx in range(0, len(records), args.batch_size):
                batch = records[idx: idx + args.batch_size]
                rows = [
                    (
                        row["aminer_id"],
                        row["title"],
                        row.get("abstract"),
                        json.dumps(row.get("keywords") or [], ensure_ascii=False),
                        json.dumps(row.get("authors") or [], ensure_ascii=False),
                        row.get("venue"),
                        row.get("year"),
                        row.get("citation_count") or 0,
                        row.get("embedding"),
                    )
                    for row in batch
                    if row.get("aminer_id")
                ]
                if rows:
                    cursor.executemany(sql, rows)
                    mysql.commit()
    finally:
        driver.close()
        mysql.close()


if __name__ == "__main__":
    main()
