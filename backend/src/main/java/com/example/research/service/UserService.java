package com.example.research.service;

import com.example.research.dto.UserDto;

public interface UserService {
    void register(UserDto.RegisterRequest request);
    UserDto.LoginResponse login(UserDto.LoginRequest request);
    UserDto.UserProfile getProfile(Long userId);
    void updateProfile(Long userId, UserDto.UpdateProfileRequest req);
}
