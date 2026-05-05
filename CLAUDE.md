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

**PythonRecClient** exposes four endpoints: `POST /recommend`, `POST /train`, `GET /model/info`, `GET /health`. All calls have try/catch degradation — failures return null/false, never propagate exceptions.

### Realtime chat (dual-path)
- **REST**: `/api/message/*` for history/persistence (returns raw entities, not `Result` envelope)
- **WebSocket**: SockJS/STOMP on `/ws-messages` for live delivery. Publish to `/app/*`, subscribe to `/user/queue/private` (direct messages) and `/topic/user-status` (presence). JWT is in STOMP message body, not HTTP `Authorization` header — `MessageWebSocketController` re-validates from the payload.

### Python service internal structure
`services/recommendation_service.py` orchestrates: feature building → candidate generation → Actor-Critic ranking → explanation generation → model reload. Key subdirectories:
- `recommender/` — candidate generation, ranking, explanation
- `env/` — RL environment (`rec_env.py`)
- `models/` — actor/critic network definitions
- `features/` — feature building from user behavior
- `knowledge_graph/` — KG construction, embedding, Neo4j queries
- `learning_path/` — path building and propagation
- `api/` — FastAPI server (training endpoints, model management)

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
- **Tune recommender** via `rl-service/config.py:default_config`, not scattered constants.
- **Frontend stack**: Vue 3 + Vite + Element Plus + Pinia. `@` alias maps to `src/`. Vite dev server proxies `/api` → `http://localhost:8080`. CORS on backend permits `http://localhost:*` and `http://127.0.0.1:*`.
- **WebSocket auth**: `MessageWebSocketController` validates JWT from STOMP message body, not headers. The `/ws-messages/**` path is in the Spring Security whitelist (auth happens at STOMP CONNECT).
- **Database**: MySQL 8.0. Tables include `user`, `paper`, `behavior_log`, `private_message`, `user_contact`, `post`, `comment`, `announcements`, `user_interest_history`, `browse_history`, `kg_entity`, `kg_relation`.

## Known Limitations
- `KnowledgeController` and `VisualizationController` serve demo/static payloads, not fully database-driven.
- The repo contains a Playwright smoke test (`tests/design.spec.js`) but no comprehensive test suite for the frontend.
