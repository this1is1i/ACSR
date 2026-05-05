package com.example.research.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDate;
import java.time.LocalDateTime;

@Data
@TableName("user_interest_history")
public class UserInterestHistory {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long userId;
    private String interestTag;
    private Double weight;
    private String source;
    private LocalDate recordDate;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
}
