# WebSocket 实时通信功能实现总结

## 一、概述

本项目使用 WebSocket + STOMP 协议实现了论坛的实时通信功能，主要用于私信消息的实时推送、已读回执和用户在线状态更新。

## 二、后端实现

### 1. WebSocket 配置

**文件位置**: `src/main/java/com/forum/config/WebSocketConfig.java`

```java
@Configuration
@EnableWebSocketMessageBroker
public class WebSocketConfig implements WebSocketMessageBrokerConfigurer {
    @Override
    public void configureMessageBroker(MessageBrokerRegistry config) {
        // 启用简单消息代理，用于向客户端发送消息
        config.enableSimpleBroker("/topic", "/queue");
        // 设置应用目标前缀
        config.setApplicationDestinationPrefixes("/app");
    }

    @Override
    public void registerStompEndpoints(StompEndpointRegistry registry) {
        // 注册STOMP端点，允许跨域
        registry.addEndpoint("/ws-messages")
                .setAllowedOriginPatterns("*")
                .withSockJS();
    }
}
```

### 2. WebSocket 消息控制器

**文件位置**: `src/main/java/com/forum/controller/MessageWebSocketController.java`

```java
@Controller
public class MessageWebSocketController {
    @Resource
    private PrivateMessageService privateMessageService;
    
    @Resource
    private SimpMessagingTemplate messagingTemplate;

    // 处理私信消息
    @MessageMapping("/send-private")
    public void handlePrivateMessage(@Payload Map<String, Object> messageData, Principal principal) {
        // 1. 解析消息数据
        Long senderId = TokenUtils.getCurrentUserWithToken((String) messageData.get("token")).getId();
        Long receiverId = Long.valueOf((String) messageData.get("receiverId"));
        String content = (String) messageData.get("content");
        
        // 2. 保存消息到数据库
        privateMessageService.sendMessage(senderId, receiverId, content);
        
        // 3. 通过WebSocket发送给接收者
        messagingTemplate.convertAndSendToUser(
            receiverId.toString(), 
            "/queue/private", 
            messageData
        );
    }

    // 处理已读回执
    @MessageMapping("/mark-read")
    public void handleMarkAsRead(@Payload Map<String, Object> data, Principal principal) {
        Long messageId = Long.valueOf((String) data.get("messageId"));
        Long userId = TokenUtils.getCurrentUserWithToken((String) data.get("token")).getId();
        
        // 标记消息为已读
        privateMessageService.markAsRead(messageId, userId);
        
        // 发送已读回执给发送者
        messagingTemplate.convertAndSendToUser(
            userId.toString(),
            "/queue/read-receipt",
            data
        );
    }

    // 处理用户上线通知
    @MessageMapping("/user-online")
    public void handleUserOnline(@Payload Map<String, Object> data, Principal principal) {
        Long userId = TokenUtils.getCurrentUserWithToken((String) data.get("token")).getId();
        
        // 广播用户上线状态
        messagingTemplate.convertAndSend(
            "/topic/user-status",
            Map.of("userId", userId, "status", "online")
        );
    }
}
```

### 3. 私信服务实现

**文件位置**: `src/main/java/com/forum/service/impl/PrivateMessageServiceImpl.java`

关键方法：
- `sendMessage()`: 保存消息到数据库并更新联系人列表
- `markAsRead()`: 标记消息为已读
- `getMessagesWithUser()`: 获取与特定用户的聊天记录
- `getUserConversations()`: 获取用户的所有对话列表

## 三、前端实现

### 1. WebSocket 连接管理

**文件位置**: `web/forum-frontend/src/composables/useWebSocket.js`

```javascript
import {onUnmounted, ref} from 'vue';
import {Client} from '@stomp/stompjs';
import SockJS from 'sockjs-client';

export function useWebSocket() {
    const messages = ref([]);
    const isConnected = ref(false);
    const unreadCount = ref(0);
    const userStatusMap = ref({});
    let stompClient = null;
    let token = null;

    const connect = (userToken) => {
        token = userToken;
        stompClient = new Client({
            webSocketFactory: () => new SockJS('http://localhost:8080/ws-messages'),
            connectHeaders: {
                Authorization: token
            },
            onConnect: (frame) => {
                isConnected.value = true;
                
                // 订阅私信消息
                stompClient.subscribe('/user/queue/private', (message) => {
                    const messageData = JSON.parse(message.body);
                    messages.value.push(messageData);
                    updateUnreadCount();
                });

                // 订阅已读回执
                stompClient.subscribe('/user/queue/read-receipt', (message) => {
                    const receiptData = JSON.parse(message.body);
                    const msgIndex = messages.value.findIndex(msg => msg.id === receiptData.messageId);
                    if (msgIndex !== -1) {
                        messages.value[msgIndex].isRead = true;
                    }
                });

                // 订阅用户状态
                stompClient.subscribe('/topic/user-status', (message) => {
                    const statusData = JSON.parse(message.body);
                    userStatusMap.value[statusData.userId] = statusData.status === 'online';
                });

                // 通知服务器用户上线
                notifyUserOnline();
            }
        });
        stompClient.activate();
    };

    const sendMessage = (receiverId, content) => {
        if (stompClient && isConnected.value) {
            stompClient.publish({
                destination: '/app/send-private',
                body: JSON.stringify({
                    receiverId: receiverId,
                    content: content,
                    token: token
                })
            });
        }
    };

    const markAsRead = (messageId) => {
        if (stompClient && isConnected.value) {
            stompClient.publish({
                destination: '/app/mark-read',
                body: JSON.stringify({
                    messageId: messageId,
                    token: token
                })
            });
        }
    };

    return {
        messages,
        isConnected,
        unreadCount,
        connect,
        disconnect,
        sendMessage,
        markAsRead,
        userStatusMap
    };
}
```

