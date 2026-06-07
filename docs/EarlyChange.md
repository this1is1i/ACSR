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

---

## 2026-05-10 (续)

### 核心目标
补全研究者推荐合作者功能、修复页面级交互缺陷、完善搜索筛选、实现社区点赞、修复推荐行为追踪链路。

### 研究者推荐合作者
| 操作 | 文件 | 说明 |
|------|------|------|
| 新增 | `dto/CollaboratorRecommendation.java` | 推荐合作者 DTO（userId, username, avatar, bio, commonInterests, matchCount, reason） |
| 新增 | `repository/PostLikeMapper.java` | 社区点赞数据访问层 |
| 修改 | `service/PrivateMessageService.java` | 新增 `getRecommendedCollaborators()` 接口 |
| 修改 | `service/impl/PrivateMessageServiceImpl.java` | 实现合作者匹配算法：解析 `researchInterests` 逗号分隔字符串为 Set，与同角色用户计算交集，按 overlap 降序取 top 2，排除已有联系人及自身 |
| 修改 | `controller/PrivateMessageController.java` | 新增 `GET /api/message/recommended-collaborators` 端点 |
| 修改 | `api/message.js` | 新增 `getRecommendedCollaborators()` 前端 API |
| 修改 | `components/chat/ConversationRail.vue` | 新增"推荐合作者"面板（头像、简介、共同兴趣标签、开始对话按钮）、空状态提示、搜索联系人栏（防抖 300ms）、搜索结果面板（overflow-y scroll） |
| 修改 | `views/RealtimeChat.vue` | 集成 `loadRecommendations()`（RESEARCHER 角色门控）、`startChatWithRecommended()` 自动发送问候语并刷新联系人、`handleSearch()` / `startChatWithUser()` 搜索联系人功能 |

### 联系人搜索
| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `repository/UserMapper.java` | 新增 `searchUsers(q, limit)`：按 username / research_interests LIKE 搜索 |
| 修改 | `service/UserService.java` | 新增 `searchUsers()` 接口 |
| 修改 | `service/impl/UserServiceImpl.java` | 实现用户搜索，返回 `UserProfile` 列表 |
| 修改 | `controller/UserController.java` | 新增 `GET /api/user/search?q=&limit=` 端点 |

### 私信页面布局修复
| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `views/RealtimeChat.vue` | CSS 重构：`height: 100vh; flex column; overflow: hidden`；`.chat-panel` 使用 `flex: 1; min-height: 0`；消息区 `flex: 1; overflow-y: auto`；修复 `meId` 从 `userStore.userInfo.id` 读取（之前错误读取 `localStorage.getItem('userId')` 导致气泡左右反转） |
| 修改 | `components/chat/ConversationRail.vue` | 联系人名称改用 `user.username`；最近消息截断 `text-overflow: ellipsis`；推荐合作者面板移至联系人上方；全面板固定高度 + 内部滚动条 |

### 个人页与论文详情
| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `views/Profile.vue` | 活动历史 `historyPageSize` 从 10 改为 4 |
| 修改 | `views/PaperDetail.vue` | 返回按钮改为 `router.back()` 而非硬编码 `/search`；新增 AMiner ID 路由支持（`/paper/aminer/:aminerId`）；追踪真实阅读时长：记录 `enterTime`，`onBeforeUnmount` 计算 duration 秒数发送 `recordRead` |
| 修改 | `components/paper/PaperPathRail.vue` | 按钮文字从"返回搜索"改为"返回" |
| 修改 | `router/index.js` | 新增 `/paper/aminer/:aminerId` 路由 |
| 修改 | `api/paper.js` | 新增 `getPaperByAminerId()`；`searchPapers` 支持 filters 参数 |
| 修改 | `components/PaperCard.vue` | 标题可点击导航；自动检测 AMiner ID 格式并路由到正确路径 |
| 修改 | `components/path/PathInsightRail.vue` | 路径论文和推荐资产卡片可点击导航；hover 高亮效果 |

