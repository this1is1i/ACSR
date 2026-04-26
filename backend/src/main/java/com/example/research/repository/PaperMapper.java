package com.example.research.repository;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.research.entity.Paper;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import java.util.List;

@Mapper
public interface PaperMapper extends BaseMapper<Paper> {

    @Select("SELECT * FROM paper WHERE aminer_id = #{aminerId} AND deleted = 0 LIMIT 1")
    Paper findByAminer(@Param("aminerId") String aminerId);

    @Select("SELECT * FROM paper WHERE MATCH(title, abstract) AGAINST(#{keyword} IN BOOLEAN MODE) AND deleted = 0 LIMIT #{limit}")
    List<Paper> searchByKeyword(@Param("keyword") String keyword, @Param("limit") int limit);

    @Select("<script>SELECT * FROM paper WHERE aminer_id IN <foreach item='id' collection='aminers' open='(' separator=',' close=')'>#{id}</foreach> AND deleted = 0</script>")
    List<Paper> findByAminers(@Param("aminers") List<String> aminers);
}
