<template>
  <div class="search-root">
    <div class="bg-animation"></div>
    <Sidebar />

    <main class="main-content">
      <section class="search-section">
        <div class="search-container glass">
          <div class="search-box">
            <div class="search-input-wrapper">
              <span class="search-icon">🔍</span>
              <input
                v-model="keyword"
                type="text"
                class="search-input"
                placeholder="输入关键词、论文标题、作者姓名或DOI..."
                @keyup.enter="handleSearch"
              />
              <button class="search-btn" type="button" :disabled="loading" @click="handleSearch">智能搜索</button>
            </div>
          </div>

          <div class="search-command-footer">
            <div class="trending-inline">
              <span class="trending-inline__label">快速主题</span>
              <button
                v-for="item in trending"
                :key="item.keyword"
                class="trending-inline__item"
                type="button"
                @click="applyTrend(item.keyword)"
              >
                {{ item.keyword }}
              </button>
            </div>

            <div v-if="searchSummary.activeFilters.length || searchSummary.activeTags.length" class="search-state-pills">
              <span v-for="label in searchSummary.activeFilters" :key="label" class="search-state-pill">{{ label }}</span>
              <span
                v-for="label in searchSummary.activeTags"
                :key="label"
                class="search-state-pill search-state-pill--accent"
              >
                {{ label }}
              </span>
            </div>
          </div>
        </div>
      </section>

      <div class="search-workspace">
        <SearchFilterRail
          :query="keyword"
          :result-count="total"
          :filters="filters"
          :tags="tags"
          :active-filters="searchSummary.activeFilters"
          :active-tags="searchSummary.activeTags"
          @update-filter="updateFilter"
          @toggle-tag="toggleTag"
          @reset="resetFilters"
        />

        <section class="results-panel">
          <div class="results-header">
            <div class="results-count">找到 <span>{{ total }}</span> 篇相关文献</div>
            <div class="sort-options">
              <button
                v-for="option in sortOptions"
                :key="option"
                class="sort-btn"
                :class="{ active: filters.sort === option }"
                type="button"
                @click="updateFilter('sort', option)"
              >
                {{ option }}
              </button>
            </div>
          </div>

          <div v-if="loading" class="results-empty card glass">正在整理与你的检索相关的论文结果...</div>
          <div v-else-if="!results.length" class="results-empty card glass">暂无搜索结果</div>
          <div v-else class="results-list">
            <SearchResultCard
              v-for="paper in pagedResults"
              :key="paper.id"
              :paper="paper"
              :query="keyword"
              :active-filters="searchSummary.activeFilters"
              :active-tags="searchSummary.activeTags"
              :favorited="isFavorited(paper)"
              @open="openDetail"
              @toggle-favorite="toggleFavorite"
            />
          </div>

          <div v-if="total > pageSize" class="results-pagination">
            <el-pagination
              background
              :current-page="currentPage"
              :page-size="pageSize"
              :total="total"
              layout="prev, pager, next"
              @current-change="changePage"
            />
          </div>
        </section>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import { searchPapers } from '@/api/paper'
import { recordFavorite } from '@/api/recommend'
import Sidebar from '@/components/Sidebar.vue'
import SearchFilterRail from '@/components/search/SearchFilterRail.vue'
import SearchResultCard from '@/components/search/SearchResultCard.vue'
import { useUserStore } from '@/store/userStore'
import {
  normalizePaper,
  SEARCH_DEFAULT_FILTERS,
  SEARCH_RESTORE_PENDING_KEY,
  SEARCH_STATE_KEY,
  summarizeSearchContext,
} from '@/utils/paper'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const defaultTags = ['Deep Learning', 'Neural Network', 'Computer Vision']
const keyword = ref('')
const results = ref([])
const loading = ref(false)
const filters = ref({ ...SEARCH_DEFAULT_FILTERS })
const tags = ref([...defaultTags])
const trending = ref([
  { keyword: 'Reinforcement Learning', count: '12.5k' },
  { keyword: 'Transformer', count: '8.3k' },
  { keyword: 'Computer Vision', count: '6.7k' },
  { keyword: 'Neural Network', count: '5.2k' },
  { keyword: 'BERT', count: '4.8k' },
])
const currentPage = ref(1)
const pageSize = ref(10)
const favorites = ref(new Set(JSON.parse(localStorage.getItem('favorites') || '[]')))
const sortOptions = ['相关度', '引用次数', '发表时间', '影响力']

