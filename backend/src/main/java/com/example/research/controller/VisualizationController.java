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

        // knowledge graph – 3D learning path visualization data
        // Node types: "keyword"=sphere, "paper"=box; mastery 0→1 maps blue→orange→green
        List<Map<String, Object>> kgNodes = new java.util.ArrayList<>();
        // depth 0 – mastered foundations
        kgNodes.add(Map.of("id","kw_ml","name","Machine Learning","type","keyword","mastery",0.92,"depth",0,"group","foundation"));
        kgNodes.add(Map.of("id","kw_dl","name","Deep Learning","type","keyword","mastery",0.85,"depth",0,"group","foundation"));
        kgNodes.add(Map.of("id","kw_prob","name","Probability & Statistics","type","keyword","mastery",0.88,"depth",0,"group","foundation"));
        kgNodes.add(Map.of("id","kw_optim","name","Optimization","type","keyword","mastery",0.80,"depth",0,"group","foundation"));
        // depth 1 – intermediate
        kgNodes.add(Map.of("id","kw_rl","name","Reinforcement Learning","type","keyword","mastery",0.65,"depth",1,"group","intermediate"));
        kgNodes.add(Map.of("id","kw_nn","name","Neural Networks","type","keyword","mastery",0.70,"depth",1,"group","intermediate"));
        kgNodes.add(Map.of("id","kw_cnn","name","CNN","type","keyword","mastery",0.68,"depth",1,"group","intermediate"));
        kgNodes.add(Map.of("id","kw_rnn","name","RNN / LSTM","type","keyword","mastery",0.55,"depth",1,"group","intermediate"));
        kgNodes.add(Map.of("id","kw_mdp","name","Markov Decision Process","type","keyword","mastery",0.50,"depth",1,"group","intermediate"));
        // depth 2 – target topics
        kgNodes.add(Map.of("id","kw_ac","name","Actor-Critic","type","keyword","mastery",0.40,"depth",2,"group","target"));
        kgNodes.add(Map.of("id","kw_pg","name","Policy Gradient","type","keyword","mastery",0.35,"depth",2,"group","target"));
        kgNodes.add(Map.of("id","kw_dqn","name","Deep Q-Network","type","keyword","mastery",0.45,"depth",2,"group","target"));
        kgNodes.add(Map.of("id","kw_trans","name","Transformer","type","keyword","mastery",0.30,"depth",2,"group","target"));
        kgNodes.add(Map.of("id","kw_gnn","name","Graph Neural Network","type","keyword","mastery",0.20,"depth",2,"group","target"));
        kgNodes.add(Map.of("id","kw_nlp","name","NLP","type","keyword","mastery",0.25,"depth",2,"group","target"));
        // depth 3 – paper nodes
        kgNodes.add(Map.of("id","p_dqn","name","Playing Atari with Deep RL","type","paper","mastery",0.75,"depth",3,"group","paper","year",2013));
        kgNodes.add(Map.of("id","p_a3c","name","Asynchronous Actor-Critic (A3C)","type","paper","mastery",0.10,"depth",3,"group","paper","year",2016));
        kgNodes.add(Map.of("id","p_ppo","name","Proximal Policy Optimization","type","paper","mastery",0.05,"depth",3,"group","paper","year",2017));
        kgNodes.add(Map.of("id","p_sac","name","Soft Actor-Critic","type","paper","mastery",0.0,"depth",3,"group","paper","year",2018));
        kgNodes.add(Map.of("id","p_att","name","Attention Is All You Need","type","paper","mastery",0.60,"depth",3,"group","paper","year",2017));
        kgNodes.add(Map.of("id","p_bert","name","BERT: Pre-training of Transformers","type","paper","mastery",0.15,"depth",3,"group","paper","year",2019));
        kgNodes.add(Map.of("id","p_gcn","name","Semi-Supervised GCN","type","paper","mastery",0.0,"depth",3,"group","paper","year",2017));
        kgNodes.add(Map.of("id","p_gat","name","Graph Attention Networks","type","paper","mastery",0.0,"depth",3,"group","paper","year",2018));

        List<Map<String, Object>> kgEdges = new java.util.ArrayList<>();
        // foundation → intermediate
        kgEdges.add(Map.of("source","kw_ml","target","kw_rl","weight",0.9));
        kgEdges.add(Map.of("source","kw_ml","target","kw_nn","weight",0.95));
        kgEdges.add(Map.of("source","kw_dl","target","kw_cnn","weight",0.9));
        kgEdges.add(Map.of("source","kw_dl","target","kw_rnn","weight",0.85));
        kgEdges.add(Map.of("source","kw_dl","target","kw_nn","weight",0.9));
        kgEdges.add(Map.of("source","kw_prob","target","kw_rl","weight",0.7));
        kgEdges.add(Map.of("source","kw_prob","target","kw_mdp","weight",0.85));
        kgEdges.add(Map.of("source","kw_optim","target","kw_nn","weight",0.75));
        kgEdges.add(Map.of("source","kw_optim","target","kw_rl","weight",0.65));
        // intermediate → target
        kgEdges.add(Map.of("source","kw_rl","target","kw_ac","weight",0.9));
        kgEdges.add(Map.of("source","kw_rl","target","kw_pg","weight",0.85));
        kgEdges.add(Map.of("source","kw_rl","target","kw_dqn","weight",0.88));
        kgEdges.add(Map.of("source","kw_mdp","target","kw_ac","weight",0.8));
        kgEdges.add(Map.of("source","kw_mdp","target","kw_dqn","weight",0.8));
        kgEdges.add(Map.of("source","kw_nn","target","kw_dqn","weight",0.7));
        kgEdges.add(Map.of("source","kw_nn","target","kw_trans","weight",0.75));
        kgEdges.add(Map.of("source","kw_nn","target","kw_gnn","weight",0.7));
        kgEdges.add(Map.of("source","kw_rnn","target","kw_nlp","weight",0.8));
        kgEdges.add(Map.of("source","kw_cnn","target","kw_gnn","weight",0.5));
        // target → papers
        kgEdges.add(Map.of("source","kw_dqn","target","p_dqn","weight",0.95));
        kgEdges.add(Map.of("source","kw_ac","target","p_a3c","weight",0.9));
        kgEdges.add(Map.of("source","kw_pg","target","p_ppo","weight",0.9));
        kgEdges.add(Map.of("source","kw_ac","target","p_sac","weight",0.85));
        kgEdges.add(Map.of("source","kw_pg","target","p_a3c","weight",0.7));
        kgEdges.add(Map.of("source","kw_trans","target","p_att","weight",0.95));
        kgEdges.add(Map.of("source","kw_nlp","target","p_bert","weight",0.9));
        kgEdges.add(Map.of("source","kw_trans","target","p_bert","weight",0.8));
        kgEdges.add(Map.of("source","kw_gnn","target","p_gcn","weight",0.95));
        kgEdges.add(Map.of("source","kw_gnn","target","p_gat","weight",0.9));
        // cross-paper citations
        kgEdges.add(Map.of("source","p_dqn","target","p_a3c","weight",0.6));
        kgEdges.add(Map.of("source","p_a3c","target","p_ppo","weight",0.5));
        kgEdges.add(Map.of("source","p_ppo","target","p_sac","weight",0.5));
        kgEdges.add(Map.of("source","p_att","target","p_bert","weight",0.7));
        kgEdges.add(Map.of("source","p_gcn","target","p_gat","weight",0.6));

        // learning path route – recommended traversal order
        Map<String, Object> learningPath = new HashMap<>();
        learningPath.put("topic", "Actor-Critic Methods");
        learningPath.put("estimatedHours", 28.0);
        learningPath.put("coverage", 0.42);
        learningPath.put("route", Arrays.asList(
            "kw_ml","kw_prob","kw_optim","kw_rl","kw_mdp","kw_ac","kw_pg","kw_dqn","p_dqn","p_a3c","p_ppo","p_sac"
        ));

        Map<String, Object> knowledge = new HashMap<>();
        knowledge.put("nodes", kgNodes);
        knowledge.put("edges", kgEdges);
        knowledge.put("learningPath", learningPath);
        payload.put("knowledge", knowledge);

        return Result.success(payload);
    }
}
