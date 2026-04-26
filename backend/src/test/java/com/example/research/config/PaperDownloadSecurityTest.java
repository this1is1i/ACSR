package com.example.research.config;

import com.example.research.controller.PaperController;
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
import org.springframework.context.annotation.Import;
import org.springframework.test.web.servlet.MockMvc;

import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(PaperController.class)
@AutoConfigureMockMvc
@Import({SecurityConfig.class, JwtFilter.class})
class PaperDownloadSecurityTest {

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
    void anonymous_user_can_download_txt() throws Exception {
        Paper paper = new Paper();
        paper.setId(1L);
        paper.setTitle("Public Paper");

        when(paperService.getPaperById(1L)).thenReturn(paper);

        mockMvc.perform(get("/api/paper/1/download/txt"))
                .andExpect(status().isOk());
    }
}
