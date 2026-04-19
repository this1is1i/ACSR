# 第六章 Spring Boot 后端系统实现

---

## 6.1 后端架构设计

### 6.1.1 分层架构

Spring Boot 后端采用经典**四层分层架构**，各层职责清晰、依赖单向：

```
表现层（Controller）  ← 处理 HTTP 请求，参数校验，统一响应格式
      ↓
业务层（Service）      ← 业务逻辑编排，事务管理，调用外部服务
      ↓
数据访问层（Repository）← MyBatis-Plus ORM，MySQL CRUD
      ↓
数据库层（MySQL）       ← 持久化存储（user/paper/behavior_log/post）
```

此外，系统新增 **Client 层**（`client/PythonRecClient.java`），专门负责与 Python 强化学习推荐服务的 HTTP 通信，与 Service 层解耦，便于单独测试和替换。

### 6.1.2 技术选型

| 技术 | 版本 | 用途 |
|---|---|---|
| Spring Boot | 3.2.0 | 主框架，自动配置，内嵌 Tomcat |
| Spring Security | 6.x | 认证授权，JWT 过滤器 |
| MyBatis-Plus | 3.5.5 | ORM 框架，分页插件，逻辑删除 |
| MySQL | 8.0+ | 主数据库，全文检索索引 |
| JJWT | 0.12.3 | JWT 生成与解析 |
| RestTemplate | Spring 内置 | 调用 Python FastAPI 服务 |
| Lombok | 1.18+ | 消除样板代码 |

### 6.1.3 统一响应格式

所有接口统一返回 `Result<T>` 对象：

```json
{
  "code":    0,          
  "message": "success",  
  "data":    { ... }     
}
```

错误码约定：`0`=成功，`400`=参数错误，`401`=未登录，`403`=无权限，`500`=系统错误。

---

## 6.2 安全认证机制

### 6.2.1 JWT 认证流程

系统采用**无状态 JWT 认证**，避免服务端维护 Session，支持水平扩展：

```
登录请求 POST /api/user/login
    → 校验用户名密码（BCrypt）
    → 生成 JWT（userId + username + role + exp）
    → 返回 token

后续请求：
    → 携带 Authorization: Bearer <token>
    → JwtFilter 解析 Token，提取 userId
    → 注入 SecurityContextHolder
    → Controller 通过 Authentication.getPrincipal() 获取 userId
```

### 6.2.2 JWT 负载结构

```json
{
  "sub":      "1",          
  "username": "alice",      
  "role":     "USER",       
  "iat":      1700000000,   
  "exp":      1700086400    
}
```

Token 有效期默认 24 小时（可在 `application.yml` 配置）。

### 6.2.3 安全配置白名单

以下接口无需认证，对外公开：
- `POST /api/user/register`：用户注册
- `POST /api/user/login`：用户登录
- `GET /api/paper/list`、`/search`、`/{id}`：论文浏览（公开数据）

---

## 6.3 推荐服务调用机制（核心）

### 6.3.1 调用链路

Spring Boot 与 Python FastAPI 推荐服务的完整调用链路如下：

```
用户 GET /api/recommend?k=10
    ↓
RecommendController.getRecommendations(k, auth)
    ↓
RecommendServiceImpl.getRecommendations(userId, k)
    ├─ 查询 behavior_log 获取历史行为（20条）
    ├─ 将 paper_id 转为 AMiner ID 列表
    ↓
PythonRecClient.getRecommendations(userId, k, history)
    ↓
POST http://localhost:8000/recommend
    {
      "user_id": "1",
      "k": 10,
      "history": ["aminer_001", "aminer_002"],
      "strategy": "hybrid"
    }
    ↓
Python FastAPI 返回推荐结果
    ↓
组装：AMiner ID → 数据库 Paper 对象（批量查询）
    ↓
Result<RecommendResponse> 返回前端
```

### 6.3.2 降级策略

当 Python 推荐服务不可用时（网络超时、服务未启动），系统自动降级为**热门论文推荐**（按被引次数排序），确保前端始终能收到推荐结果：

