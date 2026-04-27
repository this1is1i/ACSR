# Frontend UI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the frontend into one unified dark “future lab” design system where personalized recommendation and learning path become the primary user journey, search becomes a secondary workspace, and the admin experience becomes a cockpit-style dashboard.

**Architecture:** Start by extracting a shared visual foundation: tokens, shell, headers, and grouped navigation. Then redesign the user-facing journey around home → recommendation/path → detail/graph, followed by collaboration pages, and finally the admin cockpit. Preserve existing API contracts and derive new UI summaries from current frontend data sources instead of inventing backend dependencies.

**Tech Stack:** Vue 3, Vue Router, Element Plus, Axios, Chart.js, existing custom CSS, Playwright, Vite

---

## Planned File Structure

### Shared foundation

- Create: `frontend/src/styles/tokens.css` — global color, typography, radius, spacing, and motion tokens for the redesign
- Create: `frontend/src/styles/layout-system.css` — shared shell, panel, grid, and page-section utilities
- Create: `frontend/src/components/layout/AppShell.vue` — reusable shell wrapper with ambient background and main content frame
- Create: `frontend/src/components/layout/PageHeader.vue` — reusable page heading with title, subtitle, and action slot
- Modify: `frontend/src/style.css` — import tokens/layout styles and align global theme defaults
- Modify: `frontend/src/components/Sidebar.vue` — grouped navigation, vector icons, role-aware sections, improved active states

### Home / recommendation / path

- Create: `frontend/src/components/home/HubHero.vue` — hero summary for recommendation focus and current learning stage
- Create: `frontend/src/components/home/LearningPathPanel.vue` — path progress card with next-step guidance
- Create: `frontend/src/components/home/RecommendationStream.vue` — redesigned recommendation list section
- Create: `frontend/src/utils/path.js` — normalize visualization/path payload into homepage/profile/detail-friendly structures
- Modify: `frontend/src/views/Home.vue` — convert homepage into the personal research hub

### Search / paper detail

- Create: `frontend/src/components/search/SearchFilterRail.vue` — stable left filter rail
- Create: `frontend/src/components/search/SearchResultCard.vue` — redesigned result card with readable hierarchy
- Create: `frontend/src/components/paper/PaperPathRail.vue` — “path position / next step / related reading” rail
- Modify: `frontend/src/views/Search.vue` — convert search into a secondary research workspace
- Modify: `frontend/src/views/PaperDetail.vue` — make detail page a reading canvas with path context
- Modify: `frontend/src/utils/paper.js` — normalize additional path-context display helpers

### Path / profile / collaboration

- Create: `frontend/src/components/path/PathInsightRail.vue` — compact insight module reused by graph/profile
- Create: `frontend/src/components/profile/ResearchAssetsPanel.vue` — recommendation, saved papers, and path asset panel
- Create: `frontend/src/components/community/DiscussionContextRail.vue` — linked paper/topic context rail for community
- Create: `frontend/src/components/chat/ConversationRail.vue` — collaboration-oriented side rail for messaging
- Modify: `frontend/src/views/KnowledgeGraph.vue` — strengthen learning path hierarchy over generic analytics
- Modify: `frontend/src/views/Profile.vue` — foreground path/recommendation assets
- Modify: `frontend/src/views/Community.vue` — make paper/topic context more explicit
- Modify: `frontend/src/views/RealtimeChat.vue` — present messaging as a collaboration workspace

### Admin cockpit

- Create: `frontend/src/components/admin/AdminCockpitHero.vue` — admin mission header and active alert summary
- Create: `frontend/src/components/admin/AdminKpiGrid.vue` — KPI strip derived from current admin/user/post data
- Create: `frontend/src/components/admin/AdminActionRail.vue` — urgent approvals, import health, and role-change summaries
- Modify: `frontend/src/views/AdminConsole.vue` — replace tab-first layout with cockpit-first layout, then nested workspaces

### Tests

- Create: `frontend/playwright.redesign.config.cjs` — dedicated Playwright config for redesign regression tests
- Create: `frontend/tests/ui-shell.spec.js`
- Create: `frontend/tests/home-hub.spec.js`
- Create: `frontend/tests/search-detail-redesign.spec.js`
- Create: `frontend/tests/path-surfaces.spec.js`
- Create: `frontend/tests/collaboration-workspace.spec.js`
- Create: `frontend/tests/admin-cockpit.spec.js`

---

### Task 1: Establish the shared design system and shell

**Files:**
- Create: `frontend/playwright.redesign.config.cjs`
- Create: `frontend/tests/ui-shell.spec.js`
- Create: `frontend/src/styles/tokens.css`
- Create: `frontend/src/styles/layout-system.css`
- Create: `frontend/src/components/layout/AppShell.vue`
- Create: `frontend/src/components/layout/PageHeader.vue`
- Modify: `frontend/src/style.css`
- Modify: `frontend/src/components/Sidebar.vue`

