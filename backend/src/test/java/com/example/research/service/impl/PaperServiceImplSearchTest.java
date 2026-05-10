package com.example.research.service.impl;

import com.example.research.entity.Paper;
import com.example.research.graph.GraphPaperService;
import com.example.research.repository.PaperMapper;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class PaperServiceImplSearchTest {

    @Mock
    private PaperMapper paperMapper;

    @Mock
    private GraphPaperService graphPaperService;

    private PaperServiceImpl service;

    @BeforeEach
    void setUp() {
        service = new PaperServiceImpl(paperMapper, graphPaperService, new ObjectMapper());
    }

    @Test
    void searchPapers_uses_mysql_fallback_when_graph_search_is_empty() {
        Paper fallbackPaper = new Paper();
        fallbackPaper.setTitle("Attention Is All You Need");

        when(graphPaperService.isEnabled()).thenReturn(true);
        when(graphPaperService.search("Transformer", 20)).thenReturn(List.of());
        when(paperMapper.searchByKeywordExpanded("Transformer", 20, null, null)).thenReturn(List.of(fallbackPaper));

        List<Paper> results = service.searchPapers("Transformer", 20, null, null);

        assertThat(results).extracting(Paper::getTitle).containsExactly("Attention Is All You Need");
        verify(paperMapper).searchByKeywordExpanded("Transformer", 20, null, null);
    }
}
