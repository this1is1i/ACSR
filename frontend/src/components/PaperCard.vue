<template>
  <article class="paper-card" :class="`paper-card--${variant}`">
    <div class="paper-card__header">
      <div class="paper-card__title-group">
        <span class="paper-card__eyebrow">Personalized Pick</span>
        <h3 class="title">{{ paper.title }}</h3>
      </div>

      <div class="paper-card__meta-tags">
        <el-tag size="small" effect="dark" class="meta-tag" v-if="paper.year">{{ paper.year }}</el-tag>
        <el-tag size="small" type="info" class="meta-tag" v-if="paper.venue">{{ paper.venue }}</el-tag>
      </div>
    </div>

    <p class="authors" v-if="paper.authors">
      {{ formatAuthors(paper.authors) }}
    </p>

    <p class="abstract" v-if="paper.abstrakt || paper.abstract">
      {{ paper.abstrakt || paper.abstract }}
    </p>

    <div class="reason" v-if="paper.reason">
      <el-icon><InfoFilled /></el-icon>
      <span>{{ paper.reason }}</span>
    </div>

    <div class="reason-details" v-if="displayTags.length">
      <el-tag
        v-for="(tag, index) in displayTags"
        :key="`${tag}-${index}`"
        size="small"
        class="detail-tag"
      >{{ tag }}</el-tag>
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
        <el-button size="small" type="warning" plain @click="handleFavorite">收藏</el-button>
      </div>
    </div>
  </article>
</template>

<script setup>
import { computed } from 'vue'
import { InfoFilled, Star } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { recordClick, recordFavorite } from '@/api/recommend'

const props = defineProps({
  paper: { type: Object, required: true },
  source: { type: String, default: 'recommend' },
  variant: { type: String, default: 'default' },
})
const router = useRouter()

function formatAuthors(authors) {
  if (Array.isArray(authors)) return authors.slice(0, 3).join(', ')
  try { return JSON.parse(authors).slice(0, 3).join(', ') } catch { return authors }
}

function parseList(value) {
  if (Array.isArray(value)) return value
  if (!value) return []

  try {
    return JSON.parse(value)
  } catch {
    return String(value)
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean)
  }
}

function getPaperId() {
  return props.paper.paperId || props.paper.id
}

const displayTags = computed(() => {
  const reasonDetails = Array.isArray(props.paper.reasonDetails) ? props.paper.reasonDetails : []
  if (reasonDetails.length) return reasonDetails.slice(0, 3)
  return parseList(props.paper.keywords).slice(0, 3)
})

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
  position: relative;
  display: grid;
  gap: var(--space-3);
  padding: clamp(1.2rem, 2vw, 1.5rem);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-xl);
  background:
    linear-gradient(180deg, rgba(124, 140, 255, 0.08), transparent 75%),
    rgba(255, 255, 255, 0.03);
  box-shadow: var(--shadow-card);
  transition: transform 0.18s ease, border-color 0.18s ease;
}

.paper-card:hover {
  transform: translateY(-2px);
  border-color: var(--color-border-strong);
}

.paper-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
}

.paper-card__title-group {
  display: grid;
  gap: var(--space-2);
}

.paper-card__eyebrow {
  font-size: 0.72rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--color-accent-secondary);
}

.paper-card__meta-tags {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: var(--space-2);
}

.title {
  color: var(--color-text-primary);
  font-size: 1.02rem;
  line-height: 1.5;
}

.authors {
  color: var(--color-text-secondary);
  font-size: 0.92rem;
}

.abstract {
  color: var(--color-text-secondary);
  font-size: 0.92rem;
  line-height: 1.7;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.reason {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  color: #8bf0c5;
  font-size: 0.9rem;
}

.reason-details {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.detail-tag,
.meta-tag {
  border-color: rgba(124, 140, 255, 0.22);
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

.meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-4);
  color: var(--color-text-secondary);
  font-size: 0.82rem;
  align-items: center;
}

.meta b {
  color: var(--color-accent-secondary);
}

.actions {
  display: flex;
  gap: var(--space-2);
}

@media (max-width: 640px) {
  .paper-card__header,
  .card-footer {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
