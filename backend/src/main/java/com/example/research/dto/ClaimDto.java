package com.example.research.dto;

import lombok.Data;
import java.time.LocalDateTime;

public class ClaimDto {

    @Data
    public static class ClaimItem {
        private Long claimId;
        private Long paperId;
        private String aminerId;
        private String title;
        private String authors;
        private String venue;
        private Integer year;
        private String authorName;
        private String matchMethod;
        private Double confidence;
        private Integer status;
        private String statusLabel;
        private LocalDateTime respondedAt;
        private LocalDateTime createTime;

        public void applyStatus(int statusCode) {
            this.status = statusCode;
            switch (statusCode) {
                case 0: this.statusLabel = "待确认"; break;
                case 1: this.statusLabel = "已确认"; break;
                case 2: this.statusLabel = "已否认"; break;
                case 3: this.statusLabel = "已过期"; break;
                default: this.statusLabel = "未知";
            }
        }
    }

    @Data
    public static class ClaimResponse {
        private String message;
    }
}
