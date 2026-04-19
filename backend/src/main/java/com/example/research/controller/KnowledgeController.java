package com.example.research.controller;

import com.example.research.util.Result;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/api/knowledge")
public class KnowledgeController {

    @GetMapping("/graph")
    public Result<Map<String, Object>> getGraph() {
        Map<String, Object> payload = new HashMap<>();
        payload.put("nodes", Arrays.asList(
                Map.of("id",1,"name","Machine Learning","mastery",0.8),
                Map.of("id",2,"name","Reinforcement Learning","mastery",0.6),
                Map.of("id",3,"name","Actor-Critic","mastery",0.5),
                Map.of("id",4,"name","Deep Learning","mastery",0.7),
                Map.of("id",5,"name","NLP","mastery",0.3),
                Map.of("id",6,"name","Graph Neural Networks","mastery",0.2)
        ));
        payload.put("edges", Arrays.asList(
                Map.of("source",1,"target",2),
                Map.of("source",2,"target",3),
                Map.of("source",1,"target",4),
                Map.of("source",4,"target",5),
                Map.of("source",4,"target",6)
        ));
        return Result.success(payload);
    }
}
