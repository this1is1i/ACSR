package com.example.research.controller;

import com.example.research.dto.RecommendDto;
import com.example.research.service.RecommendService;
import com.example.research.util.Result;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

/**
 * 推荐模块控制器（核心）
 *
 * 接口列表：
 *   GET  /api/recommend            - 获取 Top-K 个性化推荐
 *   POST /api/recommend/train      - 触发 Python 侧模型训练
 *   GET  /api/recommend/model/info - 查询 Python 推荐模型状态
 *
 * 完整推荐调用链路：
 *   Vue 前端 → GET /api/recommend
 *       → RecommendController
 *       → RecommendServiceImpl
 *       → PythonRecClient → POST http://localhost:8000/recommend
 *       → 组装论文详情
 *       → 返回前端
 */
@Slf4j
@RestController
@RequestMapping("/api/recommend")
@RequiredArgsConstructor
public class RecommendController {

    private final RecommendService recommendService;

    /**
     * 获取个性化 Top-K 推荐（核心接口）
     *
     * 示例：GET /api/recommend?k=10
     *
     * 响应格式：
     * {
     *   "code": 0,
     *   "data": {
     *     "userId": "1",
     *     "k": 10,
     *     "modelVersion": "v1.0.0-actor-critic",
     *     "latencyMs": 45.2,
     *     "pythonServiceAvailable": true,
     *     "recommendations": [
     *       {
     *         "paperId": 1,
     *         "title": "Actor-Critic RL",
     *         "score": 0.91,
     *         "rank": 1,
     *         "reason": "与您阅读的强化学习论文高度相关",
     *         "reasonDetails": [...],
     *         "similarityScore": 0.83,
     *         "confidence": 0.78
     *       }
     *     ]
     *   }
     * }
     */
    @GetMapping
    public Result<RecommendDto.RecommendResponse> getRecommendations(
            @RequestParam(defaultValue = "10") int k,
            Authentication auth) {

        Long userId = (Long) auth.getPrincipal();
        k = Math.min(Math.max(k, 1), 50);  // 限制范围 [1, 50]

        RecommendDto.RecommendResponse response =
                recommendService.getRecommendations(userId, k);
        return Result.success(response);
    }

    /**
     * 触发 Python 侧 Actor-Critic 模型训练
     * （异步执行，不阻塞请求；需要 ADMIN 角色）
     *
     * Request:  POST /api/recommend/train?episodes=200
     * Response: { "code": 0, "message": "训练已在后台启动" }
     */
    @PostMapping("/train")
    public Result<String> triggerTraining(
            @RequestParam(required = false) Integer episodes) {

        boolean triggered = recommendService.triggerTraining(episodes);
        if (triggered) {
            return Result.success("Python 模型训练已在后台启动");
        } else {
            return Result.fail("触发训练失败，请检查 Python 推荐服务是否运行");
        }
    }

    /**
     * 查询 Python 推荐模型当前状态
     *
     * 返回：训练轮次、最优 reward、模型版本、设备信息等
     */
    @GetMapping("/model/info")
    public Result<Object> getModelInfo() {
        Object info = recommendService.getModelInfo();
        return Result.success(info);
    }
}
