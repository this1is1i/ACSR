<template>
  <div class="paper-detail-page">
    <div class="paper-detail-card">
      <div class="paper-detail-header">
        <button class="back-btn" @click="router.push('/search')">← 返回搜索</button>
        <button class="download-btn" @click="handleDownload" :disabled="downloading || !paper">
          {{ downloading ? '下载中...' : '下载 TXT' }}
        </button>
      </div>

      <div v-if="loading" class="paper-detail-state">正在加载论文详情...</div>
      <div v-else-if="paper" class="paper-detail-content">
        <h1>{{ paper.title }}</h1>
        <p class="paper-meta">{{ authorText }} · {{ paper.venue || '未知来源' }} · {{ paper.year || '未知年份' }}</p>

        <div class="paper-section">
          <h2>摘要</h2>
          <p>{{ paper.abstract || '暂无摘要' }}</p>
        </div>

        <div class="paper-grid">
          <div class="paper-section">
            <h2>关键词</h2>
            <div class="tag-list">
              <span v-for="keyword in keywordList" :key="keyword" class="tag">{{ keyword }}</span>
            </div>
          </div>
          <div class="paper-section">
            <h2>DOI</h2>
            <p>{{ paper.doi || '暂无 DOI' }}</p>
          </div>
        </div>
      </div>
      <div v-else class="paper-detail-state">未找到论文详情</div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { downloadPaperTxt, getPaperById } from '@/api/paper'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const downloading = ref(false)
const paper = ref(null)

const authorText = computed(() => {
  const authors = paper.value?.authors
  if (Array.isArray(authors)) return authors.join(', ')
  return authors || '未知作者'
})

const keywordList = computed(() => {
  const keywords = paper.value?.keywords || paper.value?.tags || []
  return Array.isArray(keywords) && keywords.length ? keywords : ['暂无关键词']
})

async function loadPaperDetail(id) {
  if (!id) return
  loading.value = true
  try {
    const res = await getPaperById(id)
    paper.value = res.data || null
  } catch (error) {
    paper.value = null
  } finally {
    loading.value = false
  }
}

async function handleDownload() {
  if (!paper.value) return
  downloading.value = true
  try {
    const blob = await downloadPaperTxt(route.params.id)
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${paper.value.title || `paper-${route.params.id}`}.txt`
    link.click()
    window.URL.revokeObjectURL(url)
  } catch (error) {
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
  padding: 40px 20px;
  background: #0f172a;
  color: #f8fafc;
}

.paper-detail-card {
  max-width: 960px;
  margin: 0 auto;
  padding: 32px;
  border-radius: 24px;
  background: rgba(30, 41, 59, 0.9);
  border: 1px solid rgba(148, 163, 184, 0.15);
}

.paper-detail-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 24px;
}

.back-btn,
.download-btn {
  padding: 10px 18px;
  border: none;
  border-radius: 12px;
  color: #fff;
  cursor: pointer;
}

.back-btn {
  background: rgba(148, 163, 184, 0.2);
}

.download-btn {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
}

.download-btn:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

.paper-detail-content h1 {
  margin-bottom: 12px;
  font-size: 32px;
}

.paper-meta,
.paper-section p {
  color: #cbd5e1;
  line-height: 1.8;
}

.paper-section {
  margin-top: 24px;
}

.paper-section h2 {
  margin-bottom: 12px;
  font-size: 18px;
}

.paper-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 24px;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.tag {
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(99, 102, 241, 0.2);
  color: #c4b5fd;
}

.paper-detail-state {
  color: #cbd5e1;
}
</style>
