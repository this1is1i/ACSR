package com.example.research.enums;

import java.util.Locale;

public enum PostStatus {
    PENDING(0, "待审核"),
    APPROVED(1, "已发布"),
    REJECTED(2, "已驳回");

    private final int code;
    private final String label;

    PostStatus(int code, String label) {
        this.code = code;
        this.label = label;
    }

    public int getCode() {
        return code;
    }

    public String getLabel() {
        return label;
    }

    public static PostStatus fromCode(Integer code) {
        if (code == null) {
            return APPROVED;
        }
        for (PostStatus status : values()) {
            if (status.code == code) {
                return status;
            }
        }
        return APPROVED;
    }

    public static PostStatus fromName(String rawStatus) {
        if (rawStatus == null || rawStatus.isBlank()) {
            throw new IllegalArgumentException("帖子状态不能为空");
        }
        String normalized = rawStatus.trim().toUpperCase(Locale.ROOT);
        for (PostStatus status : values()) {
            if (status.name().equals(normalized)) {
                return status;
            }
        }
        throw new IllegalArgumentException("不支持的帖子状态: " + rawStatus);
    }
}
