package com.example.research.client;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Component;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestTemplate;

import java.util.Collections;
import java.util.List;
import java.util.Map;

/**
 * Python 强化学习推荐服务调用客户端
 *
 * 封装对 FastAPI 推荐服务（http://localhost:8000）的 HTTP 调用。
 * 所有接口均有异常降级处理，确保 Python 服务不可用时后端仍能正常响应。
 *
 * 对应 Python 服务接口：
 *   POST /recommend       → 获取 Top-K 推荐
 *   POST /train           → 触发模型训练
 *   GET  /model/info      → 查询模型状态
 *   GET  /health          → 健康检查
 *
 * 注意：Python FastAPI 使用 snake_case 字段名，通过 @JsonProperty 映射到 Java camelCase。
 */
@Slf4j
@Component
public class PythonRecClient {

    private final RestTemplate restTemplate;
    private String baseUrl;

    public PythonRecClient(@Qualifier("pythonRestTemplate") RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    @Value("${python.rec-service.base-url:http://localhost:8000}")
    public void setBaseUrl(String baseUrl) {
        this.baseUrl = baseUrl;
    }

    // ─────────────────────────────────────────────────────────────
    //  请求 / 响应 DTO（@JsonProperty 映射 Python snake_case 字段）
    // ─────────────────────────────────────────────────────────────

    /** POST /recommend 请求体 — 序列化为 snake_case 发送给 Python */
    @Data
    public static class RecRequest {
        @JsonProperty("user_id")
        private String userId;
        private int k;
        private List<String> history;
        private String strategy = "hybrid";

        public RecRequest(String userId, int k, List<String>
                history) {
            this.userId  = userId;
            this.k       = k;
            this.history = history;
        }
    }

    /** 单条推荐结果 — 从 Python snake_case 反序列化 */
    @Data
    public static class RecItem {
        @JsonProperty("paper_id")
        private String paperId;
        private String title;
        private List<String> authors;
        private Integer year;
        private Double score;
        private Integer rank;
        private String reason;
        @JsonProperty("reason_details")
        private List<String> reasonDetails;
        @JsonProperty("similarity_score")
        private Double similarityScore;
        private List<String> topics;
        @JsonProperty("citation_count")
        private Integer citationCount;
        private Double confidence;
    }

    /** POST /recommend 响应体 */
    @Data
    public static class RecResponse {
        @JsonProperty("user_id")
        private String userId;
        private int k;
        @JsonProperty("model_version")
        private String modelVersion;
        @JsonProperty("latency_ms")
        private Double latencyMs;
        private List<RecItem> recommendations;
    }

    /** GET /model/info 响应体 */
    @Data
    public static class ModelInfo {
        @JsonProperty("model_version")
        private String modelVersion;
        @JsonProperty("train_step")
        private Integer trainStep;
        @JsonProperty("episode_count")
        private Integer episodeCount;
        @JsonProperty("model_path")
        private String modelPath;
        @JsonProperty("state_dim")
        private Integer stateDim;
        @JsonProperty("action_num")
        private Integer actionNum;
        @JsonProperty("top_k")
        private Integer topK;
        private String device;
        @JsonProperty("is_training")
        private Boolean isTraining;
        @JsonProperty("last_episode")
        private Integer lastEpisode;
        @JsonProperty("best_reward")
        private Double bestReward;
    }

    // ─────────────────────────────────────────────────────────────
    //  核心接口调用
    // ─────────────────────────────────────────────────────────────

    /**
     * 调用 Python 推荐服务获取 Top-K 推荐结果
     *
     * @param userId  用户 ID（字符串，与 Python 侧保持一致）
     * @param k       推荐数量
     * @param history 用户历史阅读论文 ID 列表（可为空）
     * @return 推荐结果响应，失败时返回 null
     */
    public RecResponse getRecommendations(String userId, int k, List<String> history) {
        String url = baseUrl + "/recommend";
        RecRequest request = new RecRequest(userId, k, history);

        try {
            log.info("调用 Python 推荐服务: userId={}, k={}", userId, k);
            long start = System.currentTimeMillis();

            ResponseEntity<RecResponse> response = restTemplate.postForEntity(
                    url,
                    buildJsonEntity(request),
                    RecResponse.class
            );

            long elapsed = System.currentTimeMillis() - start;
            log.info("Python 推荐服务响应成功，耗时 {}ms，推荐数量: {}",
                     elapsed,
                     response.getBody() != null && response.getBody().getRecommendations() != null
                             ? response.getBody().getRecommendations().size() : 0);

            return response.getBody();

        } catch (ResourceAccessException e) {
            log.error("Python 推荐服务连接失败（服务未启动？）: {}", e.getMessage());
            return null;
        } catch (Exception e) {
            log.error("调用 Python 推荐服务异常: {}", e.getMessage(), e);
            return null;
        }
    }

    /**
     * 触发 Python 侧模型训练（异步执行）
     *
     * @param episodes 训练轮数（null 使用 Python 侧默认配置）
     * @return 是否成功触发
     */
    public boolean triggerTraining(Integer episodes) {
        String url = baseUrl + "/train";
        Map<String, Object> body = episodes != null
                ? Map.of("episodes", episodes)
                : Collections.emptyMap();

        try {
            ResponseEntity<Map> response = restTemplate.postForEntity(
                    url, buildJsonEntity(body), Map.class
            );
            boolean success = response.getStatusCode().is2xxSuccessful();
            if (success) {
                log.info("Python 模型训练已触发，status={}", response.getBody());
            }
            return success;
        } catch (Exception e) {
            log.error("触发 Python 模型训练失败: {}", e.getMessage());
            return false;
        }
    }

    // ── 学习路径相关 DTO ──────────────────────────────────────────

    @Data
    public static class LearningPathRequest {
        @JsonProperty("user_id")
        private String userId;
        @JsonProperty("target_topic")
        private String targetTopic;
        private List<String> history;
        @JsonProperty("max_nodes")
        private int maxNodes = 20;
    }

    @Data
    public static class PathNode {
        @JsonProperty("node_id")
        private String nodeId;
        private String label;
        @JsonProperty("node_type")
        private String nodeType;
        private double mastery;
        private int depth;
        private Integer year;
        private String color;
        @JsonProperty("glow_intensity")
        private double glowIntensity;
    }

    @Data
    public static class LearningPathResponse {
        @JsonProperty("user_id")
        private String userId;
        private String topic;
        @JsonProperty("estimated_hours")
        private double estimatedHours;
        private double coverage;
        private List<PathNode> nodes;
        private List<Map<String, Object>> edges;
    }

    /**
     * 调用 Python 学习路径生成服务
     */
    public LearningPathResponse getLearningPath(String userId, String targetTopic,
                                                  List<String> history, int maxNodes) {
        String url = baseUrl + "/learning-path";
        LearningPathRequest req = new LearningPathRequest();
        req.setUserId(userId);
        req.setTargetTopic(targetTopic);
        req.setHistory(history);
        req.setMaxNodes(maxNodes);

        try {
            ResponseEntity<LearningPathResponse> resp = restTemplate.postForEntity(
                    url, buildJsonEntity(req), LearningPathResponse.class);
            if (resp.getStatusCode().is2xxSuccessful()) {
                return resp.getBody();
            }
        } catch (Exception e) {
            log.warn("调用 Python learning-path 失败: {}", e.getMessage());
        }
        return null;
    }

    /**
     * 获取 Python 侧模型状态信息
     */
    public ModelInfo getModelInfo() {
        String url = baseUrl + "/model/info";
        try {
            return restTemplate.getForObject(url, ModelInfo.class);
        } catch (Exception e) {
            log.warn("获取 Python 模型状态失败: {}", e.getMessage());
            return null;
        }
    }

    /**
     * 检查 Python 推荐服务是否可用
     */
    public boolean isAvailable() {
        String url = baseUrl + "/health";
        try {
            ResponseEntity<Map> resp = restTemplate.getForEntity(url, Map.class);
            return resp.getStatusCode().is2xxSuccessful();
        } catch (Exception e) {
            log.warn("Python 推荐服务不可达: {}", e.getMessage());
            return false;
        }
    }

    // ─────────────────────────────────────────────────────────────
    //  内部工具方法
    // ─────────────────────────────────────────────────────────────

    private <T> HttpEntity<T> buildJsonEntity(T body) {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        return new HttpEntity<>(body, headers);
    }
}
