package com.example.research.controller;

import com.example.research.service.PrivateMessageService;
import com.example.research.util.JwtUtil;
import lombok.RequiredArgsConstructor;
import org.springframework.messaging.handler.annotation.MessageMapping;
import org.springframework.messaging.handler.annotation.Payload;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Controller;

import java.util.Map;

/**
 * WebSocket 消息控制器
 * 处理实时私信和用户状态
 */
@Controller
@RequiredArgsConstructor
public class MessageWebSocketController {

    private final PrivateMessageService privateMessageService;
    private final SimpMessagingTemplate messagingTemplate;
    private final JwtUtil jwtUtil;

    /**
     * 处理私信消息
     */
    @MessageMapping("/send-private")
    public void handlePrivateMessage(@Payload Map<String, Object> messageData) {
        // 从消息中获取 token 并解析用户ID
        String token = (String) messageData.get("token");
        if (!jwtUtil.validateToken(token)) {
            return; // 无效token，忽略
        }
        Long senderId = jwtUtil.getUserIdFromToken(token);

        Long receiverId = Long.valueOf(String.valueOf(messageData.get("receiverId")));
        String content = (String) messageData.get("content");

        // 保存消息到数据库
        privateMessageService.sendMessage(senderId, receiverId, content);

        // 通过 WebSocket 发送给接收者
        messagingTemplate.convertAndSendToUser(
            receiverId.toString(),
            "/queue/private",
            messageData
        );
    }

    /**
     * 处理已读回执
     */
    @MessageMapping("/mark-read")
    public void handleMarkAsRead(@Payload Map<String, Object> data) {
        String token = (String) data.get("token");
        if (!jwtUtil.validateToken(token)) {
            return;
        }
        Long userId = jwtUtil.getUserIdFromToken(token);

        Long messageId = Long.valueOf(String.valueOf(data.get("messageId")));

        // 标记消息为已读
        privateMessageService.markAsRead(messageId, userId);

        // 发送已读回执给发送者（需要找到发送者ID）
        // 这里简化，假设发送者ID在data中，或者从数据库查询
        // 在实际中，可能需要传递senderId
        // messagingTemplate.convertAndSendToUser(senderId.toString(), "/queue/read-receipt", data);
    }

    /**
     * 处理用户上线通知
     */
    @MessageMapping("/user-online")
    public void handleUserOnline(@Payload Map<String, Object> data) {
        String token = (String) data.get("token");
        if (!jwtUtil.validateToken(token)) {
            return;
        }
        Long userId = jwtUtil.getUserIdFromToken(token);

        // 广播用户上线状态
        messagingTemplate.convertAndSend(
            "/topic/user-status",
            Map.of("userId", userId, "status", "online")
        );
    }
}
