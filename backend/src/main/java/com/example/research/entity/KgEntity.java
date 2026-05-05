package com.example.research.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("kg_entity")
public class KgEntity {
    @TableId(type = IdType.AUTO)
    private Long id;
    private String name;
    private String type;
    private String externalId;
    private String properties;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
}
