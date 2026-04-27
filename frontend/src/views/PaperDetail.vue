<template>
  <div class="paper-detail-page">
    <div class="paper-detail-layout">
      <section class="paper-reading-canvas card glass" data-testid="paper-reading-canvas">
        <PageHeader
          eyebrow="Reading Canvas"
          :title="paper?.title || '论文阅读画布'"
          description="在这里连续阅读论文内容，并结合当前路径上下文决定下一步研究动作。"
        />

        <div v-if="loading" class="paper-detail-state">正在加载论文详情...</div>

        <div v-else-if="paper" class="paper-detail-content">
          <p class="paper-meta">{{ authorText }} · {{ paper.venue || '未知来源' }} · {{ paper.year || '未知年份' }}</p>

          <div class="paper-section">
            <h2>摘要</h2>
            <p>{{ abstractText }}</p>
          </div>

          <div class="paper-section">
            <h2>关键词</h2>
            <div class="tag-list">
              <span v-for="keyword in keywordList" :key="keyword" class="tag">{{ keyword }}</span>
            </div>
          </div>
        </div>

        <div v-else class="paper-detail-state">未找到论文详情</div>
      </section>

      <PaperPathRail
        :paper="paper"
        :path-context="pathContext"
        :downloading="downloading"
        @back="handleBack"
        @download="handleDownload"
      />
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { downloadPaperTxt, getPaperById } from '@/api/paper'
import PageHeader from '@/components/layout/PageHeader.vue'
import PaperPathRail from '@/components/paper/PaperPathRail.vue'
import {
  buildPaperPathContext,
  getDownloadFilename,
  getStoredSearchState,
  normalizePaper,
  SEARCH_RESTORE_PENDING_KEY,
} from '@/utils/paper'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const downloading = ref(false)
const paper = ref(null)
const hasSearchContext = ref(
  typeof window !== 'undefined' && window.sessionStorage.getItem(SEARCH_RESTORE_PENDING_KEY) === '1'
)

const abstractText = computed(() => paper.value?.abstractText || '暂无摘要')
const authorText = computed(() => paper.value?.authorText || '未知作者')
const keywordList = computed(() => (paper.value?.keywordsList?.length ? paper.value.keywordsList : ['暂无关键词']))
const pathContext = computed(() => buildPaperPathContext(paper.value, {
  searchState: getStoredSearchState(),
  hasSearchContext: hasSearchContext.value,
}))

async function loadPaperDetail(id) {
  if (!id) return
  loading.value = true
  try {
    const res = await getPaperById(id)
    paper.value = res.data ? normalizePaper(res.data) : null
  } catch {
    paper.value = null
  } finally {
    loading.value = false
  }
}

function handleBack() {
  const shouldReturnToSearch = window.sessionStorage.getItem(SEARCH_RESTORE_PENDING_KEY) === '1'
  if (shouldReturnToSearch) {
    router.back()
    return
  }

  router.push('/search')
}

async function handleDownload() {
  if (!paper.value) return

  downloading.value = true
  try {
    const response = await downloadPaperTxt(route.params.id)
    const url = window.URL.createObjectURL(response.data)
    const link = document.createElement('a')
    link.href = url
    link.download = getDownloadFilename(
      response.headers?.['content-disposition'],
      `${paper.value.title || `paper-${route.params.id}`}.txt`
    )
    link.click()
    window.URL.revokeObjectURL(url)
  } catch {
    ElMessage.error('下载失败，请稍后重试')
  } finally {
    downloading.value = false
  }
}

watch(() => route.params.id, loadPaperDetail, { immediate: true })
</script>

<style scoped>
.paper-detail-page {
  min-height: 100vh;
  padding: clamp(1.2rem, 2vw, 2rem);
  background:
    radial-gradient(circle at top left, rgba(124, 140, 255, 0.16), transparent 28%),
    radial-gradient(circle at top right, rgba(55, 213, 255, 0.12), transparent 24%),
    var(--color-bg-canvas);
}

.paper-detail-layout {
  max-width: 1280px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(300px, 360px);
  gap: var(--space-6);
  align-items: start;
}

.paper-reading-canvas {
  display: grid;
  gap: var(--space-6);
  padding: clamp(1.35rem, 2vw, 2rem);
}

.paper-detail-content {
  display: grid;
  gap: var(--space-5);
}

.paper-meta,
.paper-section p {
  color: var(--color-text-secondary);
  line-height: 1.85;
}

.paper-section {
  display: grid;
  gap: var(--space-3);
  padding: var(--space-5);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-xl);
  background: rgba(255, 255, 255, 0.02);
}

.paper-section h2 {
  font-size: 1.05rem;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.tag {
  padding: 0.45rem 0.8rem;
  border-radius: 999px;
  background: rgba(124, 140, 255, 0.16);
  color: #c4b5fd;
}

.paper-detail-state {
  color: var(--color-text-secondary);
}

@media (max-width: 1120px) {
  .paper-detail-layout {
    grid-template-columns: 1fr;
  }
}
</style>