### 2. 消息窗口组件

**文件位置**: `web/forum-frontend/src/components/MessageWindow.vue`

组件功能：
- 显示消息列表
- 发送新消息
- 显示在线状态
- 自动滚动到最新消息

### 3. 路由集成

**文件位置**: `web/forum-frontend/src/router/index.js`

```javascript
{
    path: '/messages',
    name: 'Messages',
    component: MessagesView
}
```

## 四、数据库设计

### 1. 私信表 (private_messages)

**文件位置**: `src/main/java/com/forum/entity/PrivateMessage.java`

```java
@Data
@TableName("private_messages")
public class PrivateMessage {
    @TableId(type = IdType.AUTO)
    private Long id;
    
    @TableField("sender_id")
    private Long senderId;
    
    @TableField("receiver_id")
    private Long receiverId;
    
    private String content;
    
    @TableField("is_read")
    private Boolean isRead = false;
    
    @TableField("created_at")
    private LocalDateTime createdAt;
    
    @TableField(exist = false)
    private User sender;
    
    @TableField(exist = false)
    private User receiver;
}
```

### 2. 用户联系人表 (user_contacts)

**文件位置**: `src/main/java/com/forum/entity/UserContact.java`

```java
@Data
@TableName("user_contacts")
public class UserContact {
    @TableField("user_id")
    private Long userId;
    
    @TableField("contact_id")
    private Long contactId;
    
    @TableField("last_message_time")
    private LocalDateTime lastMessageTime;
    
    @TableField(exist = false)
    private User contact;
    
    @TableField(exist = false)
    private Long unreadCount;
    
    @TableField(exist = false)
    private String lastMessage;
}
```

## 五、迁移步骤

### 1. 后端迁移

1. 添加依赖：
   ```xml
   <dependency>
       <groupId>org.springframework.boot</groupId>
       <artifactId>spring-boot-starter-websocket</artifactId>
   </dependency>
   ```

2. 复制 `WebSocketConfig.java` 到目标项目

3. 创建 `MessageWebSocketController.java` 实现消息处理

4. 创建相应的 Service 和 Mapper 处理消息持久化

### 2. 前端迁移

1. 安装依赖：
   ```bash
   npm install @stomp/stompjs sockjs-client
   ```

2. 复制 `useWebSocket.js` 到目标项目

3. 创建消息窗口组件

4. 添加路由配置

### 3. 数据库迁移

1. 创建私信表：
   ```sql
   CREATE TABLE private_messages (
       id BIGINT AUTO_INCREMENT PRIMARY KEY,
       sender_id BIGINT NOT NULL,
       receiver_id BIGINT NOT NULL,
       content TEXT NOT NULL,
       is_read BOOLEAN DEFAULT FALSE,
       created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
       FOREIGN KEY (sender_id) REFERENCES user(id),
       FOREIGN KEY (receiver_id) REFERENCES user(id)
   );
   ```

2. 创建用户联系人表：
   ```sql
   CREATE TABLE user_contacts (
       user_id BIGINT NOT NULL,
       contact_id BIGINT NOT NULL,
       last_message_time DATETIME DEFAULT CURRENT_TIMESTAMP,
       PRIMARY KEY (user_id, contact_id),
       FOREIGN KEY (user_id) REFERENCES user(id),
       FOREIGN KEY (contact_id) REFERENCES user(id)
   );
   ```

## 六、注意事项

1. **安全性**：
    - WebSocket 连接需要携带认证 token
    - 消息内容需要进行过滤和验证

2. **性能优化**：
    - 使用连接池管理 WebSocket 连接
    - 对大量历史消息进行分页加载

3. **错误处理**：
    - 实现断线重连机制
    - 处理消息发送失败的情况

4. **扩展性**：
    - 可以添加消息类型支持（文本、图片、文件等）
    - 可以添加群组消息功能