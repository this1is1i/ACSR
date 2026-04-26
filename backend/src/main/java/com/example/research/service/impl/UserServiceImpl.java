package com.example.research.service.impl;

import com.example.research.dto.UserDto;
import com.example.research.enums.UserRole;
import com.example.research.entity.User;
import com.example.research.repository.UserMapper;
import com.example.research.service.UserService;
import com.example.research.util.JwtUtil;
import lombok.RequiredArgsConstructor;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class UserServiceImpl implements UserService {

    private final UserMapper userMapper;
    private final PasswordEncoder passwordEncoder;
    private final JwtUtil jwtUtil;

    @Override
    public void register(UserDto.RegisterRequest request) {
        if (userMapper.findByUsername(request.getUsername()) != null) {
            throw new IllegalArgumentException("用户名已存在");
        }
        User user = new User();
        user.setUsername(request.getUsername());
        user.setPassword(passwordEncoder.encode(request.getPassword()));
        user.setEmail(request.getEmail());
        user.setRole(UserRole.STUDENT.name());
        userMapper.insert(user);
    }

    @Override
    public UserDto.LoginResponse login(UserDto.LoginRequest request) {
        User user = userMapper.findByUsername(request.getUsername());
        if (user == null || !passwordEncoder.matches(request.getPassword(), user.getPassword())) {
            throw new IllegalArgumentException("用户名或密码错误");
        }
        UserRole role = UserRole.from(user.getRole());
        if (!role.name().equals(user.getRole())) {
            user.setRole(role.name());
            userMapper.updateById(user);
        }
        String token = jwtUtil.generateToken(user.getId(), user.getUsername(), role.name());
        UserDto.LoginResponse resp = new UserDto.LoginResponse();
        resp.setToken(token);
        resp.setUserId(user.getId());
        resp.setUsername(user.getUsername());
        resp.setRole(role.name());
        resp.setRoleLabel(role.getLabel());
        return resp;
    }

    @Override
    public UserDto.UserProfile getProfile(Long userId) {
        User user = userMapper.selectById(userId);
        if (user == null) throw new IllegalArgumentException("用户不存在");
        UserRole role = UserRole.from(user.getRole());
        UserDto.UserProfile profile = new UserDto.UserProfile();
        profile.setId(user.getId());
        profile.setUsername(user.getUsername());
        profile.setEmail(user.getEmail());
        profile.setRole(role.name());
        profile.setRoleLabel(role.getLabel());
        profile.setAvatar(user.getAvatar());
        profile.setBio(user.getBio());
        profile.setResearchInterests(user.getResearchInterests());
        return profile;
    }

    @Override
    public void updateProfile(Long userId, UserDto.UpdateProfileRequest req) {
        User user = userMapper.selectById(userId);
        if (user == null) throw new IllegalArgumentException("用户不存在");
        if (req.getEmail() != null) user.setEmail(req.getEmail());
        if (req.getAvatar() != null) user.setAvatar(req.getAvatar());
        if (req.getBio() != null) user.setBio(req.getBio());
        if (req.getResearchInterests() != null) user.setResearchInterests(req.getResearchInterests());
        userMapper.updateById(user);
    }
}