const total = computed(() => results.value.length)
const pagedResults = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return results.value.slice(start, start + pageSize.value)
})
const searchSummary = computed(() => summarizeSearchContext(filters.value, tags.value))

function saveSearchState() {
  window.sessionStorage.setItem(SEARCH_STATE_KEY, JSON.stringify({
    keyword: keyword.value,
    results: results.value,
    currentPage: currentPage.value,
    filters: { ...filters.value },
    tags: [...tags.value],
  }))
}

function restoreSearchState() {
  const rawState = window.sessionStorage.getItem(SEARCH_STATE_KEY)
  if (!rawState) return

  try {
    const savedState = JSON.parse(rawState)
    keyword.value = savedState.keyword || ''
    results.value = Array.isArray(savedState.results) ? savedState.results : []
    currentPage.value = savedState.currentPage || 1
    filters.value = {
      ...SEARCH_DEFAULT_FILTERS,
      ...(savedState.filters && typeof savedState.filters === 'object' ? savedState.filters : {}),
    }
    tags.value = Array.isArray(savedState.tags) ? [...savedState.tags] : [...defaultTags]
    window.sessionStorage.removeItem(SEARCH_RESTORE_PENDING_KEY)
  } catch {
    window.sessionStorage.removeItem(SEARCH_STATE_KEY)
    window.sessionStorage.removeItem(SEARCH_RESTORE_PENDING_KEY)
  }
}

function getFilterParams() {
  const params = {}
  const timeMap = { '近一年': 2025, '近三年': 2023, '近五年': 2021 }
  const sortMap = { '引用次数': 'citation', '发表时间': 'year' }
  if (filters.value.time && timeMap[filters.value.time]) params.yearFrom = timeMap[filters.value.time]
  if (filters.value.sort && sortMap[filters.value.sort]) params.sortBy = sortMap[filters.value.sort]
  return params
}

