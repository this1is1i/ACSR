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
