package com.example.research.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("paper_author_claim")
public class PaperAuthorClaim {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long paperId;
    private Long userId;
    private String authorName;
    private String matchMethod;
    private Double confidence;
    private Integer status;
    private LocalDateTime respondedAt;
    private String adminNote;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;
}