### 搜索页筛选器修复
| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `repository/PaperMapper.java` | `searchByKeywordExpanded` 新增 `yearFrom` / `sortBy` 动态 SQL 参数；所有 `SELECT *` 添加 `\`abstract\` AS abstrakt` 别名修复摘要字段映射 |
| 修改 | `service/PaperService.java` | `searchPapers` 签名新增 `yearFrom` / `sortBy` |
| 修改 | `service/impl/PaperServiceImpl.java` | Neo4j 路径也应用 yearFrom 过滤 + sortBy 排序（修复筛选器在 Neo4j 启用时不生效的 bug） |
| 修改 | `controller/PaperController.java` | `/search` 端点新增 `yearFrom` / `sortBy` 可选参数 |
| 修改 | `views/Search.vue` | `handleSearch` 调用 `getFilterParams()` 映射时间→yearFrom、排序→sortBy；热门关键词改为英文字段匹配（Reinforcement Learning, Transformer, etc）；默认标签同步英文化 |
| 修改 | `components/search/SearchFilterRail.vue` | 删除无法生效的"文献类型"和"研究领域"下拉框；删除"影响力"排序选项 |
| 修改 | `components/search/SearchResultCard.vue` | 删除"研究路径"和"查询条件"上下文标签 |
| 修改 | `utils/paper.js` | `SEARCH_DEFAULT_FILTERS` 精简为 time + sort |

### 社区帖子点赞
| 操作 | 文件 | 说明 |
|------|------|------|
| 新增 | `repository/PostLikeMapper.java` | `insertLike` / `deleteLike` / `existsLike` / `findLikedPostIds` |
| 修改 | `service/CommunityService.java` | 新增 `toggleLike()` 接口 |
| 修改 | `service/impl/CommunityServiceImpl.java` | 实现点赞切换（INSERT/DELETE + like_count 增减）；`listPosts` 注入 likedPostIds；`toPostItem` 设置 `liked` 字段 |
| 修改 | `controller/CommunityController.java` | 新增 `POST /api/community/posts/{postId}/like` 端点 |
| 修改 | `dto/CommunityDto.java` | `PostItem` 新增 `liked` 布尔字段 |
| 修改 | `views/Community.vue` | 点赞按钮可切换（🤍/❤️）；`handleLike()` 含登录状态守卫 |
| 修改 | `api/community.js` | 新增 `togglePostLike()` |
| — | 数据库 | 新建 `post_like` 表（user_id + post_id 唯一约束） |

### 推荐行为追踪修复
| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `views/PaperDetail.vue` | 追踪真实阅读时长：进入时记录 `enterTime`，离开时计算秒数调用 `recordRead(id, duration)` |
| 修改 | `rl-service/features/feature_builder.py` | `_build_history_from_mysql` 改为加权池化：click=0.5 / read=1.0 / favorite=2.0；阅读时长每 60s +0.5（上限 +2.0）；使用 `np.average(weights=)` 替代 `np.mean` |

### 已修复 Bug（按发现顺序）
1. `recordRead` 的 `duration` 始终为 0 → 追踪真实页面停留时长
2. `meId` 从 `localStorage.getItem('userId')` 读取但 key 为 `'userInfo'` → 消息气泡左右反转
3. Neo4j 搜索路径绕过 yearFrom/sortBy 筛选 → Java 层补充过滤
4. 搜索热门关键词为中文但数据库全为英文 → 改为英文关键词
5. 路径论文使用 AMiner ID 但路由仅处理数字 ID → 新增 `/paper/aminer/:aminerId` 路由
6. `SELECT *` 中 `abstract` 列无法自动映射到 Java `abstrakt` 字段 → 添加 `AS abstrakt` 别名
7. 社区点赞数纯静态显示 → 完整实现点赞切换 + liked 状态回传
8. 推荐合作者面板在结果为空时完全隐藏 → 增加空状态提示
9. 右侧联系人列表不显示真实用户名 → `user.name` 改为 `user.username`
10. 论文详情页返回固定跳转搜索页 → 改为 `router.back()`
11. 联系人搜索结果显示不全 → 添加 `max-height + overflow-y: auto`
12. 搜索页筛选器仅前端展示未传后端 → 连通 yearFrom/sortBy 参数链路