- [ ] **Step 1: Write the failing test**

Create `frontend/playwright.redesign.config.cjs`:

```js
module.exports = {
  testDir: './tests',
  testMatch: ['ui-shell.spec.js', 'home-hub.spec.js', 'search-detail-redesign.spec.js', 'path-surfaces.spec.js', 'collaboration-workspace.spec.js', 'admin-cockpit.spec.js'],
  timeout: 30000,
  webServer: {
    command: 'npm run dev -- --host 127.0.0.1 --port 4173',
    port: 4173,
    reuseExistingServer: false,
  },
  use: {
    headless: true,
    baseURL: 'http://127.0.0.1:4173',
  },
}
```

Create `frontend/tests/ui-shell.spec.js`:

```js
import { test, expect } from '@playwright/test'

test('renders grouped future-lab shell for regular users', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('token', 'test-token')
    localStorage.setItem('userInfo', JSON.stringify({
      username: 'researcher',
      role: 'RESEARCHER',
      roleLabel: '研究者',
    }))
  })

  await page.goto('/home')

  await expect(page.locator('.app-shell')).toBeVisible()
  await expect(page.getByText('探索')).toBeVisible()
  await expect(page.getByText('协作')).toBeVisible()
  await expect(page.getByText('管理')).toHaveCount(0)
})
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd frontend
npx playwright test tests/ui-shell.spec.js --config=playwright.redesign.config.cjs
```

Expected: FAIL because `.app-shell` and grouped navigation labels do not exist yet.

- [ ] **Step 3: Write minimal implementation**

Create `frontend/src/styles/tokens.css`:

```css
:root {
  --ui-bg-base: #020617;
  --ui-bg-elevated: #0f172a;
  --ui-bg-muted: #111827;
  --ui-panel: rgba(15, 23, 42, 0.78);
  --ui-panel-strong: rgba(15, 23, 42, 0.92);
  --ui-border: rgba(148, 163, 184, 0.16);
  --ui-text-primary: #f8fafc;
  --ui-text-secondary: #94a3b8;
  --ui-accent-primary: #7c3aed;
  --ui-accent-secondary: #22d3ee;
  --ui-success: #22c55e;
  --ui-danger: #ef4444;
  --ui-radius-xl: 24px;
  --ui-radius-lg: 18px;
  --ui-radius-md: 14px;
  --ui-shadow-soft: 0 24px 60px rgba(2, 6, 23, 0.45);
  --ui-transition-fast: 180ms ease;
}
```

Create `frontend/src/styles/layout-system.css`:

```css
.app-shell {
  min-height: 100vh;
  background:
    radial-gradient(circle at top left, rgba(124, 58, 237, 0.16), transparent 28%),
    radial-gradient(circle at top right, rgba(34, 211, 238, 0.12), transparent 24%),
    var(--ui-bg-base);
  color: var(--ui-text-primary);
}

.app-shell__main {
  margin-left: 280px;
  min-height: 100vh;
  padding: 32px 40px 40px;
}

.ui-panel {
  background: var(--ui-panel);
  border: 1px solid var(--ui-border);
  border-radius: var(--ui-radius-xl);
  box-shadow: var(--ui-shadow-soft);
  backdrop-filter: blur(18px);
}
```

Create `frontend/src/components/layout/AppShell.vue`:

```vue
<template>
  <div class="app-shell">
    <Sidebar />
    <main class="app-shell__main">
      <slot />
    </main>
  </div>
</template>

<script setup>
import Sidebar from '@/components/Sidebar.vue'
</script>
```

Create `frontend/src/components/layout/PageHeader.vue`:

```vue
<template>
  <header class="page-header ui-panel">
    <div>
      <p class="page-header__eyebrow">{{ eyebrow }}</p>
      <h1 class="page-header__title">{{ title }}</h1>
      <p class="page-header__subtitle">{{ subtitle }}</p>
    </div>
    <div class="page-header__actions">
      <slot name="actions" />
    </div>
  </header>
</template>

<script setup>
defineProps({
  eyebrow: { type: String, default: '' },
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
})
</script>
```

Update `frontend/src/style.css` near the top:

```css
@import './styles/tokens.css';
@import './styles/layout-system.css';

body {
  margin: 0;
  background: var(--ui-bg-base);
  color: var(--ui-text-primary);
  font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
}
```

Update `frontend/src/components/Sidebar.vue` so the nav is grouped and role-aware:

