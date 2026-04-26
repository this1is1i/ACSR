package com.example.research.service;

import com.example.research.dto.CommunityDto;
import com.example.research.dto.UserDto;

import java.util.List;

public interface AdminService {
    List<CommunityDto.PostItem> listPosts(String status);
    CommunityDto.PostItem updatePostStatus(Long adminId, Long postId, CommunityDto.PostStatusUpdateRequest request);
    List<UserDto.AdminUserItem> listUsers();
    UserDto.AdminUserItem updateUserRole(Long adminId, Long userId, UserDto.UserRoleUpdateRequest request);
    CommunityDto.PaperImportResult importPapers(CommunityDto.PaperImportRequest request);
}
