import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/home' },
  { path: '/login', component: () => import('@/views/Login.vue'), meta: { public: true } },
  { path: '/home', component: () => import('@/views/Home.vue') },
  { path: '/search', component: () => import('@/views/Search.vue') },
  { path: '/knowledge-graph', component: () => import('@/views/KnowledgeGraph.vue') },
  { path: '/community', component: () => import('@/views/Community.vue') },
  { path: '/profile', component: () => import('@/views/Profile.vue') },
  { path: '/profile/edit', component: () => import('@/views/EditProfile.vue') },
  { path: '/messages', component: () => import('@/views/RealtimeChat.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 未登录跳转 login
router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  if (!to.meta.public && !token) {
    return '/login'
  }
})

export default router