### 今日提交
`ff96232` chore: researcher collaborator recommendation, search filters, community likes, UI fixes, behavior tracking

---

## 2026-05-12

### 核心目标
编写本科毕业论文，以项目为根基撰写《基于知识图谱与强化学习的科研成果推荐系统》。

### 论文编写
| 操作 | 文件 | 说明 |
|------|------|------|
| 新增 | `docs/论文第二版.md` | 五章结构：引言→需求分析→概要设计→详细设计→总结展望，约2.6万字 |
| 新增 | `docs/论文第二版.docx` | pandoc md→docx 导出 |
| 修改 | 同上 | 新增 1.5 开发与运行环境章节 |
| 修改 | 同上 | 新增 3.1 系统包图（Mermaid → PlantUML → draw.io 三次迭代） |
| 修改 | 同上 | 新增后端推荐类图、社区消息类图、Python 服务类图 |

### 图表绘制（draw.io）
| 操作 | 说明 |
|------|------|
| 安装 | `@drawio/mcp`（JGraph 官方 MCP Server），配置到 `.mcp.json` |
| 新增 | `docs/draw/01-system-overview.drawio` — 系统总体包图 |
| 新增 | `docs/draw/02-frontend-package.drawio` — 前端层包图（7 子包） |
| 新增 | `docs/draw/03-backend-package.drawio` — 后端层包图（8 子包） |
| 新增 | `docs/draw/04-python-package.drawio` — 推荐引擎层包图（9 子包） |
| 新增 | `docs/draw/05-backend-recommend-class.drawio` — 推荐与行为追踪类图 |
| 新增 | `docs/draw/06-backend-community-class.drawio` — 社区与消息类图 |
| 新增 | `docs/draw/07-python-class.drawio` — Python 推荐服务核心类图（14 类） |
| 新增 | `docs/draw/08-recommend-pipeline-flow.drawio` — 推荐流水线流程图（基于实际代码） |
| 新增 | `docs/draw/09-learning-path-flow.drawio` — 学习路径构建流程图 |
| 新增 | `docs/draw/10-collaborator-matching-flow.drawio` — 合作者匹配流程图 |
| 新增 | `docs/draw/11-er-diagram.drawio` — 数据库 ER 图（13 表，中文标签） |

### 图表迭代修复
1. **mxGeometry 序列化错误**：Python `ET.tostring` 将 dict 序列化为字符串 `"{'x': '60'...}"` 而非 XML 子元素 → 改为独立 `<mxGeometry x="60" y="60" .../>` 子元素
2. **Mermaid→PlantUML→draw.io 三次迁移**：Mermaid 包图 `graph` 关键字冲突 → PlantUML 字体偏小 → 最终直接用 Python 生成 draw.io XML
3. **包图子包样式**：普通矩形→`shape=tab`（UML 标准 package 图标）
4. **流程图内容不对**：基于文字描述→基于实际代码逻辑（含 MySQL 回退、判空分支、DFS 分支等）
5. **ER 图中文化**：表名与字段名改为中文，去掉 PK/FK 标记，添加 1/N 关系基数

### .bashrc 修复
- `C:\Users\Eternity\.bashrc` 被存为 UTF-16 LE 编码导致每次 bash 命令报 `\377\376export: command not found` → 重写为 UTF-8

## 2026-05-15

### 核心目标
数据库精简、新论文版本导入、图表导出。

