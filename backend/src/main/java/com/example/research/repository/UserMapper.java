package com.example.research.repository;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.research.entity.User;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

@Mapper
public interface UserMapper extends BaseMapper<User> {

    @Select("SELECT * FROM user WHERE username = #{username} AND deleted = 0 LIMIT 1")
    User findByUsername(String username);

    @Select("SELECT * FROM user WHERE deleted = 0 AND (username LIKE CONCAT('%', #{q}, '%') OR research_interests LIKE CONCAT('%', #{q}, '%')) ORDER BY username LIMIT #{limit}")
    List<User> searchUsers(@Param("q") String q, @Param("limit") int limit);
}
