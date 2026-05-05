package com.example.research.service.impl;

import com.example.research.entity.KgEntity;
import com.example.research.entity.KgRelation;
import com.example.research.repository.KgEntityMapper;
import com.example.research.repository.KgRelationMapper;
import com.example.research.service.KnowledgeService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class KnowledgeServiceImpl implements KnowledgeService {

    private final KgEntityMapper kgEntityMapper;
    private final KgRelationMapper kgRelationMapper;

    @Override
    public Map<String, Object> getGraph() {
        List<KgEntity> entities = kgEntityMapper.findByTypes(List.of("KEYWORD"));
        if (entities.isEmpty()) {
            log.warn("Knowledge graph is empty — no entities found");
            Map<String, Object> empty = new HashMap<>();
            empty.put("nodes", List.of());
            empty.put("edges", List.of());
            return empty;
        }

        List<Long> entityIds = entities.stream().map(KgEntity::getId).collect(Collectors.toList());
        List<KgRelation> relations = kgRelationMapper.findByEntityIds(entityIds);

        // Compute degree (relation count) per entity as mastery proxy
        Map<Long, Integer> degreeMap = new HashMap<>();
        for (KgRelation rel : relations) {
            degreeMap.merge(rel.getSourceId(), 1, Integer::sum);
            degreeMap.merge(rel.getTargetId(), 1, Integer::sum);
        }
        int maxDegree = degreeMap.values().stream().max(Integer::compareTo).orElse(1);

        List<Map<String, Object>> nodes = new ArrayList<>();
        for (KgEntity entity : entities) {
            Map<String, Object> node = new HashMap<>();
            node.put("id", entity.getId());
            node.put("name", entity.getName());
            node.put("type", entity.getType().toLowerCase());

            int degree = degreeMap.getOrDefault(entity.getId(), 0);
            double mastery = maxDegree > 0 ? Math.round((double) degree / maxDegree * 100.0) / 100.0 : 0.0;
            node.put("mastery", mastery);

            int depth = mastery >= 0.7 ? 0 : mastery >= 0.4 ? 1 : 2;
            String group = mastery >= 0.7 ? "foundation" : mastery >= 0.4 ? "intermediate" : "target";
            node.put("depth", depth);
            node.put("group", group);

            nodes.add(node);
        }

        List<Map<String, Object>> edges = new ArrayList<>();
        for (KgRelation rel : relations) {
            Map<String, Object> edge = new HashMap<>();
            edge.put("source", rel.getSourceId());
            edge.put("target", rel.getTargetId());
            edge.put("weight", rel.getWeight() != null ? rel.getWeight() : 1.0);
            edges.add(edge);
        }

        Map<String, Object> result = new HashMap<>();
        result.put("nodes", nodes);
        result.put("edges", edges);
        return result;
    }
}
