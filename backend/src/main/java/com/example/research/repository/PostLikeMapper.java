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

    @Select("<script>" +
            "SELECT post_id, COUNT(*) AS cnt FROM post_like WHERE post_id IN " +
            "<choose>" +
            "<when test='postIds != null and postIds.size() > 0'>" +
            "<foreach collection='postIds' item='id' open='(' separator=',' close=')'>#{id}</foreach>" +
            "</when>" +
            "<otherwise>(NULL)</otherwise>" +
            "</choose>" +
            " GROUP BY post_id" +
            "</script>")
    java.util.List<java.util.Map<String, Object>> batchCountLikes(@Param("postIds") java.util.List<Long> postIds);
}