### 数据库精简
| 删除表 | 原因 |
|--------|------|
| board | 从未被代码引用，仅 2 条 seed 数据 |
| browse_history | 功能已被 behavior_log(action=read) 覆盖，Mapper 已删除 |
| notification | 通知功能从未实现，无 Mapper/Service/Controller |
| kg_relation | 数据已迁移至 Neo4j，仅剩死 Mapper 代码 |

MySQL 从 16 张表精简至 13 张（核心 9 张 + 辅助 1 张 + 基础设施 3 张）。

### 论文更新
| 操作 | 文件 | 说明 |
|------|------|------|
| 导入 | `docs/论文第三版.docx` | 用户提供的最新版论文，结构重组：引言→开发工具→需求分析与概要设计→详细设计→软件介绍 |

### draw.io 图表最终修复
| 问题 | 修复 |
|------|------|
| 类图旋转 90 度 | 移除 `horizontal` 约束，使用 `container=0` |
| 流程图有颜色 | 全部改为 `fillColor=none;strokeColor=#333333` |
| ER 图结构不对 | 重绘：表名方框 + 字段椭圆 + 关系菱形 + 1/N 基数标记 |

### Git 提交
`<pending>` feat: add paper v2, database cleanup, draw.io diagrams, ER diagram

---

## 2026-05-17

### 核心目标
文档维护：CLAUDE.md 补全遗漏 API 路由与架构图引用，修正记忆文件数据表计数错误。

### CLAUDE.md 更新
| 操作 | 说明 |
|------|------|
| 新增 | 5 条遗漏 API 路由（`/api/user/favorites`、`/api/behavior/history`、`/api/recommend/train`、`/api/recommend/model/info`） |
| 新增 | `## Architecture Diagrams` 章节，索引 `docs/draw/` 下 16 张 draw.io 图表 |
| 新增 | `favourite` 表孤儿状态说明（无 Mapper，实际走 behavior_log） |
| 修正 | MCP 配置描述（区分 server name vs npm package name） |

### 新增 BPD 图表
| 文件 | 说明 |
|------|------|
| `docs/draw/13-recommend-BPD.drawio` | 推荐业务流程 |
| `docs/draw/14-learning-path-BPD.drawio` | 学习路径业务流程 |
| `docs/draw/15-collaborator-matching-BPD.drawio` | 合作者匹配业务流程 |
| `docs/draw/16-forum-judge-BPD.drawio` | 论坛审核业务流程 |

### 记忆文件修正
- `data-architecture-snapshot.md`：表计数 13→12（去除重复计数的 comment 表）

---

## 2026-05-24

### 核心目标
功能补全 + 系统审计 + BUG 修复 + 死代码清理 + UI 精简。

### 功能实现

#### 作者认领功能（QA_2026-05-16_2026-06-02_v1.md Q10）
| 操作 | 文件 | 说明 |
|------|------|------|
| 新增 | `research_db.sql` | `paper_author_claim` 表（13 列，4 索引，2 外键） |
| 新增 | `entity/PaperAuthorClaim.java` | 认领记录实体 |
| 新增 | `repository/PaperAuthorClaimMapper.java` | INSERT IGNORE + JOIN 查询 |
| 新增 | `dto/ClaimDto.java` | 认领请求/响应 DTO |
| 新增 | `service/ClaimService.java` + `impl/ClaimServiceImpl.java` | 确认/否认/列表逻辑 |
| 新增 | `controller/ClaimController.java` | `/api/paper/{id}/claim-confirm\|deny`，`/api/user/claimed-papers` |
| 修改 | `AdminController/Service/ServiceImpl` | 论文导入时自动匹配作者→创建认领记录→发送系统通知 |
| 修改 | `PrivateMessageService/Impl` | 新增 `msgType` 重载方法（msgType=4 为认领通知） |
| 新增 | `frontend/src/api/claim.js` | 认领 API 模块 |
| 修改 | `frontend/src/views/Profile.vue` | 「我的论文」卡片（待确认/已确认双标签） |
| 新增 | `seed_claim_test_data.sql` | 基于 Neo4j 真实作者名 + BCrypt 密码的测试数据 |