```vue
<nav class="nav-menu" aria-label="Primary">
  <div class="nav-group">
    <div class="nav-group__label">探索</div>
    <router-link to="/home" class="nav-item">研究中枢</router-link>
    <router-link to="/knowledge-graph" class="nav-item">学习路径</router-link>
    <router-link to="/search" class="nav-item">辅助搜索</router-link>
  </div>

  <div class="nav-group">
    <div class="nav-group__label">协作</div>
    <router-link to="/community" class="nav-item">科研社区</router-link>
    <router-link to="/messages" class="nav-item">协作私信</router-link>
    <router-link to="/profile" class="nav-item">个人资产</router-link>
  </div>

  <div v-if="isAdmin" class="nav-group">
    <div class="nav-group__label">管理</div>
    <router-link to="/admin" class="nav-item">管理员驾驶舱</router-link>
  </div>
</nav>
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
cd frontend
npx playwright test tests/ui-shell.spec.js --config=playwright.redesign.config.cjs
npm run build
```

Expected: the Playwright shell test passes and the frontend build succeeds.

- [ ] **Step 5: Commit**

```bash
git add frontend/playwright.redesign.config.cjs frontend/tests/ui-shell.spec.js frontend/src/styles/tokens.css frontend/src/styles/layout-system.css frontend/src/components/layout/AppShell.vue frontend/src/components/layout/PageHeader.vue frontend/src/style.css frontend/src/components/Sidebar.vue
git commit -m "feat: add future-lab shell foundation"
```

### Task 2: Rebuild the homepage around recommendations and learning path

**Files:**
- Create: `frontend/tests/home-hub.spec.js`
- Create: `frontend/src/components/home/HubHero.vue`
- Create: `frontend/src/components/home/LearningPathPanel.vue`
- Create: `frontend/src/components/home/RecommendationStream.vue`
- Create: `frontend/src/utils/path.js`
- Modify: `frontend/src/views/Home.vue`
- Modify: `frontend/src/components/RecommendList.vue`
- Modify: `frontend/src/components/PaperCard.vue`

- [ ] **Step 1: Write the failing test**

Create `frontend/tests/home-hub.spec.js`:

```js
import { test, expect } from '@playwright/test'

test('home prioritizes recommendations and learning path over search', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('token', 'test-token')
    localStorage.setItem('userInfo', JSON.stringify({
      id: 1,
      username: 'researcher',
      role: 'RESEARCHER',
      roleLabel: '研究者',
    }))
  })

  await page.route(/\/api\/recommend(?:\?.*)?$/, async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        code: 200,
        message: 'success',
        data: {
          recommendations: [{ paperId: 1, title: 'Graph Attention Networks', authors: '["A"]', year: 2023, venue: 'AAAI', reason: 'next step' }],
        },
      }),
    })
  })

  await page.route('**/api/visualization/data', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        code: 200,
        message: 'success',
        data: {
          pathMeta: { topic: '图神经网络', estimatedHours: 12, coverage: 0.65 },
          nextNode: { name: 'Graph Attention Networks' },
        },
      }),
    })
  })

  await page.goto('/home')

  await expect(page.getByText('个性推荐')).toBeVisible()
  await expect(page.getByText('学习路径')).toBeVisible()
  await expect(page.getByText('辅助搜索')).toBeVisible()
})
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd frontend
npx playwright test tests/home-hub.spec.js --config=playwright.redesign.config.cjs
```

Expected: FAIL because the homepage still leads with generic quick actions and lacks explicit learning-path priority.

- [ ] **Step 3: Write minimal implementation**

Create `frontend/src/utils/path.js`:

```js
export function normalizePathSummary(payload = {}) {
  const meta = payload.pathMeta || {}
  return {
    topic: meta.topic || '未设置学习主题',
    estimatedHours: Number(meta.estimatedHours || 0),
    coverage: Number(meta.coverage || 0),
    nextNodeName: payload.nextNode?.name || '暂无下一步推荐',
  }
}
```

Create `frontend/src/components/home/HubHero.vue`:

```vue
<template>
  <section class="home-hero ui-panel">
    <p class="home-hero__eyebrow">PERSONAL RESEARCH HUB</p>
    <h2>{{ title }}</h2>
    <p>{{ subtitle }}</p>
  </section>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, required: true },
})
</script>
```

Create `frontend/src/components/home/LearningPathPanel.vue`:

```vue
<template>
  <section class="learning-path-panel ui-panel">
    <div class="learning-path-panel__header">
      <h3>学习路径</h3>
      <span>{{ Math.round(summary.coverage * 100) }}%</span>
    </div>
    <p>{{ summary.topic }}</p>
    <div class="learning-path-panel__track">
      <div class="learning-path-panel__fill" :style="{ width: `${summary.coverage * 100}%` }" />
    </div>
    <p>下一步：{{ summary.nextNodeName }}</p>
  </section>
</template>

<script setup>
defineProps({
  summary: { type: Object, required: true },
})
</script>
```

Create `frontend/src/components/home/RecommendationStream.vue`:

```vue
<template>
  <section class="recommendation-stream ui-panel">
    <div class="recommendation-stream__header">
      <h3>个性推荐</h3>
      <p>优先展示最符合当前学习路径与兴趣轨迹的论文。</p>
    </div>
    <RecommendList :items="items" :loading="loading" />
  </section>
</template>

<script setup>
import RecommendList from '@/components/RecommendList.vue'

defineProps({
  items: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
})
</script>
```

