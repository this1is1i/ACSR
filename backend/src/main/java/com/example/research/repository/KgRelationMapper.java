package com.example.research.repository;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.research.entity.KgRelation;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import java.util.List;

@Mapper
public interface KgRelationMapper extends BaseMapper<KgRelation> {

    @Select("SELECT * FROM kg_relation WHERE relation_type = #{relationType}")
    List<KgRelation> findByType(@Param("relationType") String relationType);

    @Select("<script>" +
            "SELECT * FROM kg_relation WHERE source_id IN " +
            "<foreach item='id' collection='entityIds' open='(' separator=',' close=')'>#{id}</foreach>" +
            " OR target_id IN " +
            "<foreach item='id' collection='entityIds' open='(' separator=',' close=')'>#{id}</foreach>" +
            "</script>")
    List<KgRelation> findByEntityIds(@Param("entityIds") List<Long> entityIds);
}
