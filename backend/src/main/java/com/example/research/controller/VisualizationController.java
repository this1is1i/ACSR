package com.example.research.controller;

import com.example.research.service.VisualizationService;
import com.example.research.util.Result;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/api/visualization")
@RequiredArgsConstructor
public class VisualizationController {

    private final VisualizationService visualizationService;

    @GetMapping("/data")
    public Result<Map<String, Object>> getVisualizationData(
            Authentication auth,
            @RequestParam(required = false) String targetTopic) {
        Long userId = (Long) auth.getPrincipal();
        return Result.success(visualizationService.getVisualizationData(userId, targetTopic));
    }
}
