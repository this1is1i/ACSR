# 每日变更记录（续）

> 续接 `EarlyChange.md`，记录 2026-06-07 起的改动。

---

## 2026-06-07

### 核心目标
排序质量门控+归一化上线、数据库整改实施、兴趣去重、资料编辑增强、注册页完善、UI精简。

### 排序管线重构（rl-service/）

| 操作 | 文件 | 说明 |
|------|------|------|
| 重写 | `recommender/ranker.py` | 三步流水线：原始得分 → 质量门控（OR逻辑，min_cos=0.05 / min_actor=0.001）→ 逐项 min-max 归一化 → 加权求和。新增 `_minmax_normalize()` 静态方法，全等时赋 0.5 中性分 |
| 修改 | `config.py` | +`min_cos_similarity=0.05`、+`min_actor_score=0.001` |

**问题**：Actor softmax 输出被压缩在均值 ~0.02，而余弦相似度轻松 0.7+，名义权重 50% 实际贡献不足 10%。
**效果**：归一化后三项在 [0,1] 公平竞争，名义权重 = 实际影响力。

### 数据库整改（backend/）

#### post 表去冗余计数器

| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `entity/Post.java` | 删除 `likeCount`/`replyCount` 字段 |
| 修改 | `repository/PostLikeMapper.java` | +`batchCountLikes(postIds)`，含空列表 `<choose>` 守卫 |
| 修改 | `repository/CommentMapper.java` | +`batchCountReplies(postIds)`，含空列表守卫 |
| 修改 | `service/impl/CommunityServiceImpl.java` | listPosts/searchPosts/listMyPosts 加批量计数；toggleLike 简化为纯 INSERT/DELETE；toPostItem/resolveComparator 增加 count maps |
| 修改 | `service/impl/AdminServiceImpl.java` | listPosts 加批量计数；toPostItem 增加 count maps；新增 `toCountMap()` |

#### 外键约束 + 字段可空

| 操作 | 文件 | 说明 |
|------|------|------|
| 新增 | `resources/db_migration.sql` | `post.reviewed_by→user.id` FK(`ON DELETE SET NULL`)；`rl_training_log.user_id→user.id` FK(`ON DELETE SET NULL`)；`rl_training_log.user_id` 改为可空；DROP `post.like_count`/`post.reply_count` |

#### 兴趣去重

| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `service/impl/UserServiceImpl.java` | `updateProfile()` 先删旧 `register`/`profile_update` 记录再插入，用 `Set<String>` 去重；`register()` 同样去重；`getProfile()`/`searchUsers()` 返回去重标签；新增 `deduplicateTags()` 私有方法；新增 `changePassword()` 方法 |
| 修改 | `repository/UserInterestHistoryMapper.java` | +`deleteByUserIdAndSource()` 按来源删除 |
| 修改 | `service/UserService.java` | +`changePassword()` 接口 |
| 新增 | `dto/UserDto.ChangePasswordRequest` | `{oldPassword, newPassword}` 带 `@NotBlank`/`@Size` 校验 |
| 新增 | `controller/UserController.java` | `PUT /api/user/password` 端点 |
| 数据清洗 | MySQL | `user_interest_history` 表全量清空，根据 `user.research_interests` 重新插入 13 用户 × 2~3 标签 = 33 条无重复记录（source='register', weight=0.5） |

### RL 训练日志激活（rl-service/）

| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `train.py` | `train()` 返回 `(agent, metrics)` 含 `total_episodes`/`best_reward`/`final_avg_loss`/`model_version`；训练结束后调用 `MySQLDataSource.insert_training_log()` 写入 MySQL |
| 修改 | `data/mysql_data.py` | `insert_training_log()` 新增 `user_id=None` 参数（系统训练不关联用户） |
| 修改 | `api/server.py` | `_run_train` 解包 metrics；更新 `_training_status["best_reward"]` 和 `last_episode`（修复先前用 config.max_episodes 的错误值） |

### 前端功能增强

#### 资料编辑页（EditProfile.vue）

| 操作 | 说明 |
|------|------|
| 重写布局 | 拆为两张卡片：基本信息 + 修改密码 |
| 新增 | 修改密码卡片：原密码/新密码/确认新密码 → `PUT /api/user/password` → 成功后清登录态跳转登录页 |
| 修改 | 研究方向选择器：Neo4j 不可用时自动回退 24 个硬编码常用 CS 关键词，不再显示文本框回退 |

