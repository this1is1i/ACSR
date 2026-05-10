package com.example.research.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.example.research.entity.Paper;
import java.util.List;

public interface PaperService {
    IPage<Paper> listPapers(int page, int size, Integer year, String venue);
    Paper getPaperById(Long id);
    Paper getPaperByAminerId(String aminerId);
    List<Paper> searchPapers(String keyword, int limit, Integer yearFrom, String sortBy);
    List<Paper> getByAminers(List<String> aminers);
    List<Paper> getByPaperIds(List<Long> ids);
}
