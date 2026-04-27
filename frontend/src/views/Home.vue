<template>
  <div class="home-root">
    <div class="bg-animation"></div>
    <Sidebar />
    <main class="main-content">
      <header class="header home-header">
        <div class="page-title">
          <p class="home-header__eyebrow">Future Lab</p>
          <h2>研究中心</h2>
          <p>让推荐流与学习路径在同一个工作台里持续衔接。</p>
        </div>
        <div class="header-actions">
          <button class="btn secondary" type="button" @click="logout">退出登录</button>
        </div>
      </header>

      <HubHero
        :user-name="userName"
        :loading="loading"
        :metrics="heroMetrics"
        :path-summary="pathSummary"
        @explore="router.push('/search')"
        @view-path="router.push('/knowledge-graph')"
      />

      <p v-if="loadError" class="home-error">{{ loadError }}</p>

      <div class="hub-layout">
        <RecommendationStream
          :items="recommendations"
          :loading="loading"
          :focus-topic="pathSummary.topic"
          @explore="router.push('/search')"
        />
        <LearningPathPanel
          :loading="loading"
          :summary="pathSummary"
          @view-path="router.push('/knowledge-graph')"
        />
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import Sidebar from '@/components/Sidebar.vue'
import HubHero from '@/components/home/HubHero.vue'
import LearningPathPanel from '@/components/home/LearningPathPanel.vue'
import RecommendationStream from '@/components/home/RecommendationStream.vue'
import { getRecommendations } from '@/api/recommend'
import { getVisualizationData } from '@/api/visualization'
import { useUserStore } from '@/store/userStore'
import { buildLearningPathSummary } from '@/utils/path'

const router = useRouter()
const userStore = useUserStore()
const recommendations = ref([])
const loading = ref(false)
const visualizationData = ref({})
const loadError = ref('')

const userName = computed(() => userStore.userInfo?.username || '研究者')
const pathSummary = computed(() => buildLearningPathSummary(visualizationData.value))
const stats = computed(() => visualizationData.value?.stats || {})
const heroMetrics = computed(() => ([
  {
    label: '推荐候选',
    value: `${recommendations.value.length} 篇`,
    caption: recommendations.value.length ? '已按近期行为完成排序' : '浏览或收藏更多论文后会刷新',
  },
  {
    label: '路径进度',
    value: `${pathSummary.value.completionPercent}%`,
    caption: `当前主线：${pathSummary.value.topic}`,
  },
  {
    label: '下一节点',
    value: pathSummary.value.isComplete ? '当前路径已完成' : (pathSummary.value.nextStep?.name || '待生成'),
    caption: pathSummary.value.nextStepCaption,
  },
  {
    label: '学习热度',
    value: stats.value.readCount ? `${stats.value.readCount} 篇` : '—',
    caption: stats.value.readTime ? `累计阅读 ${stats.value.readTime}` : '等待可视化数据同步',
  },
]))

async function loadHomeHub() {
  loading.value = true
  loadError.value = ''
  try {
    const [recommendResult, visualizationResult] = await Promise.allSettled([
      getRecommendations(10),
      getVisualizationData(),
    ])

    recommendations.value = recommendResult.status === 'fulfilled'
      ? recommendResult.value?.data?.recommendations || []
      : []

    visualizationData.value = visualizationResult.status === 'fulfilled'
      ? visualizationResult.value?.data || {}
      : {}

    if (recommendResult.status === 'rejected' && visualizationResult.status === 'rejected') {
      loadError.value = '研究中心暂时不可用，请稍后重试。'
    }
  } finally {
    loading.value = false
  }
}

function logout() {
  userStore.clearToken()
  router.push('/login')
}

onMounted(loadHomeHub)
</script>

<style scoped>
.home-root {
  min-height: 100vh;
  overflow-x: hidden;
}

.bg-animation {
  position: fixed;
  inset: 0;
  z-index: -1;
  background:
    radial-gradient(circle at 18% 18%, rgba(124, 140, 255, 0.16), transparent 28%),
    radial-gradient(circle at 82% 12%, rgba(55, 213, 255, 0.12), transparent 24%),
    radial-gradient(circle at 50% 80%, rgba(94, 234, 212, 0.08), transparent 24%);
}

.main-content {
  display: grid;
  gap: var(--space-6);
}

.home-header__eyebrow {
  margin-bottom: var(--space-2);
  font-size: 0.78rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--color-accent-secondary);
}

.hub-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(320px, 0.9fr);
  gap: var(--space-6);
  align-items: start;
}

.home-error {
  padding: var(--space-4);
  border: 1px solid rgba(251, 113, 133, 0.28);
  border-radius: var(--radius-lg);
  background: rgba(127, 29, 29, 0.16);
  color: #fecdd3;
}

@media (max-width: 1120px) {
  .hub-layout {
    grid-template-columns: 1fr;
  }
}
</style>
