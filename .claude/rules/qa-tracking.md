# QA 问答版本追踪规则

> 本文件继承自 [common/qa-tracking.md](../../../.claude/rules/common/qa-tracking.md) 系统级通用规则。此处仅列出本项目特定配置。

## 本项目的 QA 文件索引

| 文件 | Q# 范围 | 时间跨度 | 状态 |
|------|---------|---------|------|
| `docs/QA_2026-05-16_2026-06-02_v1.md` | Q0 – Q16 | 2026-05-16 → 2026-06-02 | 活跃 |
| `docs/QA_2026-06-02_2026-06-05_v2.md` | Q17 – Q37 | 2026-06-02 → 2026-06-07 | 活跃 |

## 模块 → Q# 映射（粗略）

| 代码路径 | 关联 Q# |
|---------|--------|
| `rl-service/recommender/ranker.py` | Q16, Q22, Q23, Q24 |
| `rl-service/models/actor.py` | Q2, Q5, Q20, Q24, Q25, Q26 |
| `rl-service/features/feature_builder.py` | Q18, Q33, Q36 |
| `rl-service/knowledge_graph/` | Q7, Q19, Q27, Q28 |
| `rl-service/train.py` | Q20, Q31, Q32 |
| `backend/.../entity/Post.java`, `post_like`, `comment` | Q10, Q21 |
| `backend/.../UserServiceImpl.java` | Q31, Q37 |
| `backend/.../CommunityServiceImpl.java` | Q3, Q4, Q21 |
| `frontend/src/store/`, `frontend/src/router/` | Q17 |
| `frontend/src/views/KnowledgeGraph.vue` | Q9, Q28 |
| `frontend/src/views/Login.vue` | Q1, Q37 |
