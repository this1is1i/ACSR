package com.example.research.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 用户联系人/关注表
 */
@Data
@TableName("user_contacts")
public class UserContact {

    @TableId(type = IdType.AUTO)
    private Long id;

    @TableField("user_id")
    private Long userId;

    @TableField("contact_id")
    private Long contactId;

    @TableField("relation_type")
    private String relationType = "FOLLOW"; // FOLLOW=关注 FRIEND=好友 COLLABORATOR=合作者

    private String remark;

    @TableField("create_time")
    private LocalDateTime createTime;

    // 非数据库字段
    @TableField(exist = false)
    private User contact;

    @TableField(exist = false)
    private Long unreadCount;

    @TableField(exist = false)
    private String lastMessage;
}
