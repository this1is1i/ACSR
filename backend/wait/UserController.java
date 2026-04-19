package com.example.research.controller;

import com.example.research.dto.UserDto;
import com.example.research.service.UserService;
import com.example.research.util.Result;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

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
    public Result<Void> register(@Valid @RequestBody UserDto.RegisterRequest request) {
        userService.register(request);
        return Result.success();
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
}
