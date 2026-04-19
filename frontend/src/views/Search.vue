<template>
  <div class="search-root">
    <div class="bg-animation"></div>
    <Sidebar />
    <main class="main-content">
      <header class="header">
        <div class="page-title">
          <h2>🔍 智能学术搜索</h2>
          <p>基于语义理解的科研文献检索系统</p>
        </div>
        <div class="user-info">
          <div class="user-avatar">A</div>
        </div>
      </header>

      <section class="search-section">
        <div class="search-container">
          <div class="search-box">
            <div class="search-input-wrapper">
              <span class="search-icon">🔍</span>
              <input
                type="text"
                class="search-input"
                placeholder="输入关键词、论文标题、作者姓名或DOI..."
                v-model="keyword"
                @keyup.enter="handleSearch"
              />
              <button class="search-btn" @click="handleSearch" :disabled="loading">智能搜索</button>
            </div>
          </div>

          <div class="filter-section">
            <div class="filter-group">
              <label class="filter-label">时间范围</label>
              <select class="filter-select" v-model="filters.time">
                <option>全部时间</option>
                <option>近一年</option>
                <option>近三年</option>
                <option>近五年</option>
              </select>
            </div>
            <div class="filter-group">
              <label class="filter-label">文献类型</label>
              <select class="filter-select" v-model="filters.type">
                <option>全部类型</option>
                <option>期刊论文</option>
                <option>会议论文</option>
                <option>学位论文</option>
                <option>预印本</option>
              </select>
            </div>
            <div class="filter-group">
              <label class="filter-label">研究领域</label>
              <select class="filter-select" v-model="filters.field">
                <option>全部领域</option>
                <option>人工智能</option>
                <option>计算机视觉</option>
                <option>自然语言处理</option>
                <option>数据挖掘</option>
              </select>
            </div>
            <div class="filter-group">
              <label class="filter-label">排序方式</label>
              <select class="filter-select" v-model="filters.sort">
                <option>相关度</option>
                <option>引用次数</option>
                <option>发表时间</option>
                <option>影响力</option>
              </select>
            </div>
          </div>

          <div class="filter-tags">
            <span class="filter-tag" v-for="(t, idx) in tags" :key="idx" @click="toggleTag(idx)">{{ t }} <span class="remove">×</span></span>
            <span class="filter-tag add">+ 添加筛选</span>
          </div>
        </div>
      </section>

      <section class="trending-section">
        <div class="trending-title">🔥 热门搜索</div>
        <div class="trending-grid">
          <div class="trending-item" v-for="(item, i) in trending" :key="i" @click="applyTrend(item.keyword)">
            <div class="trending-keyword">{{ item.keyword }}</div>
            <div class="trending-count">{{ item.count }} 次搜索</div>
          </div>
        </div>
      </section>

      <section class="results-section">
        <div class="results-header">
          <div class="results-count">找到 <span>{{ total }}</span> 篇相关文献</div>
          <div class="sort-options">
            <button class="sort-btn" :class="{ active: filters.sort === '相关度' }" @click="filters.sort='相关度'">相关度</button>
            <button class="sort-btn" :class="{ active: filters.sort === '引用数' }" @click="filters.sort='引用数'">引用数</button>
            <button class="sort-btn" :class="{ active: filters.sort === '最新' }" @click="filters.sort='最新'">最新</button>
            <button class="sort-btn" :class="{ active: filters.sort === '影响力' }" @click="filters.sort='影响力'">影响力</button>
          </div>
        </div>

        <div class="results-list">
          <div class="result-card" v-for="paper in pagedResults" :key="paper.id">
            <div class="result-header">
              <div style="flex:1">
                <div class="result-title">{{ paper.title }}</div>
                <div class="result-authors">{{ paper.authors }} · {{ paper.venue }} · {{ paper.year }}</div>
                <div class="result-abstract">{{ paper.abstract }}</div>
                <div class="result-meta">
                  <div class="result-tags">
                    <span class="result-tag" v-for="(tag, i) in paper.tags" :key="i">{{ tag }}</span>
                  </div>
                  <div class="result-stats">
                    <span>📊 被引 {{ paper.citations }}</span>
                    <span>⭐ 收藏 {{ paper.favorites }}</span>
                    <span>📥 下载 {{ paper.downloads }}</span>
                  </div>
                </div>
              </div>
            </div>
            <div class="result-actions">
              <button class="action-btn" @click="openDetail(paper)">📖 查看详情</button>
              <button class="action-btn" @click="toggleFavorite(paper)">💾 {{ isFavorited(paper) ? '已收藏' : '收藏' }}</button>
              <button class="action-btn">🔗 引用</button>
            </div>
          </div>
        </div>

        <el-pagination
          background
          :current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next"
          @current-change="changePage"
        />

        <el-dialog v-model:visible="detailVisible" width="60%" :before-close="closeDetail">
          <template #title>
            <div style="display:flex; justify-content:space-between; align-items:center">
              <div>
                <h3 style="margin:0">{{ detailPaper?.title }}</h3>
                <div style="color:var(--text-secondary); font-size:13px">{{ detailPaper?.authors }} · {{ detailPaper?.venue }} · {{ detailPaper?.year }}</div>
              </div>
              <div>
                <el-button type="primary" @click="toggleFavorite(detailPaper)">{{ isFavorited(detailPaper) ? '取消收藏' : '收藏' }}</el-button>
              </div>
            </div>
          </template>

          <div style="margin-top:10px">
            <p style="white-space:pre-wrap">{{ detailPaper?.abstract }}</p>
          </div>
        </el-dialog>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import Sidebar from '@/components/Sidebar.vue'
