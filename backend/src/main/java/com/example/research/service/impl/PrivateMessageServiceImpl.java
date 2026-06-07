package com.example.research.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.UpdateWrapper;
import com.example.research.dto.CollaboratorRecommendation;
import com.example.research.entity.PrivateMessage;
import com.example.research.entity.User;
import com.example.research.entity.UserContact;
import com.example.research.repository.PrivateMessageMapper;
import com.example.research.repository.UserContactMapper;
import com.example.research.repository.UserInterestHistoryMapper;
import com.example.research.repository.UserMapper;
import com.example.research.service.PrivateMessageService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;

/**
 * 私信服务实现
 */
@Service
@RequiredArgsConstructor
public class PrivateMessageServiceImpl implements PrivateMessageService {

    private final PrivateMessageMapper privateMessageMapper;
    private final UserContactMapper userContactMapper;
    private final UserMapper userMapper;
    private final UserInterestHistoryMapper userInterestHistoryMapper;

    @Override
    public void sendMessage(Long senderId, Long receiverId, String content) {
        sendMessage(senderId, receiverId, content, 1);
    }

    @Override
    public void sendMessage(Long senderId, Long receiverId, String content, Integer msgType) {
        PrivateMessage message = new PrivateMessage();
        message.setSenderId(senderId);
        message.setReceiverId(receiverId);
        message.setContent(content);
        message.setMsgType(msgType != null ? msgType : 1);
        message.setCreateTime(LocalDateTime.now());

        privateMessageMapper.insert(message);

        updateContact(senderId, receiverId);
        updateContact(receiverId, senderId);
    }

    @Override
    public void markAsRead(Long messageId, Long userId) {
        UpdateWrapper<PrivateMessage> updateWrapper = new UpdateWrapper<>();
        updateWrapper.eq("id", messageId)
                .eq("receiver_id", userId)
                .set("is_read", true)
                .set("read_time", LocalDateTime.now());

        privateMessageMapper.update(null, updateWrapper);
    }

    @Override
    public List<PrivateMessage> getMessagesWithUser(Long userId, Long contactId) {
        QueryWrapper<PrivateMessage> queryWrapper = new QueryWrapper<>();
        queryWrapper.and(wrapper -> wrapper
                .eq("sender_id", userId).eq("receiver_id", contactId)
                .or()
                .eq("sender_id", contactId).eq("receiver_id", userId)
        ).orderByAsc("create_time");

        List<PrivateMessage> messages = privateMessageMapper.selectList(queryWrapper);

        // 填充发送者和接收者信息
        for (PrivateMessage message : messages) {
            message.setSender(userMapper.selectById(message.getSenderId()));
            message.setReceiver(userMapper.selectById(message.getReceiverId()));
        }

        return messages;
    }

    @Override
    public List<UserContact> getUserConversations(Long userId) {
        QueryWrapper<UserContact> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("user_id", userId);

        List<UserContact> contacts = userContactMapper.selectList(queryWrapper);

        // 填充联系人信息、未读数量和最后消息
        for (UserContact contact : contacts) {
            contact.setContact(userMapper.selectById(contact.getContactId()));

            // 计算未读数量
            QueryWrapper<PrivateMessage> unreadQuery = new QueryWrapper<>();
            unreadQuery.eq("sender_id", contact.getContactId())
                    .eq("receiver_id", userId)
                    .eq("is_read", false);
            contact.setUnreadCount(privateMessageMapper.selectCount(unreadQuery));

            // 获取最后消息
            QueryWrapper<PrivateMessage> lastMessageQuery = new QueryWrapper<>();
            lastMessageQuery.and(wrapper -> wrapper
                    .eq("sender_id", userId).eq("receiver_id", contact.getContactId())
                    .or()
                    .eq("sender_id", contact.getContactId()).eq("receiver_id", userId)
            ).orderByDesc("create_time").last("limit 1");

            List<PrivateMessage> lastMessages = privateMessageMapper.selectList(lastMessageQuery);
            if (!lastMessages.isEmpty()) {
                contact.setLastMessage(lastMessages.get(0).getContent());
            }
        }

        return contacts;
    }

    @Override
    public List<CollaboratorRecommendation> getRecommendedCollaborators(Long userId) {
        User currentUser = userMapper.selectById(userId);
        if (currentUser == null) {
            return List.of();
        }
        if (!"RESEARCHER".equals(currentUser.getRole())) {
            return List.of();
        }

        Set<String> myTags = parseInterests(userId, userInterestHistoryMapper);
        if (myTags.isEmpty()) {
            return List.of();
        }

        Set<Long> excludedIds = new HashSet<>();
        excludedIds.add(userId);
        QueryWrapper<UserContact> contactQuery = new QueryWrapper<>();
        contactQuery.eq("user_id", userId);
        List<UserContact> contacts = userContactMapper.selectList(contactQuery);
        for (UserContact c : contacts) {
            excludedIds.add(c.getContactId());
        }

        LambdaQueryWrapper<User> userQuery = new LambdaQueryWrapper<>();
        userQuery.eq(User::getRole, "RESEARCHER");
        if (!excludedIds.isEmpty()) {
            userQuery.notIn(User::getId, excludedIds);
        }
        List<User> researchers = userMapper.selectList(userQuery);

        return researchers.stream()
                .map(u -> {
                    Set<String> theirTags = parseInterests(u.getId(), userInterestHistoryMapper);
                    Set<String> common = new HashSet<>(myTags);
                    common.retainAll(theirTags);
                    return new UserMatch(u, common.size(), common);
                })
                .filter(m -> m.overlap > 0)
                .sorted(Comparator.comparingInt(UserMatch::overlap).reversed())
                .limit(2)
                .map(m -> new CollaboratorRecommendation(
                        m.user.getId(),
                        m.user.getUsername(),
                        m.user.getAvatar(),
                        m.user.getBio(),
                        List.copyOf(m.common),
                        m.overlap,
                        "共同研究兴趣: " + String.join(", ", m.common)
                ))
                .toList();
    }

    private static Set<String> parseInterests(Long userId, UserInterestHistoryMapper mapper) {
        List<String> tags = mapper.findTagsByUserId(userId);
        return new HashSet<>(tags);
    }

    private record UserMatch(User user, int overlap, Set<String> common) {}

    private void updateContact(Long userId, Long contactId) {
        QueryWrapper<UserContact> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("user_id", userId).eq("contact_id", contactId);

        UserContact contact = userContactMapper.selectOne(queryWrapper);
        if (contact == null) {
            contact = new UserContact();
            contact.setUserId(userId);
            contact.setContactId(contactId);
            contact.setCreateTime(LocalDateTime.now());
            userContactMapper.insert(contact);
        }
        // 如果存在，可以更新最后消息时间，但这里简化
    }
}
