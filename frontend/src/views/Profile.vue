<template>
  <div class="profile-root">
    <div class="bg-animation"></div>
    <Sidebar />
    <main class="main-content">
      <header class="header">
        <div class="page-title">
          <h2>👤 个人中心</h2>
          <p>管理您的学术档案与个性化设置</p>
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
        <div class="profile-card card animate-fade-up">
          <div class="card-header">
            <div class="card-title">
              <div class="card-icon">🎯</div>
              研究兴趣分布
            </div>
            <button class="edit-btn btn secondary" @click="manageInterests">管理</button>
          </div>

          <div class="interest-list">
            <div v-for="(i, idx) in interests" :key="idx" class="interest-item">
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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import Sidebar from '@/components/Sidebar.vue'

const router = useRouter()
const interests = ref([
  { name: '深度学习', percent: 85, color: 'linear-gradient(90deg, #6366f1, #8b5cf6)' },
  { name: '计算机视觉', percent: 72, color: 'linear-gradient(90deg, #06b6d4, #22d3ee)' },
  { name: '强化学习', percent: 45, color: 'linear-gradient(90deg, #10b981, #34d399)' },
  { name: '自然语言处理', percent: 38, color: 'linear-gradient(90deg, #f59e0b, #fbbf24)' },
  { name: '数据挖掘', percent: 25, color: 'linear-gradient(90deg, #ec4899, #f472b6)' }
])

const profile = ref({ id: null, username: '', avatar: '', email: '', bio: '', researchInterests: '' })

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

function logout() {
  localStorage.removeItem('token')
  localStorage.removeItem('userId')
  ElMessage.success('已退出登录')
  router.push('/login')
}

import { getProfile } from '@/api/user'

onMounted(async () => {
  // load real profile from backend
  try {
    const res = await getProfile()
    const data = res.data || res
    profile.value = { id: data.id, username: data.username, avatar: data.avatar, email: data.email, bio: data.bio, researchInterests: data.researchInterests }
  } catch (e) {
    console.error('failed to load profile', e)
  }

  // animate fills like original template
  const fills = document.querySelectorAll('.interest-fill')
  fills.forEach(fill => {
    const width = fill.style.width
    fill.style.width = '0'
    setTimeout(() => { fill.style.width = width }, 300)
  })
})
</script>

<style scoped>
@import '@/style.css';

/* Reserve space for fixed sidebar */
.profile-root .main-content { margin-left: 260px; padding: 24px 32px; min-height: 100vh }

.profile-hero { padding: 20px; display:flex; gap:20px; align-items:center }
.profile-avatar-large { width:96px; height:96px; border-radius:12px; font-size:40px; display:flex; align-items:center; justify-content:center; position:relative; overflow:hidden }
.profile-avatar-large .avatar-img { width:100%; height:100%; object-fit:cover }
.profile-info { text-align:left }
.profile-actions { margin-left:auto; display:flex; gap:10px }

.profile-grid { display:grid; grid-template-columns: 320px 1fr; gap:22px; align-items:start }
.profile-card { padding:18px }

.header-actions { margin-left:auto; display:flex; align-items:center; gap:12px }

/* Left column summary */
.profile-summary { display:flex; flex-direction:column; gap:14px }
.profile-summary .profile-tag { display:inline-block; margin-right:6px }

/* Right column: grid of cards */
.right-cards { display:grid; grid-template-columns:1fr 1fr; gap:16px }
.collection-list .collection-item { display:flex; gap:12px; align-items:center }
.interest-list .interest-item { display:flex; gap:12px; align-items:center }

@media (max-width: 980px) {
  .profile-grid { grid-template-columns: 1fr; }
  .right-cards { grid-template-columns: 1fr }
  .profile-hero { flex-direction:column; align-items:flex-start }
  .profile-actions { margin-left:0 }
  .profile-root .main-content { margin-left: 0; padding: 18px }
}
</style>