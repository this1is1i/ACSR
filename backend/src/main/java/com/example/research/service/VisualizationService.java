package com.example.research.service;

import java.util.Map;

public interface VisualizationService {
    /**
     * Get aggregated visualization data for a user.
     * @return Map with keys: stats, interest, field, heatmap, tags, behaviors, knowledge
     */
    Map<String, Object> getVisualizationData(Long userId);
}
