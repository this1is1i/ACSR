package com.example.research.enums;

import java.util.Locale;
import java.util.Set;

public enum UserRole {
    GUEST("游客", 0, false),
    STUDENT("学生用户", 1, false),
    RESEARCHER("研究者用户", 2, true),
    ADMIN("管理员", 3, true);

    private final String label;
    private final int level;
    private final boolean directPublish;

    UserRole(String label, int level, boolean directPublish) {
        this.label = label;
        this.level = level;
        this.directPublish = directPublish;
    }

    public String getLabel() {
        return label;
    }

    public boolean canPublishDirectly() {
        return directPublish;
    }

    public boolean isHigherOrEqual(UserRole other) {
        return this.level >= other.level;
    }

    public static UserRole from(String rawRole) {
        if (rawRole == null || rawRole.isBlank()) {
            return GUEST;
        }
        String normalized = rawRole.trim().toUpperCase(Locale.ROOT);
        if ("USER".equals(normalized)) {
            return STUDENT;
        }
        for (UserRole role : values()) {
            if (role.name().equals(normalized)) {
                return role;
            }
        }
        return GUEST;
    }

    public static UserRole requireAssignable(String rawRole) {
        UserRole role = from(rawRole);
        if (!Set.of(STUDENT, RESEARCHER, ADMIN).contains(role)) {
            throw new IllegalArgumentException("不支持的角色: " + rawRole);
        }
        return role;
    }
}