#### 注册/登录页（Login.vue）

| 操作 | 说明 |
|------|------|
| 新增 | 确认密码字段，提交时校验一致性 |
| 修改 | 研究方向选择器：同上硬编码回退方案，移除文本框回退 |
| 修复 | 上轮编辑误删 `const form = reactive(...)` 导致页面白屏，已补回 |

#### UI 精简

| 操作 | 文件 | 说明 |
|------|------|------|
| 删除 | `views/Profile.vue` | "分享主页"按钮及 `shareProfile()` 函数 |
| 修改 | `components/Sidebar.vue` | "知识图谱"导航项仅对已登录用户显示（游客不可见） |
| 删除 | `views/RealtimeChat.vue` | 底部"连接：已连接/未连接"状态文字及 CSS |

#### 管理员后台（AdminConsole.vue）

| 操作 | 说明 |
|------|------|
| 新增 | "模型训练"tab：训练轮数选择 + 触发按钮 → 2s 轮询 `GET /model/info` → 完成弹窗展示 best_reward/model_version/耗时 |
| 新增 | `frontend/src/api/recommend.js`：`triggerTraining(episodes)`、`getModelInfo()` |
| 修复 | 论文导入：`authors`/`keywords` 字段自动将逗号分隔字符串转为数组再提交（兼容两种格式） |

### 文档维护

| 操作 | 文件 | 说明 |
|------|------|------|
| 更新 | `CLAUDE.md` | 排序流程（三步归一化）、Config 参数表、社区模型（动态计数）、训练流程、数据库迁移脚本 |
| 删除 | `docs/QA.md` | 已被 v1/v2 替代 |
| 新增 | `docs/QA_..._v2.md` Q37 | 密码加密机制（BCrypt strength=10）+ 三组测试账号明文密码 |
| 更新 | `docs/QA_..._v2.md` | Q23→已上线；Q31 Q3→rl_training_log 已激活；Q32 任务4→已实施；Q21→冗余计数器+缺外键标记 ✅ |
| 更新 | `docs/QA_..._v1.md` | like_count 引用改为实时 COUNT；ER 表描述同步 |

### 已修复 Bug（按发现顺序）

1. **Login 页面白屏** — `const form` 行被编辑覆盖丢失，补回后恢复
2. **Profile 页 500 错误** — `batchCountLikes`/`batchCountReplies` 空列表生成 `WHERE post_id IN ` 非法 SQL，添加 `<choose><when>` 守卫
3. **论文导入 JSON 解析失败** — 前端发送 `"authors": "Zhang San, Li Si"`（字符串）而 Jackson 期望数组，添加前端自动转换逻辑
4. **训练日志未写入 MySQL** — `insert_training_log` 使用 `user_id=0` 违反 FK 约束，改为 `user_id=None` 并将列改为可空
5. **兴趣标签大量重复** — `updateProfile()` 只增不删，改为先删后插 + Set 去重
6. **注册页关键词选择器未生效** — Neo4j 不可用导致 API 返回空列表 → 前端回退文本框，改为硬编码 24 个常用关键词兜底

### 当前服务状态
- **启动顺序**: RL service (:8000) → Backend (:8080) → Frontend (:5173)
- **Neo4j**: `bolt://localhost:7687`, user=neo4j, pass=seeworld123
- **MySQL**: `research_db`, user=root, pass=qwer1234
- **测试账号密码**: 老用户 `admin123`（id 1-10），认领用户 `123456`（id 11-16），注册用户 `qwer1234`（id 17）

---

## 2026-06-11

### 核心目标
项目整理：死文件清理、数据库 schema 回归单一来源、测试脚本归位、文档补全。

### 数据库 schema 整理

| 操作 | 文件 | 说明 |
|------|------|------|
| 删除 | `resources/db_migration.sql` | 迁移脚本已整合入 `research_db.sql`，消除 schema 双源问题 |
| 删除 | `resources/seed_claim_test_data.sql` | 测试种子数据脚本，非生产用途 |

### 脚本归位

