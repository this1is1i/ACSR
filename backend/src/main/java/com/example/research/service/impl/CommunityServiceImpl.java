package com.example.research.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.example.research.dto.CommunityDto;
import com.example.research.entity.Comment;
import com.example.research.entity.Paper;
import com.example.research.entity.Post;
import com.example.research.entity.User;
import com.example.research.enums.PostStatus;
import com.example.research.enums.UserRole;
import com.example.research.repository.CommentMapper;
import com.example.research.repository.PostLikeMapper;
import com.example.research.repository.PostMapper;
import com.example.research.repository.UserMapper;
import com.example.research.service.CommunityService;
import com.example.research.service.PaperService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class CommunityServiceImpl implements CommunityService {

    private static final int COMMENT_STATUS_NORMAL = 1;

    private final PostMapper postMapper;
    private final CommentMapper commentMapper;
    private final UserMapper userMapper;
    private final PaperService paperService;
    private final PostLikeMapper postLikeMapper;

    @Override
    public List<CommunityDto.PostItem> listPosts(Long currentUserId, String filter) {
        List<Post> approvedPosts = postMapper.selectList(Wrappers.<Post>lambdaQuery()
                .eq(Post::getStatus, PostStatus.APPROVED.getCode()));

        Map<Long, Post> mergedPosts = approvedPosts.stream()
                .collect(Collectors.toMap(Post::getId, post -> post, (left, right) -> left, LinkedHashMap::new));

        if (currentUserId != null) {
            postMapper.selectList(Wrappers.<Post>lambdaQuery()
                            .eq(Post::getUserId, currentUserId)
                            .ne(Post::getStatus, PostStatus.APPROVED.getCode()))
                    .forEach(post -> mergedPosts.put(post.getId(), post));
        }

        List<Post> posts = new ArrayList<>(mergedPosts.values());

        // 批量计数 like / reply
        List<Long> postIds = posts.stream().map(Post::getId).collect(Collectors.toList());
        Map<Long, Integer> likeCounts = toCountMap(postLikeMapper.batchCountLikes(postIds));
        Map<Long, Integer> replyCounts = toCountMap(commentMapper.batchCountReplies(postIds));
        posts.sort(resolveComparator(filter, likeCounts, replyCounts));

        Set<Long> likedPostIds = currentUserId != null
                ? new HashSet<>(postLikeMapper.findLikedPostIds(currentUserId))
                : Set.of();

        Map<Long, User> userCache = new LinkedHashMap<>();
        Map<Long, Paper> paperCache = new LinkedHashMap<>();
        return posts.stream()
                .map(post -> toPostItem(post, currentUserId, userCache, paperCache, likedPostIds, likeCounts, replyCounts))
                .collect(Collectors.toList());
    }

    @Override
    @Transactional
    public CommunityDto.PostItem createPost(Long userId, CommunityDto.PostCreateRequest request) {
        User user = requireUser(userId);
        UserRole role = UserRole.from(user.getRole());

        Post post = new Post();
        post.setUserId(userId);
        post.setPaperId(request.getPaperId());
        post.setTitle(request.getTitle());
        post.setContent(request.getContent().trim());
        post.setStatus(role.canPublishDirectly() ? PostStatus.APPROVED.getCode() : PostStatus.PENDING.getCode());

        if (request.getPaperId() != null) {
            paperService.getPaperById(request.getPaperId());
        }

        postMapper.insert(post);
        return toPostItem(postMapper.selectById(post.getId()), userId, new LinkedHashMap<>(), new LinkedHashMap<>(), Set.of(), Map.of(), Map.of());
    }

    @Override
    public List<CommunityDto.CommentItem> listComments(Long postId, Long currentUserId) {
        Post post = requirePost(postId);
        assertPostVisible(post, currentUserId);

        List<Comment> comments = commentMapper.selectList(Wrappers.<Comment>lambdaQuery()
                .eq(Comment::getPostId, postId)
                .eq(Comment::getStatus, COMMENT_STATUS_NORMAL)
                .orderByAsc(Comment::getCreateTime));

        Map<Long, User> userCache = new LinkedHashMap<>();
        Map<Long, CommunityDto.CommentItem> byId = new LinkedHashMap<>();
        List<CommunityDto.CommentItem> roots = new ArrayList<>();

        for (Comment comment : comments) {
            CommunityDto.CommentItem item = toCommentItem(comment, userCache);
            byId.put(comment.getId(), item);

            if (comment.getParentId() == null) {
                roots.add(item);
                continue;
            }

            CommunityDto.CommentItem parent = byId.get(comment.getParentId());
            if (parent != null) {
                parent.getReplies().add(item);
            } else {
                roots.add(item);
            }
        }

        return roots;
    }

    @Override
    @Transactional
    public CommunityDto.CommentItem createComment(Long userId, Long postId, CommunityDto.CommentCreateRequest request) {
        requireUser(userId);
        Post post = requirePost(postId);
        assertPostVisible(post, userId);

        Comment comment = new Comment();
        comment.setPostId(postId);
        comment.setUserId(userId);
        comment.setContent(request.getContent().trim());
        comment.setLikeCount(0);
        comment.setIsBest(0);
        comment.setStatus(COMMENT_STATUS_NORMAL);

        if (request.getParentId() != null) {
            Comment parent = commentMapper.selectById(request.getParentId());
            if (parent == null || !Objects.equals(parent.getPostId(), postId) || !Objects.equals(parent.getStatus(), COMMENT_STATUS_NORMAL)) {
                throw new IllegalArgumentException("父评论不存在或不可回复");
            }
            comment.setParentId(parent.getId());
            comment.setRootId(parent.getRootId() != null ? parent.getRootId() : parent.getId());
        }

        commentMapper.insert(comment);
        return toCommentItem(commentMapper.selectById(comment.getId()), new LinkedHashMap<>());
    }

    private Comparator<Post> resolveComparator(String filter, Map<Long, Integer> likeCounts, Map<Long, Integer> replyCounts) {
        if ("hot".equalsIgnoreCase(filter)) {
            return Comparator.comparing((Post post) -> likeCounts.getOrDefault(post.getId(), 0))
                    .thenComparing(post -> replyCounts.getOrDefault(post.getId(), 0))
                    .thenComparing(Post::getCreateTime, Comparator.nullsLast(Comparator.naturalOrder()))
                    .reversed();
        }

        return Comparator.comparing(Post::getCreateTime, Comparator.nullsLast(Comparator.naturalOrder())).reversed();
    }

    private void assertPostVisible(Post post, Long currentUserId) {
        if (PostStatus.fromCode(post.getStatus()) == PostStatus.APPROVED) {
            return;
        }
        if (currentUserId == null) {
            throw new IllegalArgumentException("帖子尚未公开");
        }
        if (Objects.equals(post.getUserId(), currentUserId) || UserRole.from(requireUser(currentUserId).getRole()) == UserRole.ADMIN) {
            return;
        }
        throw new IllegalArgumentException("帖子尚未公开");
    }

    private Post requirePost(Long postId) {
        Post post = postMapper.selectById(postId);
        if (post == null) {
            throw new IllegalArgumentException("帖子不存在");
        }
        return post;
    }

    private User requireUser(Long userId) {
        User user = userMapper.selectById(userId);
        if (user == null) {
            throw new IllegalArgumentException("用户不存在");
        }
        return user;
    }

    private CommunityDto.PostItem toPostItem(
            Post post,
            Long currentUserId,
            Map<Long, User> userCache,
            Map<Long, Paper> paperCache,
            Set<Long> likedPostIds,
            Map<Long, Integer> likeCounts,
            Map<Long, Integer> replyCounts) {

        CommunityDto.PostItem item = new CommunityDto.PostItem();
        item.setId(post.getId());
        item.setPaperId(post.getPaperId());
        item.setTitle(post.getTitle());
        item.setContent(post.getContent());
        item.setLikeCount(likeCounts.getOrDefault(post.getId(), 0));
        item.setReplyCount(replyCounts.getOrDefault(post.getId(), 0));
        item.setReviewComment(post.getReviewComment());
        item.setCreateTime(post.getCreateTime());
        item.setOwn(Objects.equals(post.getUserId(), currentUserId));
        item.setLiked(likedPostIds.contains(post.getId()));
        item.applyStatus(PostStatus.fromCode(post.getStatus()));

        User author = userCache.computeIfAbsent(post.getUserId(), userMapper::selectById);
        item.setAuthor(toAuthor(author));

        if (post.getPaperId() != null) {
            Paper paper = paperCache.computeIfAbsent(post.getPaperId(), id -> {
                try {
                    return paperService.getPaperById(id);
                } catch (Exception ignored) {
                    return null;
                }
            });
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

    private CommunityDto.CommentItem toCommentItem(Comment comment, Map<Long, User> userCache) {
        CommunityDto.CommentItem item = new CommunityDto.CommentItem();
        item.setId(comment.getId());
        item.setPostId(comment.getPostId());
        item.setParentId(comment.getParentId());
        item.setRootId(comment.getRootId());
        item.setContent(comment.getContent());
        item.setLikeCount(comment.getLikeCount() == null ? 0 : comment.getLikeCount());
        item.setCreateTime(comment.getCreateTime());
        User author = userCache.computeIfAbsent(comment.getUserId(), userMapper::selectById);
        item.setAuthor(toAuthor(author));
        return item;
    }

    @Override
    public List<CommunityDto.PostItem> searchPosts(String keyword, Long currentUserId) {
        if (keyword == null || keyword.isBlank()) {
            return List.of();
        }
        String pattern = "%" + keyword.trim() + "%";
        List<Post> posts = postMapper.selectList(Wrappers.<Post>lambdaQuery()
                .eq(Post::getStatus, PostStatus.APPROVED.getCode())
                .and(w -> w.like(Post::getTitle, pattern).or().like(Post::getContent, pattern))
                .orderByDesc(Post::getCreateTime));

        List<Long> postIds = posts.stream().map(Post::getId).collect(Collectors.toList());
        Map<Long, Integer> likeCounts = toCountMap(postLikeMapper.batchCountLikes(postIds));
        Map<Long, Integer> replyCounts = toCountMap(commentMapper.batchCountReplies(postIds));
        Set<Long> likedPostIds = currentUserId != null
                ? new HashSet<>(postLikeMapper.findLikedPostIds(currentUserId))
                : Set.of();
        Map<Long, User> userCache = new LinkedHashMap<>();
        Map<Long, Paper> paperCache = new LinkedHashMap<>();
        return posts.stream()
                .map(post -> toPostItem(post, currentUserId, userCache, paperCache, likedPostIds, likeCounts, replyCounts))
                .collect(Collectors.toList());
    }

    @Override
    public List<CommunityDto.PostItem> listMyPosts(Long userId) {
        List<Post> posts = postMapper.selectList(Wrappers.<Post>lambdaQuery()
                .eq(Post::getUserId, userId)
                .orderByDesc(Post::getCreateTime));

        List<Long> postIds = posts.stream().map(Post::getId).collect(Collectors.toList());
        Map<Long, Integer> likeCounts = toCountMap(postLikeMapper.batchCountLikes(postIds));
        Map<Long, Integer> replyCounts = toCountMap(commentMapper.batchCountReplies(postIds));
        Set<Long> likedPostIds = new HashSet<>(postLikeMapper.findLikedPostIds(userId));
        Map<Long, User> userCache = new LinkedHashMap<>();
        Map<Long, Paper> paperCache = new LinkedHashMap<>();
        return posts.stream()
                .map(post -> toPostItem(post, userId, userCache, paperCache, likedPostIds, likeCounts, replyCounts))
                .collect(Collectors.toList());
    }

    @Override
    @Transactional
    public CommunityDto.PostItem updatePost(Long userId, Long postId, CommunityDto.PostUpdateRequest request) {
        Post post = requirePost(postId);
        if (!Objects.equals(post.getUserId(), userId)) {
            throw new IllegalArgumentException("只能修改自己的帖子");
        }
        if (request.getTitle() != null) {
            post.setTitle(request.getTitle());
        }
        if (request.getContent() != null) {
            post.setContent(request.getContent().trim());
        }
        if (request.getPaperId() != null) {
            paperService.getPaperById(request.getPaperId());
            post.setPaperId(request.getPaperId());
        }
        postMapper.updateById(post);
        return toPostItem(postMapper.selectById(postId), userId, new LinkedHashMap<>(), new LinkedHashMap<>(), Set.of(), Map.of(), Map.of());
    }

    @Override
    @Transactional
    public void deletePost(Long userId, Long postId) {
        Post post = requirePost(postId);
        if (!Objects.equals(post.getUserId(), userId)) {
            throw new IllegalArgumentException("只能删除自己的帖子");
        }
        postMapper.deleteById(postId);
    }

    @Override
    @Transactional
    public boolean toggleLike(Long userId, Long postId) {
        int exists = postLikeMapper.existsLike(userId, postId);
        if (exists > 0) {
            postLikeMapper.deleteLike(userId, postId);
            return false;
        } else {
            postLikeMapper.insertLike(userId, postId);
            return true;
        }
    }

    private static Map<Long, Integer> toCountMap(List<Map<String, Object>> rows) {
        if (rows == null || rows.isEmpty()) return Map.of();
        Map<Long, Integer> map = new LinkedHashMap<>();
        for (Map<String, Object> row : rows) {
            Long postId = ((Number) row.get("post_id")).longValue();
            Integer cnt = ((Number) row.get("cnt")).intValue();
            map.put(postId, cnt);
        }
        return map;
    }

    private CommunityDto.AuthorInfo toAuthor(User user) {
        if (user == null) {
            return null;
        }
        UserRole role = UserRole.from(user.getRole());
        CommunityDto.AuthorInfo authorInfo = new CommunityDto.AuthorInfo();
        authorInfo.setId(user.getId());
        authorInfo.setUsername(user.getUsername());
        authorInfo.setRole(role.name());
        authorInfo.setRoleLabel(role.getLabel());
        authorInfo.setAvatar(user.getAvatar());
        authorInfo.setBio(user.getBio());
        return authorInfo;
    }
}
