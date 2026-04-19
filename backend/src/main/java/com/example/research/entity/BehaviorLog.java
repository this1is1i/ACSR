package com.example.research.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("behavior_log")
public class BehaviorLog {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long userId;
    private Long paperId;
    private String action;
    private Integer duration;
    private String source;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime timestamp;
}
