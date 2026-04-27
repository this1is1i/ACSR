package com.example.research.repository;

import org.apache.ibatis.annotations.Select;
import org.junit.jupiter.api.Test;

import java.lang.reflect.Method;

import static org.assertj.core.api.Assertions.assertThat;

class PaperMapperQueryTest {

    @Test
    void searchByKeywordExpanded_combines_fulltext_and_like_matching() throws NoSuchMethodException {
        Method method = PaperMapper.class.getMethod("searchByKeywordExpanded", String.class, int.class);
        Select select = method.getAnnotation(Select.class);

        assertThat(select).isNotNull();

        String sql = String.join(" ", select.value());

        assertThat(sql)
                .contains("MATCH(title, abstract) AGAINST(#{keyword} IN BOOLEAN MODE)")
                .contains("LOWER(title) LIKE CONCAT('%', LOWER(#{keyword}), '%')")
                .contains("LOWER(`abstract`) LIKE CONCAT('%', LOWER(#{keyword}), '%')")
                .contains("LOWER(COALESCE(authors, '')) LIKE CONCAT('%', LOWER(#{keyword}), '%')")
                .contains("LOWER(COALESCE(keywords, '')) LIKE CONCAT('%', LOWER(#{keyword}), '%')")
                .contains("LOWER(COALESCE(venue, '')) LIKE CONCAT('%', LOWER(#{keyword}), '%')");
    }
}
