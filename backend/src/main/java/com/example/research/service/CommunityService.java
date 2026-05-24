package com.example.research.service;

import com.example.research.dto.CommunityDto;

import java.util.List;

public interface CommunityService {
    List<CommunityDto.PostItem> listPosts(Long currentUserId, String filter);
    CommunityDto.PostItem createPost(Long userId, CommunityDto.PostCreateRequest request);
    List<CommunityDto.CommentItem> listComments(Long postId, Long currentUserId);
    CommunityDto.CommentItem createComment(Long userId, Long postId, CommunityDto.CommentCreateRequest request);
    boolean toggleLike(Long userId, Long postId);

    List<CommunityDto.PostItem> searchPosts(String keyword, Long currentUserId);
    List<CommunityDto.PostItem> listMyPosts(Long userId);
    CommunityDto.PostItem updatePost(Long userId, Long postId, CommunityDto.PostUpdateRequest request);
    void deletePost(Long userId, Long postId);
}
