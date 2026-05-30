package com.example.research.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.example.research.client.PythonRecClient;
import com.example.research.entity.BehaviorLog;
import com.example.research.entity.Paper;
import com.example.research.entity.UserInterestHistory;
import com.example.research.repository.BehaviorLogMapper;
import com.example.research.repository.PaperMapper;
import com.example.research.repository.UserInterestHistoryMapper;
import com.example.research.service.VisualizationService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class VisualizationServiceImpl implements VisualizationService {

    private final PythonRecClient pythonRecClient;
    private final BehaviorLogMapper behaviorLogMapper;
    private final UserInterestHistoryMapper interestHistoryMapper;
    private final PaperMapper paperMapper;

    @Override
    public Map<String, Object> getVisualizationData(Long userId, String targetTopic) {
        return Map.of("knowledge", buildKnowledgeGraph(userId, targetTopic));
    }

    private Map<String, Object> buildKnowledgeGraph(Long userId, String targetTopic) {
        // Use caller-provided target topic if given; otherwise auto-derive from user interest
        if (targetTopic == null || targetTopic.isBlank()) {
            List<UserInterestHistory> interests = interestHistoryMapper.selectList(
                    new LambdaQueryWrapper<UserInterestHistory>()
                            .eq(UserInterestHistory::getUserId, userId)
                            .orderByDesc(UserInterestHistory::getWeight));
            targetTopic = interests.isEmpty() ? "reinforcement learning"
                    : interests.get(0).getInterestTag();
        }

        // Gather user's history paper AMiner IDs
        List<BehaviorLog> behaviors = behaviorLogMapper.selectList(
                new LambdaQueryWrapper<BehaviorLog>()
                        .eq(BehaviorLog::getUserId, userId)
                        .orderByDesc(BehaviorLog::getTimestamp)
                        .last("LIMIT 20"));
        Set<Long> paperIds = behaviors.stream().map(BehaviorLog::getPaperId).collect(Collectors.toSet());
        List<Paper> historyPapers = paperIds.isEmpty() ? List.of()
                : paperMapper.findByIds(new ArrayList<>(paperIds));
        List<String> historyAminers = historyPapers.stream()
                .map(Paper::getAminerId).filter(Objects::nonNull).collect(Collectors.toList());

        // Call Python /learning-path (uses Neo4j KG, not MySQL)
        PythonRecClient.LearningPathResponse pyResp = null;
        try {
            pyResp = pythonRecClient.getLearningPath(
                    String.valueOf(userId), targetTopic, historyAminers, 16);
        } catch (Exception e) {
            log.warn("Python learning-path 不可用: {}", e.getMessage());
        }

        if (pyResp == null) {
            log.info("Learning path: no Python response, returning empty graph for userId={}", userId);
            return buildEmptyKnowledge();
        }

        // Map Python response to expected format
        List<Map<String, Object>> pathNodes = new ArrayList<>();
        for (var pn : pyResp.getNodes()) {
            Map<String, Object> node = new HashMap<>();
            node.put("id", pn.getNodeId());
            node.put("name", pn.getLabel());
            node.put("type", pn.getNodeType());
            node.put("mastery", pn.getMastery());
            node.put("depth", pn.getDepth());
            node.put("year", pn.getYear());
            node.put("color", pn.getColor() != null ? pn.getColor() : "#3B82F6");
            node.put("glowIntensity", pn.getGlowIntensity());
            int depth = pn.getDepth();
            String group = depth == 0 ? "foundation"
                    : depth <= 2 ? "intermediate" : "target";
            node.put("group", group);
            pathNodes.add(node);
        }

        List<Map<String, Object>> pathEdges = new ArrayList<>();
        if (pyResp.getEdges() != null) {
            pathEdges.addAll(pyResp.getEdges());
        }

        Map<String, Object> learningPath = new HashMap<>();
        learningPath.put("topic", pyResp.getTopic());
        learningPath.put("estimatedHours", pyResp.getEstimatedHours());
        learningPath.put("coverage", pyResp.getCoverage());
        List<Object> route = new ArrayList<>();
        for (var pn : pyResp.getNodes()) {
            route.add(pn.getNodeId());
        }
        learningPath.put("route", route);

        Map<String, Object> knowledge = new HashMap<>();
        knowledge.put("nodes", pathNodes);
        knowledge.put("edges", pathEdges);
        knowledge.put("learningPath", learningPath);
        knowledge.put("pathNodes", pathNodes);
        knowledge.put("pathEdges", pathEdges);
        return knowledge;
    }

    private Map<String, Object> buildEmptyKnowledge() {
        Map<String, Object> knowledge = new HashMap<>();
        knowledge.put("nodes", List.of());
        knowledge.put("edges", List.of());
        knowledge.put("learningPath", Map.of("topic", "", "estimatedHours", 0, "coverage", 0, "route", List.of()));
        knowledge.put("pathNodes", List.of());
        knowledge.put("pathEdges", List.of());
        return knowledge;
    }
}
