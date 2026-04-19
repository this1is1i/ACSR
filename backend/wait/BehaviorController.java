package com.example.research.controller;

import com.example.research.dto.RecommendDto;
import com.example.research.service.RecommendService;
import com.example.research.util.Result;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

/**
 * 用户行为日志控制器
 * 收集用户与论文的交互行为，作为强化学习训练数据
 *
 * 接口列表：
 *   POST /api/behavior/click     - 记录点击行为
 *   POST /api/behavior/favorite  - 记录收藏行为
 *   POST /api/behavior/read      - 记录阅读行为（含时长）
 */
@Slf4j
@RestController
@RequestMapping("/api/behavior")
@RequiredArgsConstructor
public class BehaviorController {

    private final RecommendService recommendService;

    /**
     * 记录点击行为
     *
     * Request:  { "paperId": 123, "source": "recommend" }
     * Response: { "code": 0, "message": "success" }
     */
    @PostMapping("/click")
    public Result<Void> click(
            @RequestBody RecommendDto.BehaviorRequest request,
            Authentication auth) {

        Long userId = (Long) auth.getPrincipal();
        recommendService.logBehavior(userId, request.getPaperId(),
                "click", null, request.getSource());
        return Result.success();
    }

    /**
     * 记录收藏行为
     */
    @PostMapping("/favorite")
    public Result<Void> favorite(
            @RequestBody RecommendDto.BehaviorRequest request,
            Authentication auth) {

        Long userId = (Long) auth.getPrincipal();
        recommendService.logBehavior(userId, request.getPaperId(),
                "favorite", null, request.getSource());
        return Result.success();
    }

    /**
     * 记录阅读行为（包含阅读时长）
     *
     * Request:  { "paperId": 123, "duration": 180, "source": "detail" }
     */
    @PostMapping("/read")
    public Result<Void> read(
            @RequestBody RecommendDto.BehaviorRequest request,
            Authentication auth) {

        Long userId = (Long) auth.getPrincipal();
        recommendService.logBehavior(userId, request.getPaperId(),
                "read", request.getDuration(), request.getSource());
        return Result.success();
    }
}
