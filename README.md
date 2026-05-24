# ACScientificRecommendation

科研推荐系统示例仓库，包含 **Vue 3 前端**、**Spring Boot 后端** 和 **Python FastAPI 强化学习推荐服务** 三个部分。前端负责交互和可视化，后端负责鉴权、数据访问与系统集成，Python 服务负责推荐、训练和知识图谱相关能力。

## 项目结构

| 目录 | 作用 |
| --- | --- |
| `frontend/` | Vue 3 + Vite 前端，包含推荐、社区、知识图谱、实时私信等页面 |
| `backend/` | Spring Boot 后端，提供 REST API、JWT 鉴权、MyBatis-Plus 数据访问、SockJS/STOMP 实时消息 |
| `rl-service/` | FastAPI 推荐服务，负责编排特征构建、候选召回、Actor-Critic 排序、解释生成和模型训练 |

## 启动顺序

1. 启动 `rl-service`，默认端口 `8000`
2. 启动 `backend`，默认端口 `8080`
3. 启动 `frontend`，默认端口 `5173`

## 常用命令

### Frontend

```bash
cd frontend
npm install
npm run dev
npm run build
npm run preview
npm run mcp:playwright
npx playwright test tests/design.spec.js
```

说明：
- `package.json` 中没有单独的 lint 脚本。
- Playwright 用于前端设计页/界面的烟雾测试。

### Backend

```bash
mvn -f backend clean package
mvn -f backend spring-boot:run
mvn -f backend test
mvn -f backend -Dtest=FullyQualifiedTestClassName#testMethod test
```

说明：
- `backend/pom.xml` 使用 Spring Boot 3.2 和 Java 17。
- 当前未配置独立的 checkstyle / lint 工作流。

### RL Service

```bash
cd rl-service
uvicorn api.server:app --reload --host 0.0.0.0 --port 8000
python train.py
python -m unittest tests.test_runtime_fixes
python -m unittest tests.test_runtime_fixes.RuntimeFixesTest.test_config_reads_neo4j_settings_from_environment
```

说明：
- 也可以直接运行 `python rl-service\api\server.py` 启动 API。
- 当前仓库中已提交的回归测试位于 `rl-service/tests/test_runtime_fixes.py`。

## 高层架构

- 前端通过 `frontend/src/utils/request.js` 中的 Axios 实例访问后端，基础路径为 `/api`，JWT 保存在 `localStorage`，并自动附加到 `Authorization: Bearer ...` 请求头。
- 后端是主要集成层：负责 REST API、MySQL/MyBatis-Plus、Spring Security JWT、以及 SockJS/STOMP 实时消息，并通过 `PythonRecClient` 调用 Python 推荐服务。
- 推荐主链路为：`frontend -> GET /api/recommend -> RecommendController -> RecommendServiceImpl -> PythonRecClient -> POST /recommend`。
- 后端会先把本地论文 ID 转换成 AMiner ID 发给 Python 服务，再把 Python 返回的 AMiner ID 映射回本地 `Paper` 数据。
- 如果 Python 推荐服务不可用，`RecommendServiceImpl` 会自动降级为本地热门论文推荐，而不是直接让接口失败。
- 实时私信采用双通道：历史记录和持久化走 `/api/message/*` REST 接口，实时收发与在线状态走 `/ws-messages` SockJS/STOMP 通道。
- Python 服务不只是一个推理包装层。`rl-service/services/recommendation_service.py` 统一编排用户特征、候选生成、强化学习排序、解释生成与模型热重载。

## 关键约定

- 大多数后端接口使用统一返回结构 `Result { code, message, data }`，但 `/api/message/*` 返回的是原始实体或列表，因此前端消息页通常兼容 `res.data || res` 两种读取方式。
- Spring Security 采用无状态 JWT。控制器里通常通过 `Long userId = (Long) authentication.getPrincipal();` 读取当前用户，因为 JWT 过滤器把数值型用户 ID 放进了 principal。
- Java 与 Python 服务之间保持 **snake_case** JSON 协议；`PythonRecClient` 通过 `@JsonProperty` 进行 camelCase / snake_case 映射。
- 推荐链路中的跨服务主键是 **AMiner ID**，不是本地数据库的自增 `paper.id`。
- 用户行为记录不仅用于埋点，也直接参与推荐：前端调用 `/api/behavior/*`，后端写入 `behavior_log`，再据此构建推荐历史。
- 推荐系统的共享参数集中在 `rl-service/config.py` 的 `default_config`，不要把关键常量分散到各模块里。
- WebSocket 鉴权不是靠 HTTP `Authorization` 头，而是把 JWT 放进 STOMP 消息体，再由 `MessageWebSocketController` 二次校验。
- `paper` 表中的 `abstract` 列映射到 `Paper.java` 的 `abstrakt` 字段；修改实体或 DTO 时要保留这个映射。

## 当前实现状态提示

- KG 和可视化数据已通过 Python 服务走 Neo4j + MySQL 真实数据链路，不再是静态/演示 payload。
- Python 服务必须运行才能使用 KG、可视化和推荐功能（不可用时推荐有本地 fallback，但 KG 无 fallback）。
- 仓库仅包含一个 Playwright 烟雾测试（`tests/design.spec.js`），无完整测试套件。