#### 论坛帖子搜索 + 个人帖子管理
| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `CommunityDto.java` | 新增 `PostUpdateRequest` |
| 修改 | `CommunityService/Impl` | 新增 searchPosts/listMyPosts/updatePost/deletePost |
| 修改 | `CommunityController.java` | 新增搜索、我的帖子、编辑、删除 4 个端点 |
| 修改 | `frontend/src/api/community.js` | 新增 4 个 API 调用 |
| 修改 | `frontend/src/views/Community.vue` | 搜索栏 + 300ms 防抖 |
| 修改 | `frontend/src/views/Profile.vue` | 「我的帖子」卡片 + 编辑弹框 + 删除确认 |

### UI 精简（本轮累计）

| 涉及页面 | 删除项 |
|---------|--------|
| 首页 | "补充检索""打开图谱"按钮；RecommendationStream/LearningPathPanel 死描述 |
| 检索页 | SearchFilterRail 死描述 |
| 图谱页 | PathInsightRail 3 段 verbose 描述 |
| 私信页 | "实时同步""论文线索""行动路径"标签；修复长用户名挤占状态标签的 CSS 溢出 |
| 登录页 | 英文→中文；删除"30天内记住我"+"忘记密码？"摆设 |
| 侧边栏 | 全部 7 个导航项的描述副标题 |
| 管理员控制台 | "导入准备度""导入载荷"两个无用信号卡片 |
| Profile | "我的收藏"改为分页式（4 条/页 + el-pagination） |
| 全局 | scrollbar 变窄变淡（5px + 半透明） |

### 全项目代码审计（QA_2026-05-16_2026-06-02_v1.md Q11）

三个并行代理审计 ~122 个文件、~520 个函数/方法：

| 层级 | BUG | DEAD | MINOR |
|------|-----|------|-------|
| 后端 Java | 0 | 12 | 9 |
| 前端 Vue | 4 | 12 | ~15 |
| Python RL | 2 | 13 | ~12 |

审计报告详见 `docs/QA_2026-05-16_2026-06-02_v1.md` Q11 节。

### BUG 修复（6 项，详见 QA_2026-05-16_2026-06-02_v1.md Q12）

| BUG | 文件 | 根因 |
|-----|------|------|
| Actor 评分 hash 碰撞 | `ranker.py:76` | `hash(item_id) % 20` 导致 500→20 槽位碰撞率 95% |
| KG reward 训练恒为 0 | `rec_env.py + mock_data.py` | kg_node_id 格式不匹配 + ID 越界 |
| AMiner 路由下载失败 | `PaperDetail.vue` | `route.params.id` 在 `/paper/aminer/:id` 下为 undefined |
| logout 未清 Pinia | `Profile.vue` | 手动操作 localStorage 绕过 store |
| 排序选项无效 | `Search.vue` | sortMap 遗漏'影响力'+'相关度' |
| 随机 ID 破坏收藏 | `Search.vue` | Math.random() 跨导航不唯一 |

### 推荐管线修复

| 问题 | 修复 |
|------|------|
| 候选数 `action_num * 2 = 40` 超出 AC 网络 20 槽位 | 改为 `action_num = 20`，1:1 精准打分 |
| `ranker.py` hash 碰撞使 Actor 评分随机 | 改为按位置线性映射 |
| `candidate_generator.py` mock pool `kg_node_id` 格式 `kg_node_xxx` 不匹配 AMiner | 改为 `aminer_xxx` 格式 |
| `mock_data.py` 候选 ID 仅前 20 个对齐 | 改为随机索引覆盖 500 范围 |

### 死代码清理（37 项）