Update `frontend/src/views/Home.vue` to load recommendation + visualization data together and replace the old quick-actions-first composition:

```vue
<template>
  <AppShell>
    <PageHeader eyebrow="PERSONAL HUB" title="个性推荐与学习路径" :subtitle="heroSubtitle" />
    <HubHero title="今天优先推进你的研究主线" :subtitle="heroSubtitle" />
    <section class="home-hub-grid">
      <RecommendationStream :items="recommendations" :loading="loading" />
      <LearningPathPanel :summary="pathSummary" />
    </section>
  </AppShell>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import AppShell from '@/components/layout/AppShell.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import HubHero from '@/components/home/HubHero.vue'
import LearningPathPanel from '@/components/home/LearningPathPanel.vue'
import RecommendationStream from '@/components/home/RecommendationStream.vue'
import { getRecommendations } from '@/api/recommend'
import { getVisualizationData } from '@/api/visualization'
import { normalizePathSummary } from '@/utils/path'

const recommendations = ref([])
const pathSummary = ref(normalizePathSummary())
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  const [recommendRes, vizRes] = await Promise.all([
    getRecommendations(6),
    getVisualizationData(),
  ])
  recommendations.value = recommendRes.data?.recommendations || []
  pathSummary.value = normalizePathSummary(vizRes.data || {})
  loading.value = false
})

const heroSubtitle = computed(() => `当前主线：${pathSummary.value.topic} · 下一步：${pathSummary.value.nextNodeName}`)
</script>
```

Update `frontend/src/components/RecommendList.vue` so it can render inside the new recommendation stream without fixed legacy width:

```vue
<style scoped>
.recommend-list {
  width: 100%;
  max-width: none;
}
</style>
```

Update `frontend/src/components/PaperCard.vue` to include a more prominent reason / next-step header:

```vue
<div class="paper-card__signal" v-if="paper.reason">
  <span class="paper-card__signal-label">推荐原因</span>
  <span>{{ paper.reason }}</span>
</div>
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
cd frontend
npx playwright test tests/home-hub.spec.js --config=playwright.redesign.config.cjs
npm run build
```

Expected: PASS, and the homepage visually leads with recommendation plus learning-path content.

- [ ] **Step 5: Commit**

```bash
git add frontend/tests/home-hub.spec.js frontend/src/components/home/HubHero.vue frontend/src/components/home/LearningPathPanel.vue frontend/src/components/home/RecommendationStream.vue frontend/src/utils/path.js frontend/src/views/Home.vue frontend/src/components/RecommendList.vue frontend/src/components/PaperCard.vue
git commit -m "feat: redesign home as recommendation hub"
```

### Task 3: Redesign search and paper detail around secondary search + path-aware reading

**Files:**
- Create: `frontend/tests/search-detail-redesign.spec.js`
- Create: `frontend/src/components/search/SearchFilterRail.vue`
- Create: `frontend/src/components/search/SearchResultCard.vue`
- Create: `frontend/src/components/paper/PaperPathRail.vue`
- Modify: `frontend/src/views/Search.vue`
- Modify: `frontend/src/views/PaperDetail.vue`
- Modify: `frontend/src/utils/paper.js`

- [ ] **Step 1: Write the failing test**

Create `frontend/tests/search-detail-redesign.spec.js`:

```js
import { test, expect } from '@playwright/test'

test('search uses a stable filter rail and detail shows path context', async ({ page }) => {
  await page.route('**/api/paper/search**', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        code: 200,
        message: 'success',
        data: [{ id: 1, title: 'Transformer Survey', authors: '["A"]', venue: 'ACL', year: 2024, abstrakt: 'summary', keywords: '["Transformer"]' }],
      }),
    })
  })

  await page.route('**/api/paper/1', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        code: 200,
        message: 'success',
        data: { id: 1, title: 'Transformer Survey', authors: '["A"]', venue: 'ACL', year: 2024, abstrakt: 'summary', keywords: '["Transformer"]' },
      }),
    })
  })

  await page.goto('/search')
  await expect(page.locator('.search-filter-rail')).toBeVisible()
  await page.getByPlaceholder('输入关键词、论文标题、作者姓名或DOI...').fill('Transformer')
  await page.getByRole('button', { name: '智能搜索' }).click()
  await page.getByRole('button', { name: '📖 查看详情' }).click()
  await expect(page.locator('.paper-path-rail')).toBeVisible()
})
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd frontend
npx playwright test tests/search-detail-redesign.spec.js --config=playwright.redesign.config.cjs
```

Expected: FAIL because the filter rail and paper path rail do not exist yet.

- [ ] **Step 3: Write minimal implementation**

Create `frontend/src/components/search/SearchFilterRail.vue`:

```vue
<template>
  <aside class="search-filter-rail ui-panel">
    <h3>辅助搜索</h3>
    <slot />
  </aside>
</template>
```

