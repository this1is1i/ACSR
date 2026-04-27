<template>
  <div class="profile-root">
    <div class="bg-animation"></div>
    <Sidebar />
    <main class="main-content">
      <header class="header">
        <div class="page-title">
          <p class="page-title__eyebrow">Future Lab</p>
          <h2>👤 研究身份与资产</h2>
          <p>优先展示与你当前路径、推荐流与研究画像直接相关的核心资产。</p>
        </div>
        <div class="header-actions">
          <button class="btn secondary" @click="logout">退出登录</button>
        </div>
      </header>

      <div class="profile-hero card glass animate-fade-up">
                <div class="profile-content">
          <div class="profile-avatar-large">{{ profile.avatar ? '' : (profile.username ? profile.username.charAt(0) : 'U') }}
            <img v-if="profile.avatar" :src="profile.avatar" alt="avatar" class="avatar-img" />
          </div>
          <div class="profile-info">
            <div class="profile-name">{{ profile.username || '用户' }}</div>
            <div class="profile-title">{{ profile.bio || '—' }}</div>
            <div class="profile-tags">
              <span v-for="(tag, idx) in (profile.researchInterests ? profile.researchInterests.split(',') : [])" :key="idx" class="profile-tag">{{ tag }}</span>
            </div>
          </div>

          <div class="profile-actions">
            <button class="profile-btn btn primary" @click="router.push('/profile/edit')">编辑资料</button>
            <button class="profile-btn btn secondary" @click="shareProfile">分享主页</button>
          </div>
        </div>
      </div>

      <div class="profile-grid">
        <ResearchAssetsPanel
          :loading="assetsLoading"
          :profile="profile"
          :summary="pathSummary"
          :recommendations="recommendations"
          :interests="interestItems"
          @view-path="router.push('/knowledge-graph')"
        />

        <div class="profile-card card animate-fade-up">
          <div class="card-header">
            <div class="card-title">
              <div class="card-icon">🎯</div>
              研究兴趣分布
            </div>
            <button class="edit-btn btn secondary" @click="manageInterests">管理</button>
          </div>

          <div class="interest-list">
            <div v-for="(i, idx) in interestItems" :key="idx" class="interest-item">
              <span class="interest-label">{{ i.name }}</span>
              <div class="interest-bar">
                <div class="interest-fill" :style="{ width: i.percent + '%', background: i.color }"></div>
              </div>
              <span class="interest-value">{{ i.percent }}%</span>
            </div>
          </div>
        </div>

        <div class="profile-card card animate-fade-up">
          <div class="card-header">
            <div class="card-title">
              <div class="card-icon">⭐</div>
              我的收藏
            </div>
            <button class="edit-btn btn secondary" @click="viewAllCollections">查看全部</button>
          </div>

          <div class="collection-list">
            <div v-for="(c, idx) in collections" :key="idx" class="collection-item">
              <div class="collection-thumb">📄</div>
              <div class="collection-info">
                <div class="collection-title">{{ c.title }}</div>
                <div class="collection-meta">{{ c.meta }}</div>
              </div>
            </div>
          </div>
        </div>

        <div class="profile-card card animate-fade-up">
          <div class="card-header">
            <div class="card-title">
              <div class="card-icon">⚙️</div>
              个性化设置
            </div>
          </div>

          <div class="settings-list">
            <div class="setting-item" v-for="(s, idx) in settings" :key="idx">
              <div class="setting-info">
                <h5>{{ s.title }}</h5>
                <p>{{ s.desc }}</p>
              </div>
              <div class="toggle" :class="{ active: s.enabled }" @click="toggleSetting(idx)"></div>
            </div>
          </div>
        </div>

        <div class="profile-card card animate-fade-up">
          <div class="card-header">
            <div class="card-title">
              <div class="card-icon">🕐</div>
              最近活动
            </div>
            <button class="edit-btn btn secondary" @click="clearHistory">清空</button>
          </div>

          <div class="history-list">
            <div v-for="(h, idx) in history" :key="idx" class="history-item">
              <div class="history-icon">{{ h.icon }}</div>
              <div class="history-text">{{ h.text }}</div>
              <div class="history-time">{{ h.time }}</div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import Sidebar from '@/components/Sidebar.vue'
