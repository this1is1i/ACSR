package com.example.research.service.impl;

import com.example.research.client.PythonRecClient;
import com.example.research.dto.RecommendDto;
import com.example.research.entity.BehaviorLog;
import com.example.research.entity.Paper;
import com.example.research.repository.BehaviorLogMapper;
import com.example.research.service.PaperService;
import com.example.research.service.RecommendService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.*;
import java.util.stream.Collectors;

/**
 * 推荐服务实现
 *
 * 核心流程：
 *   1. 从 behavior_log 表获取用户历史行为
 *   2. 调用 Python FastAPI 推荐服务（PythonRecClient）
 *   3. 将 Python 返回的 paper_id 映射为数据库中的 Paper 对象
 *   4. 组装最终推荐结果并返回给前端
 *   5. Python 服务不可用时，降级为热门论文推荐
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class RecommendServiceImpl implements RecommendService {

    private final PythonRecClient    pythonRecClient;
    private final BehaviorLogMapper  behaviorLogMapper;
    private final PaperService       paperService;

    @Override
    public RecommendDto.RecommendResponse getRecommendations(Long userId, int k) {
        long startTime = System.currentTimeMillis();

        // ── Step 1: 获取用户历史行为（构建推荐上下文）─────────────
        List<Long> historyPaperIds = behaviorLogMapper.findInteractedPaperIds(userId, 20);
        List<String> historyAminers = resolveAminers(historyPaperIds);
        log.debug("用户 [{}] 历史行为论文数: {}", userId, historyAminers.size());

        // ── Step 2: 调用 Python 推荐服务 ─────────────────────────
        PythonRecClient.RecResponse pyResp = pythonRecClient.getRecommendations(
            String.valueOf(userId), k, historyAminers
        );

        boolean pythonAvailable = (pyResp != null);
        List<RecommendDto.RecommendItem> items;

        if (pythonAvailable && pyResp.getRecommendations() != null) {
            // ── Step 3: 组装推荐结果（Python 正常响应）────────────
            items = assembleFromPython(pyResp.getRecommendations());
            if (!items.isEmpty()) {
                log.debug("Python 推荐首条: reason={}", items.get(0).getReason());
            }
        } else {
            // ── Step 4: 降级：返回热门论文 ─────────────────────────
            log.warn("Python 推荐服务不可用(pyResp={}, recs={})，降级为热门论文推荐，userId={}",
                     pyResp != null ? "parsed" : "null",
                     pyResp != null ? pyResp.getRecommendations() : "n/a",
                     userId);
            items = fallbackPopularRecommendations(k);
        }

        // ── Step 5: 组装响应 ──────────────────────────────────────
        double latencyMs = System.currentTimeMillis() - startTime;

        RecommendDto.RecommendResponse response = new RecommendDto.RecommendResponse();
        response.setUserId(String.valueOf(userId));
        response.setK(k);
        response.setModelVersion(pythonAvailable && pyResp.getModelVersion() != null
            ? pyResp.getModelVersion() : "fallback-v1.0");
        response.setLatencyMs(latencyMs);
        response.setRecommendations(items);
        response.setPythonServiceAvailable(pythonAvailable);

        log.info("推荐完成: userId={}, {}条推荐, {}ms, python={}",
                 userId, items.size(), (long) latencyMs, pythonAvailable ? "可用" : "降级");
        return response;
    }

    @Override
    @Transactional
    public void logBehavior(Long userId, Long paperId, String action,
                            Integer duration, String source) {
        // 校验 action 类型
        if (!Set.of("click", "favorite", "read").contains(action)) {
            throw new IllegalArgumentException("无效的行为类型: " + action);
        }
        // 校验论文存在
        paperService.getPaperById(paperId);

        BehaviorLog behaviorLog = new BehaviorLog();
        behaviorLog.setUserId(userId);
        behaviorLog.setPaperId(paperId);
        behaviorLog.setAction(action);
        behaviorLog.setDuration(duration);
        behaviorLog.setSource(source);
        behaviorLogMapper.insert(behaviorLog);

        log.debug("行为记录: userId={}, paperId={}, action={}", userId, paperId, action);
    }

    @Override
    public boolean triggerTraining(Integer episodes) {
        return pythonRecClient.triggerTraining(episodes);
    }

    @Override
    public Object getModelInfo() {
        PythonRecClient.ModelInfo info = pythonRecClient.getModelInfo();
        if (info == null) {
            return Map.of("available", false, "message", "Python 推荐服务不可达");
        }
        return info;
    }

    @Override
    public List<Map<String, Object>> getRecentHistory(Long userId, int limit) {
        return behaviorLogMapper.findRecentByUserId(userId, limit);
    }

    @Override
    public int clearHistory(Long userId) {
        return behaviorLogMapper.deleteByUserId(userId);
    }

    // ── 内部辅助方法 ──────────────────────────────────────────────

    /**
     * 将数据库 paper_id (Long) 转换为 AMiner ID 列表（批量查询，避免 N+1）
     */
    private List<String> resolveAminers(List<Long> paperIds) {
        if (paperIds.isEmpty()) {return Collections.emptyList();}
        return paperService.getByPaperIds(paperIds).stream()
            .map(Paper::getAminerId)
            .filter(Objects::nonNull)
            .collect(Collectors.toList());
    }

    /**
     * 将 Python 推荐结果组装为前端 DTO，
     * 并从数据库补全论文详情（标题/年份/引用数等）
     */
    private List<RecommendDto.RecommendItem> assembleFromPython(
            List<PythonRecClient.RecItem> pyItems) {

        // 提取所有 paper_id（AMiner ID）
        List<String> aminers = pyItems.stream()
            .map(PythonRecClient.RecItem::getPaperId)
            .filter(Objects::nonNull)
            .collect(Collectors.toList());

        // 批量查询数据库，建立 aminerId → Paper 的映射
        Map<String, Paper> paperMap = new HashMap<>();
        if (!aminers.isEmpty()) {
            paperService.getByAminers(aminers)
                .forEach(p -> paperMap.put(p.getAminerId(), p));
        }

        List<RecommendDto.RecommendItem> result = new ArrayList<>();
        for (PythonRecClient.RecItem pyItem : pyItems) {
            RecommendDto.RecommendItem item = new RecommendDto.RecommendItem();

            // 从数据库补全论文信息
            Paper dbPaper = paperMap.get(pyItem.getPaperId());
            if (dbPaper != null) {
                item.setPaperId(dbPaper.getId());
                item.setAminerId(dbPaper.getAminerId());
                item.setTitle(dbPaper.getTitle());
                item.setVenue(dbPaper.getVenue());
                item.setYear(dbPaper.getYear());
                item.setCitationCount(dbPaper.getCitationCount());
            } else {
                // Python 返回的论文不在数据库中（直接使用 Python 侧数据）
                item.setPaperId(null);  // 本地无此论文
                item.setAminerId(pyItem.getPaperId());
                item.setTitle(pyItem.getTitle() != null ? pyItem.getTitle() : "未知论文");
                item.setAuthors(pyItem.getAuthors());
                item.setYear(pyItem.getYear());
                item.setCitationCount(pyItem.getCitationCount());
            }

            // 推荐分数和解释
            item.setScore(pyItem.getScore());
            item.setRank(pyItem.getRank());
            item.setReason(pyItem.getReason());
            item.setReasonDetails(pyItem.getReasonDetails());
            item.setSimilarityScore(pyItem.getSimilarityScore());
            item.setTopics(pyItem.getTopics());
            item.setConfidence(pyItem.getConfidence());

            result.add(item);
        }
        return result;
    }

    /**
     * 降级方案：返回热门（高被引）论文推荐
     * 当 Python 推荐服务不可用时使用
     */
    private List<RecommendDto.RecommendItem> fallbackPopularRecommendations(int k) {
        var pageResult = paperService.listPapers(1, k, null, null);
        List<RecommendDto.RecommendItem> items = new ArrayList<>();
        int rank = 1;
        for (Paper paper : pageResult.getRecords()) {
            RecommendDto.RecommendItem item = new RecommendDto.RecommendItem();
            item.setPaperId(paper.getId());
            item.setAminerId(paper.getAminerId());
            item.setTitle(paper.getTitle());
            item.setVenue(paper.getVenue());
            item.setYear(paper.getYear());
            item.setCitationCount(paper.getCitationCount());
            item.setScore(0.5);
            item.setRank(rank++);
            item.setReason("热门推荐（推荐服务暂时不可用，展示高被引论文）");
            item.setReasonDetails(List.of("基于被引次数排序", "推荐算法服务维护中"));
            item.setConfidence(0.3);
            items.add(item);
        }
        return items;
    }
}