| 层级 | 删除文件 | 删除方法/块 |
|------|---------|------------|
| Java | BrowseHistory.java, KgRelation.java, KgRelationMapper.java, KnowledgeService.java, KnowledgeServiceImpl.java | PaperMapper.searchByKeyword, UserRole.isHigherOrEqual, PythonRecClient.isAvailable, UserInterestHistoryMapper 2 方法 |
| Vue | HelloWorld.vue, KnowledgeGraph3D.vue, AppShell.vue, design-tokens.css | getPaperList, contextLabels/pathLabel computed, messages prop, .app-shell CSS |
| Python | text_utils.py, data_importer.py, embedding_builder.py | mysql_data 3 方法, kg_builder 1, kg_embedder 1, graph_query 1, graph_storage 1, path_builder 2, reward 2 字段 |

### Git 提交
`da1460c` feat: author claim, post search/management, code audit, bug fixes, dead code cleanup, UI polish

---

## 2026-05-25

### 核心目标
修复昨日改动引入的回归 BUG + 系统理论分析文档。

### 回归 BUG 修复

| 问题 | 根因 | 修复 |
|------|------|------|
| Python 推荐服务 500 崩溃 | `ranker.py` 循环 `for item in candidates:` 缺少索引 `i`，但 B1 修复用了 `i` 变量 → NameError | `for item in candidates:` → `for i, item in enumerate(candidates):` |
| 前端页面样式崩溃、Profile/RealtimeChat 语法错误 | `sed` 注释 `console.error` 破坏了 JS 语法 | 全局替换 `// console.error` → `console.debug` |
| 左侧导航栏悬浮遮住主内容 | `sed` 删除 `.app-shell` 响应式规则时误删 `@media (max-width: 980px)` 包装行，导致 `margin-left:0;width:100%` 全屏生效 | 恢复 `@media (max-width: 980px) { ... }` 包裹 |
| 退出登录失效 | Profile.vue 调用 `userStore.clearToken()` 但未导入 `useUserStore` | 添加 `import { useUserStore }` + `const userStore = useUserStore()` |

### QA 文档更新

| 操作 | 文件 | 说明 |
|------|------|------|
| 新增 | `docs/QA_2026-05-16_2026-06-02_v1.md` Q13 | 知识图谱-强化学习协同机制（Actor/Critic 影响路径、拓扑特征-兴趣耦合循环、四层鲁棒性保障） |
| 新增 | 同上 Q13 | 推荐评估指标体系（HR/MRR/NDCG/ILS/Coverage/Novelty/Explanation Coverage） |
| 新增 | 同上 Q13 | MDP 形式化定义（S/A/R/P 严格定义 + Sutton & Barto 章节引用） |

### 记忆文件维护
- `memory/audit-plan-status.md`：审计计划 P0/P1/P2 标记为已完成
- `memory/MEMORY.md`：新增两条记录

### Git 提交
`c39fbf8` fix: regression bugs from yesterday + Q13 docs

---

## 2026-05-27

### 核心目标
Actor 网络架构重构（位置打分→逐论文打分）、训练接入真实数据、前端卡片溢出修复、后端日志精简。

### Actor 架构重构（rl-service/）
**问题：** Actor 输出 20 个固定槽位概率，ranker 按候选位置映射到槽位——同一论文在不同位置得分不同，Actor 从未见过论文特征。
**方案：** Actor 改为 pairwise scoring：输入 `[user_state(96) | paper_features(32)]` → 128 维，输出 1 个 logit。N 篇候选一次 GPU 前向传播打分，softmax 后得 N 个独立概率。

