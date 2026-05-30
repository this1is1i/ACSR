package com.example.research.service;

import java.util.Map;

public interface VisualizationService {
    /**
     * Get aggregated visualization data for a user.
     * @param userId    authenticated user ID
     * @param targetTopic optional target topic override; when blank, auto-derived from user interest
     * @return Map with keys: knowledge
     */
    Map<String, Object> getVisualizationData(Long userId, String targetTopic);
}
