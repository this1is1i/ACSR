package com.example.research.controller;

import com.example.research.service.KnowledgeService;
import com.example.research.util.Result;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Slf4j
@RestController
@RequestMapping("/api/knowledge")
@RequiredArgsConstructor
public class KnowledgeController {

    private final KnowledgeService knowledgeService;

    @GetMapping("/graph")
    public Result<Map<String, Object>> getGraph() {
        Map<String, Object> fullGraph = knowledgeService.getGraph();

        @SuppressWarnings("unchecked")
        List<Map<String, Object>> fullNodes = (List<Map<String, Object>>) fullGraph.get("nodes");
        @SuppressWarnings("unchecked")
        List<Map<String, Object>> fullEdges = (List<Map<String, Object>>) fullGraph.get("edges");

        List<Map<String, Object>> simpleNodes = fullNodes.stream()
                .map(n -> Map.of("id", n.get("id"), "name", n.get("name"),
                                 "mastery", n.get("mastery"),
                                 "color", n.getOrDefault("color", "#3B82F6"),
                                 "glowIntensity", n.getOrDefault("glowIntensity", 0.0)))
                .collect(Collectors.toList());

        List<Map<String, Object>> simpleEdges = fullEdges.stream()
                .map(e -> Map.of("source", e.get("source"), "target", e.get("target")))
                .collect(Collectors.toList());

        return Result.success(Map.of("nodes", simpleNodes, "edges", simpleEdges));
    }
}
