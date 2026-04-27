# Search And Paper Detail Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix paper search against the refreshed schema, add a shared standalone paper-detail page, and support txt downloads from that detail page.

**Architecture:** Keep `/api/paper/search` as the single backend search entry point, but broaden its fallback matching so it returns data from the current `paper` table reliably. Route both homepage recommendations and search results into one frontend detail page backed by `/api/paper/{id}`, and expose a dedicated backend txt download endpoint for that page.

**Tech Stack:** Spring Boot 3, MyBatis-Plus, Maven, Vue 3, Vue Router, Element Plus, Playwright

---

## File Map

- `backend/src/main/java/com/example/research/repository/PaperMapper.java` — expand MySQL fallback search beyond fulltext-only matching
- `backend/src/main/java/com/example/research/service/impl/PaperServiceImpl.java` — keep graph-first behavior, then call the stronger MySQL fallback
- `backend/src/main/java/com/example/research/controller/PaperController.java` — expose txt download endpoint
- `backend/src/test/java/com/example/research/service/impl/PaperServiceImplSearchTest.java` — regression test for search fallback behavior
- `backend/src/test/java/com/example/research/controller/PaperControllerDownloadTest.java` — regression test for txt download response
- `frontend/src/router/index.js` — add `/paper/:id` route
- `frontend/src/api/paper.js` — add txt download helper
- `frontend/src/views/Search.vue` — remove modal detail flow and navigate to route-based detail page
- `frontend/src/views/PaperDetail.vue` — new standalone detail page with download button
- `frontend/src/components/PaperCard.vue` — let the shared recommendation card navigate after recording click behavior
- `frontend/tests/paper-detail.spec.js` — Playwright regression coverage for search-to-detail and detail download UI
- `frontend/tests/recommend-navigation.spec.js` — Playwright regression coverage for homepage recommendation navigation

### Task 1: Fix Backend Paper Search

**Files:**
- Modify: `backend/src/main/java/com/example/research/repository/PaperMapper.java:11-20`
- Modify: `backend/src/main/java/com/example/research/service/impl/PaperServiceImpl.java:67-78`
- Test: `backend/src/test/java/com/example/research/service/impl/PaperServiceImplSearchTest.java`

- [ ] **Step 1: Write the failing test**

```java
package com.example.research.service.impl;

import com.example.research.entity.Paper;
import com.example.research.graph.GraphPaperService;
import com.example.research.repository.PaperMapper;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.*;

class PaperServiceImplSearchTest {

    @Test
    void searchPapers_uses_mysql_fallback_when_graph_search_is_empty() {
        PaperMapper paperMapper = mock(PaperMapper.class);
        GraphPaperService graphPaperService = mock(GraphPaperService.class);
        PaperServiceImpl service = new PaperServiceImpl(
                paperMapper,
                graphPaperService,
                new ObjectMapper()
        );

        Paper paper = new Paper();
        paper.setId(1L);
        paper.setTitle("Attention Is All You Need");

        when(graphPaperService.isEnabled()).thenReturn(true);
        when(graphPaperService.search("Transformer", 20)).thenReturn(List.of());
        when(paperMapper.searchByKeywordExpanded("Transformer", 20)).thenReturn(List.of(paper));

        List<Paper> results = service.searchPapers("Transformer", 20);

        assertThat(results).extracting(Paper::getTitle)
                .containsExactly("Attention Is All You Need");
        verify(paperMapper).searchByKeywordExpanded("Transformer", 20);
    }
}
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
mvn -f backend -Dtest=PaperServiceImplSearchTest test
```

Expected: FAIL because `PaperMapper` does not yet define `searchByKeywordExpanded(...)`, so the new test will not compile or will fail to link against the current service behavior.

- [ ] **Step 3: Write minimal implementation**

Update `PaperMapper.java` to add a reliable fallback query:

