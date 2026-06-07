package com.example.research.repository;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.research.entity.Favourite;
import com.example.research.entity.Paper;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

@Mapper
public interface FavouriteMapper extends BaseMapper<Favourite> {

    @Select("SELECT p.*, p.`abstract` AS abstrakt FROM favourite f " +
            "JOIN paper p ON p.id = f.paper_id AND p.deleted = 0 " +
            "WHERE f.user_id = #{userId} " +
            "ORDER BY f.create_time DESC")
    List<Paper> findFavoritePapersByUserId(@Param("userId") Long userId);
}
