package com.example.research.service;

import com.example.research.dto.UserDto;
import com.example.research.entity.Paper;
import java.util.List;
import org.springframework.web.multipart.MultipartFile;

public interface UserService {
    void register(UserDto.RegisterRequest request);
    UserDto.LoginResponse login(UserDto.LoginRequest request);
    UserDto.UserProfile getProfile(Long userId);
    void updateProfile(Long userId, UserDto.UpdateProfileRequest req);
    List<Paper> getFavoritePapers(Long userId);
    String uploadAvatar(Long userId, MultipartFile file);
}
