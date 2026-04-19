package com.example.research.repository;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.research.entity.PrivateMessage;
import org.apache.ibatis.annotations.Mapper;

/**
 * 私信数据访问层
 */
@Mapper
public interface PrivateMessageMapper extends BaseMapper<PrivateMessage> {
}
