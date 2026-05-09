<template>
  <aside class="sidebar">
    <div class="sidebar__brand">
      <div class="sidebar__brand-mark">ACS</div>
      <div class="sidebar__brand-copy">
        <p class="sidebar__eyebrow">Future Lab</p>
        <h2 class="sidebar__title">科研推荐平台</h2>
      </div>
    </div>

    <div class="sidebar__profile">
      <div class="sidebar__avatar">
        <img v-if="userAvatar" :src="userAvatar" class="sidebar__avatar-img" alt="avatar" />
        <span v-else>{{ displayAvatar }}</span>
      </div>
      <div class="sidebar__profile-copy">
        <strong class="sidebar__name">{{ username }}</strong>
        <span class="sidebar__role">{{ roleLabel }}</span>
      </div>
    </div>

    <nav class="sidebar__nav" aria-label="Primary navigation">
      <section v-for="group in navGroups" :key="group.label" class="sidebar__group">
        <p class="sidebar__group-label">{{ group.label }}</p>
        <router-link
          v-for="item in group.items"
          :key="item.to"
          :to="item.to"
          class="sidebar__link"
          :class="{ 'sidebar__link--active': isActive(item.to) }"
          :aria-label="item.label"
        >
          <span class="sidebar__icon" aria-hidden="true">{{ item.icon }}</span>
          <span class="sidebar__link-copy">
            <span class="sidebar__link-label">{{ item.label }}</span>
            <small aria-hidden="true">{{ item.description }}</small>
          </span>
        </router-link>
      </section>
    </nav>

    <div class="sidebar__footer">
      <button class="sidebar__theme-toggle" type="button" @click="toggleTheme">
        {{ themeLabel }}
      </button>
    </div>
  </aside>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useUserStore } from '@/store/userStore'

const route = useRoute()
const userStore = useUserStore()
const { userInfo, token } = storeToRefs(userStore)
const themeLabel = ref('切换浅色')

const username = computed(() => userInfo.value?.username || '访客')
const roleLabel = computed(() => userInfo.value?.roleLabel || '访客模式')
const isLoggedIn = computed(() => !!token.value)
const isAdmin = computed(() => userInfo.value?.role === 'ADMIN')
const displayAvatar = computed(() => (username.value ? username.value.charAt(0).toUpperCase() : 'U'))
const userAvatar = computed(() => userInfo.value?.avatar || '')

const exploreItems = computed(() => [
  ...(isLoggedIn.value ? [{ to: '/home', label: '研究中心', description: '推荐与路径', icon: '研' }] : []),
  { to: '/search', label: '智能搜索', description: '目标导向检索', icon: '搜' },
  { to: '/knowledge-graph', label: '知识图谱', description: '图谱与洞察', icon: '图' },
])

const collaborationItems = computed(() => (
  isLoggedIn.value
    ? [
        { to: '/community', label: '科研社区', description: '同行交流', icon: '社' },
        { to: '/messages', label: '实时私信', description: '即时协作', icon: '信' },
        { to: '/profile', label: '个人中心', description: '账号与偏好', icon: '我' },
      ]
    : []
))

const managementItems = computed(() => (
  isAdmin.value
    ? [{ to: '/admin', label: '管理员后台', description: '控制与治理', icon: '管' }]
    : []
))

const navGroups = computed(() => [
  { label: '探索', items: exploreItems.value },
  ...(collaborationItems.value.length ? [{ label: '协作', items: collaborationItems.value }] : []),
  ...(managementItems.value.length ? [{ label: '管理', items: managementItems.value }] : []),
])

function isActive(path) {
  return route.path === path || route.path.startsWith(`${path}/`)
}

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme)
  document.documentElement.classList.toggle('dark', theme !== 'light')
  localStorage.setItem('theme', theme)
  themeLabel.value = theme === 'light' ? '切换深色' : '切换浅色'
}

function toggleTheme() {
  const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark'
  applyTheme(currentTheme === 'light' ? 'dark' : 'light')
}

