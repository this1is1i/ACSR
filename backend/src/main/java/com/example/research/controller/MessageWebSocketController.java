package com.example.research.controller;

import com.example.research.service.PrivateMessageService;
import com.example.research.util.JwtUtil;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.event.EventListener;
import org.springframework.messaging.handler.annotation.MessageMapping;
import org.springframework.messaging.handler.annotation.Payload;
import org.springframework.messaging.simp.SimpMessageHeaderAccessor;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Controller;
import org.springframework.web.socket.messaging.SessionDisconnectEvent;

import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * WebSocket 消息控制器
 * 处理实时私信和用户在线状态
 */
@Slf4j
@Controller
@RequiredArgsConstructor
public class MessageWebSocketController {

    private final PrivateMessageService privateMessageService;
    private final SimpMessagingTemplate messagingTemplate;
    private final JwtUtil jwtUtil;

    /** 在线用户表：userId → sessionId */
    private final ConcurrentHashMap<Long, String> onlineUsers = new ConcurrentHashMap<>();

    /**
     * 处理私信消息（仅负责实时转发，持久化由 REST /api/message/send 完成）。
     */
    @MessageMapping("/send-private")
    public void handlePrivateMessage(@Payload Map<String, Object> messageData) {
        String token = (String) messageData.get("token");
        if (!jwtUtil.validateToken(token)) {
            return;
        }
        Long senderId = jwtUtil.getUserIdFromToken(token);

        Long receiverId = Long.valueOf(String.valueOf(messageData.get("receiverId")));
        String content = (String) messageData.get("content");

        // 补上 senderId 和 time 字段供前端识别
        Map<String, Object> payload = new java.util.HashMap<>(messageData);
        payload.put("senderId", senderId);
        payload.put("time", java.time.LocalTime.now().format(java.time.format.DateTimeFormatter.ofPattern("HH:mm")));

        messagingTemplate.convertAndSendToUser(
            receiverId.toString(),
            "/queue/private",
            payload
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
        privateMessageService.markAsRead(messageId, userId);
    }

    /**
     * 处理用户上线通知。
     * 记录在线状态，广播给所有用户，并向新上线用户发送当前在线列表。
     */
    @MessageMapping("/user-online")
    public void handleUserOnline(@Payload Map<String, Object> data,
                                  SimpMessageHeaderAccessor headerAccessor) {
        String token = (String) data.get("token");
        if (!jwtUtil.validateToken(token)) {
            return;
        }
        Long userId = jwtUtil.getUserIdFromToken(token);
        String sessionId = headerAccessor.getSessionId();

        // 1. 记录在线状态
        onlineUsers.put(userId, sessionId);
        log.info("用户 {} 上线 (session: {})，当前在线 {} 人", userId, sessionId, onlineUsers.size());

        // 2. 广播上线给所有用户
        messagingTemplate.convertAndSend(
            "/topic/user-status",
            Map.of("userId", userId, "status", "online")
        );

        // 3. 广播当前全部在线用户列表（通过 /topic/user-status 避免 convertAndSendToUser 的 Principal 依赖）
        List<Long> userIds = List.copyOf(onlineUsers.keySet());
        messagingTemplate.convertAndSend(
            "/topic/user-status",
            Map.of("type", "init_snapshot", "userIds", userIds)
        );
    }

    /**
     * 监听 WebSocket 会话断开：移除在线记录并广播离线状态。
     */
    @EventListener
    public void handleSessionDisconnect(SessionDisconnectEvent event) {
        String sessionId = event.getSessionId();

        // 查找该 session 对应的 userId
        Long disconnectedUserId = null;
        for (Map.Entry<Long, String> entry : onlineUsers.entrySet()) {
            if (sessionId.equals(entry.getValue())) {
                disconnectedUserId = entry.getKey();
                break;
            }
        }

        if (disconnectedUserId != null) {
            onlineUsers.remove(disconnectedUserId);
            log.info("用户 {} 离线 (session: {})，当前在线 {} 人",
                    disconnectedUserId, sessionId, onlineUsers.size());

            // 广播离线状态
            messagingTemplate.convertAndSend(
                "/topic/user-status",
                Map.of("userId", disconnectedUserId, "status", "offline")
            );
        }
    }
}
