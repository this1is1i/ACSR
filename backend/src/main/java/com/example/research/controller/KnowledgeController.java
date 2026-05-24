package com.example.research.controller;

import com.example.research.util.Result;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/knowledge")
public class KnowledgeController {

    @GetMapping("/graph")
    public Result<Map<String, Object>> getGraph() {
        return Result.success(Map.of("nodes", List.of(), "edges", List.of()));
    }
}
