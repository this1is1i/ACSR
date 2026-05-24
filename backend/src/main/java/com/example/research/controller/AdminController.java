package com.example.research.controller;

import com.example.research.dto.CommunityDto;
import com.example.research.dto.UserDto;
import com.example.research.service.AdminService;
import com.example.research.util.Result;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/admin")
@RequiredArgsConstructor
public class AdminController {

    private final AdminService adminService;

    @GetMapping("/posts")
    public Result<List<CommunityDto.PostItem>> listPosts(@RequestParam(required = false) String status) {
        return Result.success(adminService.listPosts(status));
    }

    @PutMapping("/posts/{postId}/status")
    public Result<CommunityDto.PostItem> updatePostStatus(
            @PathVariable Long postId,
            @Valid @RequestBody CommunityDto.PostStatusUpdateRequest request,
            Authentication authentication) {
        Long adminId = (Long) authentication.getPrincipal();
        return Result.success(adminService.updatePostStatus(adminId, postId, request));
    }

    @GetMapping("/users")
    public Result<List<UserDto.AdminUserItem>> listUsers() {
        return Result.success(adminService.listUsers());
    }

    @PutMapping("/users/{userId}/role")
    public Result<UserDto.AdminUserItem> updateUserRole(
            @PathVariable Long userId,
            @Valid @RequestBody UserDto.UserRoleUpdateRequest request,
            Authentication authentication) {
        Long adminId = (Long) authentication.getPrincipal();
        return Result.success(adminService.updateUserRole(adminId, userId, request));
    }

    @PostMapping("/papers/import")
    public Result<CommunityDto.PaperImportResult> importPapers(
            @Valid @RequestBody CommunityDto.PaperImportRequest request,
            Authentication authentication) {
        Long adminId = (Long) authentication.getPrincipal();
        return Result.success(adminService.importPapers(adminId, request));
    }
}