import { searchPapers, getPaperById } from '@/api/paper'

const keyword = ref('')
const results = ref([])
const loading = ref(false)
const filters = ref({ time: '全部时间', type: '全部类型', field: '全部领域', sort: '相关度' })
const tags = ref(['深度学习','神经网络','计算机视觉'])
const trending = ref([
  { keyword: '大语言模型', count: '12.5k' },
  { keyword: 'Transformer架构', count: '8.3k' },
  { keyword: '多模态学习', count: '6.7k' },
  { keyword: '扩散模型', count: '5.2k' },
  { keyword: '强化学习', count: '4.8k' }
])

const currentPage = ref(1)
const pageSize = ref(10)
const total = computed(() => results.value.length)

const pagedResults = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return results.value.slice(start, start + pageSize.value)
})

const detailVisible = ref(false)
const detailPaper = ref(null)

const favorites = ref(new Set(JSON.parse(localStorage.getItem('favorites') || '[]')))

async function handleSearch() {
  if (!keyword.value.trim()) return
  loading.value = true
  try {
    const res = await searchPapers(keyword.value.trim(), 100)
    results.value = (res.data || []).map(p => ({
      id: p.id || p.paperId || Math.random().toString(36).slice(2,9),
      title: p.title || p.paper_title || 'Untitled',
      authors: (p.authors && p.authors.join(', ')) || p.authors || 'Unknown',
      venue: p.venue || p.journal || '',
      year: p.year || '2024',
      abstract: p.abstract || p.summary || '无摘要',
      tags: p.tags || ['深度学习'],
      citations: p.citations || 0,
      favorites: p.favorites || 0,
      downloads: p.downloads || '0'
    }))
    currentPage.value = 1
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function changePage(page) {
  currentPage.value = page
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function toggleTag(idx) {
  const el = tags.value[idx]
  if (!el) return
  if (el.startsWith('*')) tags.value[idx] = el.replace('*','')
  else tags.value[idx] = '*'+el
}

function applyTrend(keywordStr) {
  keyword.value = keywordStr
  handleSearch()
}

function openDetail(paper) {
  if (!paper) return
  detailPaper.value = paper
  detailVisible.value = true
}

function closeDetail() {
  detailVisible.value = false
  detailPaper.value = null
}

function isFavorited(paper) {
  if (!paper) return false
  return favorites.value.has(paper.id)
}

function toggleFavorite(paper) {
  if (!paper) return
  if (favorites.value.has(paper.id)) {
    favorites.value.delete(paper.id)
    paper.favorites = Math.max(0, (paper.favorites || 1) - 1)
  } else {
    favorites.value.add(paper.id)
    paper.favorites = (paper.favorites || 0) + 1
  }
  localStorage.setItem('favorites', JSON.stringify(Array.from(favorites.value)))
}
</script>

<style scoped>
:root {
  --primary: #6366f1;
  --secondary: #8b5cf6;
  --accent: #06b6d4;
  --bg-dark: #0f172a;
  --bg-card: rgba(30, 41, 59, 0.7);
  --bg-hover: rgba(51, 65, 85, 0.8);
  --text-primary: #f8fafc;
  --text-secondary: #94a3b8;
  --border: rgba(148, 163, 184, 0.1);
}

.search-root { min-height: 100vh; background: var(--bg-dark); color: var(--text-primary); overflow-x:hidden }
.bg-animation { position: fixed; top:0; left:0; width:100%; height:100%; z-index:-1; background: radial-gradient(ellipse at 20% 20%, rgba(99,102,241,0.15) 0%, transparent 50%), radial-gradient(ellipse at 80% 80%, rgba(139,92,246,0.15) 0%, transparent 50%), radial-gradient(ellipse at 50% 50%, rgba(6,182,212,0.1) 0%, transparent 50%)}
.main-content { margin-left:260px; min-height:100vh; padding:30px 40px }
.header { display:flex; justify-content:space-between; align-items:center; margin-bottom:40px; padding:20px 30px; background:var(--bg-card); backdrop-filter: blur(20px); border-radius:20px; border:1px solid var(--border) }
.page-title h2 { font-size:28px; font-weight:700; margin-bottom:8px }
.page-title p { color:var(--text-secondary); font-size:15px }
.user-avatar { width:45px; height:45px; border-radius:50%; background:linear-gradient(135deg,var(--primary),var(--accent)); display:flex; align-items:center; justify-content:center; font-weight:600 }

.search-section { margin-bottom:40px }
.search-container { background:var(--bg-card); backdrop-filter: blur(20px); border-radius:24px; border:1px solid var(--border); padding:40px }
.search-input-wrapper { position:relative; display:flex; align-items:center }
.search-icon { position:absolute; left:25px; font-size:22px; color:var(--text-secondary) }
.search-input { width:100%; padding:22px 25px 22px 60px; font-size:17px; border:2px solid var(--border); border-radius:16px; background: rgba(255,255,255,0.05); color:var(--text-primary); outline:none }
.search-btn { position:absolute; right:8px; padding:14px 28px; background: linear-gradient(135deg,var(--primary),var(--secondary)); border:none; border-radius:12px; color:white; font-weight:600; cursor:pointer }

.filter-section { display:flex; gap:20px; flex-wrap:wrap; align-items:center; margin-top:20px }
.filter-label { font-size:13px; color:var(--text-secondary); font-weight:500 }
.filter-select { padding:12px 18px; border-radius:12px; border:1px solid var(--border); background: rgba(255,255,255,0.05); color:var(--text-primary) }
.filter-tags { display:flex; gap:10px; flex-wrap:wrap; margin-top:20px }
.filter-tag { padding:8px 16px; border-radius:20px; background:rgba(99,102,241,0.15); border:1px solid rgba(99,102,241,0.3); color:var(--primary); cursor:pointer }
.filter-tag.add { background: transparent; border:1px dashed var(--border); color:var(--text-secondary) }

.trending-section { margin-top:30px }
.trending-grid { display:grid; grid-template-columns: repeat(auto-fill, minmax(200px,1fr)); gap:15px }
.trending-item { padding:18px; background: rgba(255,255,255,0.03); border-radius:14px; border:1px solid var(--border); cursor:pointer }
.trending-keyword { font-size:14px; font-weight:500 }
.trending-count { font-size:12px; color:var(--text-secondary) }

.results-section { margin-top:30px }
.results-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:25px }
.results-count { font-size:18px; font-weight:600 }
.sort-options { display:flex; gap:10px }
.sort-btn { padding:10px 18px; border-radius:10px; border:1px solid var(--border); background:rgba(255,255,255,0.05); color:var(--text-secondary); cursor:pointer }
.sort-btn.active { background:var(--primary); color:white; border-color:var(--primary) }

.results-list { display:flex; flex-direction:column; gap:20px }
.result-card { background:var(--bg-card); border-radius:20px; border:1px solid var(--border); padding:28px }
.result-title { font-size:18px; font-weight:600; margin-bottom:12px }
.result-authors { font-size:14px; color:var(--text-secondary); margin-bottom:15px }
.result-abstract { font-size:14px; color:var(--text-secondary); line-height:1.7; margin-bottom:20px }
.result-tags { display:flex; gap:10px }
.result-tag { padding:6px 14px; border-radius:20px; font-size:12px; background:rgba(99,102,241,0.15); color:var(--primary) }
.result-stats { display:flex; gap:20px; font-size:13px; color:var(--text-secondary) }
.result-actions { display:flex; gap:10px; margin-top:16px }
.action-btn { padding:10px 18px; border-radius:10px; border:1px solid var(--border); background:rgba(255,255,255,0.05); color:var(--text-secondary); cursor:pointer }

.pagination { display:flex; justify-content:center; gap:10px; margin-top:40px }
.page-btn { width:44px; height:44px; border-radius:12px; border:1px solid var(--border); background:rgba(255,255,255,0.05); color:var(--text-secondary) }
.page-btn.active, .page-btn:hover { background:var(--primary); color:white; border-color:var(--primary) }

@media (max-width:1200px) {
  .main-content { margin-left: 0; padding:20px }
  .sidebar { transform: translateX(-100%) }
}
</style>
