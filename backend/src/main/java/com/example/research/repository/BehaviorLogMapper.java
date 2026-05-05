package com.example.research.repository;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.research.entity.BehaviorLog;
import org.apache.ibatis.annotations.Delete;
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

    @Select("SELECT p.* FROM behavior_log bl " +
            "JOIN paper p ON p.id = bl.paper_id AND p.deleted = 0 " +
            "WHERE bl.user_id = #{userId} AND bl.action = 'favorite' " +
            "ORDER BY bl.timestamp DESC")
    List<com.example.research.entity.Paper> findFavoritesByUserId(@Param("userId") Long userId);

    @Select("SELECT bl.action, bl.timestamp, bl.duration, bl.source, " +
            "p.id AS paper_id, p.title AS paper_title " +
            "FROM behavior_log bl " +
            "JOIN paper p ON p.id = bl.paper_id AND p.deleted = 0 " +
            "WHERE bl.user_id = #{userId} " +
            "ORDER BY bl.timestamp DESC LIMIT #{limit}")
    List<java.util.Map<String, Object>> findRecentByUserId(@Param("userId") Long userId, @Param("limit") int limit);

    @Delete("DELETE FROM behavior_log WHERE user_id = #{userId}")
    int deleteByUserId(@Param("userId") Long userId);
}