```java
@Select("""
    <script>
    SELECT * FROM paper
    WHERE deleted = 0
      AND (
        LOWER(title) LIKE CONCAT('%', LOWER(#{keyword}), '%')
        OR LOWER(`abstract`) LIKE CONCAT('%', LOWER(#{keyword}), '%')
        OR LOWER(COALESCE(authors, '')) LIKE CONCAT('%', LOWER(#{keyword}), '%')
        OR LOWER(COALESCE(keywords, '')) LIKE CONCAT('%', LOWER(#{keyword}), '%')
        OR LOWER(COALESCE(venue, '')) LIKE CONCAT('%', LOWER(#{keyword}), '%')
      )
    ORDER BY citation_count DESC, year DESC
    LIMIT #{limit}
    </script>
    """)
List<Paper> searchByKeywordExpanded(@Param("keyword") String keyword, @Param("limit") int limit);
```

Update `PaperServiceImpl.java` to call the new mapper method:

```java
@Override
public List<Paper> searchPapers(String keyword, int limit) {
    String normalized = keyword == null ? "" : keyword.trim();
    if (normalized.isBlank()) {
        return List.of();
    }
    if (graphPaperService.isEnabled()) {
        List<GraphPaper> graphResults = graphPaperService.search(normalized, limit);
        if (!graphResults.isEmpty()) {
            return graphResults.stream()
                    .map(this::upsertShadowPaper)
                    .collect(Collectors.toList());
        }
    }
    return paperMapper.searchByKeywordExpanded(normalized, limit);
}
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
mvn -f backend -Dtest=PaperServiceImplSearchTest test
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/src/main/java/com/example/research/repository/PaperMapper.java backend/src/main/java/com/example/research/service/impl/PaperServiceImpl.java backend/src/test/java/com/example/research/service/impl/PaperServiceImplSearchTest.java
git commit -m "fix: broaden paper search fallback"
```

### Task 2: Add Backend TXT Download Endpoint

**Files:**
- Modify: `backend/src/main/java/com/example/research/controller/PaperController.java:50-74`
- Test: `backend/src/test/java/com/example/research/controller/PaperControllerDownloadTest.java`

- [ ] **Step 1: Write the failing test**

```java
package com.example.research.controller;

import com.example.research.entity.Paper;
import com.example.research.service.PaperService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.web.servlet.MockMvc;

import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(PaperController.class)
class PaperControllerDownloadTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private PaperService paperService;

    @Test
    void downloadTxt_returns_plain_text_attachment() throws Exception {
        Paper paper = new Paper();
        paper.setId(1L);
        paper.setTitle("Attention Is All You Need");
        paper.setAuthors("[\"Vaswani, A\",\"Shazeer, N\"]");
        paper.setVenue("NeurIPS");
        paper.setYear(2017);
        paper.setAminerId("aminer_004");
        paper.setCitationCount(50000);
        paper.setKeywords("[\"Transformer\",\"Attention\",\"NLP\"]");
        paper.setAbstrakt("We propose a new simple network architecture...");

        when(paperService.getPaperById(1L)).thenReturn(paper);

        mockMvc.perform(get("/api/paper/1/download/txt"))
                .andExpect(status().isOk())
                .andExpect(header().string("Content-Type", org.hamcrest.Matchers.containsString("text/plain")))
                .andExpect(header().string("Content-Disposition", org.hamcrest.Matchers.containsString("attachment;")))
                .andExpect(content().string(org.hamcrest.Matchers.containsString("Attention Is All You Need")))
                .andExpect(content().string(org.hamcrest.Matchers.containsString("NeurIPS")))
                .andExpect(content().string(org.hamcrest.Matchers.containsString("Transformer")));
    }
}
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
mvn -f backend -Dtest=PaperControllerDownloadTest test
```

Expected: FAIL because `/api/paper/{id}/download/txt` does not exist yet.

- [ ] **Step 3: Write minimal implementation**

Add this endpoint to `PaperController.java`:

```java
@GetMapping("/{id:\\d+}/download/txt")
public ResponseEntity<String> downloadPaperTxt(@PathVariable Long id) {
    Paper paper = paperService.getPaperById(id);
    String content = """
            标题: %s
            作者: %s
            会议/期刊: %s
            年份: %s
            AMiner ID: %s
            被引次数: %s
            关键词: %s

            摘要:
            %s
            """.formatted(
            paper.getTitle() == null ? "" : paper.getTitle(),
            paper.getAuthors() == null ? "" : paper.getAuthors(),
            paper.getVenue() == null ? "" : paper.getVenue(),
            paper.getYear() == null ? "" : paper.getYear(),
            paper.getAminerId() == null ? "" : paper.getAminerId(),
            paper.getCitationCount() == null ? "" : paper.getCitationCount(),
            paper.getKeywords() == null ? "" : paper.getKeywords(),
            paper.getAbstrakt() == null ? "" : paper.getAbstrakt()
    );

    String filename = (paper.getTitle() == null || paper.getTitle().isBlank() ? "paper" : paper.getTitle())
            .replaceAll("[\\\\/:*?\"<>|]", "_");

    return ResponseEntity.ok()
            .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"" + filename + ".txt\"")
            .contentType(MediaType.parseMediaType("text/plain; charset=UTF-8"))
            .body(content);
}
```

Also add the imports used by the endpoint:

```java
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
mvn -f backend -Dtest=PaperControllerDownloadTest test
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/src/main/java/com/example/research/controller/PaperController.java backend/src/test/java/com/example/research/controller/PaperControllerDownloadTest.java
git commit -m "feat: add paper txt download endpoint"
```

### Task 3: Add Dedicated Paper Detail Page

**Files:**
- Create: `frontend/src/views/PaperDetail.vue`
- Modify: `frontend/src/router/index.js:4-15`
- Modify: `frontend/src/api/paper.js:1-6`
- Modify: `frontend/src/views/Search.vue:101-153`
- Test: `frontend/tests/paper-detail.spec.js`

- [ ] **Step 1: Write the failing test**

```javascript
const { test, expect } = require('@playwright/test')

test('search result opens standalone paper detail page', async ({ page }) => {
  await page.route('**/api/paper/search**', async route => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        code: 0,
        message: 'success',
        data: [
          {
            id: 1,
            aminerId: 'aminer_004',
            title: 'Attention Is All You Need',
            authors: '["Vaswani, A","Shazeer, N"]',
            venue: 'NeurIPS',
            year: 2017,
            abstrakt: 'Transformer paper abstract'
          }
        ]
      })
    })
  })

  await page.route('**/api/paper/1', async route => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        code: 0,
        message: 'success',
        data: {
          id: 1,
          aminerId: 'aminer_004',
          title: 'Attention Is All You Need',
          authors: '["Vaswani, A","Shazeer, N"]',
          venue: 'NeurIPS',
          year: 2017,
          citationCount: 50000,
          keywords: '["Transformer","Attention","NLP"]',
          abstrakt: 'Transformer paper abstract'
        }
      })
    })
  })

  await page.goto('/search')
  await page.getByPlaceholder(/输入关键词/i).fill('Transformer')
  await page.getByRole('button', { name: '智能搜索' }).click()
  await page.getByRole('button', { name: '📖 查看详情' }).click()

  await expect(page).toHaveURL(/\/paper\/1$/)
  await expect(page.getByText('Attention Is All You Need')).toBeVisible()
  await expect(page.getByRole('button', { name: /下载 txt/i })).toBeVisible()
})
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd frontend && npx playwright test tests/paper-detail.spec.js
```

Expected: FAIL because `/paper/:id` and `PaperDetail.vue` do not exist yet, and `Search.vue` still opens a modal instead of routing.

- [ ] **Step 3: Write minimal implementation**

Add the route in `frontend/src/router/index.js`:

```javascript
{ path: '/paper/:id', component: () => import('@/views/PaperDetail.vue'), meta: { public: true } },
```

Add the API helper in `frontend/src/api/paper.js`:

```javascript
export const downloadPaperTxt = (id) =>
  request.get(`/paper/${id}/download/txt`, { responseType: 'blob' })
```

Create `frontend/src/views/PaperDetail.vue`:

