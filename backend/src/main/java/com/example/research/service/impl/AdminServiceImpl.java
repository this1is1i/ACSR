package com.example.research.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.example.research.dto.CommunityDto;
import com.example.research.dto.UserDto;
import com.example.research.entity.Paper;
import com.example.research.entity.PaperAuthorClaim;
import com.example.research.entity.Post;
import com.example.research.entity.User;
import com.example.research.enums.PostStatus;
import com.example.research.enums.UserRole;
import com.example.research.graph.GraphPaper;
import com.example.research.graph.GraphPaperService;
import com.example.research.repository.PaperAuthorClaimMapper;
import com.example.research.repository.PaperMapper;
import com.example.research.repository.PostMapper;
import com.example.research.repository.UserMapper;
import com.example.research.service.AdminService;
import com.example.research.service.PrivateMessageService;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class AdminServiceImpl implements AdminService {

    private final UserMapper userMapper;
    private final PostMapper postMapper;
    private final PaperMapper paperMapper;
    private final GraphPaperService graphPaperService;
    private final ObjectMapper objectMapper;
    private final PrivateMessageService privateMessageService;
    private final PaperAuthorClaimMapper paperAuthorClaimMapper;

    @Override
    public List<CommunityDto.PostItem> listPosts(String status) {
        LambdaQueryWrapper<Post> wrapper = new LambdaQueryWrapper<>();
        if (status != null && !status.isBlank()) {
            wrapper.eq(Post::getStatus, PostStatus.fromName(status).getCode());
        }
        wrapper.orderByAsc(Post::getStatus).orderByDesc(Post::getCreateTime);

        Map<Long, User> userCache = new LinkedHashMap<>();
        Map<Long, Paper> paperCache = new LinkedHashMap<>();
        return postMapper.selectList(wrapper).stream()
                .map(post -> toPostItem(post, userCache, paperCache))
                .collect(Collectors.toList());
    }

    @Override
    @Transactional
    public CommunityDto.PostItem updatePostStatus(Long adminId, Long postId, CommunityDto.PostStatusUpdateRequest request) {
        Post post = postMapper.selectById(postId);
        if (post == null) {
            throw new IllegalArgumentException("帖子不存在");
        }

        PostStatus targetStatus = PostStatus.fromName(request.getStatus());
        post.setStatus(targetStatus.getCode());
        post.setReviewComment(request.getReviewComment());
        post.setReviewedBy(adminId);
        post.setReviewedTime(LocalDateTime.now());
        postMapper.updateById(post);

        return toPostItem(postMapper.selectById(postId), new LinkedHashMap<>(), new LinkedHashMap<>());
    }

    @Override
    public List<UserDto.AdminUserItem> listUsers() {
        return userMapper.selectList(new LambdaQueryWrapper<User>().orderByDesc(User::getCreateTime)).stream()
                .map(this::toAdminUser)
                .collect(Collectors.toList());
    }

    @Override
    @Transactional
    public UserDto.AdminUserItem updateUserRole(Long adminId, Long userId, UserDto.UserRoleUpdateRequest request) {
        User user = userMapper.selectById(userId);
        if (user == null) {
            throw new IllegalArgumentException("用户不存在");
        }

        UserRole targetRole = UserRole.requireAssignable(request.getRole());
        if (Objects.equals(adminId, userId) && targetRole != UserRole.ADMIN) {
            throw new IllegalArgumentException("不能将当前管理员自身降级");
        }

        user.setRole(targetRole.name());
        userMapper.updateById(user);
        return toAdminUser(userMapper.selectById(userId));
    }

    @Override
    @Transactional
    public CommunityDto.PaperImportResult importPapers(Long adminId, CommunityDto.PaperImportRequest request) {
        List<String> importedIds = new ArrayList<>();
        List<GraphPaper> graphPapers = new ArrayList<>();
        long base = System.currentTimeMillis();

        int index = 0;
        for (CommunityDto.PaperImportItem item : request.getPapers()) {
            String aminerId = item.getAminerId();
            if (aminerId == null || aminerId.isBlank()) {
                aminerId = "manual_" + base + "_" + index;
            }

            upsertShadowPaper(aminerId, item);
            importedIds.add(aminerId);

            Paper savedPaper = paperMapper.findByAminer(aminerId);
            matchAuthorsForClaim(savedPaper, item.getAuthors(), adminId);

            GraphPaper graphPaper = new GraphPaper();
            graphPaper.setGraphNodeId(aminerId);
            graphPaper.setAminerId(aminerId);
            graphPaper.setTitle(item.getTitle());
            graphPaper.setAbstractText(item.getAbstractText());
            graphPaper.setAuthors(item.getAuthors());
            graphPaper.setKeywords(item.getKeywords());
            graphPaper.setVenue(item.getVenue());
            graphPaper.setYear(item.getYear());
            graphPaper.setCitationCount(item.getCitationCount());
            graphPapers.add(graphPaper);
            index++;
        }

        if (graphPaperService.isEnabled()) {
            graphPaperService.upsertPapers(graphPapers);
        }

        CommunityDto.PaperImportResult result = new CommunityDto.PaperImportResult();
        result.setImportedCount(importedIds.size());
        result.setAminerIds(importedIds);
        return result;
    }

    private void upsertShadowPaper(String aminerId, CommunityDto.PaperImportItem item) {
        Paper paper = paperMapper.findByAminer(aminerId);
        boolean isNew = paper == null;
        if (isNew) {
            paper = new Paper();
        }

        paper.setAminerId(aminerId);
        paper.setTitle(item.getTitle());
        paper.setAbstrakt(item.getAbstractText());
        paper.setAuthors(writeJsonArray(item.getAuthors()));
        paper.setKeywords(writeJsonArray(item.getKeywords()));
        paper.setVenue(item.getVenue());
        paper.setYear(item.getYear());
        paper.setCitationCount(item.getCitationCount() == null ? 0 : item.getCitationCount());

        if (isNew) {
            paperMapper.insert(paper);
        } else {
            paperMapper.updateById(paper);
        }
    }

    private String writeJsonArray(List<String> values) {
        try {
            return objectMapper.writeValueAsString(values == null ? List.of() : values);
        } catch (JsonProcessingException e) {
            throw new IllegalStateException("论文导入序列化失败", e);
        }
    }

    private void matchAuthorsForClaim(Paper paper, List<String> authorNames, Long adminId) {
        if (authorNames == null || authorNames.isEmpty() || paper == null || paper.getId() == null) {
            return;
        }
        for (String authorName : authorNames) {
            if (authorName == null || authorName.isBlank()) {
                continue;
            }
            String trimmed = authorName.trim();
            User exactMatch = userMapper.findByUsername(trimmed);
            if (exactMatch != null) {
                createClaimIfNew(paper.getId(), exactMatch.getId(), trimmed, "exact", 1.0, adminId, paper);
                continue;
            }
            List<User> fuzzyMatches = userMapper.selectList(
                    new LambdaQueryWrapper<User>().like(User::getUsername, trimmed));
            for (User fuzzyUser : fuzzyMatches) {
                double confidence = computeFuzzyConfidence(trimmed, fuzzyUser.getUsername());
                createClaimIfNew(paper.getId(), fuzzyUser.getId(), trimmed, "fuzzy", confidence, adminId, paper);
            }
        }
    }

    private void createClaimIfNew(Long paperId, Long userId, String authorName,
                                   String matchMethod, double confidence, Long adminId, Paper paper) {
        PaperAuthorClaim claim = new PaperAuthorClaim();
        claim.setPaperId(paperId);
        claim.setUserId(userId);
        claim.setAuthorName(authorName);
        claim.setMatchMethod(matchMethod);
        claim.setConfidence(confidence);
        claim.setStatus(0);
        claim.setCreateTime(LocalDateTime.now());
        claim.setUpdateTime(LocalDateTime.now());
        int inserted = paperAuthorClaimMapper.insertIgnore(claim);
        if (inserted > 0) {
            String content = buildClaimNotificationMessage(paper);
            privateMessageService.sendMessage(adminId, userId, content, 4);
        }
    }

    private String buildClaimNotificationMessage(Paper paper) {
        return "系统检测到一篇新导入的论文可能与您有关：\n\n" +
               "标题：《" + (paper.getTitle() != null ? paper.getTitle() : "未知") + "》\n" +
               "作者列表：" + (paper.getAuthors() != null ? paper.getAuthors() : "未知") + "\n" +
               "发表年份：" + (paper.getYear() != null ? paper.getYear().toString() : "未知") + "\n" +
               "发表期刊：" + (paper.getVenue() != null ? paper.getVenue() : "未知") + "\n\n" +
               "如果这是您的论文，请在\"我的论文\"页面确认；如果不是，请忽略此消息。";
    }

    private double computeFuzzyConfidence(String authorName, String username) {
        double ratio = (double) Math.min(authorName.length(), username.length())
                     / Math.max(authorName.length(), username.length());
        return Math.max(0.5, Math.min(0.9, ratio));
    }

    private CommunityDto.PostItem toPostItem(Post post, Map<Long, User> userCache, Map<Long, Paper> paperCache) {
        CommunityDto.PostItem item = new CommunityDto.PostItem();
        item.setId(post.getId());
        item.setPaperId(post.getPaperId());
        item.setTitle(post.getTitle());
        item.setContent(post.getContent());
        item.setLikeCount(post.getLikeCount() == null ? 0 : post.getLikeCount());
        item.setReplyCount(post.getReplyCount() == null ? 0 : post.getReplyCount());
        item.setReviewComment(post.getReviewComment());
        item.setCreateTime(post.getCreateTime());
        item.applyStatus(PostStatus.fromCode(post.getStatus()));

        User author = userCache.computeIfAbsent(post.getUserId(), userMapper::selectById);
        if (author != null) {
            CommunityDto.AuthorInfo authorInfo = new CommunityDto.AuthorInfo();
            UserRole role = UserRole.from(author.getRole());
            authorInfo.setId(author.getId());
            authorInfo.setUsername(author.getUsername());
            authorInfo.setRole(role.name());
            authorInfo.setRoleLabel(role.getLabel());
            authorInfo.setAvatar(author.getAvatar());
            authorInfo.setBio(author.getBio());
            item.setAuthor(authorInfo);
        }

        if (post.getPaperId() != null) {
            Paper paper = paperCache.computeIfAbsent(post.getPaperId(), paperMapper::selectById);
            if (paper != null) {
                CommunityDto.PaperInfo paperInfo = new CommunityDto.PaperInfo();
                paperInfo.setId(paper.getId());
                paperInfo.setAminerId(paper.getAminerId());
                paperInfo.setTitle(paper.getTitle());
                paperInfo.setVenue(paper.getVenue());
                paperInfo.setYear(paper.getYear());
                paperInfo.setCitationCount(paper.getCitationCount());
                item.setPaper(paperInfo);
            }
        }

        return item;
    }

    private UserDto.AdminUserItem toAdminUser(User user) {
        UserRole role = UserRole.from(user.getRole());
        UserDto.AdminUserItem item = new UserDto.AdminUserItem();
        item.setId(user.getId());
        item.setUsername(user.getUsername());
        item.setEmail(user.getEmail());
        item.setRole(role.name());
        item.setRoleLabel(role.getLabel());
        item.setAvatar(user.getAvatar());
        item.setBio(user.getBio());
        item.setResearchInterests(user.getResearchInterests());
        item.setCreateTime(user.getCreateTime());
        return item;
    }
}
