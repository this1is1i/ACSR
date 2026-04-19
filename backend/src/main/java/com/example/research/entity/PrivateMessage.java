package com.example.research.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 用户私信表
 */
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

    @TableField("msg_type")
    private Integer msgType = 1; // 1=文本 2=图片 3=链接

    @TableField("is_read")
    private Boolean isRead = false;

    @TableField("read_time")
    private LocalDateTime readTime;

    private Integer status = 1; // 0=已撤回 1=正常

    @TableField("create_time")
    private LocalDateTime createTime;

    // 非数据库字段
    @TableField(exist = false)
    private User sender;

    @TableField(exist = false)
    private User receiver;
}
