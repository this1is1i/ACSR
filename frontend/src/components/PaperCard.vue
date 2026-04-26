<template>
  <div class="paper-card">
    <div class="card-header">
      <h3 class="title">{{ paper.title }}</h3>
      <el-tag size="small" type="info" v-if="paper.year">{{ paper.year }}</el-tag>
    </div>

    <p class="authors" v-if="paper.authors">
      {{ formatAuthors(paper.authors) }}
    </p>
    <p class="venue" v-if="paper.venue">{{ paper.venue }}</p>

    <p class="abstract" v-if="paper.abstrakt || paper.abstract">
      {{ paper.abstrakt || paper.abstract }}
    </p>

    <!-- 推荐理由 -->
    <div class="reason" v-if="paper.reason">
      <el-icon><InfoFilled /></el-icon>
      <span>{{ paper.reason }}</span>
    </div>

    <div class="reason-details" v-if="paper.reasonDetails?.length">
      <el-tag
        v-for="(d, i) in paper.reasonDetails"
        :key="i"
        size="small"
        type="success"
        class="detail-tag"
      >{{ d }}</el-tag>
    </div>

    <div class="card-footer">
      <div class="meta">
        <span v-if="paper.citationCount !== undefined">
          <el-icon><Star /></el-icon> {{ paper.citationCount }} 引用
        </span>
        <span v-if="paper.score !== undefined">
          推荐分: <b>{{ (paper.score * 100).toFixed(0) }}</b>
        </span>
      </div>
      <div class="actions">
        <el-button size="small" @click="handleClick">阅读</el-button>
        <el-button size="small" type="warning" @click="handleFavorite">收藏</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { InfoFilled, Star } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { recordClick, recordFavorite } from '@/api/recommend'

const props = defineProps({
  paper: { type: Object, required: true },
  source: { type: String, default: 'recommend' },
})
const router = useRouter()

function formatAuthors(authors) {
  if (Array.isArray(authors)) return authors.slice(0, 3).join(', ')
  try { return JSON.parse(authors).slice(0, 3).join(', ') } catch { return authors }
}

function getPaperId() {
  return props.paper.paperId || props.paper.id
}

async function handleClick() {
  const paperId = getPaperId()
  if (!paperId) return

  try {
    await recordClick(paperId, props.source)
    ElMessage.success('已记录阅读行为')
  } catch {}

  router.push(`/paper/${paperId}`)
}

async function handleFavorite() {
  const paperId = getPaperId()
  if (!paperId) return

  try {
    await recordFavorite(paperId, props.source)
    ElMessage.success('收藏成功')
  } catch {}
}
</script>

<style scoped>
.paper-card {
  background: #1c2128;
  border: 1px solid #30363d;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 16px;
  transition: border-color 0.2s;
}
.paper-card:hover { border-color: #58a6ff; }
.card-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
.title { color: #e6edf3; font-size: 15px; margin: 0 0 8px; line-height: 1.5; }
.authors { color: #8b949e; font-size: 13px; margin: 4px 0; }
.venue { color: #58a6ff; font-size: 12px; margin: 2px 0 8px; }
.abstract {
  color: #8b949e; font-size: 13px; line-height: 1.6;
  display: -webkit-box; -webkit-line-clamp: 3;
  -webkit-box-orient: vertical; overflow: hidden;
  margin-bottom: 12px;
}
.reason {
  display: flex; align-items: center; gap: 6px;
  color: #3fb950; font-size: 13px; margin-bottom: 8px;
}
.reason-details { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px; }
.detail-tag { font-size: 11px; }
.card-footer { display: flex; align-items: center; justify-content: space-between; }
.meta { display: flex; gap: 16px; color: #8b949e; font-size: 12px; align-items: center; }
.meta b { color: #58a6ff; }
.actions { display: flex; gap: 8px; }
</style>
