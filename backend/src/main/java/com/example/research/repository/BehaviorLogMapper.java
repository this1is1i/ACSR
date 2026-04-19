package com.example.research.repository;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.research.entity.BehaviorLog;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import java.util.List;

@Mapper
public interface BehaviorLogMapper extends BaseMapper<BehaviorLog> {

    @Select("SELECT DISTINCT paper_id FROM (" +
            "SELECT paper_id, timestamp FROM behavior_log " +
            "WHERE user_id = #{userId} ORDER BY timestamp DESC LIMIT #{limit}" +
            ") t")
    List<Long> findInteractedPaperIds(@Param("userId") Long userId, @Param("limit") int limit);
}
