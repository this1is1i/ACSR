<template>
  <aside class="sidebar">
    <div class="logo">
      <div class="logo-icon">🔬</div>
      <div class="logo-text">科研平台</div>
    </div>
    <div class="user-box">
      <div class="user-avatar-sm">{{ displayAvatar }}</div>
      <div>
        <div class="user-name">{{ username }}</div>
        <div class="user-role">{{ roleLabel }}</div>
      </div>
    </div>
    <nav class="nav-menu">
      <router-link v-if="isLoggedIn" to="/home" class="nav-item" :class="{ active: isActive('/home') }">
        <span class="nav-icon">🏠</span>
        <span>首页推荐</span>
      </router-link>
      <router-link to="/search" class="nav-item" :class="{ active: isActive('/search') }">
        <span class="nav-icon">🔍</span>
        <span>智能搜索</span>
      </router-link>
      <router-link to="/knowledge-graph" class="nav-item" :class="{ active: isActive('/knowledge-graph') }">
        <span class="nav-icon">📊</span>
        <span>数据可视化</span>
      </router-link>
      <router-link v-if="isLoggedIn" to="/community" class="nav-item" :class="{ active: isActive('/community') }">
        <span class="nav-icon">💬</span>
        <span>科研社区</span>
      </router-link>
      <router-link v-if="isLoggedIn" to="/messages" class="nav-item" :class="{ active: isActive('/messages') }">
        <span class="nav-icon">✉️</span>
        <span>实时私信</span>
      </router-link>
      <router-link v-if="isLoggedIn" to="/profile" class="nav-item" :class="{ active: isActive('/profile') }">
        <span class="nav-icon">👤</span>
        <span>个人中心</span>
      </router-link>
      <router-link v-if="isAdmin" to="/admin" class="nav-item" :class="{ active: isActive('/admin') }">
        <span class="nav-icon">🛡️</span>
        <span>管理员后台</span>
      </router-link>
    </nav>

    <div class="sidebar-footer">
      <button class="btn secondary" @click="toggleTheme">{{ themeLabel }}</button>
    </div>
  </aside>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { ref, onMounted, computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useUserStore } from '@/store/userStore'

const router = useRouter()
const userStore = useUserStore()
const { userInfo, token } = storeToRefs(userStore)
const themeLabel = ref('切换为浅色')

function isActive(path) {
  return router.currentRoute.value.path === path
}

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme)
  localStorage.setItem('theme', theme)
  themeLabel.value = theme === 'light' ? '切换为深色' : '切换为浅色'
}

function toggleTheme() {
  const cur = document.documentElement.getAttribute('data-theme') || 'dark'
  applyTheme(cur === 'light' ? 'dark' : 'light')
}

const displayAvatar = computed(() => {
  return username.value ? username.value.charAt(0).toUpperCase() : 'U'
})

const username = computed(() => userInfo.value?.username || '访客')
const roleLabel = computed(() => userInfo.value?.roleLabel || 'Guest')
const isLoggedIn = computed(() => !!token.value)
const isAdmin = computed(() => userInfo.value?.role === 'ADMIN')

onMounted(async () => {
  const saved = localStorage.getItem('theme')
  if (saved) applyTheme(saved)

  if (token.value && !userInfo.value) {
    try {
      await userStore.fetchProfile()
    } catch {
      userStore.clearToken()
    }
  }
})
</script>

<style scoped>
.sidebar {
  position: fixed;
  left: 0;
  top: 0;
  width: 260px;
  height: 100vh;
  background: rgba(15, 23, 42, 0.95);
  backdrop-filter: blur(20px);
  border-right: 1px solid rgba(148, 163, 184, 0.1);
  z-index: 1000;
  padding: 30px 0;
}
.logo { padding: 0 30px 12px; display:flex; align-items:center; gap:12px }
.logo-icon { width:42px; height:42px; background:linear-gradient(135deg,#6366f1,#8b5cf6); border-radius:12px; display:flex; align-items:center; justify-content:center; font-size:20px }
.logo-text { font-size:22px; font-weight:700; color: #f8fafc }
.user-box { padding: 10px 20px; display:flex; align-items:center; gap:12px }
.user-avatar-sm { width:44px; height:44px; border-radius:10px; background:linear-gradient(135deg,#6366f1,#8b5cf6); display:flex; align-items:center; justify-content:center; color:white; font-weight:700 }
.user-name { color:var(--text-primary); font-weight:600 }
.user-role { color: var(--text-secondary); font-size: 12px; margin-top: 2px }
.nav-menu { padding: 6px 20px }
.nav-item { display:flex; align-items:center; gap:14px; padding:14px 20px; margin:6px 0; border-radius:12px; color: #94a3b8; text-decoration:none; font-size:15px }
.nav-item.active { background: rgba(99,102,241,0.15); color: #f8fafc; border:1px solid rgba(99,102,241,0.3) }
.nav-icon { font-size:20px }
</style>
