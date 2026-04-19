package com.example.research.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.example.research.entity.Paper;
import com.example.research.repository.PaperMapper;
import com.example.research.service.PaperService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import java.util.List;

@Service
@RequiredArgsConstructor
public class PaperServiceImpl implements PaperService {

    private final PaperMapper paperMapper;

    @Override
    public IPage<Paper> listPapers(int page, int size, Integer year, String venue) {
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
    public List<Paper> searchPapers(String keyword, int limit) {
        return paperMapper.searchByKeyword(keyword, limit);
    }

    @Override
    public List<Paper> getByAminers(List<String> aminers) {
        if (aminers == null || aminers.isEmpty()) return List.of();
        return paperMapper.findByAminers(aminers);
    }
}
