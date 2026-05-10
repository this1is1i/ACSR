package com.example.research.repository;

import org.apache.ibatis.annotations.*;

@Mapper
public interface PostLikeMapper {

    @Insert("INSERT IGNORE INTO post_like (user_id, post_id) VALUES (#{userId}, #{postId})")
    int insertLike(@Param("userId") Long userId, @Param("postId") Long postId);

    @Delete("DELETE FROM post_like WHERE user_id = #{userId} AND post_id = #{postId}")
    int deleteLike(@Param("userId") Long userId, @Param("postId") Long postId);

    @Select("SELECT COUNT(*) FROM post_like WHERE user_id = #{userId} AND post_id = #{postId}")
    int existsLike(@Param("userId") Long userId, @Param("postId") Long postId);

    @Select("SELECT post_id FROM post_like WHERE user_id = #{userId}")
    java.util.List<Long> findLikedPostIds(@Param("userId") Long userId);
}
