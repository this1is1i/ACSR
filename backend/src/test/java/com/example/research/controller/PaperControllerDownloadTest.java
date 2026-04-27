package com.example.research.controller;

import com.example.research.entity.Paper;
import com.example.research.repository.BehaviorLogMapper;
import com.example.research.repository.CommentMapper;
import com.example.research.repository.PaperMapper;
import com.example.research.repository.PostMapper;
import com.example.research.repository.PrivateMessageMapper;
import com.example.research.repository.UserContactMapper;
import com.example.research.repository.UserMapper;
import com.example.research.service.PaperService;
import com.example.research.util.JwtUtil;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.ContentDisposition;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MvcResult;
import org.springframework.test.web.servlet.MockMvc;

import static org.assertj.core.api.Assertions.assertThat;
import static org.hamcrest.Matchers.containsString;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(PaperController.class)
@AutoConfigureMockMvc(addFilters = false)
class PaperControllerDownloadTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private PaperService paperService;

    @MockBean
    private JwtUtil jwtUtil;

    @MockBean
    private BehaviorLogMapper behaviorLogMapper;

    @MockBean
    private CommentMapper commentMapper;

    @MockBean
    private PaperMapper paperMapper;

    @MockBean
    private PostMapper postMapper;

    @MockBean
    private PrivateMessageMapper privateMessageMapper;

    @MockBean
    private UserContactMapper userContactMapper;

    @MockBean
    private UserMapper userMapper;

    @Test
    void downloadTxt_returns_plain_text_attachment() throws Exception {
        Paper paper = new Paper();
        paper.setId(1L);
        paper.setTitle("Attention Is All You Need");
        paper.setAuthors("Ashish Vaswani, Noam Shazeer");
        paper.setVenue("NeurIPS");
        paper.setYear(2017);
        paper.setAminerId("aminer-1");
        paper.setCitationCount(12345);
        paper.setKeywords("Transformer; Attention");
        paper.setAbstrakt("Transformer models rely entirely on attention mechanisms.");

        when(paperService.getPaperById(1L)).thenReturn(paper);

        mockMvc.perform(get("/api/paper/1/download/txt"))
                .andExpect(status().isOk())
                .andExpect(content().contentTypeCompatibleWith(MediaType.TEXT_PLAIN))
                .andExpect(header().string("Content-Disposition", containsString("attachment;")))
                .andExpect(content().string(containsString("Attention Is All You Need")))
                .andExpect(content().string(containsString("NeurIPS")))
                .andExpect(content().string(containsString("Transformer")));
    }

    @Test
    void downloadTxt_uses_utf8_safe_filename_for_non_ascii_title() throws Exception {
        Paper paper = new Paper();
        paper.setId(2L);
        paper.setTitle("多模态/推荐:系统");
        paper.setAuthors("作者");
        paper.setVenue("会议");
        paper.setYear(2024);
        paper.setAbstrakt("摘要");

        when(paperService.getPaperById(2L)).thenReturn(paper);

        MvcResult result = mockMvc.perform(get("/api/paper/2/download/txt"))
                .andExpect(status().isOk())
                .andReturn();

        String disposition = result.getResponse().getHeader(HttpHeaders.CONTENT_DISPOSITION);
        assertThat(disposition).contains("filename*=");

        ContentDisposition contentDisposition = ContentDisposition.parse(disposition);
        assertThat(contentDisposition.getFilename()).isEqualTo("多模态_推荐_系统.txt");
    }
}
