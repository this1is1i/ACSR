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

        <div class="profile-card card animate-fade-up" data-area="profile">
          <div class="card-header">
            <div class="card-title">
              <div class="card-icon">⭐</div>
              我的收藏
            </div>
            <button class="edit-btn btn secondary" @click="viewAllCollections">查看全部</button>
          </div>

          <div class="collection-list" v-if="collectionsLoading">
            <div class="empty-hint">加载中...</div>
          </div>
          <div class="collection-list" v-else-if="collections.length">
            <div v-for="(c, idx) in collections" :key="idx" class="collection-item" @click="c.id && router.push(`/paper/${c.id}`)">
              <div class="collection-thumb">📄</div>
              <div class="collection-info">
                <div class="collection-title">{{ c.title }}</div>
                <div class="collection-meta">{{ c.meta }}</div>
              </div>
            </div>
          </div>
          <div class="collection-list" v-else>
            <div class="empty-hint">还没有收藏论文</div>
          </div>
        </div>

        <div class="profile-card card animate-fade-up" data-area="profile">
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

        <div class="profile-card card animate-fade-up" data-area="profile">
          <div class="card-header">
            <div class="card-title">
              <div class="card-icon">🕐</div>
              最近活动
            </div>
            <button class="edit-btn btn secondary" @click="doClearHistory">清空</button>
          </div>

          <div class="history-list" v-if="historyLoading">
            <div class="empty-hint">加载中...</div>
          </div>
          <div class="history-list" v-else-if="history.length">
            <div v-for="(h, idx) in history" :key="idx" class="history-item">
              <div class="history-icon">{{ h.icon }}</div>
              <div class="history-text">{{ h.text }}</div>
              <div class="history-time">{{ h.time }}</div>
            </div>
          </div>
          <div class="history-list" v-else>
            <div class="empty-hint">暂无活动记录</div>
          </div>
        </div>
      </div>

      <!-- Interests edit dialog -->
      <div class="dialog-overlay" v-if="interestsEditVisible" @click.self="interestsEditVisible = false">
        <div class="dialog-card">
          <h3>管理研究兴趣</h3>
          <p class="dialog-desc">用逗号分隔多个研究方向</p>
          <input v-model="interestsEditValue" class="dialog-input" placeholder="例如：深度学习, 强化学习, 计算机视觉" @keyup.enter="saveInterests" />
          <div class="dialog-actions">
            <button class="btn secondary" @click="interestsEditVisible = false">取消</button>
            <button class="btn primary" @click="saveInterests">保存</button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import Sidebar from '@/components/Sidebar.vue'
import ResearchAssetsPanel from '@/components/profile/ResearchAssetsPanel.vue'
import { getPathSurfaceData } from '@/api/visualization'
import { buildLearningPathSummary } from '@/utils/path'
import { getProfile, updateProfile, getFavorites } from '@/api/user'
import { getActivityHistory, clearActivityHistory } from '@/api/recommend'

const router = useRouter()

const profile = ref({ id: null, username: '', avatar: '', email: '', bio: '', researchInterests: '' })
const visualizationData = ref({})
const recommendations = ref([])
const assetsLoading = ref(false)
const collectionsLoading = ref(false)
const historyLoading = ref(false)
const pathSummary = computed(() => buildLearningPathSummary(visualizationData.value))

const collections = ref([])
const history = ref([])
const interestsEditVisible = ref(false)
const interestsEditValue = ref('')

const settings = ref(loadSettings())

function loadSettings() {
  try {
    const saved = localStorage.getItem('profileSettings')
    if (saved) return JSON.parse(saved)
  } catch (e) { /* ignore */ }
  return [
    { title: '个性化推荐', desc: '基于阅读历史智能推荐论文', enabled: true },
    { title: '邮件通知', desc: '接收关注领域的新论文提醒', enabled: true },
    { title: '社区互动', desc: '允许其他用户查看我的动态', enabled: false },
    { title: '数据同步', desc: '跨设备同步阅读记录和收藏', enabled: true }
  ]
}

function saveSettings() {
  localStorage.setItem('profileSettings', JSON.stringify(settings.value))
}

