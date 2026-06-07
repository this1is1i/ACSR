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
```

Startup order: 1. RL service (:8000) → 2. Backend (:8080) → 3. Frontend (:5173)

Seed test data: `backend/src/main/resources/seed_claim_test_data.sql` populates paper-author claim test data for development.

No dedicated lint/checkstyle is configured for any service.

## Architecture

### Recommendation flow
`frontend GET /api/recommend` → `RecommendController` → `RecommendServiceImpl` → `PythonRecClient` → Python `POST /recommend`. The backend converts local paper IDs to AMiner IDs before calling Python, then maps returned AMiner IDs back to local `Paper` rows. Falls back to local popular papers if Python service is unavailable.

**PythonRecClient** wraps five Python endpoints: `POST /recommend`, `POST /train`, `GET /model/info`, `GET /health`, `POST /learning-path`. Python API also exposes `POST /model/reload` for hot-reloading model weights without restart. All calls have try/catch degradation — failures return null/false, never propagate exceptions. The learning-path endpoint returns path nodes with mastery, color, and glowIntensity for frontend 3D visualization.

**Training flow**: `train.py` returns `(agent, metrics)` including `best_reward`, `total_episodes`, and `model_version`. The API server polls `_training_status` during training; frontend `AdminConsole` has a "模型训练" tab that triggers training and polls `GET /model/info` every 2s until completion, then displays the results dialog.

### Realtime chat (dual-path)
- **REST**: `/api/message/*` for history/persistence (returns raw entities, not `Result` envelope)
- **WebSocket**: SockJS/STOMP on `/ws-messages` for live delivery. Publish to `/app/*`, subscribe to `/user/queue/private` (direct messages) and `/topic/user-status` (presence). JWT is in STOMP message body, not HTTP `Authorization` header — `MessageWebSocketController` re-validates from the payload.

### Python service internal structure
`services/recommendation_service.py` orchestrates: feature building → candidate generation → Actor-Critic ranking → explanation generation → model reload. Key subdirectories:
- `recommender/` — candidate generation (`candidate_generator.py`), ranking (`ranker.py`)
- `env/` — RL environment (`rec_env.py`)
- `models/` — actor/critic network definitions
- `features/` — feature building from MySQL behavior data
- `data/` — `mysql_data.py` (MySQL access layer for behavior_log, user_interest_history), `mock_data.py` (training-only mock data generator)
- `knowledge_graph/` — KG construction (`kg_builder.py`), embedding (`kg_embedder.py`), Neo4j queries (`graph_query.py`), storage abstraction (`graph_storage.py`)
- `learning_path/` — path building and propagation
- `api/` — FastAPI server (recommend, train, model/info, model/reload, learning-path, health)
- `utils/text_utils.py` — text cleaning/tokenization utilities

Everything is driven from `config.py:default_config` — a single `@dataclass` with state dims, KG settings, network structure, training hyperparameters, and reward weights.

### Mock data: training vs production split

Training and production now share the same data architecture — both prefer real data with graceful fallback:

- **Training** (`train.py` → `env/rec_env.py`): Initializes MySQL + KG data sources via `_init_real_data_sources()`. When available, `reset()` samples real users from MySQL, builds states from real behavior data, and generates candidates from the real paper pool. The `_simulate_interaction()` method still simulates user feedback (we can't get real-time user feedback during training), but the simulation uses real user interest × real paper topic vectors for realistic reward signals. Falls back to `MockDataGenerator` only when MySQL or KG is unavailable.
- **Production** (`recommendation_service.py`): Same data path — real MySQL + Neo4j with three-tier fallback:
  - Feature building: MySQL `user_feature_snapshot` cache (6h TTL) → MySQL real-time from `behavior_log` + `user_interest_history` → deterministic hash-based random vectors (`_fallback_vec`)
  - KG loading: Neo4j → local JSON/Pickle file → AMiner data file → no KG (mock paper pool fallback)
  - Paper pool: Real papers from KG nodes → 500 fake `CandidateItem` entries (`_build_mock_pool()`)

There is no `use_mock` config flag — all fallback decisions are made at runtime by checking resource availability.

### AC network: per-paper pairwise scoring

The Actor network in `models/actor.py` takes **both user state AND paper features** as input, producing a per-paper relevance score:

```
Input:  [user_state(96) | paper_features(32)] → 128 维
Output: 1 scalar logit per paper
For N candidates: batch N×(128) → N logits → softmax → N probabilities
```

**`score_candidates(state, candidate_features)`** (`actor.py:67-85`): Expands user state to (N, 96), concatenates with (N, 32) paper features, runs a single GPU forward pass, applies softmax. N=50 papers in ∼0.1ms.

**Production ranking** (`recommender/ranker.py`): Three-step pipeline:
1. **Raw scores** — Actor probability (batched `score_candidates()`), cosine similarity (vectorized `topic_matrix @ base_state`), KG topology score (`user_kg` computed once, then per-paper `dot(user_kg, paper_emb)`)
2. **Quality gate** — filter out papers where ALL three scores fall below thresholds (`min_cos_similarity=0.05`, `min_actor_score=0.001`), preventing normalization from "rescuing" irrelevant papers
3. **Min-max normalization** — normalize each score dimension to [0,1] independently, eliminating magnitude differences (Actor softmax outputs cluster around ~0.02 while cosine can reach 0.7–0.8)

**Final ranking formula** (`ranker.py`):
- With KG: `final = 0.5 * norm(actor) + 0.3 * norm(cos_sim) + 0.2 * norm(kg_score)`
- Without KG: `final = 0.6 * norm(actor) + 0.4 * norm(cos_sim)`

The Critic (`models/critic.py`) is unchanged: input state_dim, output scalar V(s), used only during training for TD error calculation.

### Config parameters (Python RL service)

Key numbers in `rl-service/config.py`:

| Parameter | Value | Role |
|-----------|-------|------|
| `base_state_dim` | 64 | interest(32) + history(32) |
| `paper_feature_dim` | 32 | Paper features for actor input |
| `action_num` | 50 | Max candidates per request |
| `top_k` | 10 | Default recommendation count (overridden by request param `k`) |
| `kg_embedding_dim` | 32 | KG embedding dimension |
| `state_dim` | 96 (=64+32, dynamic) | Full actor/critic input; computed as `base_state_dim + (kg_embedding_dim if use_kg else 0)` — 64 when KG disabled |
| `actor_hidden` | 128 | Actor hidden layer width |
| `critic_hidden` | 128 | Critic hidden layer width |
| `max_episodes` | 300 | Training episodes (overridden by request param) |
| `max_steps` | 50 | Steps per episode |
| `entropy_coeff` | 0.01 | Entropy regularization |
| `min_cos_similarity` | 0.05 | Quality gate: minimum cosine similarity |
| `min_actor_score` | 0.001 | Quality gate: minimum Actor probability |

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
| `/api/community/posts/{postId}/like` | Auth | POST toggle like (creates/deletes `post_like` row) |
| `/api/community/posts/search` | Auth* | GET search posts by keyword |
| `/api/community/posts/my` | Auth | GET current user's own posts |
| `/api/community/posts/{postId}` | Auth | PUT update own post; DELETE remove own post |
| `/api/user/password` | Auth | PUT change password |
| `/api/knowledge/keywords` | Public | GET keyword tags for registration selector |
| `/api/paper/claim` | Auth | POST claim authorship of a paper |
| `/api/paper/claims` | Auth | GET list own author claims |
| `/api/message/recommended-collaborators` | Auth | Researcher collaborator recommendations (shared-interest overlap, top 2, excludes contacts/self) |
| `/api/user/search` | Auth | Search users by username or research_interests, query params `q` + `limit` |
| `/api/user/favorites` | Auth | Papers favorited by current user (from `behavior_log`, not `favourite` table) |
| `/api/behavior/history` | Auth | GET user's behavior log history; DELETE to clear |
| `/api/recommend/train` | Auth | POST trigger RL model training |
| `/api/recommend/model/info` | Auth | GET current model state (version, trainStep, bestReward) |
| `/api/admin/posts` | ADMIN | List all posts with status filter |
| `/api/admin/posts/{id}/status` | ADMIN | Review/approve/reject posts |
| `/api/admin/users` | ADMIN | List users, update roles |
| `/api/admin/papers/import` | ADMIN | Batch paper import |
| `/api/message/*` | Auth | Chat history (raw entities, not `Result` envelope) |
| `/ws-messages/**` | STOMP | Real-time messaging (JWT in STOMP body, whitelisted in SecurityConfig) |

### Community data model
Posts and comments use `post` and `comment` tables. Posts have status lifecycle (0=PENDING → 1=APPROVED / 2=REJECTED) managed by admin via `/api/admin/posts/{id}/status`. Comments support nested replies via `parent_id`. The `CommunityDto` classes encode the request/response shapes; see `CommunityController` for the exact contract.

**Like/reply counts are computed dynamically** via `PostLikeMapper.batchCountLikes()` and `CommentMapper.batchCountReplies()` — the `post.like_count` and `post.reply_count` columns have been removed (see `db_migration.sql`). This eliminates stale counter bugs.

### User interest tracking
`UserInterestHistory` (table `user_interest_history`) records interest tags per user with weight, source, and date. Interests are seeded at registration from the `researchInterests` comma-separated field and feed into the recommendation pipeline. Paper reads are tracked via `behavior_log` (action=`read`) — the `browse_history` table was removed (2026-05-15) as its functionality was subsumed.

### Frontend route structure
| Path | Auth | Role | View |
|------|------|------|------|
| `/login` | Public | — | Login |
| `/search` | Public | — | Search |
| `/paper/:id` | Public | — | PaperDetail |
| `/paper/aminer/:aminerId` | Public | — | PaperDetail (by AMiner ID) |
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
- **Behavior tracking feeds recommendation**: POST `/api/behavior` writes to `behavior_log` (actions: `click`, `favorite`, `read`). `feature_builder.py` builds user vectors via weighted pooling: click=0.5, read=1.0, favorite=2.0, plus reading duration bonus (+0.5 per 60s, max +2.0). PaperDetail tracks real reading duration via `enterTime` → `onBeforeUnmount` delta.
- **Collaborator recommendations**: `PrivateMessageServiceImpl.getRecommendedCollaborators()` parses each user's `researchInterests` comma-separated string into a Set, computes intersection overlap between same-role users, returns top 2 by overlap descending, excluding existing contacts and self.
- **Community post likes**: `post_like` table (user_id + post_id unique constraint). `PostItem.liked` field is backfilled from `PostLikeMapper.findLikedPostIds()` during `listPosts()`. Toggle endpoint creates or deletes the like row. Like counts are computed via `batchCountLikes()` rather than stored in a `post.like_count` column.
- **Paper search filters**: `/api/paper/search` accepts `yearFrom` (int year) and `sortBy` (`relevance` / `newest` / `cited`). These are applied in both the MyBatis SQL path and the Neo4j fallback path.
- **Tune recommender** via `rl-service/config.py:default_config`, not scattered constants. Config includes MySQL connection (`MYSQL_HOST`, `MYSQL_PORT` env vars), Neo4j connection (`GRAPH_NEO4J_URI`, `GRAPH_NEO4J_USERNAME`, `GRAPH_NEO4J_PASSWORD` env vars), and RL hyperparameters.
- **Python service data sources**: MySQL for user behavior/interest history (`data/mysql_data.py`), Neo4j for paper graph and KG embeddings (`knowledge_graph/`). Data flow: `behavior_log` + `user_interest_history` → feature building → MySQL-backed `user_feature_snapshot` cache; Paper pool and KG from Neo4j, embeddings computed from graph structure at runtime.
- **Frontend stack**: Vue 3 + Vite + Element Plus + Pinia. `@` alias maps to `src/`. Vite dev server proxies `/api` → `http://localhost:8080`. CORS on backend permits `http://localhost:*` and `http://127.0.0.1:*`.
- **WebSocket auth**: `MessageWebSocketController` validates JWT from STOMP message body, not headers. The `/ws-messages/**` path is in the Spring Security whitelist (auth happens at STOMP CONNECT).
- **Database**: MySQL 8.0 (`research_db`, user=root, pass=qwer1234). Current tables (13): `user`, `paper`, `behavior_log`, `private_messages`, `user_contacts`, `post`, `post_like`, `comment`, `user_interest_history`, `favourite`, `user_feature_snapshot`, `rl_training_log`, `paper_author_claim`. Removed tables (2026-05-15): `board`, `browse_history`, `notification`, `kg_relation`. Schema migrations: `backend/src/main/resources/db_migration.sql` (adds FKs, drops `post.like_count`/`post.reply_count`).
- **Neo4j**: `bolt://localhost:7687`, user=neo4j, pass=seeworld123. Stores Paper nodes and 5 relationship types (HAS_KEYWORD, AUTHOR_OF, CITE, PUBLISH_IN, CO_AUTHOR). KG data flows through Python service — backend no longer uses MySQL `kg_entity`/`kg_relation` tables.
- **KnowledgeGraph edges**: Python `path_builder.to_dict()` outputs `src`/`dst`, but 3D force-graph expects `source`/`target`. The frontend normalizes edges with `l.src || l.source` / `l.dst || l.target` fallback. Keep both field forms when modifying the graph pipeline.
- **MCP config**: `.mcp.json` at repo root configures two MCP servers — `refactor` (regex-based code search/replace via `@myuon/refactor-mcp`) and `drawio` (JGraph draw.io diagram generation via `@drawio/mcp`).
- **Avatar uploads**: Frontend dev server proxies `/uploads` → `http://localhost:8080` for avatar image loading.

## Architecture Diagrams

`docs/draw/` contains 16 draw.io diagrams (open with draw.io desktop or VS Code extension):

| File | Content |
|------|---------|
| `01-04-*-package.drawio` | System overview + 3-layer package diagrams |
| `05-07-*-class.drawio` | Backend recommend, community/message, and Python service class diagrams |
| `08-10-*-flow.drawio` | Recommend pipeline, learning path, and collaborator matching flowcharts |
| `11-er-diagram.drawio` | Database ER diagram (Chinese labels, 1/N cardinality) |
| `12-neo4j-graph.drawio` | Neo4j graph schema (Paper nodes + 5 relationship types) |
| `13-16-*-BPD.drawio` | Business process diagrams: recommend, learning-path, collaborator-matching, forum-judge |

## Known Limitations
- No test suite for any service. Backend has 4 unit tests; RL service and frontend have no tests.
- Python service must be running for KG, visualization, and recommendation features to work with real data (no in-process fallback for KG/learning-path).
- `VisualizationServiceImpl` was slimmed to a single method (`getVisualizationData`); all stats/chart/trend endpoints are gone — the profile page now gets visualization data from the KG endpoint only.
- The `favourite` table exists in MySQL but has no dedicated Java mapper/service — favorites are tracked via `behavior_log` (action=`favorite`) and queried through `BehaviorLogMapper.findFavoritesByUserId()`.
