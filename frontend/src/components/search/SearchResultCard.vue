<template>
  <article class="result-card search-result-card card glass" :data-testid="`search-result-card-${paper.id}`" data-area="search">
    <div class="search-result-card__header">
      <div class="search-result-card__copy">
        <p class="search-result-card__eyebrow">Secondary Search Result</p>
        <h3 class="result-title">{{ paper.title }}</h3>
        <p class="result-authors">{{ paper.authors }} · {{ paper.venue }} · {{ paper.year }}</p>
      </div>
      <div class="search-result-card__path">
        <span>研究路径</span>
        <strong>{{ pathLabel }}</strong>
      </div>
    </div>

    <p class="result-abstract">{{ paper.abstract }}</p>

    <div class="search-result-card__context">
      <span v-if="query" class="search-result-card__chip">查询：{{ query }}</span>
      <span v-for="label in contextLabels" :key="label" class="search-result-card__chip">{{ label }}</span>
    </div>

    <div class="result-meta">
      <div class="result-tags">
        <span class="result-tag" v-for="tag in paper.tags" :key="tag">{{ tag }}</span>
      </div>
      <div class="result-stats">
        <span>📊 被引 {{ paper.citations }}</span>
        <span>⭐ 收藏 {{ paper.favorites }}</span>
        <span>📥 下载 {{ paper.downloads }}</span>
      </div>
    </div>

    <div class="result-actions">
      <button class="action-btn action-btn--primary" type="button" @click="emit('open', paper)">📖 查看详情</button>
      <button class="action-btn" type="button" @click="emit('toggle-favorite', paper)">
        💾 {{ favorited ? '已收藏' : '收藏' }}
      </button>
    </div>
  </article>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  paper: {
    type: Object,
    required: true,
  },
  query: {
    type: String,
    default: '',
  },
  activeFilters: {
    type: Array,
    default: () => [],
  },
  activeTags: {
    type: Array,
    default: () => [],
  },
  favorited: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['open', 'toggle-favorite'])

const contextLabels = computed(() => [...props.activeFilters, ...props.activeTags].slice(0, 3))
const pathLabel = computed(() => {
  if (props.query) return `围绕 ${props.query} 展开比对`
  if (props.activeTags.length) return `围绕 ${props.activeTags[0]} 延伸阅读`
  return '进入论文阅读画布'
})
</script>

<style scoped>
.search-result-card {
  display: grid;
  gap: var(--space-4);
  padding: clamp(1.2rem, 2vw, 1.6rem);
}

.search-result-card[data-area="search"] {
  border-left: 3px solid var(--color-area-search);
}

.search-result-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
}

.search-result-card__copy {
  display: grid;
  gap: var(--space-2);
}

.search-result-card__eyebrow {
  font-size: 0.74rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--color-accent-secondary);
}

.search-result-card__path {
  min-width: 11rem;
  display: grid;
  gap: var(--space-2);
  padding: var(--space-4);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.03);
}

.search-result-card__path span {
  font-size: 0.8rem;
  color: var(--color-text-muted);
}

.result-title {
  font-size: 1.2rem;
  line-height: 1.45;
}

.result-authors,
.result-abstract {
  color: var(--color-text-secondary);
  line-height: 1.75;
}

.search-result-card__context,
.result-tags,
.result-stats,
.result-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.search-result-card__chip,
.result-tag {
  padding: 0.45rem 0.75rem;
  border: 1px solid rgba(124, 140, 255, 0.22);
  border-radius: 999px;
  background: rgba(124, 140, 255, 0.12);
  color: var(--color-text-primary);
  font-size: 0.82rem;
}

.result-meta {
  display: grid;
  gap: var(--space-3);
}

.result-stats {
  color: var(--color-text-secondary);
  font-size: 0.88rem;
}

.action-btn {
  padding: 0.75rem 1rem;
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.03);
  color: var(--color-text-primary);
  cursor: pointer;
}

.action-btn--primary {
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  border-color: transparent;
  color: #fff;
}

@media (max-width: 760px) {
  .search-result-card__header {
    flex-direction: column;
  }

  .search-result-card__path {
    min-width: 0;
    width: 100%;
  }
}
</style>
