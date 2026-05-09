# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Three-part academic research recommendation system: Vue 3 frontend, Spring Boot backend (Java 17, Spring Boot 3.2), and Python FastAPI RL recommendation service. See `README.md` for detailed architecture descriptions.

## Commands

### Frontend (`frontend/`)
```bash
cd frontend && npm install
npm run dev            # Dev server on :5173, proxies /api -> :8080
npm run build          # Production build
npm run preview        # Preview built app
npm run mcp:playwright # Playwright smoke test via MCP
npx playwright test tests/design.spec.js   # Single smoke test
```

### Backend (`backend/`)
```bash
mvn -f backend clean package
mvn -f backend spring-boot:run             # Dev run on :8080
mvn -f backend test
mvn -f backend -Dtest=FullyQualifiedClassName#methodName test
```

### RL Service (`rl-service/`)
```bash
cd rl-service
uvicorn api.server:app --reload --host 0.0.0.0 --port 8000
python train.py
python -m unittest tests.test_runtime_fixes
python -m unittest tests.test_runtime_fixes.RuntimeFixesTest.test_config_reads_neo4j_settings_from_environment
```

Startup order: 1. RL service (:8000) → 2. Backend (:8080) → 3. Frontend (:5173)

No dedicated lint/checkstyle is configured for any service.

## Architecture

### Recommendation flow
`frontend GET /api/recommend` → `RecommendController` → `RecommendServiceImpl` → `PythonRecClient` → Python `POST /recommend`. The backend converts local paper IDs to AMiner IDs before calling Python, then maps returned AMiner IDs back to local `Paper` rows. Falls back to local popular papers if Python service is unavailable.

**PythonRecClient** exposes five endpoints: `POST /recommend`, `POST /train`, `GET /model/info`, `GET /health`, `POST /learning-path`. All calls have try/catch degradation — failures return null/false, never propagate exceptions. The learning-path endpoint returns path nodes with mastery, color, and glowIntensity for frontend 3D visualization.

### Realtime chat (dual-path)
- **REST**: `/api/message/*` for history/persistence (returns raw entities, not `Result` envelope)
- **WebSocket**: SockJS/STOMP on `/ws-messages` for live delivery. Publish to `/app/*`, subscribe to `/user/queue/private` (direct messages) and `/topic/user-status` (presence). JWT is in STOMP message body, not HTTP `Authorization` header — `MessageWebSocketController` re-validates from the payload.

### Python service internal structure
`services/recommendation_service.py` orchestrates: feature building → candidate generation → Actor-Critic ranking → explanation generation → model reload. Key subdirectories:
- `recommender/` — candidate generation, ranking
- `env/` — RL environment (`rec_env.py`)
- `models/` — actor/critic network definitions
- `features/` — feature building from MySQL behavior data
- `data/` — `mysql_data.py` (MySQL access layer for behavior_log, user_interest_history)
- `knowledge_graph/` — KG construction (`kg_builder.py`), embedding (`kg_embedder.py`), Neo4j queries (`graph_query.py`), storage abstraction (`graph_storage.py`)
- `learning_path/` — path building and propagation
- `api/` — FastAPI server (recommend, train, model management, learning-path, health)
- `utils/text_utils.py` — text cleaning/tokenization utilities

Everything is driven from `config.py:default_config` — a single `@dataclass` with state dims, KG settings, network structure, training hyperparameters, and reward weights.

### Backend package conventions
Standard Spring Boot layered architecture:
- `controller/` — REST endpoints, auth via `(Long) authentication.getPrincipal()`
- `service/` + `service/impl/` — business logic interfaces and implementations
- `repository/` — MyBatis-Plus mappers (extends `BaseMapper<T>`)
- `entity/` — database entities + request/response DTOs
- `config/` — Spring Security, CORS, MyBatis-Plus, RestTemplate, WebSocket
- `client/` — `PythonRecClient` (cross-service HTTP calls)
- `util/` — `JwtUtil`, `Result<T>` response envelope
- `graph/` — graph paper domain objects (separate from relational entities)

### API route summary (beyond authentication)

| Endpoint | Auth | Notes |
|----------|------|-------|
| `/api/user/register` | Public | Auto-logs in on success, returns JWT |
| `/api/user/login` | Public | Returns `LoginResponse { token, userId, username, role }` |
| `/api/user/profile` | Auth | GET own profile; PUT to update (bio, avatar, researchInterests) |
| `/api/user/avatar/upload` | Auth | POST multipart, returns avatar URL |
| `/api/paper/list` | Public | Paginated paper list |
| `/api/paper/search` | Public | Search by keyword, filters |
| `/api/paper/{id}` | Public | Paper detail |
| `/api/paper/{id}/download/txt` | Public | TXT download |
| `/api/paper/aminer/{aminerId}` | Public | Lookup by AMiner ID |
| `/api/recommend` | Auth | Personalized recommendations; falls back to popular if RL service down |
| `/api/behavior` | Auth | POST click/favorite/read actions → `behavior_log` |
| `/api/knowledge/graph` | Auth | KG nodes + edges from Neo4j via Python learning-path endpoint — nodes include color/glowIntensity |
| `/api/visualization/data` | Auth | Visualization payload for profile page; builds KG from Python /learning-path, keyword frequencies from interest_history |
| `/api/community/posts` | Auth* | GET list (optional auth); POST create |
| `/api/community/posts/{id}/comments` | Auth* | GET list (optional auth); POST create |
| `/api/admin/posts` | ADMIN | List all posts with status filter |
| `/api/admin/posts/{id}/status` | ADMIN | Review/approve/reject posts |
| `/api/admin/users` | ADMIN | List users, update roles |
| `/api/admin/papers/import` | ADMIN | Batch paper import |
| `/api/message/*` | Auth | Chat history (raw entities, not `Result` envelope) |
| `/ws-messages/**` | STOMP | Real-time messaging (JWT in STOMP body, whitelisted in SecurityConfig) |

