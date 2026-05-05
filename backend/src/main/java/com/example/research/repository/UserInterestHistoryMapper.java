package com.example.research.repository;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.research.entity.UserInterestHistory;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import java.util.List;
import java.util.Map;

@Mapper
public interface UserInterestHistoryMapper extends BaseMapper<UserInterestHistory> {

    @Select("SELECT * FROM user_interest_history WHERE user_id = #{userId} ORDER BY record_date ASC")
    List<UserInterestHistory> findByUserId(@Param("userId") Long userId);

    @Select("SELECT interest_tag, " +
            "DATE_FORMAT(record_date, '%Y-%m') AS month, " +
            "AVG(weight) AS avg_weight " +
            "FROM user_interest_history " +
            "WHERE user_id = #{userId} " +
            "GROUP BY interest_tag, DATE_FORMAT(record_date, '%Y-%m') " +
            "ORDER BY month ASC, interest_tag")
    List<Map<String, Object>> findMonthlyAggregation(@Param("userId") Long userId);
}
