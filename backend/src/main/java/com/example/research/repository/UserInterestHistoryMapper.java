package com.example.research.repository;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.research.entity.UserInterestHistory;
import org.apache.ibatis.annotations.Delete;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;
import java.util.Map;

@Mapper
public interface UserInterestHistoryMapper extends BaseMapper<UserInterestHistory> {

    /** 获取单个用户的所有兴趣标签（按权重降序）。用于替代 user.research_interests 字段。 */
    @Select("SELECT interest_tag FROM user_interest_history WHERE user_id = #{userId} ORDER BY weight DESC, record_date DESC")
    List<String> findTagsByUserId(@Param("userId") Long userId);

    /** 批量获取多个用户的兴趣标签。返回行含 user_id 和 interest_tag 两列。 */
    @Select("<script>" +
            "SELECT user_id, interest_tag FROM user_interest_history " +
            "WHERE user_id IN " +
            "<foreach collection='userIds' item='id' open='(' separator=',' close=')'>#{id}</foreach>" +
            " ORDER BY user_id, weight DESC" +
            "</script>")
    List<Map<String, Object>> findTagsByUserIds(@Param("userIds") List<Long> userIds);

    /** 删除指定用户指定来源的兴趣历史记录（用于更新时替换旧记录）。 */
    @Delete("DELETE FROM user_interest_history WHERE user_id = #{userId} AND source = #{source}")
    int deleteByUserIdAndSource(@Param("userId") Long userId, @Param("source") String source);
}
