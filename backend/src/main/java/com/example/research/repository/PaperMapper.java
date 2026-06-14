package com.example.research.repository;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.research.entity.Paper;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import java.util.List;

@Mapper
public interface PaperMapper extends BaseMapper<Paper> {

    @Select("SELECT *, `abstract` AS abstrakt FROM paper WHERE aminer_id = #{aminerId} AND deleted = 0 LIMIT 1")
    Paper findByAminer(@Param("aminerId") String aminerId);

    @Select("""
            <script>
            SELECT *, `abstract` AS abstrakt FROM paper
            WHERE deleted = 0
              AND (
                MATCH(title, abstract) AGAINST(#{keyword} IN BOOLEAN MODE)
                OR
                LOWER(title) LIKE CONCAT('%', LOWER(#{keyword}), '%')
                OR LOWER(`abstract`) LIKE CONCAT('%', LOWER(#{keyword}), '%')
                OR LOWER(COALESCE(authors, '')) LIKE CONCAT('%', LOWER(#{keyword}), '%')
                OR LOWER(COALESCE(keywords, '')) LIKE CONCAT('%', LOWER(#{keyword}), '%')
                OR LOWER(COALESCE(venue, '')) LIKE CONCAT('%', LOWER(#{keyword}), '%')
              )
              <if test="yearFrom != null">AND year >= #{yearFrom}</if>
            ORDER BY
              <choose>
                <when test="sortBy == 'citation' or sortBy == 'cited'">citation_count DESC, year DESC</when>
                <when test="sortBy == 'year'">year DESC, citation_count DESC</when>
                <when test="sortBy == 'relevance'">
                  MATCH(title, abstract) AGAINST(#{keyword} IN BOOLEAN MODE) DESC, citation_count DESC
                </when>
                <otherwise>citation_count DESC, year DESC</otherwise>
              </choose>
            LIMIT #{limit}
            </script>
            """)
    List<Paper> searchByKeywordExpanded(@Param("keyword") String keyword, @Param("limit") int limit, @Param("yearFrom") Integer yearFrom, @Param("sortBy") String sortBy);

    @Select("<script>SELECT *, `abstract` AS abstrakt FROM paper WHERE aminer_id IN <foreach item='id' collection='aminers' open='(' separator=',' close=')'>#{id}</foreach> AND deleted = 0</script>")
    List<Paper> findByAminers(@Param("aminers") List<String> aminers);

    @Select("<script>SELECT *, `abstract` AS abstrakt FROM paper WHERE id IN <foreach item='id' collection='ids' open='(' separator=',' close=')'>#{id}</foreach> AND deleted = 0</script>")
    List<Paper> findByIds(@Param("ids") List<Long> ids);
}