| 操作 | 文件 | 说明 |
|------|------|------|
| 重写 | `models/actor.py` | 输入 96+32→128，输出 1；新增 `score_candidates()` 批量打分方法 |
| 修改 | `agent.py` | `select_action`/`update`/`recommend_top_k` 全部接受 `candidate_features` 参数 |
| 重写 | `env/rec_env.py` | 新增 `_reset_real()` 路径：MySQL 采样用户→FeatureBuilder 构建状态→CandidateGenerator 生成候选；`_reset_mock()` 兜底 |
| 修改 | `recommender/ranker.py` | 删除位置→槽位映射；余弦相似度矩阵向量化；`user_kg` 提到循环外只算一次 |
| 修改 | `train.py` | `_init_real_data_sources()` 逐级初始化 MySQL→KG→FeatureBuilder→CandidateGenerator→用户ID列表 |
| 修改 | `config.py` | +`paper_feature_dim:32`；`action_num` 20→50；`top_k` 5→10 |
| 修改 | `features/feature_builder.py` | `build_item_vector()` 加入标题+关键词哈希编码 |
| 修改 | `data/mysql_data.py` | +`get_all_user_ids()` 训练用户池查询 |

### 前端卡片修复（frontend/）
| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `components/PaperCard.vue` | 标题 `line-clamp:2`；推荐理由 `line-clamp:2` icon 顶部对齐；作者单行省略号；el-tag 内容 `text-overflow:ellipsis`；`displayTags` 跳过与 reason 重复的第一条；删除"阅读"按钮（标题点击已导航）；header/footer/meta 防溢出约束 |

### 后端日志精简（backend/）
| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `application.yml` | `com.example.research` DEBUG→INFO；+`org.apache.ibatis:WARN`；+`com.zaxxer.hikari:WARN`；移除 MyBatis `StdOutImpl` |

### CLAUDE.md 更新
- AC 网络描述：位置打分→逐论文 pairwise scoring
- 新增 Config 参数表（13 项关键参数 + 含义）
- Mock data 章节：训练已接入真实数据
- 推荐流水线流程更新

### 记忆文件
- 新增 `memory/rl-actor-refactor-20260527.md`：Actor 架构变更 + 训练数据源变更 + 关键配置

### Git 提交
`2a38d76` feat: Actor pairwise scoring, real data training, PaperCard UI fixes, log reduction

---

## 2026-05-29

### 核心目标
论文向量去随机化（Q14）+ 注册关键词选择器（Q15）+ 数据同步链路修复。

### Q14: 论文向量去随机化

**问题：** 推荐链路中所有论文向量通过 `hash(paper_id+text) → rng.standard_normal(64)` 生成，任意两篇论文在高维空间中期望余弦相似度为 0，Actor 的 paper_features 和余弦相似度分量均为噪声。

**方案：** 论文向量改为从真实结构特征投影计算 —— 10 维原始特征（被引数/关键词数/作者数/年份等）→ Z-score → 投影矩阵 P(10×32) → L2-norm → 32 维向量。离线预计算写入 `paper.embedding`，推理时直接读取。

| 操作 | 文件 | 说明 |
|------|------|------|
| 新增 | `rl-service/scripts/generate_paper_embeddings.py` | 离线脚本：读取 MySQL paper + Neo4j KG → 10维结构特征 → Z-score → P(10×32)投影 → 写入 MySQL + Neo4j |
| 重写 | `rl-service/recommender/candidate_generator.py` | 新增 `_load_paper_embedding()` 三级优先级；`_build_from_metadata()` 元数据回退；投影矩阵加载；`_build_vector` 降级紧急回退 |
| 修改 | `rl-service/features/feature_builder.py` | `build_item_vector` 优先读取 `item_meta["embedding"]` |
| 修改 | `rl-service/knowledge_graph/kg_embedder.py` | 新增 `extract_features_from_metadata()`；暴露投影矩阵和统计量 |
| 修改 | `rl-service/services/recommendation_service.py` | 从 Neo4j 读取 embedding/embedding_raw；传递 kg_embedder；保存投影矩阵 |
| 修改 | `rl-service/dataset/aminer_loader.py` | Paper 新增 `embedding_raw` 字段 |
| 修改 | `rl-service/config.py` | 新增 `use_stored_embeddings` / `embedding_seed` |
| 修改 | `backend/src/main/resources/research_db.sql` | paper 表新增 `embedding_raw TEXT` 列 |