### Community data model
Posts and comments use `post` and `comment` tables. Posts have status lifecycle (`draft` → `published` / `rejected`) managed by admin. Comments support nested replies via `parent_id`. The `CommunityDto` classes encode the request/response shapes; see `CommunityController` for the exact contract.

### User interest tracking
`UserInterestHistory` (table `user_interest_history`) records interest tags per user with weight, source, and date. Interests are seeded at registration from the `researchInterests` comma-separated field and feed into the recommendation pipeline. The `browse_history` table separately tracks paper reads.

### Frontend route structure
| Path | Auth | Role | View |
|------|------|------|------|
| `/login` | Public | — | Login |
| `/search` | Public | — | Search |
| `/paper/:id` | Public | — | PaperDetail |
| `/` | Auth redirect | — | → `/home` or `/search` |
| `/home` | Auth | — | Home |
| `/knowledge-graph` | Auth | — | KnowledgeGraph |
| `/community` | Auth | — | Community |
| `/profile` | Auth | — | Profile |
| `/profile/edit` | Auth | — | EditProfile |
| `/messages` | Auth | — | RealtimeChat |
| `/admin` | Auth | ADMIN | AdminConsole |

Router guards check `public` meta and `roles` meta, redirecting unauthenticated users to `/login` and unauthorized users to `/home`.

## Key Conventions

- **API response format**: Most endpoints return `Result { code, message, data }` envelope. Exception: `/api/message/*` returns raw entities/lists. Frontend handles both with `res.data || res`.
- **Axios instance** (`src/utils/request.js`): `baseURL: '/api'`, 15s timeout, auto-attaches JWT `Authorization: Bearer ...` header, 401 → clear auth + redirect login. Responses unwrap to `res.data` by default; pass `config.rawResponse = true` to get the full response object.
- **Auth**: Stateless JWT. `JwtFilter` extracts token from `Authorization` header, validates, and stores numeric user ID as principal. Controllers get current user via `(Long) authentication.getPrincipal()`. Password encoder is BCrypt.
- **Cross-service IDs**: AMiner IDs (`paper.aminer_id`) are the recommendation cross-service key, NOT local `paper.id`.
- **JSON contract**: snake_case between Java and Python. `PythonRecClient` uses `@JsonProperty` for camelCase/snake_case mapping on all request/response DTOs.
- **`abstract` column**: Mapped to `Paper.java` field `abstrakt`. Preserve this mapping when modifying paper entities/DTOs.
- **Config properties** (`application.yml` or env vars): `python.rec-service.base-url` (default `http://localhost:8000`), `python.rec-service.timeout` (default 5000ms), `python.rec-service.read-timeout` (default 10000ms), `jwt.header` (default `Authorization`).
- **Behavior tracking feeds recommendation**: POST `/api/behavior` writes to `behavior_log` (actions: `click`, `favorite`, `read`) → recommendation history is built from `behavior_log` before calling Python.
- **Tune recommender** via `rl-service/config.py:default_config`, not scattered constants. Config includes MySQL connection (`MYSQL_HOST`, `MYSQL_PORT` env vars), Neo4j connection (`GRAPH_NEO4J_URI`, `GRAPH_NEO4J_USERNAME`, `GRAPH_NEO4J_PASSWORD` env vars), and RL hyperparameters.
- **Python service data sources**: MySQL for user behavior/interest history (`data/mysql_data.py`), Neo4j for paper graph and KG embeddings (`knowledge_graph/`). Data flow: `behavior_log` + `user_interest_history` → feature building → MySQL-backed `user_feature_snapshot` cache; Paper pool and KG from Neo4j, embeddings computed from graph structure at runtime.
- **Frontend stack**: Vue 3 + Vite + Element Plus + Pinia. `@` alias maps to `src/`. Vite dev server proxies `/api` → `http://localhost:8080`. CORS on backend permits `http://localhost:*` and `http://127.0.0.1:*`.
- **WebSocket auth**: `MessageWebSocketController` validates JWT from STOMP message body, not headers. The `/ws-messages/**` path is in the Spring Security whitelist (auth happens at STOMP CONNECT).
- **Database**: MySQL 8.0 (`research_db`, user=root, pass=qwer1234). Tables: `user`, `paper`, `behavior_log`, `private_message`, `user_contact`, `post`, `comment`, `announcements`, `user_interest_history`, `browse_history`, `user_feature_snapshot`, `rl_training_log`, `favourite`, `board`, `notification`.
- **Neo4j**: `bolt://localhost:7687`, user=neo4j, pass=seeworld123. Stores Paper nodes and 5 relationship types (HAS_KEYWORD, AUTHOR_OF, CITE, PUBLISH_IN, CO_AUTHOR). KG data flows through Python service — backend no longer uses MySQL `kg_entity`/`kg_relation` tables.

## Known Limitations
- `VisualizationServiceImpl.buildInterestTrends` falls back to profile `researchInterests` + random data when `user_interest_history` has no monthly data.
- The repo contains a Playwright smoke test (`tests/design.spec.js`) but no comprehensive test suite for the frontend.
- Python service must be running for KG, visualization, and recommendation features to work with real data (no in-process fallback for KG/learning-path).