onMounted(async () => {
  applyTheme(localStorage.getItem('theme') || 'dark')

  if (token.value) {
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
  inset: 0 auto 0 0;
  z-index: 20;
  width: var(--shell-sidebar-width);
  padding: var(--space-7) var(--space-4) var(--space-5);
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
  background:
    linear-gradient(180deg, rgba(124, 140, 255, 0.14), transparent 24%),
    var(--color-sidebar-surface);
  border-right: 1px solid var(--color-border-subtle);
  box-shadow: var(--shadow-card);
  backdrop-filter: blur(18px);
}

.sidebar__brand {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: 0 var(--space-2);
}

.sidebar__brand-mark {
  width: 3rem;
  height: 3rem;
  border-radius: var(--radius-md);
  display: grid;
  place-items: center;
  font-size: 0.95rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: #fff;
  background: linear-gradient(135deg, var(--primary), var(--accent));
  box-shadow: var(--shadow-glow);
}

.sidebar__eyebrow {
  margin: 0 0 var(--space-1);
  font-size: 0.72rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--color-accent-secondary);
}

.sidebar__title {
  font-size: 1.1rem;
}

.sidebar__profile {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-4);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-xl);
  background: rgba(255, 255, 255, 0.03);
}

.sidebar__avatar {
  width: 3rem;
  height: 3rem;
  border-radius: var(--radius-md);
  display: grid;
  place-items: center;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  overflow: hidden;
}
.sidebar__avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: var(--radius-md);
}

.sidebar__profile-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.sidebar__name {
  color: var(--color-text-primary);
}

.sidebar__role {
  font-size: 0.82rem;
  color: var(--color-text-secondary);
}

.sidebar__nav {
  flex: 1;
  overflow-y: auto;
  padding-right: var(--space-1);
}

.sidebar__group + .sidebar__group {
  margin-top: var(--space-6);
}

.sidebar__group-label {
  margin: 0 0 var(--space-3);
  padding: 0 var(--space-3);
  font-size: 0.76rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.sidebar__link {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: 0.9rem 1rem;
  border: 1px solid transparent;
  border-radius: var(--radius-lg);
  color: var(--color-text-secondary);
  transition:
    transform 0.16s ease,
    border-color 0.16s ease,
    background 0.16s ease,
    color 0.16s ease;
}

.sidebar__link + .sidebar__link {
  margin-top: var(--space-2);
}

.sidebar__link:hover {
  transform: translateX(2px);
  color: var(--color-text-primary);
  background: var(--color-bg-hover);
  border-color: var(--color-border-subtle);
}

.sidebar__link--active {
  color: var(--color-text-primary);
  background: linear-gradient(135deg, rgba(124, 140, 255, 0.18), rgba(55, 213, 255, 0.08));
  border-color: var(--color-border-strong);
  box-shadow: var(--shadow-glow);
}

.sidebar__icon {
  flex: 0 0 auto;
  width: 2.25rem;
  height: 2.25rem;
  border-radius: var(--radius-md);
  display: grid;
  place-items: center;
  font-size: 0.88rem;
  font-weight: 700;
  color: var(--color-text-primary);
  background: rgba(255, 255, 255, 0.05);
}

.sidebar__link-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.12rem;
}

.sidebar__link-label {
  font-weight: 600;
}

.sidebar__link-copy small {
  color: var(--color-text-muted);
}

.sidebar__footer {
  padding: 0 var(--space-2);
}

.sidebar__theme-toggle {
  width: 100%;
  padding: 0.85rem 1rem;
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.03);
  color: var(--color-text-primary);
  cursor: pointer;
  transition: border-color 0.16s ease, background 0.16s ease;
}

.sidebar__theme-toggle:hover {
  background: var(--color-bg-hover);
  border-color: var(--color-border-strong);
}

@media (max-width: 980px) {
  .sidebar {
    position: relative;
    inset: auto;
    width: 100%;
    padding: var(--space-4);
    gap: var(--space-4);
    border-right: none;
    border-bottom: 1px solid var(--color-border-subtle);
  }

  .sidebar__nav {
    display: flex;
    gap: var(--space-4);
    overflow-x: auto;
    overflow-y: hidden;
    padding-bottom: var(--space-2);
  }

  .sidebar__group {
    min-width: 13rem;
  }
}
</style>
