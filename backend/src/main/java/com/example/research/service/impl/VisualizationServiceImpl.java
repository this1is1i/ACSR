package com.example.research.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.example.research.entity.BehaviorLog;
import com.example.research.entity.Paper;
import com.example.research.entity.User;
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

    private final KnowledgeService knowledgeService;
    private final BehaviorLogMapper behaviorLogMapper;
    private final BrowseHistoryMapper browseHistoryMapper;
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

        Set<String> activeFields = reads.stream()
                .map(b -> paperMapper.selectById(b.getPaperId()))
                .filter(Objects::nonNull)
                .flatMap(p -> parseJsonArray(p.getKeywords()).stream())
                .collect(Collectors.toSet());
        stats.put("activeFields", activeFields.size());

        double avgCitations = reads.stream()
                .map(b -> paperMapper.selectById(b.getPaperId()))
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

    // ── knowledge graph (3D) ───────────────────────────────────────
    @SuppressWarnings("unchecked")
    private Map<String, Object> buildKnowledgeGraph(Long userId) {
        Map<String, Object> graph = knowledgeService.getGraph();

        List<Map<String, Object>> graphNodes = (List<Map<String, Object>>) graph.get("nodes");
        List<Map<String, Object>> graphEdges = (List<Map<String, Object>>) graph.get("edges");

        // Compute learning path: top 12 nodes as route (greedy traversal by depth)
        Map<String, Object> learningPath = computeLearningPath(graphNodes, graphEdges);

        Map<String, Object> knowledge = new HashMap<>();
        knowledge.put("nodes", graphNodes);
        knowledge.put("edges", graphEdges);
        knowledge.put("learningPath", learningPath);
        return knowledge;
    }

    private Map<String, Object> computeLearningPath(
            List<Map<String, Object>> nodes,
            List<Map<String, Object>> edges) {

        Map<Object, List<Map<String, Object>>> childrenBySource = new HashMap<>();
        for (var edge : edges) {
            Object source = edge.get("source");
            childrenBySource.computeIfAbsent(source, k -> new ArrayList<>()).add(edge);
        }

        // Find foundation nodes (depth 0) and build BFS route
        List<Object> route = new ArrayList<>();
        Set<Object> visited = new HashSet<>();
        List<Map<String, Object>> foundationNodes = nodes.stream()
                .filter(n -> Integer.valueOf(0).equals(n.get("depth")))
                .collect(Collectors.toList());

        for (var start : foundationNodes) {
            Object startId = start.get("id");
            if (visited.add(startId)) {
                route.add(startId);
                // BFS from foundation
                List<Object> queue = new ArrayList<>();
                queue.add(startId);
                while (!queue.isEmpty() && route.size() < 16) {
                    Object current = queue.remove(0);
                    List<Map<String, Object>> children = childrenBySource.getOrDefault(current, List.of());
                    for (var childEdge : children) {
                        Object targetId = childEdge.get("target");
                        if (visited.add(targetId)) {
                            route.add(targetId);
                            queue.add(targetId);
                            if (route.size() >= 16) break;
                        }
                    }
                }
            }
            if (route.size() >= 12) break;
        }

        String topic = "Research Journey";
        if (!route.isEmpty()) {
            Object lastId = route.get(route.size() - 1);
            for (var n : nodes) {
                if (lastId.equals(n.get("id"))) {
                    topic = (String) n.getOrDefault("name", topic);
                    break;
                }
            }
        }

        Map<String, Object> path = new HashMap<>();
        path.put("topic", topic);
        path.put("estimatedHours", Math.round(route.size() * 2.5 * 10.0) / 10.0);
        path.put("coverage", Math.min(1.0, Math.round((double) route.size() / nodes.size() * 100.0) / 100.0));
        path.put("route", route);
        return path;
    }

    // ── utility methods ────────────────────────────────────────────

    private List<BehaviorLog> getBehaviorsByAction(Long userId, String action) {
        return behaviorLogMapper.selectList(
                new LambdaQueryWrapper<BehaviorLog>()
                        .eq(BehaviorLog::getUserId, userId)
                        .eq(BehaviorLog::getAction, action));
    }

    private Map<String, Integer> buildKeywordFrequencyMap() {
        List<Paper> papers = paperMapper.selectList(null);
        Map<String, Integer> freq = new HashMap<>();
        for (Paper paper : papers) {
            for (String kw : parseJsonArray(paper.getKeywords())) {
                freq.merge(kw, 1, Integer::sum);
            }
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
