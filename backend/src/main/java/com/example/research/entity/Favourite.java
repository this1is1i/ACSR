package com.example.research.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 用户论文收藏表
 */
@Data
@TableName("favourite")
public class Favourite {

    @TableId(type = IdType.AUTO)
    private Long id;

    @TableField("user_id")
    private Long userId;

    @TableField("paper_id")
    private Long paperId;

    @TableField("folder_name")
    private String folderName = "默认收藏夹";

    private String remark;

    @TableField("create_time")
    private LocalDateTime createTime;
}
