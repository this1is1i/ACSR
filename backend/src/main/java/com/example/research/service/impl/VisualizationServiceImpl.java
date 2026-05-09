package com.example.research.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.example.research.client.PythonRecClient;
import com.example.research.entity.BehaviorLog;
import com.example.research.entity.KgEntity;
import com.example.research.entity.Paper;
import com.example.research.entity.User;
import com.example.research.entity.UserInterestHistory;
import com.example.research.repository.*;
import com.example.research.service.KnowledgeService;
import com.example.research.service.VisualizationService;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
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
    private final KnowledgeService knowledgeService;
    private final BehaviorLogMapper behaviorLogMapper;
    private final BrowseHistoryMapper browseHistoryMapper;
    private final KgEntityMapper kgEntityMapper;
    private final UserInterestHistoryMapper interestHistoryMapper;
    private final PaperMapper paperMapper;
    private final UserMapper userMapper;
    private final ObjectMapper objectMapper;

    @Override
    public Map<String, Object> getVisualizationData(Long userId) {
        Map<String, Object> payload = new HashMap<>();
        payload.put("stats", buildStats(userId));
        payload.put("interest", buildInterestTrends(userId));
        payload.put("field", buildFieldDistribution());
        payload.put("heatmap", buildHeatmap(userId));
        payload.put("tags", buildTagCloud());
        payload.put("behaviors", buildBehaviors(userId));
        payload.put("knowledge", buildKnowledgeGraph(userId));
        return payload;
    }

    // ── stats ─────────────────────────────────────────────────────
    private Map<String, Object> buildStats(Long userId) {
        Map<String, Object> stats = new HashMap<>();

        List<BehaviorLog> reads = getBehaviorsByAction(userId, "read");
        int totalReadSeconds = reads.stream()
                .mapToInt(b -> b.getDuration() != null ? b.getDuration() : 0).sum();
        stats.put("readTime", formatHours(totalReadSeconds));
        stats.put("readCount", reads.size());

        // Batch-fetch all distinct papers in a single query (fixes N+1)
        Set<Long> distinctPaperIds = reads.stream()
                .map(BehaviorLog::getPaperId).collect(Collectors.toSet());
        List<Paper> batchPapers = distinctPaperIds.isEmpty()
                ? List.of()
                : paperMapper.findByIds(new ArrayList<>(distinctPaperIds));
        Map<Long, Paper> paperMap = batchPapers.stream()
                .collect(Collectors.toMap(Paper::getId, p -> p, (a, b) -> a));

        Set<String> activeFields = reads.stream()
                .map(b -> paperMap.get(b.getPaperId()))
                .filter(Objects::nonNull)
                .flatMap(p -> parseJsonArray(p.getKeywords()).stream())
                .collect(Collectors.toSet());
        stats.put("activeFields", activeFields.size());

        double avgCitations = reads.stream()
                .map(b -> paperMap.get(b.getPaperId()))
                .filter(Objects::nonNull)
                .mapToInt(Paper::getCitationCount)
                .average().orElse(0);
        stats.put("depth", Math.min(100.0, Math.round(avgCitations / 100.0 * 10) / 10.0));

        stats.put("readTimeChange", "0%");
        stats.put("readCountChange", "0");
        stats.put("activeFieldsChange", 0);
        stats.put("depthChange", "0.0");

        return stats;
    }

    // ── interest trends ────────────────────────────────────────────
    private Map<String, Object> buildInterestTrends(Long userId) {
        List<Map<String, Object>> monthlyData = interestHistoryMapper.findMonthlyAggregation(userId);

        if (monthlyData.isEmpty()) {
            return buildInterestFromUserProfile(userId);
        }

        Map<String, List<Map<String, Object>>> byTag = monthlyData.stream()
                .collect(Collectors.groupingBy(row -> (String) row.get("interest_tag")));

        List<String> labels = monthlyData.stream()
                .map(row -> (String) row.get("month"))
                .distinct().sorted().collect(Collectors.toList());

        List<Map<String, Object>> datasets = new ArrayList<>();
        for (var entry : byTag.entrySet()) {
            Map<String, Number> tagMonthMap = entry.getValue().stream()
                    .collect(Collectors.toMap(
                            row -> (String) row.get("month"),
                            row -> (Number) row.get("avg_weight"),
                            (a, b) -> b));
            List<Number> data = labels.stream()
                    .map(m -> tagMonthMap.getOrDefault(m, 0))
                    .collect(Collectors.toList());
            Map<String, Object> ds = new HashMap<>();
            ds.put("label", entry.getKey());
            ds.put("data", data);
            datasets.add(ds);
        }

        return Map.of("labels", labels, "datasets", datasets);
    }

    private Map<String, Object> buildInterestFromUserProfile(Long userId) {
        User user = userMapper.selectById(userId);
        List<String> interests = parseCommaSeparated(
                user != null ? user.getResearchInterests() : null);

        List<String> labels = Arrays.asList("1月", "2月", "3月", "4月", "5月", "6月",
                "7月", "8月", "9月", "10月", "11月", "12月");
        List<Map<String, Object>> datasets = new ArrayList<>();
        Random rng = new Random(42);
        for (String interest : interests) {
            List<Integer> data = new ArrayList<>();
            double base = 30 + rng.nextDouble() * 30;
            for (int i = 0; i < 12; i++) {
                base += rng.nextDouble() * 8 - 2;
                data.add((int) Math.max(0, base));
            }
            Map<String, Object> ds = new HashMap<>();
            ds.put("label", interest.trim());
            ds.put("data", data);
            datasets.add(ds);
        }
        return Map.of("labels", labels, "datasets", datasets);
    }

    // ── field distribution ─────────────────────────────────────────
    private Map<String, Object> buildFieldDistribution() {
        Map<String, Integer> freq = buildKeywordFrequencyMap();
        if (freq.isEmpty()) {
            return Map.of("labels", List.of(), "data", List.of());
        }

        List<Map.Entry<String, Integer>> sorted = freq.entrySet().stream()
                .sorted(Map.Entry.<String, Integer>comparingByValue().reversed())
                .collect(Collectors.toList());

        List<String> labels = new ArrayList<>();
        List<Integer> data = new ArrayList<>();
        int other = 0;
        for (int i = 0; i < sorted.size(); i++) {
            if (i < 5) {
                labels.add(sorted.get(i).getKey());
                data.add(sorted.get(i).getValue());
            } else {
                other += sorted.get(i).getValue();
            }
        }
        if (other > 0) {
            labels.add("Other");
            data.add(other);
        }
        return Map.of("labels", labels, "data", data);
    }

    // ── heatmap ────────────────────────────────────────────────────
    private Map<String, Object> buildHeatmap(Long userId) {
        List<Map<String, Object>> rows = browseHistoryMapper.countByDayOfWeek(userId);
        int[] counts = new int[7];
        for (var row : rows) {
            int mysqlDow = ((Number) row.get("day_of_week")).intValue();
            int jsDow = (mysqlDow + 5) % 7; // MySQL 1(Sun)→6, 2(Mon)→0, etc.
            counts[jsDow] = ((Number) row.get("cnt")).intValue();
        }
        // Convert 0-indexed Mon-Sun array to match frontend labels
        return Map.of(
                "labels", Arrays.asList("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"),
                "data", Arrays.stream(counts).boxed().collect(Collectors.toList())
        );
    }

    // ── tag cloud ──────────────────────────────────────────────────
    private List<Map<String, Object>> buildTagCloud() {
        Map<String, Integer> freq = buildKeywordFrequencyMap();
        if (freq.isEmpty()) return List.of();

        int maxFreq = freq.values().stream().max(Integer::compareTo).orElse(1);
        return freq.entrySet().stream()
                .sorted(Map.Entry.<String, Integer>comparingByValue().reversed())
                .limit(30)
                .map(e -> {
                    int size = Math.max(1, (int) Math.ceil(5.0 * e.getValue() / maxFreq));
                    return Map.of("text", e.getKey(), "size", (Object) size);
                })
                .collect(Collectors.toList());
    }

    // ── behaviors ──────────────────────────────────────────────────
    private List<Map<String, Object>> buildBehaviors(Long userId) {
        List<BehaviorLog> reads = getBehaviorsByAction(userId, "read");
        List<BehaviorLog> favorites = getBehaviorsByAction(userId, "favorite");

        double avgDuration = reads.stream()
                .mapToInt(b -> b.getDuration() != null ? b.getDuration() : 0)
                .average().orElse(0);
        double avgMinutes = avgDuration / 60.0;

        long distinctReadPapers = reads.stream().map(BehaviorLog::getPaperId).distinct().count();
        long favoritedPapers = favorites.stream().map(BehaviorLog::getPaperId).distinct().count();
        double favoriteRate = distinctReadPapers > 0
                ? Math.round(favoritedPapers * 1000.0 / distinctReadPapers) / 10.0
                : 0;

        long totalReads = reads.size();
        long repeatReads = totalReads - distinctReadPapers;
        double repeatRate = totalReads > 0
                ? Math.round(repeatReads * 1000.0 / totalReads) / 10.0
                : 0;

        return Arrays.asList(
                Map.of("icon", "read", "title", "Avg Reading Time",
                       "desc", "Per paper", "value", String.format("%.1f min", avgMinutes)),
                Map.of("icon", "bookmark", "title", "Favorite Rate",
                       "desc", "Read-then-favorite ratio", "value", favoriteRate + "%"),
                Map.of("icon", "repeat", "title", "Re-read Rate",
                       "desc", "Papers read multiple times", "value", repeatRate + "%"),
                Map.of("icon", "clock", "title", "Peak Active Hour",
                       "desc", "Highest activity", "value", "N/A")
        );
    }

    // ── knowledge graph (3D) from Python /learning-path ───────────

    private Map<String, Object> buildKnowledgeGraph(Long userId) {
        // Determine target topic from user's top interest tag
        List<UserInterestHistory> interests = interestHistoryMapper.selectList(
                new LambdaQueryWrapper<UserInterestHistory>()
                        .eq(UserInterestHistory::getUserId, userId)
                        .orderByDesc(UserInterestHistory::getWeight));
        String targetTopic = interests.isEmpty() ? "reinforcement learning"
                : interests.get(0).getInterestTag();

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
            // Ultimate fallback: empty graph (frontend shows placeholder)
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
            // Derive group from mastery
            String group = pn.getMastery() >= 0.7 ? "foundation"
                    : pn.getMastery() >= 0.4 ? "intermediate" : "target";
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

    // ── utility methods ────────────────────────────────────────────

    private List<BehaviorLog> getBehaviorsByAction(Long userId, String action) {
        return behaviorLogMapper.selectList(
                new LambdaQueryWrapper<BehaviorLog>()
                        .eq(BehaviorLog::getUserId, userId)
                        .eq(BehaviorLog::getAction, action));
    }

    private Map<String, Integer> buildKeywordFrequencyMap() {
        // Aggregate keyword frequencies from user_interest_history (avoids full paper scan)
        List<UserInterestHistory> allInterests = interestHistoryMapper.selectList(null);
        Map<String, Integer> freq = new HashMap<>();
        for (UserInterestHistory h : allInterests) {
            freq.merge(h.getInterestTag(), (int) (h.getWeight() * 10), Integer::sum);
        }
        return freq;
    }

    private List<String> parseJsonArray(String json) {
        if (json == null || json.isBlank()) return List.of();
        try {
            return objectMapper.readValue(json, new TypeReference<List<String>>() {});
        } catch (Exception e) {
            return parseCommaSeparated(json);
        }
    }

    private List<String> parseCommaSeparated(String csv) {
        if (csv == null || csv.isBlank()) return List.of();
        return Arrays.stream(csv.split(","))
                .map(String::trim)
                .filter(s -> !s.isEmpty())
                .collect(Collectors.toList());
    }

    private String formatHours(int totalSeconds) {
        double hours = totalSeconds / 3600.0;
        return String.format("%.1fh", hours);
    }
}
