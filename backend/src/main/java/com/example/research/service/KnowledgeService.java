package com.example.research.service;

import java.util.Map;

public interface KnowledgeService {
    /**
     * Get knowledge graph nodes and edges from database.
     * @return Map with keys: "nodes", "edges"
     */
    Map<String, Object> getGraph();
}
