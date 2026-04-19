package com.example.research.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("paper")
public class Paper {
    @TableId(type = IdType.AUTO)
    private Long id;
    private String aminerId;
    private String title;
    @TableField("`abstract`")
    private String abstrakt;   // 'abstract' is a Java keyword — mapped to column `abstract`
    private String keywords;
    private String authors;
    private String venue;
    private Integer year;
    private Integer citationCount;
    private String embedding;
    @TableLogic
    private Integer deleted;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;
}
