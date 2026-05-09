# 每日变更记录

## 2026-05-08

### 核心目标
消除 Python 推荐服务的"假数据"问题，打通 MySQL + Neo4j 真实数据链路。

### 数据架构变更
- **MySQL**: 删除 `kg_entity` / `kg_relation` 表（与 Neo4j 冗余），新增 `user_feature_snapshot` 表（用户 RL 特征缓存）
- **Neo4j**: 5 类关系齐全（HAS_KEYWORD 4018、AUTHOR_OF 2470、CITE 1993、PUBLISH_IN 1005、CO_AUTHOR 310），1005 Paper 节点
- **数据流**: 用户特征从 MySQL behavior_log 读取，论文池从 Neo4j 加载，KG 嵌入从图结构实时计算

### Python 服务 (`rl-service/`)
| 操作 | 文件 | 说明 |
|------|------|------|
| 新增 | `data/mysql_data.py` | MySQL 数据访问层，读 behavior_log / user_interest_history |
| 重写 | `features/feature_builder.py` | 从 MySQL 真实数据构建用户向量（兴趣/历史/KG），支持缓存 |
| 修改 | `services/recommendation_service.py` | 注入 MySQLDataSource；KG 初始化支持 Neo4j 三级回退；推荐解释改用 KG 图结构 |
| 修改 | `config.py` | +MySQL 五参数配置段 |
| 新增 | `knowledge_graph/kg_embedder.py` | `create_kg_embedder()` 工厂函数 |
| 修改 | `knowledge_graph/graph_query.py` | 索引构建兼容大小写；修复 explain_recommendation 引用边匹配 |
| 修改 | `knowledge_graph/graph_storage.py` | `_edge_from_row` 统一 relation 小写规范化 |
| 修改 | `api/server.py` | 学习路径端点集成 KnowledgePropagation，返回 color/glowIntensity；训练触发 config 拷贝 |
| 修改 | `train.py` | KG 构建共享 create_kg_embedder |
| 新增 | `utils/text_utils.py` | clean_text / tokenize（从 preprocess.py 提取） |
| 删除 | `recommender/explain.py` | 模板解释被 GraphQuery.explain_recommendation 取代 |
| 删除 | `dataset/preprocess.py` | 有用部分迁移到 text_utils.py |
| 删除 | `dataset_pipeline.py` | 功能已被 RecommendationService 覆盖 |
| 删除 | 9 处空壳接口 | agent/candidate_generator/reward/logger/mock_data |

### Java 后端
| 操作 | 文件 | 说明 |
|------|------|------|
| 重写 | `KnowledgeServiceImpl.java` | 不再读 MySQL kg_entity/kg_relation，改由 Python 提供图谱数据 |
| 修改 | `VisualizationServiceImpl.java` | buildKnowledgeGraph 改为调 Python /learning-path；修复 N+1 查询；buildKeywordFrequencyMap 改用 interest_history |
| 修改 | `PythonRecClient.java` | 新增 LearningPathRequest/Response DTO 和 getLearningPath() 方法 |
| 修改 | `RecommendServiceImpl.java` | 添加诊断日志（pyResp 状态 / reason 预览） |
| 修改 | `KnowledgeController.java` | 节点数据透传 color/glowIntensity |

### Vue 前端
| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `KnowledgeGraph.vue` | 删除本地 masteryColor/masteryHex；3D 渲染改用 pathNodes/pathEdges；修复空数组 fallback |
| 修改 | `utils/path.js` | buildLearningPathSummary 透传 pathNodes |

### 已修复 Bug（按发现顺序）
1. `self._graph_query = None` 在 `_init_kg()` 之后执行 → 覆盖了已初始化的 GraphQuery
2. `train.py` 调用已删除的 `predict_for_api()` → crash
3. `KnowledgeGraph.vue` 空 `[]` 不触发 fallback（JS 中 [] 是 truthy）
4. `path_builder.py` 关键词可能被加上双重 `kw_` 前缀
5. `graph_query.py` edge.relation 大小写不匹配导致索引为空
6. N+1 查询：每条 behavior_log 逐一 selectById → 改为批量 findByIds
7. 全表扫描：`paperMapper.selectList(null)` → 改用 interest_history 聚合
8. mutable 全局 config：`train.py` 和 `server.py` 直接修改 `default_config`
9. `assembleFromPython` 中 paperId 可能为 null