async function handleSearch() {
  if (!keyword.value.trim()) return

  loading.value = true
  try {
    const res = await searchPapers(keyword.value.trim(), 100, getFilterParams())
    results.value = (res.data || []).map((paper) => {
      const normalized = normalizePaper(paper)
      return {
        id: paper.id || paper.paperId || Math.random().toString(36).slice(2, 9),
        title: paper.title || paper.paper_title || 'Untitled',
        authors: normalized.authorText === '未知作者' ? 'Unknown' : normalized.authorText,
        venue: paper.venue || paper.journal || '未知来源',
        year: paper.year || '2024',
        abstract: normalized.abstractText || '无摘要',
        tags: normalized.keywordsList.length ? normalized.keywordsList : ['深度学习'],
        citations: paper.citations || paper.citationCount || 0,
        favorites: paper.favorites || 0,
        downloads: paper.downloads || '0',
      }
    })
    currentPage.value = 1
    saveSearchState()
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

function updateFilter(key, value) {
  filters.value = {
    ...filters.value,
    [key]: value,
  }
}

function resetFilters() {
  filters.value = { ...SEARCH_DEFAULT_FILTERS }
  tags.value = [...defaultTags]
}

function changePage(page) {
  currentPage.value = page
  saveSearchState()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function toggleTag(index) {
  const tag = tags.value[index]
  if (!tag) return
  tags.value[index] = tag.startsWith('*') ? tag.replace('*', '') : `*${tag}`
}

function applyTrend(keywordStr) {
  keyword.value = keywordStr
  handleSearch()
}

function openDetail(paper) {
  if (!paper) return
  saveSearchState()
  window.sessionStorage.setItem(SEARCH_RESTORE_PENDING_KEY, '1')
  router.push(`/paper/${paper.id}`)
}

function isFavorited(paper) {
  if (!paper) return false
  return favorites.value.has(paper.id)
}

function toggleFavorite(paper) {
  if (!userStore.isLoggedIn()) {
    ElMessage.warning('游客仅可搜索和查看详情，收藏功能需要登录')
    return
  }

  if (!paper) return

  const wasFav = favorites.value.has(paper.id)
  if (wasFav) {
    favorites.value.delete(paper.id)
    paper.favorites = Math.max(0, (paper.favorites || 1) - 1)
  } else {
    favorites.value.add(paper.id)
    paper.favorites = (paper.favorites || 0) + 1
  }

  // Sync to localStorage for optimistic state
  localStorage.setItem('favorites', JSON.stringify(Array.from(favorites.value)))
  // Call API to persist
  recordFavorite(paper.id, 'search').catch(err => {
    console.error('Failed to record favorite', err)
    // Revert on failure
    if (wasFav) {
      favorites.value.add(paper.id)
      paper.favorites = (paper.favorites || 0) + 1
    } else {
      favorites.value.delete(paper.id)
      paper.favorites = Math.max(0, (paper.favorites || 1) - 1)
    }
    localStorage.setItem('favorites', JSON.stringify(Array.from(favorites.value)))
  })
}

onMounted(() => {
  const shouldRestore = route.query.restore === '1' || window.sessionStorage.getItem(SEARCH_RESTORE_PENDING_KEY) === '1'
  if (shouldRestore) {
    restoreSearchState()
  }
})
</script>

<style scoped>
.search-root {
  min-height: 100vh;
  overflow-x: hidden;
}

.bg-animation {
  position: fixed;
  inset: 0;
  z-index: -1;
  background:
    radial-gradient(circle at 15% 18%, rgba(124, 140, 255, 0.16), transparent 30%),
    radial-gradient(circle at 82% 10%, rgba(55, 213, 255, 0.12), transparent 24%),
    radial-gradient(circle at 50% 75%, rgba(94, 234, 212, 0.08), transparent 26%);
}

.main-content {
  display: grid;
  gap: var(--space-6);
}

.search-container {
  display: grid;
  gap: var(--space-5);
  padding: clamp(1.35rem, 2vw, 2rem);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
}

.search-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 1.2rem;
  font-size: 1.1rem;
  color: var(--color-text-muted);
}

.search-input {
  width: 100%;
  padding: 1.15rem 8.8rem 1.15rem 3rem;
  font-size: 1rem;
}

.search-btn {
  position: absolute;
  top: 50%;
  right: 0.45rem;
  transform: translateY(-50%);
  padding: 0.85rem 1.2rem;
  border: none;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  color: #fff;
  cursor: pointer;
}

.search-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.search-command-footer {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: var(--space-4);
}

.trending-inline,
.search-state-pills,
.search-header-status {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.trending-inline {
  align-items: center;
}

.trending-inline__label {
  font-size: 0.82rem;
  color: var(--color-text-muted);
}

.trending-inline__item,
.search-state-pill {
  padding: 0.55rem 0.85rem;
  border: 1px solid var(--color-border-subtle);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.03);
  color: var(--color-text-primary);
}

.trending-inline__item {
  cursor: pointer;
}

.search-state-pill--accent {
  border-color: rgba(55, 213, 255, 0.22);
  background: rgba(55, 213, 255, 0.12);
}

.search-header-status__item {
  min-width: 9rem;
  display: grid;
  gap: var(--space-1);
  padding: 0.9rem 1rem;
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.03);
}

.search-header-status__item span {
  font-size: 0.78rem;
  color: var(--color-text-muted);
}

.search-workspace {
  display: grid;
  grid-template-columns: minmax(280px, 320px) minmax(0, 1fr);
  gap: var(--space-6);
  align-items: start;
}

.results-panel {
  display: grid;
  gap: var(--space-5);
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-4);
}

.results-count {
  font-size: 1.05rem;
  color: var(--color-text-primary);
}

.results-count span {
  color: var(--color-accent-secondary);
}

.sort-options {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.sort-btn {
  padding: 0.65rem 0.9rem;
  border: 1px solid var(--color-border-subtle);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.03);
  color: var(--color-text-secondary);
  cursor: pointer;
}

.sort-btn.active {
  background: linear-gradient(135deg, rgba(124, 140, 255, 0.24), rgba(55, 213, 255, 0.16));
  border-color: var(--color-border-strong);
  color: var(--color-text-primary);
}

.results-list {
  display: grid;
  gap: var(--space-4);
}

.results-empty {
  padding: var(--space-6);
  border: 1px solid var(--color-border-subtle);
}

.results-pagination {
  display: flex;
  justify-content: center;
}

@media (max-width: 1120px) {
  .search-workspace {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .search-input {
    padding-right: 1rem;
  }

  .search-btn {
    position: static;
    transform: none;
    margin-top: var(--space-3);
    width: 100%;
  }

  .search-input-wrapper {
    display: block;
  }

  .search-icon {
    top: 1.15rem;
  }

  .results-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