import ResearchAssetsPanel from '@/components/profile/ResearchAssetsPanel.vue'
import { getPathSurfaceData } from '@/api/visualization'
import { buildLearningPathSummary } from '@/utils/path'

const router = useRouter()
const defaultInterests = [
  { name: '深度学习', percent: 85, color: 'linear-gradient(90deg, #6366f1, #8b5cf6)' },
  { name: '计算机视觉', percent: 72, color: 'linear-gradient(90deg, #06b6d4, #22d3ee)' },
  { name: '强化学习', percent: 45, color: 'linear-gradient(90deg, #10b981, #34d399)' },
  { name: '自然语言处理', percent: 38, color: 'linear-gradient(90deg, #f59e0b, #fbbf24)' },
  { name: '数据挖掘', percent: 25, color: 'linear-gradient(90deg, #ec4899, #f472b6)' }
]
const interestPalette = [
  'linear-gradient(90deg, #6366f1, #8b5cf6)',
  'linear-gradient(90deg, #06b6d4, #22d3ee)',
  'linear-gradient(90deg, #10b981, #34d399)',
  'linear-gradient(90deg, #f59e0b, #fbbf24)',
  'linear-gradient(90deg, #ec4899, #f472b6)',
]

const profile = ref({ id: null, username: '', avatar: '', email: '', bio: '', researchInterests: '' })
const visualizationData = ref({})
const recommendations = ref([])
const assetsLoading = ref(false)
const pathSummary = computed(() => buildLearningPathSummary(visualizationData.value))
const interestItems = computed(() => {
  const labels = visualizationData.value?.field?.labels || []
  const values = visualizationData.value?.field?.data || []

  if (!labels.length || !values.length) return defaultInterests

  return labels.map((label, index) => ({
    name: label,
    percent: Number(values[index] || 0),
    color: interestPalette[index % interestPalette.length],
  }))
})

const collections = ref([
  { title: 'Attention Is All You Need', meta: 'Vaswani et al. · NeurIPS 2017' },
  { title: 'Deep Residual Learning for Image Recognition', meta: 'He et al. · CVPR 2016' },
  { title: 'BERT: Pre-training of Deep Bidirectional Transformers', meta: 'Devlin et al. · NAACL 2019' }
])

const settings = ref([
  { title: '个性化推荐', desc: '基于阅读历史智能推荐论文', enabled: true },
  { title: '邮件通知', desc: '接收关注领域的新论文提醒', enabled: true },
  { title: '社区互动', desc: '允许其他用户查看我的动态', enabled: false },
  { title: '数据同步', desc: '跨设备同步阅读记录和收藏', enabled: true }
])

const history = ref([
  { icon: '👁️', text: '阅读了《Graph Neural Networks Survey》', time: '2小时前' },
  { icon: '⭐', text: '收藏了《Transformer Architecture》', time: '5小时前' },
  { icon: '💬', text: '评论了李四的论文分享', time: '昨天' },
  { icon: '🔍', text: '搜索了"自监督学习"', time: '昨天' }
])

function editProfile() { console.log('edit') }
function shareProfile() { console.log('share') }
function manageInterests() { console.log('manage interests') }
function viewAllCollections() { console.log('view all') }
function toggleSetting(i) { settings.value[i].enabled = !settings.value[i].enabled }
function clearHistory() { history.value = [] }

function animateInterestBars() {
  const fills = document.querySelectorAll('.interest-fill')
  fills.forEach(fill => {
    const width = fill.style.width
    fill.style.width = '0'
    setTimeout(() => { fill.style.width = width }, 300)
  })
}

function logout() {
  localStorage.removeItem('token')
  localStorage.removeItem('userId')
  ElMessage.success('已退出登录')
  router.push('/login')
}