Create `frontend/src/components/search/SearchResultCard.vue`:

```vue
<template>
  <article class="search-result-card ui-panel">
    <h3>{{ paper.title }}</h3>
    <p>{{ paper.authors }} · {{ paper.venue }} · {{ paper.year }}</p>
    <p>{{ paper.abstract }}</p>
    <div class="search-result-card__actions">
      <button class="action-btn" @click="$emit('open-detail', paper)">📖 查看详情</button>
    </div>
  </article>
</template>

<script setup>
defineProps({ paper: { type: Object, required: true } })
defineEmits(['open-detail'])
</script>
```

Create `frontend/src/components/paper/PaperPathRail.vue`:

```vue
<template>
  <aside class="paper-path-rail ui-panel">
    <h3>学习路径位置</h3>
    <p>{{ current }}</p>
    <p>下一步：{{ next }}</p>
  </aside>
</template>

<script setup>
defineProps({
  current: { type: String, default: '当前论文' },
  next: { type: String, default: '暂无下一步推荐' },
})
</script>
```

Update `frontend/src/views/Search.vue` so the page becomes a split workspace:

```vue
<template>
  <AppShell>
    <PageHeader eyebrow="AUXILIARY SEARCH" title="辅助搜索工作区" subtitle="用于明确目标下的检索与筛选" />
    <section class="search-workspace">
      <SearchFilterRail>
        <!-- keep existing filter controls here -->
      </SearchFilterRail>
      <div class="search-workspace__results">
        <SearchResultCard
          v-for="paper in pagedResults"
          :key="paper.id"
          :paper="paper"
          @open-detail="openDetail"
        />
      </div>
    </section>
  </AppShell>
</template>
```

Update `frontend/src/views/PaperDetail.vue` to render the reading canvas + path rail:

```vue
<template>
  <AppShell>
    <section class="paper-detail-layout">
      <article class="paper-detail-card ui-panel">
        <!-- keep existing metadata, abstract, and download controls -->
      </article>
      <PaperPathRail current="当前阅读节点" :next="paper?.title || '暂无下一步推荐'" />
    </section>
  </AppShell>
</template>
```

Update `frontend/src/utils/paper.js` with a helper for path-side labels:

```js
export function getPathLabel(raw = {}) {
  return raw.pathLabel || raw.venue || '当前阅读节点'
}
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
cd frontend
npx playwright test tests/search-detail-redesign.spec.js --config=playwright.redesign.config.cjs
npx playwright test tests/paper-detail.spec.js --config=playwright.paper-detail.config.cjs
npm run build
```

Expected: both search/detail tests pass and the build stays green.

- [ ] **Step 5: Commit**

```bash
git add frontend/tests/search-detail-redesign.spec.js frontend/src/components/search/SearchFilterRail.vue frontend/src/components/search/SearchResultCard.vue frontend/src/components/paper/PaperPathRail.vue frontend/src/views/Search.vue frontend/src/views/PaperDetail.vue frontend/src/utils/paper.js
git commit -m "feat: redesign search and detail workspace"
```

### Task 4: Lift learning path and recommendation assets into graph and profile

**Files:**
- Create: `frontend/tests/path-surfaces.spec.js`
- Create: `frontend/src/components/path/PathInsightRail.vue`
- Create: `frontend/src/components/profile/ResearchAssetsPanel.vue`
- Modify: `frontend/src/views/KnowledgeGraph.vue`
- Modify: `frontend/src/views/Profile.vue`
- Modify: `frontend/src/api/visualization.js`

- [ ] **Step 1: Write the failing test**

Create `frontend/tests/path-surfaces.spec.js`:

```js
import { test, expect } from '@playwright/test'

test('knowledge graph and profile foreground learning-path assets', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('token', 'test-token')
    localStorage.setItem('userInfo', JSON.stringify({ id: 1, username: 'researcher', role: 'RESEARCHER', roleLabel: '研究者' }))
  })

  await page.route('**/api/visualization/data', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        code: 200,
        message: 'success',
        data: { pathMeta: { topic: '图神经网络', estimatedHours: 12, coverage: 0.65 } },
      }),
    })
  })

  await page.route('**/api/user/profile', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        code: 200,
        message: 'success',
        data: { id: 1, username: 'researcher', researchInterests: '图神经网络,推荐系统' },
      }),
    })
  })

  await page.goto('/knowledge-graph')
  await expect(page.getByText('学习路径')).toBeVisible()

  await page.goto('/profile')
  await expect(page.getByText('研究资产')).toBeVisible()
})
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd frontend
npx playwright test tests/path-surfaces.spec.js --config=playwright.redesign.config.cjs
```

Expected: FAIL because neither page currently foregrounds the requested learning-path assets.

- [ ] **Step 3: Write minimal implementation**

Create `frontend/src/components/path/PathInsightRail.vue`:

```vue
<template>
  <aside class="path-insight-rail ui-panel">
    <h3>学习路径</h3>
    <p>{{ summary.topic }}</p>
    <p>预估 {{ summary.estimatedHours }}h · 完成度 {{ Math.round(summary.coverage * 100) }}%</p>
  </aside>
</template>

<script setup>
defineProps({
  summary: { type: Object, required: true },
})
</script>
```

Create `frontend/src/components/profile/ResearchAssetsPanel.vue`:

```vue
<template>
  <section class="research-assets-panel ui-panel">
    <h3>研究资产</h3>
    <ul>
      <li>当前路径：{{ pathSummary.topic }}</li>
      <li>下一步阅读：{{ pathSummary.nextNodeName }}</li>
      <li>推荐强度：{{ recommendationCount }} 篇</li>
    </ul>
  </section>
</template>

<script setup>
defineProps({
  pathSummary: { type: Object, required: true },
  recommendationCount: { type: Number, default: 0 },
})
</script>
```

Update `frontend/src/api/visualization.js` with a named summary helper export:

```js
import request from '@/utils/request'

export const getVisualizationData = () => request.get('/visualization/data')
export const getVisualizationSummary = async () => (await getVisualizationData()).data || {}
```

Update `frontend/src/views/KnowledgeGraph.vue`:

```vue
<template>
  <AppShell>
    <PageHeader eyebrow="PATH & INSIGHT" title="学习路径与知识图谱" subtitle="把推荐、关系网络与进度感连接起来" />
    <section class="knowledge-layout">
      <PathInsightRail :summary="pathSummary" />
      <div class="knowledge-layout__main">
        <!-- keep existing chart + graph content here -->
      </div>
    </section>
  </AppShell>
</template>
```

Update `frontend/src/views/Profile.vue` to insert `ResearchAssetsPanel` before the older interest / collection cards:

```vue
<ResearchAssetsPanel
  :path-summary="pathSummary"
  :recommendation-count="recommendationCount"
/>
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
cd frontend
npx playwright test tests/path-surfaces.spec.js --config=playwright.redesign.config.cjs
npm run build
```

Expected: PASS and the graph/profile pages now expose learning-path assets first.

- [ ] **Step 5: Commit**

```bash
git add frontend/tests/path-surfaces.spec.js frontend/src/components/path/PathInsightRail.vue frontend/src/components/profile/ResearchAssetsPanel.vue frontend/src/views/KnowledgeGraph.vue frontend/src/views/Profile.vue frontend/src/api/visualization.js
git commit -m "feat: foreground learning path surfaces"
```

### Task 5: Recast community and messaging as collaboration workspaces

**Files:**
- Create: `frontend/tests/collaboration-workspace.spec.js`
- Create: `frontend/src/components/community/DiscussionContextRail.vue`
- Create: `frontend/src/components/chat/ConversationRail.vue`
- Modify: `frontend/src/views/Community.vue`
- Modify: `frontend/src/views/RealtimeChat.vue`

- [ ] **Step 1: Write the failing test**

Create `frontend/tests/collaboration-workspace.spec.js`:

```js
import { test, expect } from '@playwright/test'

test('community and messaging present collaboration context', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('token', 'test-token')
    localStorage.setItem('userInfo', JSON.stringify({ id: 1, username: 'researcher', role: 'RESEARCHER', roleLabel: '研究者' }))
  })

  await page.route('**/api/community/posts**', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        code: 200,
        message: 'success',
        data: [{ id: 1, title: 'Graph topic', content: 'Discuss this paper', author: { username: 'A', roleLabel: '研究者' }, statusName: 'APPROVED', statusLabel: '已发布', replyCount: 0, likeCount: 0 }],
      }),
    })
  })

  await page.route('**/api/message/conversations', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([{ contact: { id: 2, nickname: 'Dr.B' }, unreadCount: 0, lastMessage: 'sync path' }]),
    })
  })

  await page.goto('/community')
  await expect(page.getByText('讨论上下文')).toBeVisible()

  await page.goto('/messages')
  await expect(page.getByText('协作上下文')).toBeVisible()
})
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd frontend
npx playwright test tests/collaboration-workspace.spec.js --config=playwright.redesign.config.cjs
```

Expected: FAIL because the contextual collaboration rails are missing.

- [ ] **Step 3: Write minimal implementation**

Create `frontend/src/components/community/DiscussionContextRail.vue`:

```vue
<template>
  <aside class="discussion-context-rail ui-panel">
    <h3>讨论上下文</h3>
    <p>围绕论文、主题和学习阶段组织讨论。</p>
  </aside>
</template>
```

Create `frontend/src/components/chat/ConversationRail.vue`:

```vue
<template>
  <aside class="conversation-rail ui-panel">
    <h3>协作上下文</h3>
    <p>显示当前联系人、最近论文话题、以及待推进事项。</p>
  </aside>
</template>
```