function toggleSetting(i) {
  settings.value[i].enabled = !settings.value[i].enabled
  saveSettings()
}

async function fetchFavorites() {
  collectionsLoading.value = true
  try {
    const res = await getFavorites()
    const data = res.data || res
    collections.value = (data || []).map(p => ({
      id: p.id,
      title: p.title || 'Untitled',
      meta: [p.authors, p.venue, p.year].filter(Boolean).join(' · ') || '—'
    }))
  } catch (e) {
    console.error('Failed to load favorites', e)
    collections.value = []
  } finally {
    collectionsLoading.value = false
  }
}

async function fetchHistory() {
  historyLoading.value = true
  try {
    const res = await getActivityHistory(20)
    const data = res.data || res
    const actionIcons = { click: '👁️', favorite: '⭐', read: '📖' }
    const actionLabels = { click: '浏览了', favorite: '收藏了', read: '阅读了' }
    history.value = (data || []).map(item => {
      const action = item.action || 'click'
      return {
        icon: actionIcons[action] || '📌',
        text: `${actionLabels[action] || '查看了'}《${item.paper_title || 'Unknown'}》`,
        time: formatRelativeTime(item.timestamp)
      }
    })
  } catch (e) {
    console.error('Failed to load history', e)
    history.value = []
  } finally {
    historyLoading.value = false
  }
}

function formatRelativeTime(timestamp) {
  if (!timestamp) return ''
  const now = Date.now()
  const then = new Date(timestamp).getTime()
  const diff = now - then
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}小时前`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}天前`
  return new Date(timestamp).toLocaleDateString()
}

function shareProfile() {
  // Browser share API — no-op when unsupported
  if (navigator.share) {
    navigator.share({ title: profile.value.username + ' 的研究主页', url: window.location.href }).catch(() => {})
  } else {
    ElMessage.info('复制链接分享给好友')
  }
}

function manageInterests() {
  interestsEditValue.value = profile.value.researchInterests || ''
  interestsEditVisible.value = true
}

async function saveInterests() {
  try {
    await updateProfile({ researchInterests: interestsEditValue.value })
    profile.value.researchInterests = interestsEditValue.value
    interestsEditVisible.value = false
    ElMessage.success('研究兴趣已更新')
  } catch (e) {
    ElMessage.error('保存失败，请重试')
  }
}

function viewAllCollections() {
  const el = document.querySelector('.collection-list')
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
}

async function doClearHistory() {
  try {
    await ElMessageBox.confirm('确定要清空所有活动记录吗？', '确认', { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' })
    await clearActivityHistory()
    history.value = []
    ElMessage.success('已清空')
  } catch (e) {
    // cancelled or error
    if (e !== 'cancel') console.error('Failed to clear history', e)
  }
}

function logout() {
  localStorage.removeItem('token')
  localStorage.removeItem('userId')
  ElMessage.success('已退出登录')
  router.push('/login')
}

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
    fetchFavorites(),
    fetchHistory(),
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

.profile-card[data-area="profile"] {
  border-left: 3px solid var(--color-area-profile);
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

/* ─── Dialog ─────────────────────────────────────────────────── */
.dialog-overlay {
  position: fixed; inset: 0; z-index: 1000;
  background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center;
}
.dialog-card {
  background: var(--bg-card); padding: 28px 32px; border-radius: 16px;
  width: 90%; max-width: 440px; box-shadow: 0 20px 60px rgba(0,0,0,0.3);
}
.dialog-card h3 { margin: 0 0 8px; font-size: 18px; color: var(--text-h); }
.dialog-desc { margin: 0 0 16px; font-size: 13px; color: var(--text); }
.dialog-input {
  width: 100%; height: 42px; padding: 0 14px; border-radius: 10px;
  border: 1px solid var(--border); background: var(--bg); color: var(--text-h);
  font-size: 14px; outline: none; margin-bottom: 20px;
}
.dialog-input:focus { border-color: var(--primary); }
.dialog-actions { display: flex; gap: 10px; justify-content: flex-end; }

/* ─── Empty state ────────────────────────────────────────────── */
.empty-hint {
  text-align: center; padding: 20px 0; font-size: 13px; color: var(--text);
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

}
</style>
