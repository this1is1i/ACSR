import { createRouter, createWebHistory } from 'vue-router'
import { getStoredToken, getStoredUserInfo } from '@/utils/auth'

const routes = [
  { path: '/', redirect: () => (getStoredToken() ? '/home' : '/search') },
  { path: '/login', component: () => import('@/views/Login.vue'), meta: { public: true } },
  { path: '/home', component: () => import('@/views/Home.vue') },
  { path: '/search', component: () => import('@/views/Search.vue'), meta: { public: true } },
  { path: '/paper/:id', component: () => import('@/views/PaperDetail.vue'), meta: { public: true } },
  { path: '/paper/aminer/:aminerId', component: () => import('@/views/PaperDetail.vue'), meta: { public: true } },
  { path: '/knowledge-graph', component: () => import('@/views/KnowledgeGraph.vue') },
  { path: '/community', component: () => import('@/views/Community.vue') },
  { path: '/profile', component: () => import('@/views/Profile.vue') },
  { path: '/profile/edit', component: () => import('@/views/EditProfile.vue') },
  { path: '/messages', component: () => import('@/views/RealtimeChat.vue') },
  { path: '/admin', component: () => import('@/views/AdminConsole.vue'), meta: { roles: ['ADMIN'] } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 未登录跳转 login
router.beforeEach((to) => {
  // SockJS 内部传输路径（iframe.html 等），放行不做路由拦截
  if (to.path.startsWith('/ws-messages/')) {
    return
  }

  const token = getStoredToken()
  const userInfo = getStoredUserInfo()

  if (!to.meta.public && !token) {
    return '/login'
  }

  if (to.meta.roles?.length) {
    if (!token) return '/login'
    if (!userInfo?.role || !to.meta.roles.includes(userInfo.role)) {
      return '/home'
    }
  }
})

export default router
