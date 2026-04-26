package com.example.research.controller;

import com.example.research.dto.CommunityDto;
import com.example.research.service.CommunityService;
import com.example.research.util.Result;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/community")
@RequiredArgsConstructor
public class CommunityController {

    private final CommunityService communityService;

    @GetMapping("/posts")
    public Result<List<CommunityDto.PostItem>> listPosts(
            @RequestParam(defaultValue = "latest") String filter,
            Authentication authentication) {
        Long userId = authentication == null ? null : (Long) authentication.getPrincipal();
        return Result.success(communityService.listPosts(userId, filter));
    }

    @PostMapping("/posts")
    public Result<CommunityDto.PostItem> createPost(
            @Valid @RequestBody CommunityDto.PostCreateRequest request,
            Authentication authentication) {
        Long userId = (Long) authentication.getPrincipal();
        return Result.success(communityService.createPost(userId, request));
    }

    @GetMapping("/posts/{postId}/comments")
    public Result<List<CommunityDto.CommentItem>> listComments(
            @PathVariable Long postId,
            Authentication authentication) {
        Long userId = authentication == null ? null : (Long) authentication.getPrincipal();
        return Result.success(communityService.listComments(postId, userId));
    }

    @PostMapping("/posts/{postId}/comments")
    public Result<CommunityDto.CommentItem> createComment(
            @PathVariable Long postId,
            @Valid @RequestBody CommunityDto.CommentCreateRequest request,
            Authentication authentication) {
        Long userId = (Long) authentication.getPrincipal();
        return Result.success(communityService.createComment(userId, postId, request));
    }
}
