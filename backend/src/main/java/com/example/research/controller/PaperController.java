package com.example.research.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.example.research.entity.Paper;
import com.example.research.service.PaperService;
import com.example.research.util.Result;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.nio.charset.StandardCharsets;
import java.util.List;

/**
 * 论文模块控制器
 *
 * 接口列表：
 *   GET /api/paper/list         - 分页获取论文列表
 *   GET /api/paper/{id}         - 获取单篇论文详情
 *   GET /api/paper/search       - 关键词搜索论文
 */
@Slf4j
@RestController
@RequestMapping("/api/paper")
@RequiredArgsConstructor
public class PaperController {

    private final PaperService paperService;

    /**
     * 分页获取论文列表
     *
     * 示例：GET /api/paper/list?page=1&size=10&year=2023
     */
    @GetMapping("/list")
    public Result<IPage<Paper>> listPapers(
            @RequestParam(defaultValue = "1")  int page,
            @RequestParam(defaultValue = "10") int size,
            @RequestParam(required = false)    Integer year,
            @RequestParam(required = false)    String venue) {

        IPage<Paper> result = paperService.listPapers(page, size, year, venue);
        return Result.success(result);
    }

    /**
     * 获取单篇论文详情
     *
     * 示例：GET /api/paper/1
     */
    @GetMapping("/{id:\\d+}")
    public Result<Paper> getPaper(@PathVariable Long id) {
        Paper paper = paperService.getPaperById(id);
        return Result.success(paper);
    }

    @GetMapping("/{id:\\d+}/download/txt")
    public ResponseEntity<String> downloadPaperTxt(@PathVariable Long id) {
        Paper paper = paperService.getPaperById(id);
        String filename = sanitizeFilename(paper.getTitle());
        String content = buildPaperTxtContent(paper);

        return ResponseEntity.ok()
                .contentType(new MediaType("text", "plain", StandardCharsets.UTF_8))
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"" + filename + ".txt\"")
                .body(content);
    }

    @GetMapping("/aminer/{aminerId}")
    public Result<Paper> getPaperByAminer(@PathVariable String aminerId) {
        return Result.success(paperService.getPaperByAminerId(aminerId));
    }

    /**
     * 关键词搜索论文（支持标题和摘要全文检索）
     *
     * 示例：GET /api/paper/search?keyword=reinforcement+learning&limit=20
     */
    @GetMapping("/search")
    public Result<List<Paper>> searchPapers(
            @RequestParam String keyword,
            @RequestParam(defaultValue = "20") int limit) {

        List<Paper> results = paperService.searchPapers(keyword, Math.min(limit, 50));
        return Result.success(results);
    }

    private String buildPaperTxtContent(Paper paper) {
        return String.join("\n",
                "Title: " + valueOrEmpty(paper.getTitle()),
                "Authors: " + valueOrEmpty(paper.getAuthors()),
                "Venue: " + valueOrEmpty(paper.getVenue()),
                "Year: " + valueOrEmpty(paper.getYear()),
                "AMiner ID: " + valueOrEmpty(paper.getAminerId()),
                "Citation Count: " + valueOrEmpty(paper.getCitationCount()),
                "Keywords: " + valueOrEmpty(paper.getKeywords()),
                "Abstract: " + valueOrEmpty(paper.getAbstrakt()));
    }

    private String sanitizeFilename(String title) {
        String baseName = valueOrEmpty(title).trim();
        if (baseName.isEmpty()) {
            baseName = "paper";
        }
        return baseName.replaceAll("[\\\\/:*?\"<>|]", "_");
    }

    private String valueOrEmpty(Object value) {
        return value == null ? "" : value.toString();
    }
}
