# Copilot instructions for ACScientificRecommendation

Purpose
- Short reference for Copilot/assistant sessions: how to build, run, test, and where key conventions and architecture live.

1) Build / run / test / lint (per-subproject)

Frontend (Vue 3 + Vite)
- Install: from repo root: cd frontend && npm install
- Dev server: npm run dev (Vite dev server, default port 5173)
- Build: npm run build
- Preview build: npm run preview
- Tests/Lint: no dedicated test or lint scripts detected in package.json. Single-file tests not present.

Backend (Spring Boot / Maven)
- Build: mvn -f backend clean package
- Run (dev): mvn -f backend spring-boot:run
- Run the packaged JAR: java -jar backend\target\*.jar
- Test suite: mvn -f backend test
- Run a single test: mvn -f backend -Dtest=FullyQualifiedTestClassName#testMethod test
- Lint: no centralized linter/checkstyle configured in pom.xml (none detected).

RL service (Python FastAPI)
- Setup: python -m venv .venv && .\.venv\Scripts\activate
- Install deps: pip install -r requirements.txt (if present). If not, install core deps observed in code: pip install fastapi uvicorn pydantic sentence-transformers pymysql networkx neo4j
- Run (dev): cd rl-service && uvicorn api.server:app --reload --host 0.0.0.0 --port 8000
  (Alternative: python rl-service\api\server.py also starts uvicorn when executed directly.)
- Tests/Lint: no test runner or linter configuration discovered.

2) High-level architecture (big picture)
- Three-tier application:
  1. Frontend: Vue 3 + Vite (frontend/) serves UI and calls backend APIs (axios).
  2. Backend: Spring Boot (backend/) hosts REST APIs, persists behavior logs to MySQL and acts as glue. It contains a Python client (PythonRecClient) that calls the RL service.
  3. RL recommender: Python FastAPI service (rl-service/) implements an Actor-Critic recommender, exposes endpoints: POST /recommend, POST /train, POST /model/reload, GET /model/info, GET /health. It uses local training, model checkpoints, optional KG embeddings, and provides hot-reload for models.
- Default ports observed: frontend (Vite) ≈ 5173, backend (Spring Boot) ≈ 8080, Python recommender (uvicorn) = 8000. Backend application.yml includes python service base-url: http://localhost:8000.

3) Key conventions and repository-specific patterns
- Inter-service contract: Backend → Python recommender uses POST /recommend and expects snake_case payloads (see PythonRecClient). Keep request/response shapes in sync when altering models or API fields.
- rl-service coding conventions:
  - config.py exports default_config used across modules. Modify default_config to change global behavior rather than scattering constants.
  - env/ (rec_env.py) implements an OpenAI Gym-style environment: reset() → (state, info), step(action) → (next_state, reward, done, info).
  - train.py orchestrates training; API triggers async background training and hot-reload via RecommendationService.reload_model().
  - Knowledge graph and dataset modules are optional plugs: graph storage mentions networkx/neo4j, data importers reference pymysql.
- Backend database schema is under backend/src/main/resources/schema.sql. MyBatis-Plus is used for ORM patterns (look at mappers & entities under backend/src/main/java).
- Frontend: standard Vite + Vue 3 SFCs (script setup). axios is used for HTTP; check where base URLs are set (frontend code references backend endpoints via Vue/axios configs).

4) Existing docs and files consulted
- frontend/README.md (basic Vite+Vue info)
- backend/pom.xml and backend/src/main/resources/application.yml (Spring Boot wiring and python base-url)
- rl-service/api/server.py and several rl-service markdowns (paper_*.md) describing system/algorithms.

5) AI assistant / other assistant configs
- No CLAUDE.md, .cursorrules, AGENTS.md, .windsurfrules, AIDER_CONVENTIONS.md, or .clinerules found. If such files are added, copy relevant constraints/commands into this instructions file.

Quick local dev order (recommended)
1. Start rl-service (uvicorn on :8000) so model endpoints are available.
2. Start backend (mvn spring-boot:run on :8080).
3. Start frontend (npm run dev) and open Vite dev URL.

If you want this file expanded to include exact environment variables, recommended requirements.txt, or Playwright/CI setup, say which area to add.

6) MCP servers (added)
- Playwright (E2E) — frontend/tests + playwright.config.js
  - Install: cd frontend && npm install -D @playwright/test && npx playwright install
  - Run: cd frontend && npm run mcp:playwright
  - Purpose: automated visual/E2E checks against the design HTML pages (frontend/public/design/*). Tests included: frontend/tests/design.spec.js
- Lighthouse / Performance — suggest using Lighthouse CI in CI when adding CI workflow. No config added automatically.
- Accessibility / a11y — recommend axe or Playwright-axe integration; can be added to tests if needed.

Design assets added:
- Copied ter/*.html into frontend/public/design/ as design mockups: index.html, search.html, visualization.html, community.html, profile.html.
  - Access locally when frontend dev server runs: http://localhost:5173/design/index.html

Frontend changes made:
- Added dev scripts: "serve:design" and "mcp:playwright" to frontend/package.json
- Added Playwright config: frontend/playwright.config.js and an example test at frontend/tests/design.spec.js

-- end of file