### 当前服务状态
- **启动顺序**: RL service (:8000) → Backend (:8080) → Frontend (:5173)
- **Neo4j**: `bolt://localhost:7687`, user=neo4j, pass=seeworld123
- **MySQL**: `research_db`, user=root, pass=qwer1234
- **Python 服务启动日志关键行**: `GraphQuery 索引: paper_kw=..., KG 初始化完成` 确认数据链路正常

## 2026-05-09

### 核心目标
精简前端冗余模块、清理后端死代码、填充测试数据、补全游客浏览入口。

### 前端精简（删除 9 个布局模块）

| 编号 | 页面 | 删除模块 |
|------|------|---------|
| H2 | Home | HubHero 英雄区（指标卡片 + 操作按钮） |
| S2 | Search | PageHeader 标题栏（搜索状态徽章） |
| K2 | KnowledgeGraph | 页面标题栏（Future Lab header） |
| K4 | KnowledgeGraph | 时间筛选按钮（7d/30d/3m/6m/1y） |
| K5 | KnowledgeGraph | 4 张统计卡片（阅读时长/论文数/活跃领域/研究深度） |
| K6 | KnowledgeGraph | 兴趣演化趋势图（Chart.js 折线图） |
| K7 | KnowledgeGraph | 兴趣标签云 |
| PR6 | Profile | 个性化设置卡片（4 个 toggle 开关） |
| A2 | AdminConsole | PageHeader 标题栏 |

| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `views/Home.vue` | 删除 HubHero 引用和 heroMetrics 计算逻辑 |
| 修改 | `views/Search.vue` | 删除 PageHeader 引用 |
| 修改 | `views/KnowledgeGraph.vue` | 删除 K2/K4/K5/K6/K7 模板和 Chart.js 导入；保留 3D 知识图谱 + 学习路径 |
| 修改 | `views/Profile.vue` | 删除 PR6 设置卡片和相关 JS 逻辑 |
| 修改 | `views/AdminConsole.vue` | 删除 PageHeader 引用 |
| 修改 | `views/Login.vue` | 新增"游客模式"按钮，点击跳转 `/search` |
| 删除 | `components/home/HubHero.vue` | 已无引用 |
| 修改 | `package.json` | 移除 `chart.js`、`echarts` 依赖（均无代码引用） |

### 后端死代码清理

| 操作 | 文件 | 说明 |
|------|------|------|
| 重写 | `VisualizationServiceImpl.java` | 删除 6 个死方法（buildStats/buildInterestTrends/buildFieldDistribution/buildHeatmap/buildTagCloud/buildBehaviors）；移除 BrowseHistoryMapper/KgEntityMapper/UserMapper/ObjectMapper/KnowledgeService 注入；仅保留 buildKnowledgeGraph。375→123 行 |
| 删除 | `BrowseHistoryMapper.java` | 仅被已删除的 buildHeatmap 使用 |
| 删除 | `KgEntityMapper.java` | 无任何代码引用 |
| 删除 | `KgEntity.java` | 对应实体，无引用 |
| 修改 | `CLAUDE.md` | 更新 PythonRecClient 端点、知识图谱数据来源、数据库表、已知限制等章节 |

### 测试数据填充

在 MySQL `research_db` 中填入适量测试数据：

| 表 | 填充前 | 填充后 | 说明 |
|------|--------|--------|------|
| user | 3 | 8 | +5 用户（2 RESEARCHER + 2 STUDENT + 1 RESEARCHER） |
| behavior_log | 5 | 59 | +27 条 click/favorite/read 行为 |
| browse_history | 4 | 20 | +16 条浏览记录 |
| favourite | 0 | 10 | 收藏论文（Profile 页"我的收藏"使用） |
| board | 0 | 2 | 社区板块 |
| post | 5 | 15 | +5 社区帖子 |
| comment | 10 | 30 | +10 评论（含嵌套回复） |
| user_contacts | 5 | 13 | +8 联系人关系 |
| private_messages | 10 | 20 | +10 私信 |
| notification | 0 | 5 | 系统通知 |
| rl_training_log | 0 | 5 | 训练日志（episode 100→500） |
| user_feature_snapshot | 4 | 4 | 未变 |
| user_interest_history | 48 | 72 | +12 新用户兴趣记录 |

测试数据脚本：`backend/src/main/resources/seed_test_data.sql`

### Git 提交
`3a9d8ea` chore: finalize data architecture migration and repo cleanup → 推送到 `ACSR/main`

## 2026-05-10

