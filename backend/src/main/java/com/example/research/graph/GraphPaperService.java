package com.example.research.graph;

import lombok.RequiredArgsConstructor;
import org.neo4j.driver.Driver;
import org.neo4j.driver.Record;
import org.neo4j.driver.Session;
import org.neo4j.driver.SessionConfig;
import org.neo4j.driver.types.Node;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class GraphPaperService {

    private final ObjectProvider<Driver> neo4jDriverProvider;

    @Value("${graph.neo4j.database:neo4j}")
    private String database;

    public boolean isEnabled() {
        return neo4jDriverProvider.getIfAvailable() != null;
    }

    public Optional<GraphPaper> findByAminerId(String aminerId) {
        List<GraphPaper> papers = fetchPapers("""
                MATCH (p:Paper {aminer_id: $aminerId})
                RETURN p
                LIMIT 1
                """, Map.of("aminerId", aminerId));
        return papers.stream().findFirst();
    }

    public List<GraphPaper> findByAminerIds(List<String> aminers) {
        if (aminers == null || aminers.isEmpty()) {
            return List.of();
        }
        List<GraphPaper> papers = fetchPapers("""
                UNWIND $aminers AS aminerId
                MATCH (p:Paper {aminer_id: aminerId})
                RETURN p
                """, Map.of("aminers", aminers));

        Map<String, GraphPaper> paperMap = papers.stream()
                .filter(p -> p.getAminerId() != null)
                .collect(Collectors.toMap(GraphPaper::getAminerId, p -> p, (left, right) -> left, LinkedHashMap::new));

        return aminers.stream()
                .map(paperMap::get)
                .filter(Objects::nonNull)
                .collect(Collectors.toList());
    }

    public List<GraphPaper> search(String keyword, int limit) {
        if (keyword == null || keyword.isBlank()) {
            return List.of();
        }
        return fetchPapers("""
                MATCH (p:Paper)
                WHERE toLower(coalesce(p.title, "")) CONTAINS toLower($keyword)
                   OR toLower(coalesce(p.abstract, "")) CONTAINS toLower($keyword)
                   OR ANY(kw IN coalesce(p.keywords, []) WHERE toLower(kw) CONTAINS toLower($keyword))
                RETURN p
                ORDER BY coalesce(p.citation_count, 0) DESC, coalesce(p.year, 0) DESC
                LIMIT $limit
                """, Map.of("keyword", keyword, "limit", limit));
    }

    public List<GraphPaper> listPopular(int offset, int limit, Integer year, String venue) {
        Map<String, Object> params = filterParams(offset, limit, year, venue);
        return fetchPapers("""
                MATCH (p:Paper)
                WHERE ($year IS NULL OR p.year = $year)
                  AND ($venue IS NULL OR toLower(coalesce(p.venue, "")) = toLower($venue))
                RETURN p
                ORDER BY coalesce(p.citation_count, 0) DESC, coalesce(p.year, 0) DESC
                SKIP $offset
                LIMIT $limit
                """, params);
    }

    public void upsertPapers(List<GraphPaper> papers) {
        if (papers == null || papers.isEmpty()) {
            return;
        }
        Driver driver = neo4jDriverProvider.getIfAvailable();
        if (driver == null) {
            return;
        }

        List<Map<String, Object>> rows = papers.stream()
                .map(paper -> {
                    Map<String, Object> row = new LinkedHashMap<>();
                    row.put("nodeId", paper.getGraphNodeId() == null || paper.getGraphNodeId().isBlank() ? paper.getAminerId() : paper.getGraphNodeId());
                    row.put("aminerId", paper.getAminerId());
                    row.put("title", paper.getTitle());
                    row.put("abstract", paper.getAbstractText());
                    row.put("authors", paper.getAuthors() == null ? List.of() : paper.getAuthors());
                    row.put("keywords", paper.getKeywords() == null ? List.of() : paper.getKeywords());
                    row.put("venue", paper.getVenue());
                    row.put("year", paper.getYear());
                    row.put("citationCount", paper.getCitationCount() == null ? 0 : paper.getCitationCount());
                    row.put("embedding", paper.getEmbedding());
                    return row;
                })
                .collect(Collectors.toList());

        try (Session session = driver.session(sessionConfig())) {
            session.executeWrite(tx -> {
                tx.run("""
                        UNWIND $rows AS row
                        MERGE (p:GraphNode:Paper {node_id: row.nodeId})
                        SET p.aminer_id = row.aminerId,
                            p.title = row.title,
                            p.abstract = row.abstract,
                            p.authors = row.authors,
                            p.keywords = row.keywords,
                            p.venue = row.venue,
                            p.year = row.year,
                            p.citation_count = row.citationCount,
                            p.embedding = row.embedding,
                            p.label = row.title,
                            p.node_type = "paper"
                        """, Map.of("rows", rows));
                return null;
            });
        }
    }

    public long countPapers(Integer year, String venue) {
        Driver driver = neo4jDriverProvider.getIfAvailable();
        if (driver == null) {
            return 0L;
        }
        try (Session session = driver.session(sessionConfig())) {
            return session.executeRead(tx -> tx.run("""
                    MATCH (p:Paper)
                    WHERE ($year IS NULL OR p.year = $year)
                      AND ($venue IS NULL OR toLower(coalesce(p.venue, "")) = toLower($venue))
                    RETURN count(p) AS total
                    """, filterParams(0, 0, year, venue)).single().get("total").asLong());
        }
    }

    private List<GraphPaper> fetchPapers(String cypher, Map<String, Object> params) {
        Driver driver = neo4jDriverProvider.getIfAvailable();
        if (driver == null) {
            return List.of();
        }
        try (Session session = driver.session(sessionConfig())) {
            return session.executeRead(tx -> tx.run(cypher, params).list(this::mapPaper));
        }
    }

    private SessionConfig sessionConfig() {
        return SessionConfig.forDatabase(database);
    }

    private Map<String, Object> filterParams(int offset, int limit, Integer year, String venue) {
        Map<String, Object> params = new LinkedHashMap<>();
        params.put("offset", Math.max(offset, 0));
        params.put("limit", Math.max(limit, 0));
        params.put("year", year);
        params.put("venue", venue == null || venue.isBlank() ? null : venue);
        return params;
    }

    private GraphPaper mapPaper(Record record) {
        Node node = record.get("p").asNode();
        GraphPaper paper = new GraphPaper();
        paper.setGraphNodeId(readString(node, "node_id"));
        paper.setAminerId(readString(node, "aminer_id"));
        paper.setTitle(readString(node, "title"));
        paper.setAbstractText(readString(node, "abstract"));
        paper.setKeywords(readStringList(node.get("keywords")));
        paper.setAuthors(readStringList(node.get("authors")));
        paper.setVenue(readString(node, "venue"));
        paper.setYear(readInteger(node, "year"));
        paper.setCitationCount(readInteger(node, "citation_count"));
        paper.setEmbedding(readNullableString(node.get("embedding")));
        return paper;
    }

    private String readString(Node node, String property) {
        return node.get(property).asString("");
    }

    private String readNullableString(org.neo4j.driver.Value value) {
        return value == null || value.isNull() ? null : value.asString();
    }

    private Integer readInteger(Node node, String property) {
        org.neo4j.driver.Value value = node.get(property);
        return value == null || value.isNull() ? null : value.asInt();
    }

    private List<String> readStringList(org.neo4j.driver.Value value) {
        if (value == null || value.isNull()) {
            return List.of();
        }
        List<Object> rawList = value.asList();
        List<String> results = new ArrayList<>(rawList.size());
        for (Object item : rawList) {
            if (item != null) {
                results.add(String.valueOf(item));
            }
        }
        return results;
    }
}
