# ACScientificRecommendation

基于知识图谱与强化学习的科研成果推荐系统。三端协作：**Vue 3 前端**提供交互与可视化，**Spring Boot 后端**负责鉴权与业务集成，**Python FastAPI 服务**驱动 Actor-Critic 推荐引擎与知识图谱计算。

> 本科毕业设计项目，论文约 2.6 万字，架构图 16 张。详细设计文档见 `docs/QA.md`，每日变更记录见 `docs/EarlyChange.md`。

## 目录

- [系统概览](#系统概览)
- [项目结构](#项目结构)
- [架构与数据流](#架构与数据流)
- [快速开始](#快速开始)
- [关键文件索引](#关键文件索引)
- [个性化配置](#个性化配置)
- [可升级与可替换部分](#可升级与可替换部分)
- [数据同步](#数据同步)
- [测试](#测试)
- [引用与复刻规范](#引用与复刻规范)

## 系统概览

```
┌──────────────────────────────────────────────────────────┐
│  Vue 3 Frontend (:5173)                                  │
│  推荐流 │ 论文检索 │ 知识图谱3D │ 社区 │ 实时私信 │ 管理  │
└──────────┬───────────────────────────────────────────────┘
           │ REST /api/*  +  WebSocket /ws-messages
           ▼
┌──────────────────────────────────────────────────────────┐
│  Spring Boot Backend (:8080)                             │
│  JWT鉴权 │ REST API │ MyBatis-Plus │ STOMP消息 │ 业务逻辑  │
└──────────┬───────────────────────────────────────────────┘
           │ POST /recommend (AMiner ID)
           ▼
┌──────────────────────────────────────────────────────────┐
│  Python FastAPI RL Service (:8000)                       │
│  特征构建 │ 候选召回 │ Actor-Critic排序 │ 解释生成 │ 训练  │
└──────────┬───────────────────┬───────────────────────────┘
           │                   │
           ▼                   ▼
      MySQL (8.0)         Neo4j (5.x)
   用户行为/论文元数据     知识图谱/拓扑特征
```

## 项目结构

```
ACScientificRecommendation/
├── frontend/                        # Vue 3 + Vite + Element Plus
│   ├── src/
│   │   ├── views/                   # 页面组件（11个路由页面）
│   │   │   ├── Home.vue             # 首页推荐流
│   │   │   ├── Search.vue           # 论文检索（全文搜索+筛选）
│   │   │   ├── PaperDetail.vue      # 论文详情+阅读时长追踪
│   │   │   ├── KnowledgeGraph.vue   # 3D知识图谱（3d-force-graph）
│   │   │   ├── Community.vue        # 社区帖子（发布/搜索/点赞）
│   │   │   ├── Profile.vue          # 个人主页（收藏/论文/帖子/活动）
│   │   │   ├── EditProfile.vue      # 资料编辑（关键词标签选择器）
│   │   │   ├── Login.vue            # 登录/注册（含关键词选择器）
│   │   │   ├── RealtimeChat.vue     # 实时私信（WebSocket+推荐合作者）
│   │   │   └── AdminConsole.vue     # 管理后台（帖子审核/用户管理/论文导入）
│   │   ├── components/              # 可复用组件
│   │   │   ├── Sidebar.vue          # 全局侧边导航
│   │   │   ├── PaperCard.vue        # 论文卡片
│   │   │   ├── RecommendList.vue    # 推荐列表
│   │   │   ├── search/              # 搜索相关组件
│   │   │   ├── chat/                # 私信相关组件
│   │   │   └── home/                # 首页相关组件
│   │   ├── api/                     # API 调用模块（axios封装）
│   │   ├── store/                   # Pinia 状态管理
│   │   ├── router/                  # Vue Router 路由配置
│   │   ├── utils/                   # 工具函数（request/auth/path）
│   │   └── styles/                  # 全局样式
│   ├── package.json
│   └── vite.config.js               # 代理 /api→:8080, /uploads→:8080
│
├── backend/                         # Spring Boot 3.2 + Java 17
│   └── src/main/java/com/example/research/
│       ├── controller/              # REST 控制器（14个端点组）
│       ├── service/impl/            # 业务逻辑实现
│       ├── repository/              # MyBatis-Plus Mapper
│       ├── entity/                  # 数据库实体
│       ├── dto/                     # 请求/响应 DTO
│       ├── config/                  # Spring Security/CORS/MyBatis/WebSocket
│       ├── client/PythonRecClient.java  # Python 服务 HTTP 客户端
│       ├── graph/                   # Neo4j 图数据访问
│       └── util/                    # JWT/Result 工具类
│
├── rl-service/                      # Python 推荐引擎
│   ├── api/server.py                # FastAPI 入口（6个端点）
│   ├── services/recommendation_service.py  # 推荐编排核心
│   ├── recommender/
│   │   ├── candidate_generator.py   # 候选集生成（预存向量读取）
│   │   └── ranker.py                # RL 排序（Actor+Cosine+KG）
│   ├── models/
│   │   ├── actor.py                 # Actor 网络（pairwise scoring）
│   │   └── critic.py                # Critic 网络（状态价值估计）
│   ├── features/feature_builder.py  # 用户特征构建（MySQL→向量）
│   ├── env/rec_env.py               # RL 训练环境
│   ├── knowledge_graph/
│   │   ├── kg_builder.py            # KG 构建（AMiner→内存图）
│   │   ├── kg_embedder.py           # 图拓扑特征嵌入（10→32维投影）
│   │   ├── graph_query.py           # 图查询（解释生成/关键词聚类）
│   │   └── graph_storage.py         # 持久化存储（JSON/Pickle/Neo4j）
│   ├── data/
│   │   ├── mysql_data.py            # MySQL 数据访问层
│   │   └── mock_data.py             # 训练用模拟数据生成器
│   ├── scripts/                     # 数据同步脚本
│   │   ├── generate_paper_embeddings.py  # 论文向量离线生成
│   │   ├── migrate_to_neo4j.py      # MySQL→Neo4j 迁移
│   │   ├── backfill_mysql_shadow_papers.py  # Neo4j→MySQL 回填
│   │   └── neo4j_schema.cypher      # Neo4j 约束与索引
│   ├── config.py                    # 全局配置（维度/超参/连接）
│   └── train.py                     # 训练入口
│
├── docs/
│   ├── QA.md                        # 详细技术问答（Q10-Q15）
│   ├── EarlyChange.md               # 每日变更记录
│   └── draw/                        # 16 张 draw.io 架构图
│
├── memory/                          # Claude Code 持久记忆
├── CLAUDE.md                        # Claude Code 项目指引
└── .mcp.json                        # MCP 服务器配置
```

## 架构与数据流

### 推荐链路（核心路径）

```
用户请求 → RecommendController → RecommendServiceImpl → PythonRecClient
                                                              │
                                                  POST /recommend
                                                              ▼
                                              RecommendationService
                                              ┌──────────────────┐
                                              │ 1. 特征构建      │
                                              │    behavior_log  │
                                              │    + interest_history → 用户状态向量(96维)
                                              │                  │
                                              │ 2. 候选召回      │
                                              │    paper.embedding(预存32维) → topic_vector
                                              │    hybrid策略(70%相似+30%热门) → 50候选
                                              │                  │
                                              │ 3. RL排序        │
                                              │    Actor: [state|paper_features]→logit→概率
                                              │    Cosine: dot(state, topic_vector)
                                              │    KG: dot(user_kg, paper_kg)
                                              │    综合: 0.5a+0.3c+0.2k → Top-10
                                              │                  │
                                              │ 4. 解释生成      │
                                              │    GraphQuery.explain(引用链/共作者/关键词)
                                              └──────────────────┘
                                                              │
                                          ← RecommendationResponse
                                                              │
                                     AMiner ID → 本地 Paper 映射 → Result JSON
```

### 论文向量去随机化（Q14）

论文向量从随机哈希改为真实结构特征投影：

- **离线**：`generate_paper_embeddings.py` → 10维原始特征（被引数/关键词数/作者数/年份等）→ Z-score → P(10×32)投影 → L2-norm → 写入 `paper.embedding`(32维) + `paper.embedding_raw`(10维) → 同步 Neo4j
- **推理**：`CandidateGenerator._load_paper_embedding()` 三级优先级：预存向量 → KGEmbedder 实时计算 → 元数据近似（citation/year/keywords/authors）→ 哈希紧急回退

### 实时私信（双通道）

- REST `/api/message/*`：历史记录与持久化
- WebSocket `/ws-messages`：SockJS/STOMP 实时推送 + 在线状态
- JWT 在 STOMP 消息体中传递（非 HTTP Header）

## 快速开始

### 前置依赖

| 组件 | 版本要求 | 说明 |
|------|---------|------|
| JDK | 17+ | 后端编译与运行 |
| Maven | 3.8+ | 后端构建 |
| Node.js | 18+ | 前端构建 |
| Python | 3.10+ | RL 服务 |
| MySQL | 8.0 | 业务数据库 |
| Neo4j | 5.x | 知识图谱数据库 |

### 1. 数据库初始化

```sql
-- 执行建表脚本
mysql -u root -p < backend/src/main/resources/research_db.sql

-- 已有数据库需添加 embedding_raw 列
ALTER TABLE paper ADD COLUMN embedding_raw TEXT NULL COMMENT '论文原始特征(10维JSON)';
```

### 2. Neo4j 启动与数据迁移

```bash
# 启动 Neo4j（确保 bolt://localhost:7687 可用）
# 迁移数据：MySQL paper 表 + AMiner 文件 → Neo4j
cd rl-service
python scripts/migrate_to_neo4j.py --neo4j-password seeworld123
```

### 3. 生成论文向量

```bash
cd rl-service
python scripts/generate_paper_embeddings.py
```

### 4. 启动服务（按顺序）

```bash
# 终端 1: Python RL 服务 (:8000)
cd rl-service
uvicorn api.server:app --reload --host 0.0.0.0 --port 8000

# 终端 2: Java 后端 (:8080)
mvn -f backend spring-boot:run

# 终端 3: Vue 前端 (:5173)
cd frontend
npm install
npm run dev
```

### 5. 训练模型（可选）

```bash
cd rl-service
python train.py
```

模型权重保存到 `rl-service/checkpoints/ac_model.pth`，推理服务启动时自动加载。

## 关键文件索引

### 你需要修改的核心文件

| 场景 | 文件 | 修改内容 |
|------|------|---------|
| 调整推荐策略 | `rl-service/config.py` | `action_num`, `top_k`, `reward_weights` |
| 修改排序公式 | `rl-service/recommender/ranker.py:109-113` | Actor/Cosine/KG 权重比例 |
| 新增推荐解释逻辑 | `rl-service/knowledge_graph/graph_query.py:explain_recommendation()` | 图查询规则 |
| 调整用户特征构建 | `rl-service/features/feature_builder.py` | 加权池化权重、向量维度 |
| 修改论文向量生成 | `rl-service/scripts/generate_paper_embeddings.py` | 10维特征选择、投影维度 |
| 调整 AKN 网络结构 | `rl-service/models/actor.py:__init__()` | hidden_dim、层数、dropout |
| 前端推荐卡片样式 | `frontend/src/components/PaperCard.vue` | 卡片布局、信息展示 |
| 后端 API 响应格式 | `backend/.../util/Result.java` | 统一返回值结构 |
| 认证逻辑 | `backend/.../config/SecurityConfig.java` | 白名单、角色权限 |

### 架构图

| 文件 | 内容 |
|------|------|
| `docs/draw/01-04-*-package.drawio` | 系统包图 + 三层架构 |
| `docs/draw/05-07-*-class.drawio` | 后端推荐/社区/消息 + Python 服务类图 |
| `docs/draw/08-10-*-flow.drawio` | 推荐管道/学习路径/合作者匹配流程图 |
| `docs/draw/11-er-diagram.drawio` | 数据库 ER 图（中文，1/N 基数） |
| `docs/draw/12-neo4j-graph.drawio` | Neo4j 图模型（5 关系类型） |
| `docs/draw/13-16-*-BPD.drawio` | 业务流程：推荐/学习路径/合作者/论坛审核 |

## 个性化配置

### 数据库连接

| 配置位置 | 默认值 | 说明 |
|---------|--------|------|
| `rl-service/config.py` MySQL 段 | `root:qwer1234@localhost:3306/research_db` | Python 侧数据库连接 |
| `rl-service/config.py` Neo4j 段 | `neo4j:seeworld123@bolt://localhost:7687` | Python 侧图数据库连接 |
| `backend/.../application.yml` | `root:qwer1234@localhost:3306/research_db` | Java 侧数据源 |
| 环境变量 `GRAPH_NEO4J_*` | 覆盖 Neo4j 连接参数 | 同步脚本和服务共用 |

### Python 推荐超参数

所有推荐参数集中在 `rl-service/config.py:default_config`：

| 参数 | 默认值 | 含义 |
|------|--------|------|
| `base_state_dim` | 64 | 用户基础状态维度 |
| `paper_feature_dim` | 32 | 论文特征维度 |
| `kg_embedding_dim` | 32 | KG 嵌入维度 |
| `action_num` | 50 | 候选集最大数量 |
| `top_k` | 10 | 默认推荐数量 |
| `actor_hidden` | 128 | Actor 隐藏层宽度 |
| `gamma` | 0.99 | RL 折扣因子 |
| `actor_lr` / `critic_lr` | 1e-3 | 学习率 |
| `reward_weights` | 见代码 | 6 项奖励权重 |

### 前端代理

`frontend/vite.config.js` 中配置开发代理：
```js
proxy: {
  '/api': 'http://localhost:8080',
  '/uploads': 'http://localhost:8080',
}
```

## 可升级与可替换部分

| 当前实现 | 局限 | 升级方向 |
|---------|------|---------|
| `CandidateGenerator._retrieve_by_similarity()` — Numpy 暴力点积 | O(N×D)，N>10000 时性能下降 | Faiss/Milvus 向量检索 |
| Actor-Critic MLP (128→128→1) | 浅层网络，无注意力机制 | Transformer Encoder + Cross-Attention |
| `paper.embedding` 10维结构特征投影 | 无文本语义，关键词/摘要未被编码 | SciBERT/Specter 论文嵌入模型 |
| `ranker.py` 固定权重 (0.5/0.3/0.2) | 无法根据场景自适应 | 可学习融合层 (Learned Fusion) |
| 用户冷启动用全局热门兴趣 | 新用户前 5 次推荐质量低 | 注册时收集更多偏好信号或使用预训练模型 |
| `PythonRecClient` 同步 HTTP 调用 | 推荐延迟受 Python 服务响应影响 | gRPC + 异步流式返回 |
| 单个 Actor-Critic 模型 | 无法捕捉多兴趣维度 | 多臂 Bandit 或 Mixture-of-Experts |
| MySQL `behavior_log` 全量查询 | 用户行为数据量大后特征构建变慢 | 增量特征更新 + Redis 缓存 |
| 无 A/B 测试框架 | 无法量化改动效果 | 推荐结果带实验标记 + 指标对比 |
| Neo4j 社区版单机 | 无高可用 | Neo4j AuraDB / 集群部署 |

## 数据同步

三个脚本覆盖全部数据方向：

| 脚本 | 方向 | 说明 |
|------|------|------|
| `scripts/migrate_to_neo4j.py` | MySQL + AMiner → Neo4j | 论文/作者/关键词/关系全量迁移 |
| `scripts/backfill_mysql_shadow_papers.py` | Neo4j → MySQL | 反向回填（含 embedding） |
| `scripts/generate_paper_embeddings.py` | 计算 → MySQL + Neo4j | 论文向量双写 |

本地保底：`data/kg/knowledge_graph.{json,pkl}` — Neo4j 不可用时 RecommendationService 从本地文件加载 KG。

## 测试

```bash
# Java 后端
mvn -f backend test
mvn -f backend -Dtest=ClassName#methodName test

# Python
cd rl-service
python -m unittest tests.test_runtime_fixes

# 前端烟雾测试
cd frontend
npx playwright test tests/design.spec.js
```

当前测试覆盖有限，建议为推荐链路（特征构建→候选召回→排序→解释）添加集成测试。

## 引用与复刻规范

### 学术引用

如果本项目对您的研究有帮助，请引用：

```
@misc{ACScientificRecommendation,
  author = {[Your Name]},
  title = {ACScientificRecommendation: Academic Recommendation System with Knowledge Graph and Reinforcement Learning},
  year = {2026},
  publisher = {GitHub},
  howpublished = {\url{https://github.com/[username]/ACScientificRecommendation}}
}
```

### 复刻指南

1. **Fork** 本仓库后，修改以下位置的连接信息：
   - `rl-service/config.py` 中的 `mysql_*` 和 `neo4j_*` 参数
   - `backend/src/main/resources/application.yml` 中的数据源配置
   - `frontend/vite.config.js` 中的 API 代理目标

2. **准备数据**：导入 AMiner 数据集到 `rl-service/data/AMiner/`，或使用自有论文数据并修改 `aminer_loader.py` 的解析逻辑

3. **初始化数据库**：
   ```bash
   mysql -u root -p < backend/src/main/resources/research_db.sql
   python rl-service/scripts/migrate_to_neo4j.py
   python rl-service/scripts/generate_paper_embeddings.py
   ```

4. **启动服务**（按 1→2→3 顺序）并访问 `http://localhost:5173`

5. **训练模型**（可选）：`python rl-service/train.py`，训练完成后重启 Python 服务加载新权重

### 许可

MIT License
