<template>
  <div class="home-root page-root">
    <div class="bg-animation"></div>
    <Sidebar />
    <main class="main-content">
      <p v-if="loadError" class="home-error">{{ loadError }}</p>

      <div class="hub-layout">
        <RecommendationStream
          :items="recommendations"
          :loading="loading"
          :focus-topic="pathSummary.topic"
        />
        <LearningPathPanel
          :loading="loading"
          :summary="pathSummary"
        />
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import Sidebar from '@/components/Sidebar.vue'
import LearningPathPanel from '@/components/home/LearningPathPanel.vue'
import RecommendationStream from '@/components/home/RecommendationStream.vue'
import { getRecommendations } from '@/api/recommend'
import { getVisualizationData } from '@/api/visualization'
import { buildLearningPathSummary } from '@/utils/path'

const router = useRouter()
const recommendations = ref([])
const loading = ref(false)
const visualizationData = ref({})
const loadError = ref('')

const pathSummary = computed(() => buildLearningPathSummary(visualizationData.value))
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
  grid-template-columns: minmax(0, 1.35fr) minmax(280px, 0.9fr);
  gap: var(--space-6);
  align-items: start;
  overflow: hidden;
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
