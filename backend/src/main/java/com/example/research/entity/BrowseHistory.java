package com.example.research.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDate;
import java.time.LocalDateTime;

@Data
@TableName("browse_history")
public class BrowseHistory {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long userId;
    private Long paperId;
    private Integer stayDuration;
    private LocalDate browseDate;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
}
