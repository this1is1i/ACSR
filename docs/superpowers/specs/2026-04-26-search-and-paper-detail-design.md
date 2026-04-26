# Search And Paper Detail Design

## Background

This repository already has:

- a backend `paper` table defined in `backend/src/main/resources/research_db.sql`
- paper APIs under `/api/paper`
- a public search page in `frontend/src/views/Search.vue`
- recommendation cards on the homepage through `RecommendList.vue` and `PaperCard.vue`

The current user-visible problems are:

1. search returns no useful data even though the refreshed schema and seed data include papers
2. homepage recommendations and search results do not share a consistent paper-detail experience
3. users cannot download a paper summary as a `.txt` file

## Goals

1. Make keyword search return papers from the current dataset.
2. Let homepage recommendation cards and search results both navigate to a single dedicated paper-detail page.
3. Provide a download button on the detail page that downloads a `.txt` file containing at least the paper's basic information.

## Non-Goals

- No DOI search in this change.
- No PDF download in this change.
- No full advanced-search implementation for the existing UI filters.
- No redesign of the search or homepage layout beyond what is needed to support the new flow.

## Database Findings

The refreshed schema in `research_db.sql` defines:

- table: `paper`
- columns: `id`, `aminer_id`, `title`, `abstract`, `keywords`, `authors`, `venue`, `year`, `citation_count`, `embedding`, `deleted`
- indexes:
  - unique index on `aminer_id`
  - btree indexes on `year` and `citation_count`
  - fulltext index `ft_title_abstract(title, abstract)`

The seed data also shows that:

- `authors` and `keywords` are stored as JSON-array strings in MySQL
- many records have `embedding = NULL`
- there is enough local paper data for search to return matches without relying only on Neo4j

## Chosen Approach

Use **backend-led unified search + dedicated detail route + backend txt download**.

This keeps search behavior consistent, avoids pushing query logic into the frontend, and gives both homepage recommendations and search results one shared paper-detail destination.

## Backend Design

### 1. Search behavior

Keep `/api/paper/search`, but broaden its matching logic to cover:

- `title`
- `abstract`
- `authors`
- `keywords`
- `venue`

The backend search flow should be:

1. If Neo4j is enabled, keep using `GraphPaperService.search(keyword, limit)` as the first path.
2. If Neo4j returns no results or Neo4j is unavailable, use a stronger MySQL fallback query.
3. The MySQL fallback must not depend only on `MATCH(title, abstract) AGAINST(...)`, because the refreshed schema/data may still fail to match user-entered terms depending on tokenization and keyword shape.

The MySQL fallback query should combine:

- fulltext search on `title` and `abstract` when available
- `LIKE` matching on `title`
- `LIKE` matching on `abstract`
- `LIKE` matching on `authors`
- `LIKE` matching on `keywords`
- `LIKE` matching on `venue`

Default ordering for fallback results:

1. `citation_count DESC`
2. `year DESC`

This is intentionally simple and reliable. It prioritizes returning useful results over building a full ranking system.

### 2. Detail retrieval

Reuse the existing detail API shape:

- `GET /api/paper/{id}`

The frontend detail page will treat the database `paper.id` as the canonical route parameter.

This works with both search and recommendation flows because:

- MySQL search results already have `id`
- graph-backed results are already shadow-written into the `paper` table through `upsertShadowPaper`, which produces a local `id`

### 3. TXT download endpoint

Add a dedicated paper download endpoint:

- `GET /api/paper/{id}/download/txt`

Response behavior:

- content type: `text/plain; charset=UTF-8`
- `Content-Disposition` attachment header with a readable filename derived from the paper title

The downloaded txt content must include:

- title
- authors
- venue
- year
- AMiner ID
- citation count
- keywords
- abstract

If a field is missing, the txt should still be generated with an empty value rather than failing the request.

## Frontend Design

### 1. Dedicated paper detail page

Add a new route:

- `/paper/:id`

Add a new page component:

- `frontend/src/views/PaperDetail.vue`

The detail page responsibilities are:

- fetch paper details from `GET /api/paper/{id}`
- render the paper's core information
- expose a download button for the txt export

### 2. Search page behavior

Update `Search.vue` so that:

- the dialog-based detail view is removed
- each result card's “查看详情” action routes to `/paper/:id`
- result mapping preserves backend `id` and `aminerId`
- the search placeholder reflects actual behavior and no longer claims DOI support

The existing filter UI can remain visible, but this change does not make those filters backend-driven.

### 3. Homepage recommendation behavior

Update homepage recommendation cards so that the “阅读” action:

1. records click behavior as it already does
2. navigates to `/paper/:id`

This should be implemented in the shared recommendation card flow rather than duplicated in the homepage.

### 4. Download behavior

The detail page will be the only place with a download button.

The frontend download action should call the backend txt endpoint and trigger a browser download.

No list-page download button will be added in this change.

## Expected Files To Change

### Backend

- `backend/src/main/java/com/example/research/repository/PaperMapper.java`
- `backend/src/main/java/com/example/research/service/impl/PaperServiceImpl.java`
- `backend/src/main/java/com/example/research/controller/PaperController.java`

### Frontend

- `frontend/src/router/index.js`
- `frontend/src/api/paper.js`
- `frontend/src/views/Search.vue`
- `frontend/src/components/PaperCard.vue`
- `frontend/src/views/PaperDetail.vue` (new)

## User Experience Outcome

After this change:

1. A user enters a keyword on the search page and receives actual paper results.
2. Clicking a search result opens a standalone detail page instead of a modal.
3. Clicking a homepage recommendation opens the same standalone detail page.
4. The detail page provides a single download button that exports the paper's information as a `.txt` file.

## Verification Plan

The implementation will be considered correct when all of the following are true:

1. Searching for terms that exist in seeded data, such as `Transformer`, `Reinforcement Learning`, or `NeurIPS`, returns results.
2. Clicking a homepage recommendation opens `/paper/:id`.
3. Clicking a search result opens `/paper/:id`.
4. The detail page renders the paper title, authors, venue, year, keywords, and abstract.
5. Clicking the detail-page download button downloads a `.txt` file containing the paper information.

## Scope Check

This design is intentionally limited to one coherent feature set:

- search reliability
- shared paper-detail navigation
- txt download from the detail page

It does not branch into DOI support, PDF export, or full advanced filtering, so it is appropriate for a single implementation plan.
