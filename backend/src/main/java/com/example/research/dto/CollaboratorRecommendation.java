package com.example.research.dto;

import java.util.List;

public record CollaboratorRecommendation(
    Long userId,
    String username,
    String avatar,
    String bio,
    List<String> commonInterests,
    int matchCount,
    String reason
) {}