| 操作 | 文件 | 说明 |
|------|------|------|
| 迁移 | `evaluate.py` → `scripts/evaluate.py` | 离线评估脚本归入 scripts/ 目录，与其他工具脚本统一管理 |

### 死文件清理

| 类别 | 数量 | 说明 |
|------|------|------|
| draw.io 自动备份 | 21 | `docs/draw/.$*.drawio.bkp` — Office 编辑产生的临时文件 |
| 孤儿字节码 | ~60 | `rl-service/**/__pycache__/` — 含已删除模块 `data_importer.py`/`preprocess.py`/`explain.py` 的残留 `.pyc` |
| 空目录 | 3 | `frontend/src/assets/`、`components/community/`、`components/profile/` |

### 文档建设

| 操作 | 文件 | 说明 |
|------|------|------|
| 新增 | `docs/说明文档.md` | 12 章从零部署指南（前置依赖→数据库→Neo4j→三端启动→验证→FAQ） |
| 新增 | `docs/说明文档.docx` | pandoc 转换的 Word 版本 |
| 新增 | `docs/draw/21-forum-flow.drawio` | 论坛功能流转图（三泳道：普通用户/管理员/系统层） |
| 新增 | `docs/draw/22-admin-functions.drawio` | 管理员四大功能模块图（帖子审核/用户管理/论文导入/模型训练） |
| 更新 | `CLAUDE.md` | DB 表数 14→13、删除 seed/migration 引用、evaluate.py 路径更新、drawio 图 16→21、收藏双写说明 |
| 更新 | `README.md` | 同上同步 + 新增 drawio 图表索引 + evaluate.py 路径 |

### 已修复 Bug（按发现顺序）

1. **CLAUDE.md 表计数错误** — `research_db.sql` 实际 13 张表，误写为 14
2. **Git 追踪 18 个 .bkp 死文件** — 已 `git rm` 全部 21 个备份文件
3. **`evaluate.py` 路径散乱** — 从根目录移至 `scripts/` 统一管理
4. **`db_migration.sql` 造成 schema 双源** — 删除后以 `research_db.sql` 为唯一权威

---

## 2026-06-11（续）

### 核心目标
QA 文档知识库建设：Obsidian 标签 + wikilink + MOC 索引 + MkDocs 静态站配置。

### 文档知识库建设

| 操作 | 文件 | 说明 |
|------|------|------|
| 新增 | `scripts/tag_qa.py` | 批量为 4 个 QA 文件（Q0-Q51）的每个 Q# 标题添加 `**标签**` + `**关联**` wikilink 元数据 |
| 新增 | `docs/索引.md` | MOC 内容地图，14 个主题簇（架构/推荐/RL训练/特征工程/KG/学习路径/DB/前端/私信/安全/异步/评估/审计/理论） |
| 新增 | `mkdocs.yml` | MkDocs Material 配置，含搜索、导航、深色模式；`mkdocs build` 即生成静态文档站 |

### Obsidian 使用方式

1. 用 Obsidian 打开 `docs/` 作为 Vault
2. 图视图可展示 Q# 间的引用网络（每个 Q 的 `**关联**` wikilink 自动生成连线）
3. `Ctrl+O` 搜索任意 Q# 或主题标签
4. 标签格式 `#推荐 #Actor-Critic` 会被 Obsidian 识别为可搜索标签

### MkDocs 静态站构建

