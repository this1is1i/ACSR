package com.example.research.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.example.research.graph.GraphPaper;
import com.example.research.graph.GraphPaperService;
import com.example.research.entity.Paper;
import com.example.research.repository.PaperMapper;
import com.example.research.service.PaperService;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class PaperServiceImpl implements PaperService {

    private final PaperMapper paperMapper;
    private final GraphPaperService graphPaperService;
    private final ObjectMapper objectMapper;

    @Override
    public IPage<Paper> listPapers(int page, int size, Integer year, String venue) {
        if (graphPaperService.isEnabled()) {
            long total = graphPaperService.countPapers(year, venue);
            List<Paper> records = graphPaperService.listPopular((Math.max(page, 1) - 1) * size, size, year, venue)
                    .stream()
                    .map(this::upsertShadowPaper)
                    .collect(Collectors.toList());
            Page<Paper> graphPage = new Page<>(page, size, total);
            graphPage.setRecords(records);
            return graphPage;
        }

        LambdaQueryWrapper<Paper> wrapper = new LambdaQueryWrapper<Paper>()
                .eq(year != null, Paper::getYear, year)
                .eq(venue != null && !venue.isBlank(), Paper::getVenue, venue)
                .orderByDesc(Paper::getCitationCount);
        return paperMapper.selectPage(new Page<>(page, size), wrapper);
    }

    @Override
    public Paper getPaperById(Long id) {
        Paper paper = paperMapper.selectById(id);
        if (paper == null) throw new IllegalArgumentException("论文不存在: " + id);
        return paper;
    }

    @Override
    public Paper getPaperByAminerId(String aminerId) {
        Paper localPaper = paperMapper.findByAminer(aminerId);
        if (localPaper != null) {
            return localPaper;
        }
        return graphPaperService.findByAminerId(aminerId)
                .map(this::upsertShadowPaper)
                .orElseThrow(() -> new IllegalArgumentException("论文不存在: " + aminerId));
    }

    @Override
    public List<Paper> searchPapers(String keyword, int limit) {
        if (graphPaperService.isEnabled()) {
            List<GraphPaper> graphResults = graphPaperService.search(keyword, limit);
            if (!graphResults.isEmpty()) {
                return graphResults.stream()
                        .map(this::upsertShadowPaper)
                        .collect(Collectors.toList());
            }
        }
        return paperMapper.searchByKeyword(keyword, limit);
    }

    @Override
    public List<Paper> getByAminers(List<String> aminers) {
        if (aminers == null || aminers.isEmpty()) return List.of();

        Map<String, Paper> resolved = paperMapper.findByAminers(aminers).stream()
                .filter(paper -> paper.getAminerId() != null)
                .collect(Collectors.toMap(Paper::getAminerId, paper -> paper, (left, right) -> left));

        if (graphPaperService.isEnabled()) {
            List<String> missingAminers = aminers.stream()
                    .filter(aminerId -> !resolved.containsKey(aminerId))
                    .distinct()
                    .collect(Collectors.toList());

            if (!missingAminers.isEmpty()) {
                graphPaperService.findByAminerIds(missingAminers).stream()
                        .map(this::upsertShadowPaper)
                        .filter(paper -> paper.getAminerId() != null)
                        .forEach(paper -> resolved.put(paper.getAminerId(), paper));
            }
        }

        return aminers.stream()
                .map(resolved::get)
                .filter(Objects::nonNull)
                .collect(Collectors.toList());
    }

    private Paper upsertShadowPaper(GraphPaper graphPaper) {
        Paper target = paperMapper.findByAminer(graphPaper.getAminerId());
        boolean isNew = target == null;
        if (isNew) {
            target = new Paper();
        }

        target.setAminerId(graphPaper.getAminerId());
        target.setTitle(graphPaper.getTitle() == null || graphPaper.getTitle().isBlank()
                ? graphPaper.getAminerId()
                : graphPaper.getTitle());
        target.setAbstrakt(graphPaper.getAbstractText());
        target.setKeywords(writeJsonArray(graphPaper.getKeywords()));
        target.setAuthors(writeJsonArray(graphPaper.getAuthors()));
        target.setVenue(graphPaper.getVenue());
        target.setYear(graphPaper.getYear());
        target.setCitationCount(graphPaper.getCitationCount() == null ? 0 : graphPaper.getCitationCount());
        target.setEmbedding(graphPaper.getEmbedding());

        if (isNew) {
            paperMapper.insert(target);
            return target;
        }

        paperMapper.updateById(target);
        return target;
    }

    private String writeJsonArray(List<String> values) {
        try {
            return objectMapper.writeValueAsString(values == null ? List.of() : values);
        } catch (JsonProcessingException e) {
            throw new IllegalStateException("论文影子数据序列化失败", e);
        }
    }
}