```vue
<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import Sidebar from '@/components/Sidebar.vue'
import { getPaperById, downloadPaperTxt } from '@/api/paper'

const route = useRoute()
const paper = ref(null)

async function loadPaper() {
  const res = await getPaperById(route.params.id)
  paper.value = res.data
}

async function handleDownload() {
  const res = await downloadPaperTxt(route.params.id)
  const blob = new Blob([res], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${paper.value?.title || 'paper'}.txt`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('TXT 下载已开始')
}

onMounted(loadPaper)
</script>
```

Update `Search.vue` to remove the dialog state and route instead:

```javascript
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

function openDetail(paper) {
  if (!paper?.id) return
  router.push(`/paper/${paper.id}`)
}
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
cd frontend && npx playwright test tests/paper-detail.spec.js
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/router/index.js frontend/src/api/paper.js frontend/src/views/Search.vue frontend/src/views/PaperDetail.vue frontend/tests/paper-detail.spec.js
git commit -m "feat: add standalone paper detail page"
```

### Task 4: Route Homepage Recommendations To The Shared Detail Page

**Files:**
- Modify: `frontend/src/components/PaperCard.vue:42-77`
- Test: `frontend/tests/recommend-navigation.spec.js`

- [ ] **Step 1: Write the failing test**

```javascript
const { test, expect } = require('@playwright/test')

test('homepage recommendation card routes to shared detail page after recording click', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('token', 'fake-token')
    localStorage.setItem('userInfo', JSON.stringify({ id: 1, role: 'USER' }))
  })

  await page.route('**/api/recommend**', async route => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        code: 0,
        message: 'success',
        data: {
          recommendations: [
            {
              paperId: 1,
              title: 'Attention Is All You Need',
              authors: ['Vaswani, A'],
              venue: 'NeurIPS',
              year: 2017,
              citationCount: 50000,
              reason: 'Highly relevant'
            }
          ]
        }
      })
    })
  })

  await page.route('**/api/behavior/click', async route => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({ code: 0, message: 'success', data: null })
    })
  })

  await page.route('**/api/paper/1', async route => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        code: 0,
        message: 'success',
        data: {
          id: 1,
          title: 'Attention Is All You Need',
          authors: '["Vaswani, A"]',
          venue: 'NeurIPS',
          year: 2017,
          abstrakt: 'Transformer paper abstract'
        }
      })
    })
  })

  await page.goto('/home')
  await page.getByRole('button', { name: '阅读' }).first().click()

  await expect(page).toHaveURL(/\/paper\/1$/)
  await expect(page.getByText('Attention Is All You Need')).toBeVisible()
})
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd frontend && npx playwright test tests/recommend-navigation.spec.js
```

Expected: FAIL because `PaperCard.vue` only records the click today and does not route to `/paper/:id`.

- [ ] **Step 3: Write minimal implementation**

Update `PaperCard.vue`:

```vue
<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

async function handleClick() {
  try {
    await recordClick(props.paper.paperId || props.paper.id, props.source)
  } catch {}
  const targetId = props.paper.paperId || props.paper.id
  if (targetId) {
    router.push(`/paper/${targetId}`)
  }
}
</script>
```

Keep the button label as `阅读` so the homepage card interaction stays familiar while reusing the new detail route.

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
cd frontend && npx playwright test tests/recommend-navigation.spec.js
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/PaperCard.vue frontend/tests/recommend-navigation.spec.js
git commit -m "feat: route recommendations to paper detail"
```

## Self-Review Notes

- **Spec coverage:** Task 1 covers search reliability, Task 2 covers txt download, Task 3 covers route-based detail for search results, and Task 4 covers homepage recommendation navigation.
- **Placeholder scan:** No TODO/TBD placeholders remain; each task has concrete files, test code, commands, and expected outcomes.
- **Type consistency:** The plan consistently uses `paper.id` for frontend routing, `GET /api/paper/{id}` for detail retrieval, and `GET /api/paper/{id}/download/txt` for txt export.