```bash
pip install mkdocs-material
cd ACScientificRecommendation
mkdocs build          # 生成 site/ 目录，可部署到任意静态托管
mkdocs serve          # 本地预览 http://localhost:8000

---

## 2026-06-14

### 核心目标
搜索筛选修复、实时私信在线状态实装、学习路径最优三节点播放、首页路径卡片同步。

### 搜索筛选修复

| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `frontend/src/views/Search.vue` | `updateFilter()` 改为筛选变化后自动触发 `handleSearch()` 重新请求 API（之前只改本地状态不搜索）; `timeMap` 改为动态计算 `new Date().getFullYear()` |
| 修改 | `frontend/src/components/search/SearchFilterRail.vue` | 排序下拉补上缺失的 `影响力` 选项 |
| 修改 | `backend/.../service/impl/PaperServiceImpl.java` | 图谱搜索路径 `sortBy` 补齐 `"relevance"`（保持原序）和 `"cited"`（按引用数）处理 |
| 修改 | `backend/.../repository/PaperMapper.java` | SQL 中 `sortBy='relevance'` 改为用 MySQL fulltext MATCH 分数排序; `'cited'` 与 `'citation'` 统一 |

### 实时私信在线状态

| 操作 | 文件 | 说明 |
|------|------|------|
| 重写 | `backend/.../controller/MessageWebSocketController.java` | 新增 `ConcurrentHashMap<Long,String> onlineUsers` 在线用户表; `/user-online` 记录 sessionId 并广播状态; 新增 `@EventListener SessionDisconnectEvent` 处理断线广播离线; 初始在线列表改为 `/topic/user-status` 公共频道广播 `init_snapshot` 解决 `convertAndSendToUser` 无 STOMP Principal 问题 |
| 修改 | `backend/.../controller/MessageWebSocketController.java` | `handlePrivateMessage` 移除重复 DB 保存（仅负责实时转发）; 转发消息补 `senderId` + `time` 字段 |
| 修改 | `frontend/src/views/RealtimeChat.vue` | 在线文案改为"同步协作中，在线消息模式"/"异步协作中，离线消息模式"; 去掉冗余的第二颗 pill; `handleIncoming` 新增去重检查; `/topic/user-status` 处理器统一处理 `init_snapshot` 批量填充 |
| 修改 | `frontend/src/components/chat/ConversationRail.vue` | 在线文案改为"同步协作中"/"离线" |
| 修改 | `frontend/vite.config.js` | 新增 `/ws-messages` WebSocket 代理到 `:8080`（`ws: true`） |
| 修改 | `frontend/src/router/index.js` | `beforeEach` 跳过 `/ws-messages/iframe.html` 等 SockJS 内部路径 |

### 学习路径最优三节点

| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `rl-service/learning_path/path_builder.py` | `LearningPath` 新增 `best_path`（label 链）+ `best_path_ids`（ID 链）; 新增 `get_best_path_chain()` 方法: BFS（需 ≥3 个 kw_* 节点才采纳）+ 层级回退（始终 3 节点去重）; `to_dict()` 输出两字段 |
| 修改 | `rl-service/api/server.py` | `LearningPathResponse` 新增 `best_path` + `best_path_ids` |
| 修改 | `rl-service/knowledge_graph/graph_query.py` | `shortest_path()` 改为双向 BFS（同时遍历 `_adj` + `_rev_adj`），使 keyword 节点能通过入边逆向行走 |
| 修改 | `backend/.../client/PythonRecClient.java` | `LearningPathResponse` 新增 `bestPath` + `bestPathIds` |
| 修改 | `backend/.../service/impl/VisualizationServiceImpl.java` | `route` 优先取 `bestPathIds`（3 个），为空回退全部节点; 传递 `bestPath` |
| 修改 | `frontend/src/utils/path.js` | `buildLearningPathSummary` 新增 `bestPathChain`/`bestPathDisplay`/`bestPathIds`; `bestPathChain` 优先 Python 标签，兜底从 route ID 反查节点名 |
| 修改 | `frontend/src/components/path/PathInsightRail.vue` | 第一个卡片新增"当前学习路径"文字链显示（如 `RL → Deep Learning → Transfer Learning`），空状态显示引导提示; 推进节奏/关键资源在未选主题时隐藏 |
| 修改 | `frontend/src/views/KnowledgeGraph.vue` | `onMounted` 从 sessionStorage 恢复已选主题; `onSelectTargetTopic` 写入 sessionStorage 持久化 |

### 首页路径卡片

| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `frontend/src/views/Home.vue` | 从 sessionStorage 读取 `kg_selected_topic` 并传给可视化 API; 新增 `currentTargetTopic` ref 传给 `LearningPathPanel` |
| 修改 | `frontend/src/components/home/LearningPathPanel.vue` | 未选主题时显示 🎯"请选择要学习的目标" 引导提示（含知识图谱页链接），已选时渲染完整路径卡片 |

### CLAUDE.md 更新

| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `CLAUDE.md` | 新增 Docs 命令（`mkdocs serve/build`、QA 脚本）; CI/CD 节（GitHub Actions）; Obsidian↔MkDocs 管线架构; 已知限制条目标注 Q52 前向引用; MCP 配置扩展 |
```
