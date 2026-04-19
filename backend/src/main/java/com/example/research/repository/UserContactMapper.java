package com.example.research.repository;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.research.entity.UserContact;
import org.apache.ibatis.annotations.Mapper;

/**
 * 用户联系人数据访问层
 */
@Mapper
public interface UserContactMapper extends BaseMapper<UserContact> {
}
