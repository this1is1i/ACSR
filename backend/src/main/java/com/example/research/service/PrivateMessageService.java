package com.example.research.service;

import com.example.research.dto.CollaboratorRecommendation;
import com.example.research.entity.PrivateMessage;
import com.example.research.entity.UserContact;

import java.util.List;

/**
 * 私信服务接口
 */
public interface PrivateMessageService {

    /**
     * 发送私信
     */
    void sendMessage(Long senderId, Long receiverId, String content);

    /**
     * 标记消息为已读
     */
    void markAsRead(Long messageId, Long userId);

    /**
     * 获取与指定用户的聊天记录
     */
    List<PrivateMessage> getMessagesWithUser(Long userId, Long contactId);

    /**
     * 获取用户的所有对话列表
     */
    List<UserContact> getUserConversations(Long userId);

    /**
     * 获取推荐合作者（基于研究兴趣匹配，仅 RESEARCHER 角色有结果）
     */
    List<CollaboratorRecommendation> getRecommendedCollaborators(Long userId);
}
