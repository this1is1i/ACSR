package com.example.research.repository;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.research.entity.PaperAuthorClaim;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;
import java.util.Map;

@Mapper
public interface PaperAuthorClaimMapper extends BaseMapper<PaperAuthorClaim> {

    @Insert("INSERT IGNORE INTO paper_author_claim (paper_id, user_id, author_name, match_method, confidence, status, create_time, update_time) " +
            "VALUES (#{paperId}, #{userId}, #{authorName}, #{matchMethod}, #{confidence}, #{status}, #{createTime}, #{updateTime})")
    int insertIgnore(PaperAuthorClaim claim);

    @Select("SELECT c.id AS claim_id, c.paper_id, c.author_name, c.match_method, c.confidence, " +
            "c.status, c.responded_at, c.create_time AS claim_time, " +
            "p.id AS paper_pk, p.title, p.authors, p.venue, p.year, p.aminer_id " +
            "FROM paper_author_claim c " +
            "JOIN paper p ON p.id = c.paper_id AND p.deleted = 0 " +
            "WHERE c.user_id = #{userId} AND c.status = #{status} " +
            "ORDER BY c.create_time DESC")
    List<Map<String, Object>> findByUserAndStatus(@Param("userId") Long userId, @Param("status") Integer status);
}
