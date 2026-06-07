# QA 问答版本追踪规则

> 本文件继承自 [common/qa-tracking.md](../../../.claude/rules/common/qa-tracking.md) 系统级通用规则。此处仅列出本项目特定配置。

## 本项目的 QA 文件索引

| 文件 | Q# 范围 | 时间跨度 | 状态 |
|------|---------|---------|------|
| `docs/QA_2026-05-16_2026-06-02_v1.md` | Q0 – Q16 | 2026-05-16 → 2026-06-02 | 活跃 |
| `docs/QA_2026-06-02_2026-06-05_v2.md` | Q17 – Q37 | 2026-06-02 → 2026-06-07 | 活跃 |
| `docs/QA_2026-06-07_2026-06-08_v3.md` | Q38 – Q43 | 2026-06-07 → 2026-06-08 | 活跃 |

## 模块 → Q# 映射（粗略）

| 代码路径 | 关联 Q# |
|---------|--------|
| `rl-service/recommender/ranker.py` | Q16, Q22, Q23, Q24, Q42, Q43 |
| `rl-service/recommender/candidate_generator.py` | Q42, Q43 |
| `rl-service/models/actor.py` | Q2, Q5, Q20, Q24, Q25, Q26, Q38, Q42 |
| `rl-service/models/critic.py` | Q38 |
| `rl-service/agent.py` | Q38 |
| `rl-service/features/feature_builder.py` | Q18, Q33, Q36, Q42, Q43 |
| `rl-service/knowledge_graph/` | Q7, Q19, Q27, Q28, Q39 |
| `rl-service/learning_path/path_builder.py` | Q39 |
| `rl-service/learning_path/propagation.py` | Q39 |
| `rl-service/train.py` | Q20, Q31, Q32, Q38 |
| `rl-service/env/rec_env.py` | Q38 |
| `rl-service/utils/reward.py` | Q38 |
| `backend/.../controller/PrivateMessageController.java` | Q40 |
| `backend/.../controller/MessageWebSocketController.java` | Q40 |
| `backend/.../service/impl/PrivateMessageServiceImpl.java` | Q40 |
| `backend/.../entity/PrivateMessage.java` | Q40 |
| `backend/.../entity/UserContact.java` | Q40 |
| `backend/.../config/WebSocketConfig.java` | Q40 |
| `frontend/src/views/RealtimeChat.vue` | Q40 |
| `frontend/src/components/chat/ConversationRail.vue` | Q40 |
| `frontend/src/api/message.js` | Q40 |
| `backend/.../entity/Post.java`, `post_like`, `comment` | Q10, Q21 |
| `backend/.../UserServiceImpl.java` | Q31, Q37 |
| `backend/.../CommunityServiceImpl.java` | Q3, Q4, Q21 |
| `frontend/src/store/`, `frontend/src/router/` | Q17 |
| `frontend/src/views/KnowledgeGraph.vue` | Q9, Q28 |
| `frontend/src/views/Login.vue` | Q1, Q37 |
| `frontend/src/styles/tokens.css` | Q41 |
| `frontend/src/styles/layout-system.css` | Q41 |
| `frontend/src/style.css` | Q41 |
| `frontend/src/main.js` | Q41 |