```java
// RecommendServiceImpl.java
PythonRecClient.RecResponse pyResp =
    pythonRecClient.getRecommendations(userId, k, historyAminers);

if (pyResp == null) {
    // 降级：返回热门论文
    items = fallbackPopularRecommendations(k);
}
```

响应中 `pythonServiceAvailable` 字段指示降级状态，前端可据此展示不同的 UI 提示。

### 6.3.3 超时配置

```yaml
python:
  rec-service:
    timeout: 5000       # 连接超时 5s
    read-timeout: 10000 # 读取超时 10s
```

连接超时和读取超时独立配置，防止 Python 服务响应慢拖垮主服务线程池。

---

## 6.4 用户行为数据收集

### 6.4.1 行为类型设计

系统收集三类用户行为，构成强化学习的交互信号 $\{click, favorite, read\}$：

| 行为类型 | 触发时机 | RL 奖励对应项 |
|---|---|---|
| `click` | 用户点击论文标题 | $c_{\text{click}}$（点击信号） |
| `favorite` | 用户收藏论文 | $c_{\text{fav}}$（收藏信号） |
| `read` | 用户关闭阅读界面时上报时长 | $c_{\text{read}}$（阅读时长，归一化） |

### 6.4.2 行为日志接口

Vue 前端在用户交互时自动调用：

```javascript
// Vue 前端示例（用户点击论文时）
axios.post('/api/behavior/click', {
    paperId: paper.id,
    source: 'recommend'    // 来源：推荐/搜索/详情
}, { headers: { Authorization: `Bearer ${token}` } })
```

### 6.4.3 历史行为利用

用户历史行为在推荐时作为上下文传入 Python 服务：

```java
// 查询用户最近 20 条行为（去重论文 ID）
List<Long> historyPaperIds =
    behaviorLogMapper.findInteractedPaperIds(userId, 20);

// 转为 AMiner ID → 传入 Python 推荐服务
List<String> historyAminers = resolveAminers(historyPaperIds);
```

Python 侧据此过滤已读论文，并利用历史 embedding 更新用户状态向量，实现个性化推荐。

---

## 6.5 数据库设计

系统共设计 5 张核心表：

| 表名 | 记录数量级 | 主要索引 |
|---|---|---|
| `user` | 万级 | `username` 唯一索引 |
| `paper` | 百万级（AMiner） | `year`、`citation_count`、全文索引 |
| `behavior_log` | 亿级 | `user_id`、`timestamp`、联合索引 |
| `post` | 万级 | `user_id`、`create_time` |
| `recommendation_log` | 千万级 | `user_id`、`create_time` |

`paper` 表建有 MySQL FULLTEXT 索引（`title` + `abstract`），支持中文全文检索（需配置 `ngram` 解析器）。MyBatis-Plus 在全文索引不可用时自动降级为 LIKE 模糊查询。

---

## 6.6 API 接口汇总

| 方法 | 路径 | 认证 | 功能 |
|---|---|---|---|
| POST | `/api/user/register` | 否 | 用户注册 |
| POST | `/api/user/login` | 否 | 用户登录，返回 JWT |
| GET | `/api/user/profile` | 是 | 当前用户信息 |
| GET | `/api/paper/list` | 否 | 分页论文列表 |
| GET | `/api/paper/{id}` | 否 | 论文详情 |
| GET | `/api/paper/search` | 否 | 关键词搜索 |
| POST | `/api/behavior/click` | 是 | 记录点击 |
| POST | `/api/behavior/favorite` | 是 | 记录收藏 |
| POST | `/api/behavior/read` | 是 | 记录阅读时长 |
| GET | `/api/recommend` | 是 | **Top-K 推荐（核心）** |
| POST | `/api/recommend/train` | 是 | 触发 Python 模型训练 |
| GET | `/api/recommend/model/info` | 是 | 查询模型状态 |

---

*启动方式：配置 `application.yml` 中的 MySQL 连接信息，执行 `schema.sql` 建表，然后运行 `mvn spring-boot:run`。Python 推荐服务需同时在 `:8000` 端口运行。*
