package com.example.research.repository;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.research.entity.KgEntity;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import java.util.List;

@Mapper
public interface KgEntityMapper extends BaseMapper<KgEntity> {

    @Select("SELECT * FROM kg_entity WHERE type = 'KEYWORD' ORDER BY id")
    List<KgEntity> findAllKeywords();

    @Select("SELECT * FROM kg_entity WHERE type = 'PAPER' ORDER BY id")
    List<KgEntity> findAllPapers();

    @Select("<script>" +
            "SELECT * FROM kg_entity WHERE type IN " +
            "<foreach item='t' collection='types' open='(' separator=',' close=')'>#{t}</foreach>" +
            "</script>")
    List<KgEntity> findByTypes(@Param("types") List<String> types);

    @Select("SELECT * FROM kg_entity WHERE name = #{name} AND type = #{type} LIMIT 1")
    KgEntity findByNameAndType(@Param("name") String name, @Param("type") String type);
}
