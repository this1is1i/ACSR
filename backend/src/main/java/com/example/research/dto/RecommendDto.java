package com.example.research.dto;

import lombok.Data;
import java.util.List;

public class RecommendDto {

    @Data
    public static class RecommendResponse {
        private String userId;
        private int k;
        private String modelVersion;
        private Double latencyMs;
        private Boolean pythonServiceAvailable;
        private List<RecommendItem> recommendations;
    }

    @Data
    public static class RecommendItem {
        private Long paperId;
        private String aminerId;
        private String title;
        private String venue;
        private Integer year;
        private Integer citationCount;
        private List<String> authors;
        private Double score;
        private Integer rank;
        private String reason;
        private List<String> reasonDetails;
        private Double similarityScore;
        private List<String> topics;
        private Double confidence;
    }

    @Data
    public static class BehaviorRequest {
        private Long paperId;
        private Integer duration;
        private String source;
    }
}