### 核心目标
修复全局布局、精简页面死文本、补全游客模式、修正管理员审核逻辑、修复头像显示。

### 前端布局修复
**全局布局系统：**
| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `styles/layout-system.css` | 新增 `width: calc(100% - 288px - 24px)` 约束 main-content；980px 断点新增 `width: 100%` |
| 修改 | `vite.config.js` | 新增 `/uploads` 代理规则，头像图片可正确加载 |

**页面级布局修复：**
| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `views/KnowledgeGraph.vue` | CSS 重写：删除 100+ 行死规则（time-filter/stats-row/tag-cloud 等）；`.chart-card` 添加 `overflow: hidden`；`.node-detail` 添加 `position: relative`；移除与全局布局冲突的 scoped 规则 |
| 修改 | `views/Profile.vue` | 删除 `margin-left: 260px` 和 `padding` 覆盖；`.profile-card` 添加 `overflow: hidden` |
| 修改 | `views/Community.vue` | 删除 `margin-left: 260px` 覆盖 |
| 修改 | `views/EditProfile.vue` | 删除 `margin-left: 260px` 覆盖 |
| 修改 | `views/RealtimeChat.vue` | 删除 `margin-left: 260px` 覆盖 |
| 修改 | `components/home/RecommendationStream.vue` | 卡片添加 `overflow: hidden` |
| 修改 | `components/PaperCard.vue` | 卡片添加 `overflow: hidden`；`.title` 添加 `overflow-wrap: break-word`；`.paper-card__title-group` 添加 `min-width: 0` |
| 修改 | `components/RecommendList.vue` | `.recommend-list__stack` 添加 `min-width: 0` |
| 修改 | `views/Home.vue` | `.hub-layout` 添加 `overflow: hidden` |

### 前端页面精简

| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `views/Home.vue` | 删除顶部 header 卡片（标题 + 退出登录）；删除 `logout` 函数、`userName` computed、`useUserStore` |
| 删除 | `components/profile/ResearchAssetsPanel.vue` | 整个组件删除 |
| 修改 | `views/Profile.vue` | 删除 ResearchAssetsPanel 引用；删除 `getPathSurfaceData`/`buildLearningPathSummary` 调用；新增活动历史分页（10条/页，Element Plus `el-pagination`） |
| 修改 | `components/chat/ConversationRail.vue` | 删除 3 个静态占位面板（主题焦点/论文线索/协作路径）+ 70+ 行死代码 |
| 修改 | `views/Login.vue` | 新增"游客模式"按钮，点击跳转 `/search` |

### 死文本清理（7 个视图，16 处）
Home("Future Lab" eyebrow、描述文本)、Search(空状态文案)、Community(PageHeader eyebrow+description)、Profile("Future Lab" eyebrow、描述文本)、PaperDetail(PageHeader eyebrow+description)、RealtimeChat("Realtime Collaboration" eyebrow、REST/STOMP 技术描述、默认会话文本)、AdminConsole("Operations Deck" eyebrow、"保留原有后台操作流" 说明、演示 JSON 数据、cockpitDescription)

### 头像显示修复

| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `components/Sidebar.vue` | 新增 `<img>` 头像显示 + `.sidebar__avatar-img` CSS（`object-fit: cover`）；`onMounted` 移除 `!userInfo.value` 条件，始终调用 `fetchProfile()` 获取含 avatar 的完整资料 |
| 修改 | `vite.config.js` | 新增 `/uploads` 代理规则 |

### 3D 知识图谱边字段名修复
**Bug：** Python `path_builder.to_dict()` 输出 `src`/`dst`，前端读 `source`/`target` → 无边数据 → dagMode 无层级 → 节点聚在一起
**修复：** `KnowledgeGraph.vue` 边归一化增加 `l.src`/`l.dst` fallback

### 管理员审核功能修复

| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `views/AdminConsole.vue` | PENDING(0) → "通过"+"驳回"按钮；APPROVED(1)/REJECTED(2) → "撤回"按钮；撤回跳过审核备注弹窗；修复 `row.status` 整数/字符串比较 |
| 修改 | 同上 | 新增"查看"列 + 弹窗预览帖子内容（作者/标题/正文） |

### 数据库维护
- `post` 表去重：删除 5 条重复帖子（按 title+content+user_id 分组，保留最小 ID）

### MCP 工具配置
- 安装 `@myuon/refactor-mcp`（正则搜索替换）
- 创建 `.mcp.json` 配置文件
