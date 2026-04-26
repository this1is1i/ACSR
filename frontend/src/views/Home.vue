<template>
  <div class="home-root">
    <div class="bg-animation"></div>
    <Sidebar />
    <main class="main-content">
      <header class="header">
        <div class="user-info">
          <div class="user-avatar">A</div>
          <div class="user-details">
            <h4>欢迎回来，用户A</h4>
            <p>研究方向：机器学习 · 深度学习</p>
          </div>
        </div>
        <div class="header-actions">
          <button class="icon-btn">🔔<span class="badge">3</span></button>
          <button class="icon-btn">⚙️</button>
          <button class="icon-btn" @click="logout">🚪</button>
        </div>
      </header>

      <div class="quick-actions">
        <div class="action-card" @click="$router.push('/search')">
          <div class="action-icon purple">🔍</div>
          <h4>智能检索</h4>
          <p>基于语义理解的论文搜索</p>
        </div>
        <div class="action-card" @click="$router.push('/knowledge-graph')">
          <div class="action-icon blue">📈</div>
          <h4>趋势分析</h4>
          <p>追踪研究热点与兴趣演化</p>
        </div>
        <div class="action-card">
          <div class="action-icon cyan">🌐</div>
          <h4>学术交流</h4>
          <p>与同行探讨前沿话题</p>
        </div>
        <div class="action-card">
          <div class="action-icon green">🤝</div>
          <h4>合作匹配</h4>
          <p>发现潜在研究合作伙伴</p>
        </div>
      </div>

      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-header">
            <span class="stat-label">本周阅读论文</span>
            <div class="stat-icon">📄</div>
          </div>
          <div class="stat-value">24</div>
          <div class="stat-change">↑ 12% 较上周</div>
        </div>
        <div class="stat-card">
          <div class="stat-header">
            <span class="stat-label">收藏文献</span>
            <div class="stat-icon">⭐</div>
          </div>
          <div class="stat-value">156</div>
          <div class="stat-change">↑ 8 新增</div>
        </div>
        <div class="stat-card">
          <div class="stat-header">
            <span class="stat-label">学术影响力</span>
            <div class="stat-icon">🎯</div>
          </div>
          <div class="stat-value">892</div>
          <div class="stat-change">↑ 23 本周互动</div>
        </div>
      </div>

      <div class="dashboard-grid">
        <div class="card">
          <div class="card-header">
            <div class="card-title"><div class="card-title-icon">📌</div>个性化推荐</div>
            <a href="#" class="view-all">查看全部 →</a>
          </div>

          <RecommendList :items="recommendations" :loading="loading" />
        </div>

        <div class="card">
          <div class="card-header">
            <div class="card-title"><div class="card-title-icon">🤝</div>推荐合作者</div>
            <a href="#" class="view-all">更多 →</a>
          </div>

          <div class="collaborator-grid">
            <div class="collaborator-item" v-for="c in collaborators" :key="c.name">
              <div class="collab-avatar">{{ c.initial }}</div>
              <div class="collab-info">
                <h5>{{ c.name }}</h5>
                <p>{{ c.affiliation }} · {{ c.field }}</p>
              </div>
              <div class="match-score">{{ c.score }}%匹配</div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Sidebar from '@/components/Sidebar.vue'
import RecommendList from '@/components/RecommendList.vue'
import { getRecommendations } from '@/api/recommend'
import { useUserStore } from '@/store/userStore'

const router = useRouter()
const userStore = useUserStore()
const recommendations = ref([])
const loading = ref(false)
const collaborators = ref([
  { name: '张三 教授', initial: '张', affiliation: '清华大学', field: '机器学习', score: 95 },
  { name: '李四 博士', initial: '李', affiliation: '中科院', field: '数据挖掘', score: 88 },
  { name: '王五 研究员', initial: '王', affiliation: '北大', field: '计算机视觉', score: 82 },
  { name: '赵六 副教授', initial: '赵', affiliation: '浙大', field: '自然语言处理', score: 76 },
])

async function loadRecommendations() {
  loading.value = true
  try {
    const res = await getRecommendations(10)
    recommendations.value = res.data?.recommendations || []
  } finally {
    loading.value = false
  }
}

function logout() {
  userStore.clearToken()
  router.push('/login')
}

onMounted(loadRecommendations)
</script>

<style scoped>
:root { --primary: #6366f1; --secondary:#8b5cf6; --accent:#06b6d4; --bg-dark:#0f172a; --bg-card:rgba(30,41,59,0.7); --border: rgba(148,163,184,0.1) }
.home-root { min-height:100vh; background:var(--bg-dark); color:var(--text-primary); overflow-x:hidden }
.bg-animation { position:fixed; top:0; left:0; width:100%; height:100%; z-index:-1; background: radial-gradient(ellipse at 20% 20%, rgba(99,102,241,0.15) 0%, transparent 50%), radial-gradient(ellipse at 80% 80%, rgba(139,92,246,0.15) 0%, transparent 50%), radial-gradient(ellipse at 50% 50%, rgba(6,182,212,0.1) 0%, transparent 50%) }
.main-content { margin-left:260px; min-height:100vh; padding:30px 40px }
.header { display:flex; justify-content:space-between; align-items:center; margin-bottom:40px; padding:20px 30px; background:var(--bg-card); backdrop-filter: blur(20px); border-radius:20px; border:1px solid var(--border) }
.user-avatar { width:45px; height:45px; border-radius:50%; background:linear-gradient(135deg,var(--primary),var(--accent)); display:flex; align-items:center; justify-content:center; font-weight:600 }
.quick-actions { display:grid; grid-template-columns: repeat(4,1fr); gap:20px; margin-bottom:30px }
.action-card { background:var(--bg-card); border-radius:20px; padding:25px; border:1px solid var(--border); text-align:center; cursor:pointer }
.action-icon { width:60px; height:60px; border-radius:16px; margin:0 auto 15px; display:flex; align-items:center; justify-content:center; font-size:28px }
.action-icon.purple { background: linear-gradient(135deg, #8b5cf6, #a78bfa) }
.action-icon.blue { background: linear-gradient(135deg, #3b82f6, #60a5fa) }
.action-icon.cyan { background: linear-gradient(135deg, #06b6d4, #22d3ee) }
.action-icon.green { background: linear-gradient(135deg, #10b981, #34d399) }
.stats-grid { display:grid; grid-template-columns: repeat(3,1fr); gap:25px; margin-bottom:30px }
.stat-card { background:var(--bg-card); border-radius:20px; padding:25px; border:1px solid var(--border) }
.dashboard-grid { display:grid; grid-template-columns: 2fr 1fr; gap:30px }
.card { background:var(--bg-card); border-radius:24px; padding:30px; border:1px solid var(--border) }
</style>
