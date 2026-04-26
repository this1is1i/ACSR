package com.example.research.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("comment")
public class Comment {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long postId;
    private Long userId;
    private Long parentId;
    private Long rootId;
    private String content;
    private Integer likeCount;
    private Integer isBest;
    private Integer status;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
