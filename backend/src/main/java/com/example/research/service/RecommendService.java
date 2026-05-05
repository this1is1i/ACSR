package com.example.research.service;

import com.example.research.dto.RecommendDto;

import java.util.List;
import java.util.Map;

public interface RecommendService {
    RecommendDto.RecommendResponse getRecommendations(Long userId, int k);
    void logBehavior(Long userId, Long paperId, String action, Integer duration, String source);
    boolean triggerTraining(Integer episodes);
    Object getModelInfo();
    List<Map<String, Object>> getRecentHistory(Long userId, int limit);
    int clearHistory(Long userId);
}