Update `frontend/src/views/Community.vue`:

```vue
<template>
  <AppShell>
    <PageHeader eyebrow="COLLABORATE" title="科研社区" subtitle="围绕论文与研究主题协作讨论" />
    <section class="community-layout">
      <DiscussionContextRail />
      <div class="community-layout__feed">
        <!-- keep creator + feed here -->
      </div>
    </section>
  </AppShell>
</template>
```

Update `frontend/src/views/RealtimeChat.vue`:

```vue
<template>
  <AppShell>
    <PageHeader eyebrow="COLLABORATION" title="协作私信" subtitle="在研究联系人之间推进论文与路径协作" />
    <section class="chat-layout">
      <ConversationRail />
      <div class="chat-layout__main">
        <!-- keep contacts + message area here -->
      </div>
    </section>
  </AppShell>
</template>
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
cd frontend
npx playwright test tests/collaboration-workspace.spec.js --config=playwright.redesign.config.cjs
npm run build
```

Expected: PASS and both collaboration pages read as integrated workspaces instead of isolated screens.

- [ ] **Step 5: Commit**

```bash
git add frontend/tests/collaboration-workspace.spec.js frontend/src/components/community/DiscussionContextRail.vue frontend/src/components/chat/ConversationRail.vue frontend/src/views/Community.vue frontend/src/views/RealtimeChat.vue
git commit -m "feat: redesign collaboration workspaces"
```

### Task 6: Replace the admin landing page with a cockpit dashboard

**Files:**
- Create: `frontend/tests/admin-cockpit.spec.js`
- Create: `frontend/src/components/admin/AdminCockpitHero.vue`
- Create: `frontend/src/components/admin/AdminKpiGrid.vue`
- Create: `frontend/src/components/admin/AdminActionRail.vue`
- Modify: `frontend/src/views/AdminConsole.vue`

- [ ] **Step 1: Write the failing test**

Create `frontend/tests/admin-cockpit.spec.js`:

```js
import { test, expect } from '@playwright/test'

test('admin lands on cockpit summary before operational tabs', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('token', 'admin-token')
    localStorage.setItem('userInfo', JSON.stringify({ id: 99, username: 'admin', role: 'ADMIN', roleLabel: '管理员' }))
  })

  await page.route('**/api/admin/posts**', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ code: 200, message: 'success', data: [{ id: 1, statusName: 'PENDING', statusLabel: '待审核' }] }),
    })
  })

  await page.route('**/api/admin/users', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ code: 200, message: 'success', data: [{ id: 1, username: 'alice', role: 'RESEARCHER', roleLabel: '研究者' }] }),
    })
  })

  await page.goto('/admin')

  await expect(page.getByText('管理员驾驶舱')).toBeVisible()
  await expect(page.getByText('全局态势')).toBeVisible()
  await expect(page.getByText('待审核')).toBeVisible()
})
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd frontend
npx playwright test tests/admin-cockpit.spec.js --config=playwright.redesign.config.cjs
```

Expected: FAIL because the admin page still opens into a generic tabbed backend without cockpit framing.

- [ ] **Step 3: Write minimal implementation**

Create `frontend/src/components/admin/AdminCockpitHero.vue`:

```vue
<template>
  <section class="admin-cockpit-hero ui-panel">
    <p class="admin-cockpit-hero__eyebrow">COMMAND COCKPIT</p>
    <h2>管理员驾驶舱</h2>
    <p>统一查看审核压力、导入健康、用户态势与异常提醒。</p>
  </section>
</template>
```

Create `frontend/src/components/admin/AdminKpiGrid.vue`:

```vue
<template>
  <section class="admin-kpi-grid">
    <article class="ui-panel">
      <h3>待审核</h3>
      <p>{{ pendingPosts }}</p>
    </article>
    <article class="ui-panel">
      <h3>活跃用户</h3>
      <p>{{ totalUsers }}</p>
    </article>
  </section>
</template>

<script setup>
defineProps({
  pendingPosts: { type: Number, default: 0 },
  totalUsers: { type: Number, default: 0 },
})
</script>
```

Create `frontend/src/components/admin/AdminActionRail.vue`:

```vue
<template>
  <aside class="admin-action-rail ui-panel">
    <h3>全局态势</h3>
    <ul>
      <li>待审核：{{ pendingPosts }}</li>
      <li>用户总数：{{ totalUsers }}</li>
      <li>导入入口：可用</li>
    </ul>
  </aside>
</template>

<script setup>
defineProps({
  pendingPosts: { type: Number, default: 0 },
  totalUsers: { type: Number, default: 0 },
})
</script>
```

Update `frontend/src/views/AdminConsole.vue` so the cockpit comes before the operational tabs:

```vue
<template>
  <AppShell>
    <PageHeader eyebrow="CONTROL" title="管理员驾驶舱" subtitle="先总览全局，再进入审核、导入和权限工作台" />

    <AdminCockpitHero />
    <AdminKpiGrid :pending-posts="pendingPosts" :total-users="adminUsers.length" />

    <section class="admin-layout">
      <div class="admin-layout__main">
        <el-tabs v-model="activeTab" class="admin-tabs">
          <!-- keep existing post / paper / user tab panes -->
        </el-tabs>
      </div>
      <AdminActionRail :pending-posts="pendingPosts" :total-users="adminUsers.length" />
    </section>
  </AppShell>
</template>

<script setup>
const pendingPosts = computed(() => adminPosts.value.filter(post => post.statusName === 'PENDING').length)
</script>
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
cd frontend
npx playwright test tests/admin-cockpit.spec.js --config=playwright.redesign.config.cjs
npm run build
```

Expected: PASS and the admin route now reads as a cockpit before the tabs.

- [ ] **Step 5: Commit**

```bash
git add frontend/tests/admin-cockpit.spec.js frontend/src/components/admin/AdminCockpitHero.vue frontend/src/components/admin/AdminKpiGrid.vue frontend/src/components/admin/AdminActionRail.vue frontend/src/views/AdminConsole.vue
git commit -m "feat: redesign admin as cockpit"
```

### Task 7: Run the full redesign regression pass and fix integration seams

**Files:**
- Modify: `frontend/tests/homepage-recommendation.spec.js`
- Modify: `frontend/tests/paper-detail.spec.js`
- Modify: `frontend/playwright.redesign.config.cjs`

- [ ] **Step 1: Write the failing integration assertions**

Extend `frontend/tests/paper-detail.spec.js` with the new reading-canvas / path-rail expectations:

```js
await expect(page.locator('.paper-path-rail')).toBeVisible()
await expect(page.getByText('学习路径位置')).toBeVisible()
```

Extend `frontend/tests/homepage-recommendation.spec.js` to verify the redesigned home still routes through shared recommendation cards:

```js
await expect(page.getByText('个性推荐')).toBeVisible()
await expect(page.getByText('学习路径')).toBeVisible()
await page.getByRole('button', { name: '阅读' }).click()
await expect(page).toHaveURL(/\/paper\/1$/)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
cd frontend
npx playwright test tests/paper-detail.spec.js --config=playwright.paper-detail.config.cjs
npx playwright test tests/homepage-recommendation.spec.js --config=playwright.homepage.config.cjs
```

Expected: FAIL until the redesigned structure and copy are fully wired.

- [ ] **Step 3: Write minimal integration fixes**

Update `frontend/playwright.redesign.config.cjs` to include all redesign specs:

```js
module.exports = {
  testDir: './tests',
  testMatch: ['ui-shell.spec.js', 'home-hub.spec.js', 'search-detail-redesign.spec.js', 'path-surfaces.spec.js', 'collaboration-workspace.spec.js', 'admin-cockpit.spec.js'],
  timeout: 30000,
  webServer: {
    command: 'npm run dev -- --host 127.0.0.1 --port 4173',
    port: 4173,
    reuseExistingServer: false,
  },
  use: {
    headless: true,
    baseURL: 'http://127.0.0.1:4173',
  },
}
```

Update the older tests so they assert the new copy and new path-centered panels instead of the legacy page structure.

- [ ] **Step 4: Run the full verification pass**

Run:

```bash
cd frontend
npm run build
npx playwright test --config=playwright.redesign.config.cjs
npx playwright test tests/paper-detail.spec.js --config=playwright.paper-detail.config.cjs
npx playwright test tests/homepage-recommendation.spec.js --config=playwright.homepage.config.cjs
```

Expected: all redesign-specific Playwright tests pass and the build succeeds.

- [ ] **Step 5: Commit**

```bash
git add frontend/tests/homepage-recommendation.spec.js frontend/tests/paper-detail.spec.js frontend/playwright.redesign.config.cjs
git commit -m "test: cover ui redesign regressions"
```

---

## Self-Review

### Spec coverage

- Global visual system → Task 1
- Recommendation and learning path become primary → Task 2 and Task 4
- Search becomes secondary workspace → Task 3
- Reading canvas and path-aware detail → Task 3
- Knowledge graph as strongest futuristic surface → Task 4
- Community / messaging / profile integration → Task 5 and Task 4
- Admin cockpit → Task 6
- Regression verification → Task 7

No spec section is left without a task.

### Placeholder scan

- No `TBD`, `TODO`, or “implement later” placeholders remain.
- Every code-changing step includes explicit file paths and code snippets.
- Every test step includes a concrete command and expected failure/pass condition.

### Type consistency

- `normalizePathSummary()` is introduced in Task 2 and reused as the path-summary contract in later tasks.
- `AppShell` and `PageHeader` are introduced in Task 1 and consistently reused by all later page tasks.
- `PaperPathRail`, `PathInsightRail`, and `ResearchAssetsPanel` all treat path context as summary data instead of inventing incompatible APIs.