import { getProfile } from '@/api/user'

watch(interestItems, async () => {
  await nextTick()
  animateInterestBars()
}, { flush: 'post' })

onMounted(async () => {
  await Promise.allSettled([
    (async () => {
      try {
        const res = await getProfile()
        const data = res.data || res
        profile.value = { id: data.id, username: data.username, avatar: data.avatar, email: data.email, bio: data.bio, researchInterests: data.researchInterests }
      } catch (e) {
        console.error('failed to load profile', e)
      }
    })(),
    (async () => {
      assetsLoading.value = true
      try {
        const surface = await getPathSurfaceData()
        visualizationData.value = surface.visualization || {}
        recommendations.value = surface.recommendations || []
      } catch (e) {
        console.error('failed to load research assets', e)
      } finally {
        assetsLoading.value = false
      }
    })(),
  ])
})
</script>

<style scoped>
/* ─── Page Layout ────────────────────────────────────────────── */
.profile-root {
  min-height: 100vh;
  background: var(--bg);
  color: var(--text-primary);
  overflow-x: hidden;
}

.bg-animation {
  position: fixed;
  top: 0; left: 0; width: 100%; height: 100%;
  z-index: -1;
  background:
    radial-gradient(ellipse at 20% 20%, rgba(99,102,241,0.12) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 80%, rgba(139,92,246,0.12) 0%, transparent 50%),
    radial-gradient(ellipse at 50% 50%, rgba(6,182,212,0.08) 0%, transparent 50%);
}

.main-content {
  margin-left: 260px;
  min-height: 100vh;
  padding: 30px 40px;
}

/* ─── Header ─────────────────────────────────────────────────── */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  padding: 20px 28px;
  background: var(--bg-card);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  border: 1px solid var(--border);
}

.page-title h2 {
  font-size: 22px;
  margin: 0 0 4px;
  color: var(--text-h);
}

.page-title__eyebrow {
  margin: 0 0 8px;
  font-size: 0.78rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--color-accent-secondary);
}

.page-title p {
  font-size: 14px;
  color: var(--text);
  margin: 0;
}

.header-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 12px;
}

/* ─── Profile Hero Card ──────────────────────────────────────── */
.profile-hero {
  padding: 28px 32px;
  margin-bottom: 28px;
  border-radius: 20px;
  border: 1px solid var(--border);
  background: var(--bg-card);
  backdrop-filter: blur(20px);
}

.profile-content {
  display: flex;
  align-items: center;
  gap: 24px;
}

.profile-avatar-large {
  width: 88px;
  height: 88px;
  border-radius: 20px;
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  color: #fff;
  font-size: 36px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  flex-shrink: 0;
  box-shadow: 0 8px 24px rgba(99,102,241,0.25);
}

.profile-avatar-large .avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 20px;
}

.profile-info {
  flex: 1;
  text-align: left;
}

.profile-name {
  font-size: 22px;
  font-weight: 600;
  color: var(--text-h);
  margin-bottom: 4px;
}

.profile-title {
  font-size: 14px;
  color: var(--text);
  margin-bottom: 10px;
}

.profile-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.profile-tag {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  background: var(--accent-bg);
  color: var(--accent);
  border: 1px solid var(--accent-border);
  transition: transform 0.15s ease;
}

.profile-tag:hover {
  transform: scale(1.05);
}

.profile-actions {
  margin-left: auto;
  display: flex;
  gap: 10px;
  flex-shrink: 0;
}

/* ─── 2×2 Grid for Profile Cards ─────────────────────────────── */
.profile-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  align-items: start;
}

.profile-card {
  padding: 24px;
  border-radius: 20px;
  border: 1px solid var(--border);
  background: var(--bg-card);
  backdrop-filter: blur(12px);
  min-height: 200px;
}

/* ─── Card Header ────────────────────────────────────────────── */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-h);
}

.card-icon {
  font-size: 20px;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--accent-bg);
}

