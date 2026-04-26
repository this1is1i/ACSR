from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from dataset.aminer_loader import AMinerLoader, Author, Citation


@dataclass
class MergedPaper:
    aminer_id: str
    title: str
    abstract: str = ""
    authors: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    venue: str = ""
    year: int = 0
    citation_count: int = 0
    embedding: Optional[str] = None
    mysql_id: Optional[int] = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="将 MySQL + AMiner 数据迁移到 Neo4j")
    parser.add_argument("--neo4j-uri", default=os.getenv("GRAPH_NEO4J_URI", "bolt://localhost:7687"))
    parser.add_argument("--neo4j-user", default=os.getenv("GRAPH_NEO4J_USERNAME", "neo4j"))
    parser.add_argument("--neo4j-password", default=os.getenv("GRAPH_NEO4J_PASSWORD", ""))
    parser.add_argument("--neo4j-database", default=os.getenv("GRAPH_NEO4J_DATABASE", "neo4j"))
    parser.add_argument("--mysql-host", default=os.getenv("MYSQL_HOST", "localhost"))
    parser.add_argument("--mysql-port", type=int, default=int(os.getenv("MYSQL_PORT", "3306")))
    parser.add_argument("--mysql-db", default=os.getenv("MYSQL_DB", "research_db"))
    parser.add_argument("--mysql-user", default=os.getenv("MYSQL_USER", "root"))
    parser.add_argument("--mysql-password", default=os.getenv("MYSQL_PASSWORD", ""))
    parser.add_argument("--data-dir", default=os.path.join(ROOT_DIR, "data", "A+9+Miner"))
    parser.add_argument("--paper-limit", type=int, default=1000)
    parser.add_argument("--clear", action="store_true")
    parser.add_argument("--skip-mysql", action="store_true")
    parser.add_argument("--skip-aminer", action="store_true")
    parser.add_argument("--skip-legacy-kg", action="store_true")
    parser.add_argument("--batch-size", type=int, default=500)
    return parser.parse_args()


def json_list(value) -> List[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if item is not None]
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return [str(item) for item in parsed if item is not None]
    except (TypeError, json.JSONDecodeError):
        pass
    return [item.strip() for item in str(value).split(",") if item.strip()]


def mysql_connection(args):
    import pymysql

    return pymysql.connect(
        host=args.mysql_host,
        port=args.mysql_port,
        user=args.mysql_user,
        password=args.mysql_password,
        database=args.mysql_db,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )


def load_mysql_papers(args) -> Dict[str, MergedPaper]:
    papers: Dict[str, MergedPaper] = {}
    with mysql_connection(args) as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, aminer_id, title, abstract, keywords, authors, venue, year, citation_count, embedding
                FROM paper
                WHERE deleted = 0 AND aminer_id IS NOT NULL
            """)
            for row in cursor.fetchall():
                papers[row["aminer_id"]] = MergedPaper(
                    aminer_id=row["aminer_id"],
                    title=row["title"],
                    abstract=row.get("abstract") or "",
                    authors=json_list(row.get("authors")),
                    keywords=json_list(row.get("keywords")),
                    venue=row.get("venue") or "",
                    year=int(row.get("year") or 0),
                    citation_count=int(row.get("citation_count") or 0),
                    embedding=row.get("embedding"),
                    mysql_id=int(row["id"]) if row.get("id") is not None else None,
                )
    return papers


def merge_aminer_data(args, papers: Dict[str, MergedPaper]) -> Tuple[Dict[str, MergedPaper], Dict[str, Author], List[Citation]]:
    authors_map: Dict[str, Author] = {}
    citations: List[Citation] = []
    if args.skip_aminer:
        return papers, authors_map, citations

    loader = AMinerLoader(data_dir=args.data_dir)
    aminer_papers = loader.load_papers(limit=args.paper_limit)
    aminer_authors = loader.load_authors(limit=max(args.paper_limit, 200))
    citations = loader.load_citations(aminer_papers)

    for author in aminer_authors:
        authors_map[author.author_id] = author

    for paper in aminer_papers:
        merged = papers.get(paper.paper_id)
        if merged is None:
            papers[paper.paper_id] = MergedPaper(
                aminer_id=paper.paper_id,
                title=paper.title,
                abstract=paper.abstract,
                authors=list(paper.authors),
                keywords=list(paper.keywords),
                venue=paper.venue,
                year=paper.year,
                citation_count=paper.citation_count,
            )
            continue

        if not merged.abstract and paper.abstract:
            merged.abstract = paper.abstract
        if not merged.authors and paper.authors:
            merged.authors = list(paper.authors)
        if not merged.keywords and paper.keywords:
            merged.keywords = list(paper.keywords)
        if not merged.venue and paper.venue:
            merged.venue = paper.venue
        if not merged.year and paper.year:
            merged.year = paper.year
        if merged.citation_count <= 0 and paper.citation_count > 0:
            merged.citation_count = paper.citation_count

    return papers, authors_map, citations


def load_legacy_kg(args):
    if args.skip_legacy_kg or args.skip_mysql:
        return [], []

    with mysql_connection(args) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name, type, external_id, properties FROM kg_entity")
            entities = cursor.fetchall()
            cursor.execute("SELECT source_id, target_id, relation_type, weight FROM kg_relation")
            relations = cursor.fetchall()
    return entities, relations


def chunked(rows: List[dict], size: int) -> Iterable[List[dict]]:
    for index in range(0, len(rows), size):
        yield rows[index: index + size]


def keyword_id(keyword: str) -> str:
    return "kw_" + keyword.strip().lower().replace(" ", "_")


def venue_id(venue: str) -> str:
    return "venue_" + venue.strip().lower().replace(" ", "_")


def run_schema(session) -> None:
    schema_path = os.path.join(os.path.dirname(__file__), "neo4j_schema.cypher")
    with open(schema_path, "r", encoding="utf-8") as handle:
        statements = [stmt.strip() for stmt in handle.read().split(";") if stmt.strip()]
    for statement in statements:
        session.run(statement)


def import_to_neo4j(args, papers: Dict[str, MergedPaper], authors_map: Dict[str, Author], citations: List[Citation], legacy_entities, legacy_relations) -> None:
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(args.neo4j_uri, auth=(args.neo4j_user, args.neo4j_password))
    try:
        with driver.session(database=args.neo4j_database) as session:
            run_schema(session)
            if args.clear:
                session.run("MATCH (n:GraphNode) DETACH DELETE n")

            paper_rows = []
            author_rows = {}
            keyword_rows = {}
            venue_rows = {}
            authorship_rows = []
            keyword_edges = []
            venue_edges = []
            coauthor_pairs = set()

            for paper in papers.values():
                paper_rows.append({
                    "node_id": paper.aminer_id,
                    "aminer_id": paper.aminer_id,
                    "title": paper.title,
                    "abstract": paper.abstract,
                    "authors": paper.authors,
                    "keywords": paper.keywords,
                    "venue": paper.venue,
                    "year": paper.year,
                    "citation_count": paper.citation_count,
                    "embedding": paper.embedding,
                    "mysql_id": paper.mysql_id,
                })

                if paper.venue:
                    vid = venue_id(paper.venue)
                    venue_rows[vid] = {"venue_id": vid, "name": paper.venue}
                    venue_edges.append({"paper_id": paper.aminer_id, "venue_id": vid})

                ordered_authors = [author_id for author_id in paper.authors if author_id]
                for author_id in ordered_authors:
                    author = authors_map.get(author_id)
                    author_rows[author_id] = {
                        "author_id": author_id,
                        "name": author.name if author else author_id,
                        "org": author.org if author else "",
                        "interests": author.interests if author else [],
                    }
                    authorship_rows.append({"author_id": author_id, "paper_id": paper.aminer_id})

                for keyword in paper.keywords:
                    kid = keyword_id(keyword)
                    keyword_rows[kid] = {"keyword_id": kid, "name": keyword}
                    keyword_edges.append({"paper_id": paper.aminer_id, "keyword_id": kid})

                for index, left in enumerate(ordered_authors):
                    for right in ordered_authors[index + 1:]:
                        if left != right:
                            coauthor_pairs.add(tuple(sorted((left, right))))

            citation_rows = [
                {"citing": citation.citing_paper_id, "cited": citation.cited_paper_id}
                for citation in citations
                if citation.citing_paper_id in papers and citation.cited_paper_id in papers
            ]

            for rows in chunked(paper_rows, args.batch_size):
                session.run("""
                    UNWIND $rows AS row
                    MERGE (p:GraphNode:Paper {node_id: row.node_id})
                    SET p.aminer_id = row.aminer_id,
                        p.title = row.title,
                        p.abstract = row.abstract,
                        p.authors = row.authors,
                        p.keywords = row.keywords,
                        p.venue = row.venue,
                        p.year = row.year,
                        p.citation_count = row.citation_count,
                        p.embedding = row.embedding,
                        p.mysql_id = row.mysql_id,
                        p.label = row.title,
                        p.node_type = "paper"
                """, rows=rows)

            for rows in chunked(list(author_rows.values()), args.batch_size):
                session.run("""
                    UNWIND $rows AS row
                    MERGE (a:GraphNode:Author {node_id: row.author_id})
                    SET a.author_id = row.author_id,
                        a.name = row.name,
                        a.org = row.org,
                        a.interests = row.interests,
                        a.label = row.name,
                        a.node_type = "author"
                """, rows=rows)

            for rows in chunked(list(keyword_rows.values()), args.batch_size):
                session.run("""
                    UNWIND $rows AS row
                    MERGE (k:GraphNode:Keyword {node_id: row.keyword_id})
                    SET k.keyword_id = row.keyword_id,
                        k.name = row.name,
                        k.label = row.name,
                        k.node_type = "keyword"
                """, rows=rows)

            for rows in chunked(list(venue_rows.values()), args.batch_size):
                session.run("""
                    UNWIND $rows AS row
                    MERGE (v:GraphNode:Venue {node_id: row.venue_id})
                    SET v.venue_id = row.venue_id,
                        v.name = row.name,
                        v.label = row.name,
                        v.node_type = "venue"
                """, rows=rows)

            for rows in chunked(authorship_rows, args.batch_size):
                session.run("""
                    UNWIND $rows AS row
                    MATCH (a:Author {author_id: row.author_id})
                    MATCH (p:Paper {aminer_id: row.paper_id})
                    MERGE (a)-[:AUTHOR_OF {relation: "author_of"}]->(p)
                """, rows=rows)

            for rows in chunked(keyword_edges, args.batch_size):
                session.run("""
                    UNWIND $rows AS row
                    MATCH (p:Paper {aminer_id: row.paper_id})
                    MATCH (k:Keyword {keyword_id: row.keyword_id})
                    MERGE (p)-[:HAS_KEYWORD {relation: "has_keyword"}]->(k)
                """, rows=rows)

            for rows in chunked(venue_edges, args.batch_size):
                session.run("""
                    UNWIND $rows AS row
                    MATCH (p:Paper {aminer_id: row.paper_id})
                    MATCH (v:Venue {venue_id: row.venue_id})
                    MERGE (p)-[:PUBLISH_IN {relation: "publish_in"}]->(v)
                """, rows=rows)

            for rows in chunked(citation_rows, args.batch_size):
                session.run("""
                    UNWIND $rows AS row
                    MATCH (src:Paper {aminer_id: row.citing})
                    MATCH (dst:Paper {aminer_id: row.cited})
                    MERGE (src)-[:CITE {relation: "cite"}]->(dst)
                """, rows=rows)

            for rows in chunked(
                [{"left": left, "right": right} for left, right in sorted(coauthor_pairs)],
                args.batch_size,
            ):
                session.run("""
                    UNWIND $rows AS row
                    MATCH (left:Author {author_id: row.left})
                    MATCH (right:Author {author_id: row.right})
                    MERGE (left)-[:CO_AUTHOR {relation: "co_author"}]->(right)
                    MERGE (right)-[:CO_AUTHOR {relation: "co_author"}]->(left)
                """, rows=rows)

            if legacy_entities:
                for rows in chunked([
                    {
                        "node_id": f"legacy_entity_{entity['id']}",
                        "legacy_id": entity["id"],
                        "name": entity["name"],
                        "type": entity["type"],
                        "external_id": entity.get("external_id"),
                        "properties_json": entity.get("properties"),
                    }
                    for entity in legacy_entities
                ], args.batch_size):
                    session.run("""
                        UNWIND $rows AS row
                        MERGE (n:GraphNode:LegacyEntity {node_id: row.node_id})
                        SET n.legacy_id = row.legacy_id,
                            n.name = row.name,
                            n.entity_type = row.type,
                            n.external_id = row.external_id,
                            n.properties_json = row.properties_json,
                            n.label = row.name,
                            n.node_type = "legacy_entity"
                    """, rows=rows)

                for rows in chunked([
                    {
                        "source": f"legacy_entity_{relation['source_id']}",
                        "target": f"legacy_entity_{relation['target_id']}",
                        "relation_type": relation["relation_type"],
                        "weight": relation.get("weight") or 1.0,
                    }
                    for relation in legacy_relations
                ], args.batch_size):
                    session.run("""
                        UNWIND $rows AS row
                        MATCH (src:LegacyEntity {node_id: row.source})
                        MATCH (dst:LegacyEntity {node_id: row.target})
                        MERGE (src)-[r:LEGACY_RELATION {relation: row.relation_type, dst_id: row.target}]->(dst)
                        SET r.weight = row.weight
                    """, rows=rows)
    finally:
        driver.close()


def print_summary(args) -> None:
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(args.neo4j_uri, auth=(args.neo4j_user, args.neo4j_password))
    try:
        with driver.session(database=args.neo4j_database) as session:
            counts = {
                "papers": session.run("MATCH (p:Paper) RETURN count(p) AS total").single()["total"],
                "authors": session.run("MATCH (a:Author) RETURN count(a) AS total").single()["total"],
                "keywords": session.run("MATCH (k:Keyword) RETURN count(k) AS total").single()["total"],
                "venues": session.run("MATCH (v:Venue) RETURN count(v) AS total").single()["total"],
                "relations": session.run("MATCH ()-[r]->() RETURN count(r) AS total").single()["total"],
            }
    finally:
        driver.close()

    print(json.dumps(counts, ensure_ascii=False, indent=2))


def main() -> None:
    args = parse_args()
    papers: Dict[str, MergedPaper] = {}
    if not args.skip_mysql:
        papers.update(load_mysql_papers(args))
    papers, authors_map, citations = merge_aminer_data(args, papers)
    legacy_entities, legacy_relations = load_legacy_kg(args)
    import_to_neo4j(args, papers, authors_map, citations, legacy_entities, legacy_relations)
    print_summary(args)


if __name__ == "__main__":
    main()
