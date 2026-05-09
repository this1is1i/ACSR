package com.example.research.service.impl;

import com.example.research.service.KnowledgeService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.*;

/**
 * 知识图谱服务——已废弃 MySQL kg_entity/kg_relation 数据源，
 * 改为由 VisualizationServiceImpl 通过 Python /learning-path 提供图谱数据。
 * 保留空实现，避免 /api/knowledge/graph 端点 500 错误。
 */
@Slf4j
@Service
public class KnowledgeServiceImpl implements KnowledgeService {

    @Override
    public Map<String, Object> getGraph() {
        log.debug("KnowledgeService.getGraph() 已废弃——图谱数据现由 Python /learning-path 提供");
        Map<String, Object> empty = new HashMap<>();
        empty.put("nodes", List.of());
        empty.put("edges", List.of());
        return empty;
    }

    /**
     * 将掌握度 [0,1] 映射为 HEX 颜色字符串，与 Python propagation.py 的 _mastery_to_color 一致。
     * 蓝(0.0) -> 橙(0.5) -> 绿(1.0)
     */
    public static String masteryToColor(double mastery) {
        double m = Math.max(0, Math.min(1, mastery));
        int r, g, b;
        if (m <= 0.5) {
            double t = m / 0.5;
            r = (int) Math.round(0x3B + (0xF5 - 0x3B) * t);
            g = (int) Math.round(0x82 + (0x9E - 0x82) * t);
            b = (int) Math.round(0xF6 + (0x0B - 0xF6) * t);
        } else {
            double t = (m - 0.5) / 0.5;
            r = (int) Math.round(0xF5 + (0x10 - 0xF5) * t);
            g = (int) Math.round(0x9E + (0xB9 - 0x9E) * t);
            b = (int) Math.round(0x0B + (0x81 - 0x0B) * t);
        }
        return String.format("#%02X%02X%02X", r, g, b);
    }
}
