package com.example.research.controller;

import com.example.research.util.Result;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/api/visualization")
public class VisualizationController {

    @GetMapping("/data")
    public Result<Map<String, Object>> getVisualizationData() {
        Map<String, Object> payload = new HashMap<>();

        // stats
        Map<String, Object> stats = new HashMap<>();
        stats.put("readTime", "42.5h");
        stats.put("readTimeChange", "18%");
        stats.put("readCount", 128);
        stats.put("readCountChange", "24");
        stats.put("activeFields", 6);
        stats.put("activeFieldsChange", 2);
        stats.put("depth", 85.3);
        stats.put("depthChange", "5.2");
        payload.put("stats", stats);

        // interest trend (labels + datasets)
        List<String> labels = Arrays.asList("1月","2月","3月","4月","5月","6月","7月","8月","9月","10月","11月","12月");
        Map<String, Object> series1 = new HashMap<>();
        series1.put("label", "深度学习");
        series1.put("data", Arrays.asList(65,72,78,85,82,88,92,89,95,98,102,108));
        Map<String, Object> series2 = new HashMap<>();
        series2.put("label", "计算机视觉");
        series2.put("data", Arrays.asList(45,52,58,62,68,72,75,78,82,85,88,92));
        payload.put("interest", Map.of("labels", labels, "datasets", Arrays.asList(series1, series2)));

        // field distribution
        payload.put("field", Map.of(
                "labels", Arrays.asList("深度学习","计算机视觉","自然语言处理","强化学习","数据挖掘","其他"),
                "data", Arrays.asList(35,25,20,12,5,3)
        ));

        // heatmap (weekly counts)
        payload.put("heatmap", Map.of(
                "labels", Arrays.asList("周一","周二","周三","周四","周五","周六","周日"),
                "data", Arrays.asList(12,18,15,22,28,35,30)
        ));

        // tag cloud
        payload.put("tags", Arrays.asList(
                Map.of("text","深度学习","size",5),
                Map.of("text","神经网络","size",4),
                Map.of("text","计算机视觉","size",4),
                Map.of("text","Transformer","size",3),
                Map.of("text","强化学习","size",3),
                Map.of("text","GAN","size",3),
                Map.of("text","目标检测","size",2),
                Map.of("text","语义分割","size",2),
                Map.of("text","迁移学习","size",2),
                Map.of("text","联邦学习","size",1)
        ));

        // behaviors
        payload.put("behaviors", Arrays.asList(
                Map.of("icon","📖","title","平均阅读时长","desc","每篇论文停留时间","value","12.5 min"),
                Map.of("icon","🔖","title","收藏转化率","desc","阅读后收藏比例","value","34.2%"),
                Map.of("icon","🔄","title","重复阅读率","desc","多次查看的论文占比","value","18.7%"),
                Map.of("icon","⚡","title","峰值活跃时段","desc","最高频阅读时间","value","20:00-22:00")
        ));

        // knowledge graph nodes/edges
        payload.put("knowledge", Map.of(
                "nodes", Arrays.asList(
                        Map.of("id",1,"name","Machine Learning","mastery",0.8),
                        Map.of("id",2,"name","Reinforcement Learning","mastery",0.6),
                        Map.of("id",3,"name","Actor-Critic","mastery",0.5),
                        Map.of("id",4,"name","Deep Learning","mastery",0.7),
                        Map.of("id",5,"name","NLP","mastery",0.3),
                        Map.of("id",6,"name","Graph Neural Networks","mastery",0.2)
                ),
                "edges", Arrays.asList(
                        Map.of("source",1,"target",2),
                        Map.of("source",2,"target",3),
                        Map.of("source",1,"target",4),
                        Map.of("source",4,"target",5),
                        Map.of("source",4,"target",6)
                )
        ));

        return Result.success(payload);
    }
}
