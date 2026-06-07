package com.example.research.repository;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.research.entity.Comment;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;
import java.util.Map;

@Mapper
public interface CommentMapper extends BaseMapper<Comment> {

    @Select("<script>" +
            "SELECT post_id, COUNT(*) AS cnt FROM comment WHERE post_id IN " +
            "<choose>" +
            "<when test='postIds != null and postIds.size() > 0'>" +
            "<foreach collection='postIds' item='id' open='(' separator=',' close=')'>#{id}</foreach>" +
            "</when>" +
            "<otherwise>(NULL)</otherwise>" +
            "</choose>" +
            " AND status = 1 GROUP BY post_id" +
            "</script>")
    List<Map<String, Object>> batchCountReplies(@Param("postIds") List<Long> postIds);
}
