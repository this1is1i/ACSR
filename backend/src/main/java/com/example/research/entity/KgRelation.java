package com.example.research.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("kg_relation")
public class KgRelation {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long sourceId;
    private Long targetId;
    private String relationType;
    private Double weight;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
}