### Q15: 注册关键词选择器

**问题：** 注册时研究方向为自由文本输入，用户自填关键词与系统论文实际关键词不匹配，冷启动推荐质量差。

**方案：** 查询 Neo4j Keyword 节点（46 个，来自真实论文数据），展示 6 个热门标签 + `···` 弹窗浏览全部，点击选中自动拼接。

| 操作 | 文件 | 说明 |
|------|------|------|
| 新增 | `backend/.../dto/KeywordDto.java` | `{label, frequency}` record |
| 重写 | `backend/.../controller/KnowledgeController.java` | 新增 `GET /api/knowledge/keywords` |
| 修改 | `backend/.../config/SecurityConfig.java` | `/api/knowledge/keywords` 加入白名单 |
| 修改 | `frontend/src/views/Login.vue` | 研究方向文本输入→标签选择器（6热词+ElDialog+搜索） |
| 修改 | `frontend/src/views/EditProfile.vue` | 同上；加载时回填已有研究方向为选中态 |

### 数据同步脚本修复

| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `rl-service/scripts/migrate_to_neo4j.py` | +embedding_raw 列；删除已废弃 kg_entity/kg_relation 引用 + LegacyEntity 导入（~50行） |
| 修改 | `rl-service/scripts/backfill_mysql_shadow_papers.py` | +embedding_raw 列 |
| 修改 | `rl-service/knowledge_graph/graph_storage.py` | 默认路径从相对 `"data/kg"` 改为基于 `__file__` |
| 删除 | `rl-service/data/embeddings/` `processed/` `research.db` | 旧版死文件清理 |

### 数据现状
- MySQL: 1005 篇论文，embedding/embedding_raw 覆盖率 100%
- Neo4j: 1121 节点 + 9796 关系，所有 Paper 含 embedding/embedding_raw
- 本地备份: `data/kg/knowledge_graph.{json,pkl}` (4.2M)，含完整嵌入

### Git 提交
`ab296f8` feat: paper embedding de-randomization (Q14), keyword tag selector (Q15), sync scripts fix, README rewrite

---

## 2026-05-30

### 核心目标
学习路径交互增强、知识图谱页主题切换、QA 文档过期修正。

### 学习路径 Bug 修正
| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `backend/.../VisualizationServiceImpl.java` | group 标签：mastery→depth（depth=0 基础能力，1-2 进阶主题，3 目标专题） |
| 修改 | `rl-service/learning_path/path_builder.py` | 覆盖率公式修正：分子从全部 known_keywords 改为与 related_kws 的交集 |
| 修改 | `backend/.../KnowledgeController.java` | 关键词频率：读不存在属性→运行时 count(p) HAS_KEYWORD 关系 |

### 知识图谱页 — 切换目标专题
| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `backend/.../VisualizationController.java` | `GET /api/visualization/data` 新增可选 `targetTopic` 参数 |
| 修改 | `backend/.../VisualizationService.java` | 接口签名增加 `targetTopic` |
| 修改 | `backend/.../VisualizationServiceImpl.java` | targetTopic 透明降级 |
| 新增 | `frontend/src/api/knowledge.js` | `getKeywords()` |
| 修改 | `frontend/src/api/visualization.js` | 增加可选 targetTopic 参数 |
| 修改 | `frontend/src/views/KnowledgeGraph.vue` | 关键词获取 + `onSelectTargetTopic` |
| 重写 | `frontend/.../PathInsightRail.vue` | "路径检查点"→"切换目标专题"（搜索框+滚动+过滤） |

### QA 文档过期修正
Q2/Q5/Q5追问/Q10 中 Actor 架构、排序伪代码、Config 默认值、模块图、表数量等全面更新至当前代码状态。

### 文档清理
移除 docs/ 下除 draw/、EarlyChange.md、QA_2026-05-16_2026-06-02_v1.md 以外的文件，更新 .gitignore。

### Git 提交
`<pending>`
