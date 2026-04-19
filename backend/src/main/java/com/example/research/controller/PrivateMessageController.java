package com.example.research.controller;

import com.example.research.entity.PrivateMessage;
import com.example.research.entity.UserContact;
import com.example.research.service.PrivateMessageService;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 私信 REST 控制器
 */
@RestController
@RequestMapping("/api/message")
@RequiredArgsConstructor
public class PrivateMessageController {

    private final PrivateMessageService privateMessageService;

    /**
     * 获取用户的所有对话列表
     */
    @GetMapping("/conversations")
    public List<UserContact> getConversations(Authentication authentication) {
        Long userId = (Long) authentication.getPrincipal();
        return privateMessageService.getUserConversations(userId);
    }

    /**
     * 获取与指定用户的聊天记录
     */
    @GetMapping("/chat/{contactId}")
    public List<PrivateMessage> getChatHistory(@PathVariable Long contactId, Authentication authentication) {
        Long userId = (Long) authentication.getPrincipal();
        return privateMessageService.getMessagesWithUser(userId, contactId);
    }

    /**
     * 发送私信（REST 方式，可选，与 WebSocket 配合）
     */
    @PostMapping("/send")
    public void sendMessage(@RequestParam Long receiverId, @RequestParam String content, Authentication authentication) {
        Long senderId = (Long) authentication.getPrincipal();
        privateMessageService.sendMessage(senderId, receiverId, content);
    }

    /**
     * 标记消息为已读
     */
    @PostMapping("/mark-read/{messageId}")
    public void markAsRead(@PathVariable Long messageId, Authentication authentication) {
        Long userId = (Long) authentication.getPrincipal();
        privateMessageService.markAsRead(messageId, userId);
    }
}
