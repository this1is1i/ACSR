package com.example.research.controller;

import com.example.research.dto.UserDto;
import com.example.research.entity.Paper;
import com.example.research.service.UserService;
import com.example.research.util.Result;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;
import java.util.Map;

/**
 * 用户模块控制器
 *
 * 接口列表：
 *   POST /api/user/register   - 用户注册
 *   POST /api/user/login      - 用户登录（返回 JWT Token）
 *   GET  /api/user/profile    - 获取当前登录用户信息
 */
@Slf4j
@RestController
@RequestMapping("/api/user")
@RequiredArgsConstructor
public class UserController {

    private final UserService userService;

    /**
     * 用户注册
     *
     * Request:  { "username": "alice", "password": "abc123", "email": "..." }
     * Response: { "code": 0, "message": "注册成功", "data": null }
     */
    @PostMapping("/register")
    public Result<UserDto.LoginResponse> register(@Valid @RequestBody UserDto.RegisterRequest request) {
        userService.register(request);
        // 注册后自动登录，返回 JWT token
        UserDto.LoginRequest loginReq = new UserDto.LoginRequest();
        loginReq.setUsername(request.getUsername());
        loginReq.setPassword(request.getPassword());
        UserDto.LoginResponse resp = userService.login(loginReq);
        return Result.success(resp);
    }

    /**
     * 用户登录
     *
     * Request:  { "username": "alice", "password": "abc123" }
     * Response: { "code": 0, "data": { "token": "eyJ...", "userId": 1, "username": "alice" } }
     */
    @PostMapping("/login")
    public Result<UserDto.LoginResponse> login(@Valid @RequestBody UserDto.LoginRequest request) {
        UserDto.LoginResponse resp = userService.login(request);
        return Result.success(resp);
    }

    /**
     * 获取当前登录用户个人信息
     * 需要携带 Authorization: Bearer <token> 请求头
     */
    @GetMapping("/profile")
    public Result<UserDto.UserProfile> getProfile(Authentication authentication) {
        // Authentication.getPrincipal() 存储的是 userId（见 JwtFilter）
        Long userId = (Long) authentication.getPrincipal();
        return Result.success(userService.getProfile(userId));
    }

    @PutMapping("/profile")
    public Result<String> updateProfile(@RequestBody UserDto.UpdateProfileRequest req, Authentication authentication) {
        Long userId = (Long) authentication.getPrincipal();
        userService.updateProfile(userId, req);
        return Result.success("更新成功");
    }

    @GetMapping("/favorites")
    public Result<List<Paper>> getFavorites(Authentication authentication) {
        Long userId = (Long) authentication.getPrincipal();
        return Result.success(userService.getFavoritePapers(userId));
    }

    @PostMapping("/avatar")
    public Result<Map<String, String>> uploadAvatar(
            @RequestParam("file") MultipartFile file,
            Authentication authentication) {
        Long userId = (Long) authentication.getPrincipal();
        String url = userService.uploadAvatar(userId, file);
        return Result.success(Map.of("avatarUrl", url));
    }
}

