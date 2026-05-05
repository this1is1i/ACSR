package com.example.research.repository;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.research.entity.BrowseHistory;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import java.util.List;
import java.util.Map;

@Mapper
public interface BrowseHistoryMapper extends BaseMapper<BrowseHistory> {

    @Select("SELECT DAYOFWEEK(browse_date) AS day_of_week, COUNT(*) AS cnt " +
            "FROM browse_history " +
            "WHERE user_id = #{userId} " +
            "GROUP BY DAYOFWEEK(browse_date) " +
            "ORDER BY day_of_week")
    List<Map<String, Object>> countByDayOfWeek(@Param("userId") Long userId);
}
