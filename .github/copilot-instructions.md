# Copilot instructions for ACScientificRecommendation

## Build, test, and lint commands

### Frontend (`frontend/`)
- Install: `cd frontend && npm install`
- Dev server: `npm run dev`
- Production build: `npm run build`
- Preview built app: `npm run preview`
- Playwright smoke test for the design pages (after installing `@playwright/test` and browsers): `npm run mcp:playwright`
- Run a single Playwright test file: `npx playwright test tests/design.spec.js`
- No dedicated lint script is defined in `frontend/package.json`.

### Backend (`backend/`)
- Build package: `mvn -f backend clean package`
- Run in dev: `mvn -f backend spring-boot:run`
- Run tests: `mvn -f backend test`
- Run a single test: `mvn -f backend -Dtest=FullyQualifiedTestClassName#testMethod test`
- No dedicated lint/checkstyle plugin is configured in `backend/pom.xml`.

### RL service (`rl-service/`)
- Run API locally: `cd rl-service && uvicorn api.server:app --reload --host 0.0.0.0 --port 8000`
- Alternative API entrypoint: `python rl-service\api\server.py`
- Run training directly: `python rl-service\train.py`
- Run committed regression tests: `cd rl-service && python -m unittest tests.test_runtime_fixes`
- Run a single RL service test: `cd rl-service && python -m unittest tests.test_runtime_fixes.RuntimeFixesTest.test_config_reads_neo4j_settings_from_environment`
- No repo-level lint command is configured for this service.

## High-level architecture

- This repo is a three-part system: a Vue 3 + Vite frontend, a Spring Boot backend, and a Python FastAPI recommender service.
- The frontend talks to the backend through Axios with `baseURL: '/api'`. JWTs are stored in `localStorage` and attached as `Authorization: Bearer ...` headers by `frontend/src/utils/request.js`.
- The backend is the main integration layer. It exposes REST endpoints under `/api`, persists application data in MySQL through MyBatis-Plus entities/mappers, handles STOMP/SockJS realtime messaging, and calls the Python recommender through `PythonRecClient`.
- Personalized recommendations flow like this: frontend `GET /api/recommend` -> `RecommendController` -> `RecommendServiceImpl` -> `PythonRecClient` -> Python `POST /recommend`. The backend converts local paper IDs to AMiner IDs before the Python call, then maps returned AMiner IDs back onto local `Paper` rows before sending the final response to the frontend.
- The backend recommendation path has a built-in fallback: if the FastAPI service is unavailable, `RecommendServiceImpl` returns popular papers from the local database instead of failing the whole request.
- Realtime chat is a dual-path feature: the frontend uses `/api/message/*` REST endpoints for conversation history and persistence, then opens a SockJS/STOMP connection to `/ws-messages` for live private delivery and presence updates handled by `MessageWebSocketController`.
- The Python service is not just an inference wrapper. `services/recommendation_service.py` orchestrates feature building, candidate generation, Actor-Critic ranking, and explanation generation. `api/server.py` also exposes training/model-management endpoints and reloads the model after background training.
- Knowledge-graph support is optional on the Python side and is driven from `default_config` in `rl-service/config.py`. Both runtime recommendation and training build around that same shared config object.
- Some backend data APIs are currently demo/static payloads for frontend views rather than database-backed model output, notably `KnowledgeController` and `VisualizationController`.

## Key conventions

- Most backend REST responses use the common envelope `Result { code, message, data }`, but `/api/message/*` endpoints return raw entities/lists/void. Because the frontend Axios wrapper returns `res.data`, callers against wrapped APIs usually consume `response.data`, while messaging views often need `res.data || res`.
- Spring Security is stateless JWT auth. Controllers commonly read the current user as `Long userId = (Long) authentication.getPrincipal();`, because the JWT filter stores the numeric user ID as the principal.
- Keep the backend/Python contract in sync with snake_case JSON fields. `PythonRecClient` uses `@JsonProperty` to bridge Java camelCase DTOs with FastAPI request/response payloads.
- AMiner IDs are the cross-service identifier for recommendation data. The backend database uses numeric `paper.id`, but recommendation history sent to Python and recommendation items returned from Python are keyed by `paper.aminer_id`.
- User interaction logging is part of the recommender pipeline, not just analytics. Frontend actions call `/api/behavior/*`, those records are stored in `behavior_log`, and recommendation history is built from that table before calling the Python service.
- Tune recommender behavior through `rl-service/config.py` instead of scattering constants. The service and training code both depend on the shared `default_config`.
- Realtime messaging uses SockJS + STOMP, not raw WebSocket. The frontend connects to `/ws-messages`, publishes to `/app/*`, subscribes to `/user/queue/private` for direct messages, and listens on `/topic/user-status` for presence updates. STOMP payloads include the JWT token in the message body because `MessageWebSocketController` re-validates auth from the payload instead of an `Authorization` header.
- The `paper` table column named `abstract` is mapped to the Java field `abstrakt` in `Paper.java`; preserve that mapping when changing paper DTO/entity code.

## Useful run order

1. Start the RL service on port 8000.
2. Start the Spring Boot backend on port 8080.
3. Start the Vite frontend on port 5173.