/* ─── Interest Bars ──────────────────────────────────────────── */
.interest-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.interest-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.interest-label {
  font-size: 13px;
  color: var(--text);
  width: 90px;
  flex-shrink: 0;
  text-align: right;
}

.interest-bar {
  flex: 1;
  height: 8px;
  border-radius: 8px;
  background: rgba(148,163,184,0.12);
  overflow: hidden;
}

.interest-fill {
  height: 100%;
  border-radius: 8px;
  transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 8px rgba(99,102,241,0.2);
}

.interest-value {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-h);
  width: 42px;
  text-align: right;
  flex-shrink: 0;
}

/* ─── Collection List ────────────────────────────────────────── */
.collection-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.collection-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 14px;
  border-radius: 12px;
  background: rgba(148,163,184,0.04);
  border: 1px solid transparent;
  transition: all 0.2s ease;
  cursor: pointer;
}

.collection-item:hover {
  background: rgba(99,102,241,0.06);
  border-color: rgba(99,102,241,0.15);
  transform: translateX(4px);
}

.collection-thumb {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, rgba(99,102,241,0.15), rgba(139,92,246,0.15));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}

.collection-info {
  flex: 1;
  min-width: 0;
}

.collection-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-h);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.collection-meta {
  font-size: 12px;
  color: var(--text);
  margin-top: 2px;
}

/* ─── Settings Toggles ───────────────────────────────────────── */
.settings-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 10px 0;
  border-bottom: 1px solid rgba(148,163,184,0.08);
}

.setting-item:last-child {
  border-bottom: none;
}

.setting-info h5 {
  margin: 0 0 2px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-h);
}

.setting-info p {
  margin: 0;
  font-size: 12px;
  color: var(--text);
}

.toggle {
  width: 44px;
  height: 24px;
  border-radius: 12px;
  background: rgba(148,163,184,0.2);
  cursor: pointer;
  position: relative;
  transition: background 0.25s ease;
  flex-shrink: 0;
}

.toggle::after {
  content: '';
  position: absolute;
  top: 3px;
  left: 3px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 2px 6px rgba(0,0,0,0.15);
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.toggle.active {
  background: linear-gradient(90deg, var(--primary), var(--secondary));
}

.toggle.active::after {
  transform: translateX(20px);
}

/* ─── History List ───────────────────────────────────────────── */
.history-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 10px;
  transition: background 0.15s ease;
}

.history-item:hover {
  background: rgba(148,163,184,0.06);
}

.history-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: var(--accent-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  flex-shrink: 0;
}

.history-text {
  flex: 1;
  font-size: 13px;
  color: var(--text-h);
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.history-time {
  font-size: 12px;
  color: var(--text);
  flex-shrink: 0;
}

/* ─── Animation Delays ───────────────────────────────────────── */
.profile-grid .profile-card:nth-child(1) { animation-delay: 0.1s; }
.profile-grid .profile-card:nth-child(2) { animation-delay: 0.2s; }
.profile-grid .profile-card:nth-child(3) { animation-delay: 0.3s; }
.profile-grid .profile-card:nth-child(4) { animation-delay: 0.4s; }

/* ─── Responsive ─────────────────────────────────────────────── */
@media (max-width: 1200px) {
  .profile-grid {
    grid-template-columns: 1fr 1fr;
    gap: 20px;
  }
}

@media (max-width: 980px) {
  .main-content {
    margin-left: 0;
    padding: 20px;
  }

  .profile-grid {
    grid-template-columns: 1fr;
  }

  .profile-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .profile-actions {
    margin-left: 0;
    width: 100%;
  }

  .profile-actions .btn {
    flex: 1;
    justify-content: center;
  }

  .header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .header-actions {
    margin-left: 0;
  }
}

@media (max-width: 640px) {
  .main-content {
    padding: 16px;
  }

  .profile-hero {
    padding: 20px;
  }

  .interest-label {
    width: 70px;
    font-size: 12px;
  }
}
</style>
