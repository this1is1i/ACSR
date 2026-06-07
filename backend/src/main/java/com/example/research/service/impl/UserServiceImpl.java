package com.example.research.service.impl;

import com.example.research.dto.UserDto;
import com.example.research.entity.Favourite;
import com.example.research.entity.Paper;
import com.example.research.entity.UserInterestHistory;
import com.example.research.enums.UserRole;
import com.example.research.entity.User;
import com.example.research.repository.BehaviorLogMapper;
import com.example.research.repository.FavouriteMapper;
import com.example.research.repository.UserInterestHistoryMapper;
import com.example.research.repository.UserMapper;
import com.example.research.service.UserService;
import com.example.research.util.JwtUtil;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.time.LocalDate;
import java.util.*;
import java.util.stream.Collectors;

@Slf4j

@Service
@RequiredArgsConstructor
public class UserServiceImpl implements UserService {

    private final UserMapper userMapper;
    private final BehaviorLogMapper behaviorLogMapper;
    private final FavouriteMapper favouriteMapper;
    private final UserInterestHistoryMapper userInterestHistoryMapper;
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
        // 用户选择身份：学生或研究者；非法值时回退为 STUDENT
        String rawRole = request.getRole();
        UserRole chosenRole = (rawRole != null && Set.of("STUDENT", "RESEARCHER").contains(rawRole.toUpperCase()))
                ? UserRole.valueOf(rawRole.toUpperCase()) : UserRole.STUDENT;
        user.setRole(chosenRole.name());

        // research_interests 不再写入 user 表，统一由 user_interest_history 管理
        userMapper.insert(user);

