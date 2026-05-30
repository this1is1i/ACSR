package com.example.research.controller;

import com.example.research.dto.KeywordDto;
import com.example.research.util.Result;
import org.neo4j.driver.Driver;
import org.neo4j.driver.Session;
import org.neo4j.driver.SessionConfig;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/knowledge")
public class KnowledgeController {

    private final ObjectProvider<Driver> neo4jDriverProvider;

    @Value("${graph.neo4j.database:neo4j}")
    private String database;

    public KnowledgeController(ObjectProvider<Driver> neo4jDriverProvider) {
        this.neo4jDriverProvider = neo4jDriverProvider;
    }

    @GetMapping("/graph")
    public Result<Map<String, Object>> getGraph() {
        return Result.success(Map.of("nodes", List.of(), "edges", List.of()));
    }

    @GetMapping("/keywords")
    public Result<List<KeywordDto>> getKeywords() {
        Driver driver = neo4jDriverProvider.getIfAvailable();
        if (driver == null) {
            return Result.success(List.of());
        }
        List<KeywordDto> keywords = new ArrayList<>();
        try (Session session = driver.session(SessionConfig.forDatabase(database))) {
            var result = session.run(
                "MATCH (k:Keyword)<-[:HAS_KEYWORD]-(p:Paper) " +
                "RETURN k.label AS label, count(p) AS freq ORDER BY freq DESC");
            while (result.hasNext()) {
                var record = result.next();
                String label = record.get("label").asString();
                long freq = record.get("freq").asLong(0);
                keywords.add(new KeywordDto(label, freq));
            }
        }
        return Result.success(keywords);
    }
}