        // 创建初始兴趣画像记录
        if (request.getResearchInterests() != null && !request.getResearchInterests().isBlank()) {
            String[] interests = request.getResearchInterests().split(",");
            LocalDate today = LocalDate.now();
            Set<String> seen = new HashSet<>();
            for (String interest : interests) {
                String trimmed = interest.trim();
                if (!trimmed.isEmpty() && seen.add(trimmed)) {
                    UserInterestHistory history = new UserInterestHistory();
                    history.setUserId(user.getId());
                    history.setInterestTag(trimmed);
                    history.setWeight(0.5);
                    history.setSource("register");
                    history.setRecordDate(today);
                    userInterestHistoryMapper.insert(history);
                }
            }
        }
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
        profile.setResearchInterests(
                String.join(", ", deduplicateTags(userInterestHistoryMapper.findTagsByUserId(user.getId())))
        );
        return profile;
    }

    @Override
    public void updateProfile(Long userId, UserDto.UpdateProfileRequest req) {
        User user = userMapper.selectById(userId);
        if (user == null) throw new IllegalArgumentException("用户不存在");
        if (req.getEmail() != null) user.setEmail(req.getEmail());
        if (req.getAvatar() != null) user.setAvatar(req.getAvatar());
        if (req.getBio() != null) user.setBio(req.getBio());
        if (req.getResearchInterests() != null) {
            // 同步到 user_interest_history（不再写入 user.research_interests 列）
            LocalDate today = LocalDate.now();
            // 删除该用户之前通过 register / profile_update 来源的记录，避免重复堆积
            userInterestHistoryMapper.deleteByUserIdAndSource(userId, "register");
            userInterestHistoryMapper.deleteByUserIdAndSource(userId, "profile_update");
            // 去重后插入新记录
            Set<String> seen = new HashSet<>();
            for (String tag : req.getResearchInterests().split(",")) {
                String trimmed = tag.trim();
                if (!trimmed.isEmpty() && seen.add(trimmed)) {
                    UserInterestHistory h = new UserInterestHistory();
                    h.setUserId(userId);
                    h.setInterestTag(trimmed);
                    h.setWeight(0.5);
                    h.setSource("profile_update");
                    h.setRecordDate(today);
                    userInterestHistoryMapper.insert(h);
                }
            }
        }
        userMapper.updateById(user);
    }

    @Override
    public List<Paper> getFavoritePapers(Long userId) {
        return favouriteMapper.findFavoritePapersByUserId(userId);
    }

    @Override
    public String uploadAvatar(Long userId, MultipartFile file) {
        User user = userMapper.selectById(userId);
        if (user == null) throw new IllegalArgumentException("用户不存在");

        // Validate file type
        String contentType = file.getContentType();
        if (contentType == null || !contentType.startsWith("image/")) {
            throw new IllegalArgumentException("仅支持图片文件");
        }

        // Generate unique filename
        String originalName = file.getOriginalFilename();
        String ext = ".png";
        if (originalName != null && originalName.contains(".")) {
            ext = originalName.substring(originalName.lastIndexOf("."));
        }
        String filename = "avatar_" + userId + "_" + UUID.randomUUID().toString().substring(0, 8) + ext;

        // Save to uploads/avatars/
        try {
            Path uploadDir = Paths.get("uploads", "avatars");
            Files.createDirectories(uploadDir);
            Path targetPath = uploadDir.resolve(filename);
            Files.copy(file.getInputStream(), targetPath, StandardCopyOption.REPLACE_EXISTING);

            String avatarUrl = "/uploads/avatars/" + filename;
            user.setAvatar(avatarUrl);
            userMapper.updateById(user);

            log.info("Avatar uploaded: userId={}, url={}", userId, avatarUrl);
            return avatarUrl;
        } catch (IOException e) {
            throw new RuntimeException("头像上传失败", e);
        }
    }

    @Override
    public List<UserDto.UserProfile> searchUsers(String query, int limit) {
        if (query == null || query.isBlank()) {
            return List.of();
        }
        List<User> users = userMapper.searchUsers(query.trim(), Math.min(limit, 20));

        // 批量查询兴趣标签，避免 N+1
        List<Long> userIds = users.stream().map(User::getId).collect(Collectors.toList());
        Map<Long, String> interestMap = new HashMap<>();
        if (!userIds.isEmpty()) {
            Map<Long, List<String>> grouped = new HashMap<>();
            for (Map<String, Object> row : userInterestHistoryMapper.findTagsByUserIds(userIds)) {
                Long uid = ((Number) row.get("user_id")).longValue();
                grouped.computeIfAbsent(uid, k -> new ArrayList<>()).add((String) row.get("interest_tag"));
            }
            grouped.forEach((uid, tags) -> interestMap.put(uid, String.join(", ", tags)));
        }

        return users.stream()
                .map(u -> {
                    UserDto.UserProfile profile = new UserDto.UserProfile();
                    profile.setId(u.getId());
                    profile.setUsername(u.getUsername());
                    profile.setEmail(u.getEmail());
                    profile.setAvatar(u.getAvatar());
                    profile.setBio(u.getBio());
                    profile.setResearchInterests(interestMap.getOrDefault(u.getId(), ""));
                    profile.setRole(u.getRole());
                    profile.setRoleLabel(UserRole.from(u.getRole()).getLabel());
                    return profile;
                })
                .collect(Collectors.toList());
    }

    @Override
    public void changePassword(Long userId, UserDto.ChangePasswordRequest req) {
        User user = userMapper.selectById(userId);
        if (user == null) throw new IllegalArgumentException("用户不存在");
        if (!passwordEncoder.matches(req.getOldPassword(), user.getPassword())) {
            throw new IllegalArgumentException("原密码错误");
        }
        user.setPassword(passwordEncoder.encode(req.getNewPassword()));
        userMapper.updateById(user);
    }

    /**
     * 对标签列表去重（保持顺序，首次出现保留）。
     */
    private static List<String> deduplicateTags(List<String> tags) {
        if (tags == null || tags.isEmpty()) return List.of();
        List<String> result = new ArrayList<>();
        Set<String> seen = new HashSet<>();
        for (String tag : tags) {
            if (tag != null && seen.add(tag.trim())) {
                result.add(tag.trim());
            }
        }
        return result;
    }
}
