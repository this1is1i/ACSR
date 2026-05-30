<template>
  <aside class="path-insight-rail" data-testid="path-insight-rail">
    <template v-if="loading">
      <section class="path-insight-rail__card path-insight-rail__card--loading">
        <el-skeleton :rows="10" animated />
      </section>
    </template>

    <div v-else class="path-insight-rail__grid" data-testid="path-insight-grid">
      <section
        class="path-insight-rail__card path-insight-rail__card--spotlight"
        data-testid="path-insight-card-spotlight"
      >
        <div class="path-insight-rail__header">
          <div>
            <p class="path-insight-rail__eyebrow">Path Immersion</p>
            <h2>学习路径洞察</h2>
            <p>{{ summary.headline }}</p>
          </div>
        </div>

        <div class="path-insight-rail__spotlight">
          <section class="path-insight-rail__spotlight-main">
            <span class="path-insight-rail__label">当前主线</span>
            <strong>{{ summary.topic }}</strong>
            <p>{{ summary.nextStepCaption }}</p>
          </section>

          <div class="path-insight-rail__highlight-stack">
            <article class="path-insight-rail__highlight">
              <span>当前聚焦</span>
              <strong>{{ activeNodeLabel }}</strong>
              <small>{{ activeNodeMeta }}</small>
            </article>
            <article class="path-insight-rail__highlight">
              <span>路径锚点</span>
              <strong>{{ summary.paperCount }}</strong>
              <small>{{ summary.paperCount ? '篇关键论文已纳入本轮路径' : '等待关键论文加入路径' }}</small>
            </article>
          </div>
        </div>
      </section>

      <section
        class="path-insight-rail__card path-insight-rail__card--focus"
        data-testid="path-insight-card-focus"
      >
        <div class="path-insight-rail__section-head">
          <div>
            <p class="path-insight-rail__section-eyebrow">Path Progress</p>
            <h3>推进节奏</h3>
          </div>
        </div>

        <div class="path-insight-rail__metrics">
          <article class="path-insight-rail__metric">
            <span>完成度</span>
            <strong>{{ summary.completionPercent }}%</strong>
            <small>路径覆盖率</small>
          </article>
          <article class="path-insight-rail__metric">
            <span>预估投入</span>
            <strong>{{ summary.estimatedHours || '—' }}</strong>
            <small>{{ summary.estimatedHoursLabel }}</small>
          </article>
          <article class="path-insight-rail__metric">
            <span>基础铺垫</span>
            <strong>{{ summary.masteredFoundations }}/{{ summary.foundationCount }}</strong>
            <small>已完成基础节点</small>
          </article>
        </div>

        <div v-if="summary.focusAreas.length" class="path-insight-rail__section">
          <h4>聚焦主题</h4>
          <div class="path-insight-rail__chips">
            <span v-for="step in summary.focusAreas" :key="step.id" class="path-insight-rail__chip">
              {{ step.name }}
            </span>
          </div>
        </div>
      </section>

      <section
        class="path-insight-rail__card path-insight-rail__card--resources"
        data-testid="path-insight-card-resources"
      >
        <div class="path-insight-rail__section-head">
          <div>
            <p class="path-insight-rail__section-eyebrow">Resource Stack</p>
            <h3>关键资源</h3>
          </div>
        </div>

        <div class="path-insight-rail__resource-columns">
          <section v-if="summary.resourcePapers.length" class="path-insight-rail__section">
            <h4>路径关键论文</h4>
            <div class="path-insight-rail__stack">
              <article
                v-for="paper in summary.resourcePapers.slice(0, 3)"
                :key="paper.id"
                class="path-insight-rail__item path-insight-rail__item--clickable"
                @click="goToPaper(paper.id)"
              >
                <strong>{{ paper.name }}</strong>
                <small>{{ getPathStepMeta(paper) }}</small>
              </article>
            </div>
          </section>

          <section v-if="recommendations.length" class="path-insight-rail__section">
            <h4>关联推荐资产</h4>
            <div class="path-insight-rail__stack">
              <article
                v-for="paper in recommendations.slice(0, 2)"
                :key="paper.paperId || paper.id"
                class="path-insight-rail__item path-insight-rail__item--clickable"
                @click="goToPaper(paper.paperId || paper.id)"
              >
                <strong>{{ paper.title }}</strong>
                <small>{{ paper.reason || recommendationMeta(paper) }}</small>
              </article>
            </div>
          </section>
        </div>
      </section>

      <section
        class="path-insight-rail__card path-insight-rail__card--topics"
        data-testid="path-insight-card-topics"
      >
        <div class="path-insight-rail__section-head">
          <div>
            <p class="path-insight-rail__section-eyebrow">Topic Switcher</p>
            <h3>切换目标专题</h3>
          </div>
        </div>

        <template v-if="keywordsLoading">
          <el-skeleton :rows="4" animated />
        </template>

        <template v-else-if="keywords.length === 0">
          <p class="path-insight-rail__empty">暂无可用专题，系统将使用默认学习路径。</p>
        </template>

        <template v-else>
          <input
            v-model="filterQuery"
            class="path-insight-rail__topic-search"
            type="text"
            placeholder="搜索专题关键词..."
          />
          <div class="path-insight-rail__topic-chips">
            <button
              v-for="kw in filteredKeywords"
              :key="kw.label"
              class="path-insight-rail__topic-chip"
              :class="{ 'path-insight-rail__topic-chip--active': currentTargetTopic === kw.label }"
              :disabled="loading"
              @click="emit('select-topic', kw.label)"
            >
              <span class="path-insight-rail__topic-label">{{ kw.label }}</span>
              <span class="path-insight-rail__topic-freq">{{ kw.frequency }}</span>
            </button>
            <p v-if="filteredKeywords.length === 0" class="path-insight-rail__empty">
              未找到匹配的专题
            </p>
          </div>
        </template>
      </section>
    </div>
  </aside>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { formatMastery, getPathStepMeta } from '@/utils/path'

const router = useRouter()

function goToPaper(id) {
  if (!id) return
  if (typeof id === 'string' && !/^\d+$/.test(id)) {
    router.push(`/paper/aminer/${id}`)
  } else {
    router.push(`/paper/${id}`)
  }
}

const filterQuery = ref('')

const filteredKeywords = computed(() => {
  if (!filterQuery.value.trim()) return props.keywords
  const q = filterQuery.value.trim().toLowerCase()
  return props.keywords.filter(kw => kw.label.toLowerCase().includes(q))
})

const emit = defineEmits(['select-topic'])

const props = defineProps({
  loading: {
    type: Boolean,
    default: false,
  },
  keywords: {
    type: Array,
    default: () => [],
  },
  keywordsLoading: {
    type: Boolean,
    default: false,
  },
  currentTargetTopic: {
    type: String,
    default: '',
  },
  summary: {
    type: Object,
    default: () => ({
      topic: '个性化学习路径',
      headline: '根据推荐结果继续推进你的研究主线',
      completionPercent: 0,
      estimatedHoursLabel: '待估算',
      nextStepCaption: '',
      steps: [],
      focusAreas: [],
      resourcePapers: [],
      nextStep: null,
      isComplete: false,
      paperCount: 0,
      foundationCount: 0,
      masteredFoundations: 0,
    }),
  },
  recommendations: {
    type: Array,
    default: () => [],
  },
  activeNode: {
    type: Object,
    default: null,
  },
})

const activeNodeLabel = computed(() => (
  props.activeNode?.name
    || (props.summary.isComplete ? '当前路径已完成' : props.summary.nextStep?.name)
    || '等待路径生成'
))

const activeNodeMeta = computed(() => (
  props.activeNode
    ? getPathStepMeta(props.activeNode)
    : props.summary.nextStepCaption
))

function recommendationMeta(paper) {
  const parts = [paper.venue, paper.year].filter(Boolean)
  return parts.join(' · ') || '推荐资产'
}
</script>

<style scoped>
.path-insight-rail {
  align-self: start;
}

.path-insight-rail__grid {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: var(--space-4);
}

.path-insight-rail__card {
  display: grid;
  gap: var(--space-4);
  padding: clamp(1.25rem, 1.9vw, 1.7rem);
  border: 1px solid var(--design-border);
  border-radius: calc(var(--radius-lg) + 0.2rem);
  background: var(--bg-card);
  box-shadow: var(--shadow-card);
}

.path-insight-rail__card--loading,
.path-insight-rail__card--spotlight {
  grid-column: span 7;
}

.path-insight-rail__card--focus,
.path-insight-rail__card--topics {
  grid-column: span 5;
}

.path-insight-rail__card--resources {
  grid-column: span 7;
}

.path-insight-rail__header,
.path-insight-rail__section-head,
.path-insight-rail__section,
.path-insight-rail__metric,
.path-insight-rail__item,
.path-insight-rail__highlight {
  display: grid;
  gap: var(--space-2);
}

.path-insight-rail__eyebrow {
  margin-bottom: var(--space-2);
  font-size: 0.78rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--color-accent-secondary);
}

.path-insight-rail__section-eyebrow {
  font-size: 0.74rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.path-insight-rail__header h2,
.path-insight-rail__section-head h3,
.path-insight-rail__section h4 {
  color: var(--color-text-primary);
}

.path-insight-rail__section-head p,
.path-insight-rail__header p {
  color: var(--color-text-secondary);
}

.path-insight-rail__label {
  display: inline-flex;
  width: fit-content;
  padding: 0.32rem 0.72rem;
  border-radius: 999px;
  background: rgba(55, 213, 255, 0.12);
  color: var(--color-accent-secondary);
}

.path-insight-rail__spotlight {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(0, 0.95fr);
  gap: var(--space-3);
}

.path-insight-rail__spotlight-main,
.path-insight-rail__highlight {
  display: grid;
  gap: var(--space-3);
  padding: var(--space-4);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-lg);
  background: var(--bg-hover);
}

.path-insight-rail__spotlight-main strong {
  font-size: clamp(1.35rem, 2vw, 1.8rem);
}

.path-insight-rail__highlight-stack {
  display: grid;
  gap: var(--space-3);
}

.path-insight-rail__spotlight-main strong,
.path-insight-rail__highlight strong,
.path-insight-rail__metric strong,
.path-insight-rail__item strong,
.path-insight-rail__route-item strong {
  color: var(--color-text-primary);
}

.path-insight-rail__metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-3);
}

.path-insight-rail__metric,
.path-insight-rail__item {
  padding: var(--space-4);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  background: var(--bg-hover);
}

.path-insight-rail__chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.path-insight-rail__chip {
  padding: 0.5rem 0.82rem;
  border-radius: 999px;
  border: 1px solid rgba(124, 140, 255, 0.22);
  background: rgba(124, 140, 255, 0.12);
  color: var(--color-text-primary);
}

.path-insight-rail__stack,
.path-insight-rail__route,
.path-insight-rail__resource-columns {
  display: grid;
  gap: var(--space-3);
}

.path-insight-rail__resource-columns {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-4);
}

.path-insight-rail__route {
  margin: 0;
  padding: 0;
  list-style: none;
}

.path-insight-rail__item--clickable {
  cursor: pointer;
  transition: transform 0.16s ease, border-color 0.16s ease;
}

.path-insight-rail__item--clickable:hover {
  transform: translateX(2px);
  border-color: var(--color-border-strong);
}

/* ── Topic switcher card ───────────────────────────────────── */

.path-insight-rail__topic-search {
  width: 100%;
  padding: 0.45rem 0.7rem;
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-md);
  background: var(--bg-hover);
  color: var(--color-text-primary);
  font-size: 0.82rem;
  font-family: inherit;
  outline: none;
  transition: border-color 0.2s ease;
  margin-bottom: var(--space-3);
  box-sizing: border-box;
}

.path-insight-rail__topic-search:focus {
  border-color: rgba(124, 140, 255, 0.5);
}

.path-insight-rail__topic-search::placeholder {
  color: var(--color-text-muted);
}

.path-insight-rail__topic-chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  max-height: 200px;
  overflow-y: auto;
  align-content: flex-start;
  padding-right: 2px;
}

.path-insight-rail__topic-chip {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: 0.45rem 0.75rem;
  border-radius: 999px;
  border: 1px solid rgba(124, 140, 255, 0.22);
  background: rgba(124, 140, 255, 0.08);
  color: var(--color-text-primary);
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.85rem;
  font-family: inherit;
}

.path-insight-rail__topic-chip:hover:not(:disabled) {
  background: rgba(124, 140, 255, 0.2);
  border-color: rgba(124, 140, 255, 0.5);
  transform: translateY(-1px);
}

.path-insight-rail__topic-chip--active {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.3), rgba(139, 92, 246, 0.3));
  border-color: rgba(99, 102, 241, 0.6);
  color: #e2e8f0;
}

.path-insight-rail__topic-chip:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.path-insight-rail__topic-label {
  font-weight: 500;
}

.path-insight-rail__topic-freq {
  font-size: 0.72rem;
  padding: 0.1rem 0.4rem;
  border-radius: 8px;
  background: rgba(148, 163, 184, 0.15);
  color: var(--color-text-muted);
}

.path-insight-rail__topic-chips::-webkit-scrollbar {
  width: 4px;
}

.path-insight-rail__topic-chips::-webkit-scrollbar-thumb {
  border-radius: 4px;
  background: rgba(148, 163, 184, 0.25);
}

.path-insight-rail__empty {
  font-size: 0.82rem;
  color: var(--color-text-muted);
  text-align: center;
  padding: var(--space-4) 0;
  width: 100%;
}

.path-insight-rail__route-item {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: var(--space-3);
  align-items: center;
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  background: var(--bg-hover);
}

.path-insight-rail__index {
  width: 2rem;
  height: 2rem;
  display: grid;
  place-items: center;
  border-radius: 999px;
  background: var(--bg-hover);
  color: var(--color-text-primary);
}

@media (max-width: 1280px) {
  .path-insight-rail__card--loading,
  .path-insight-rail__card--spotlight,
  .path-insight-rail__card--focus,
  .path-insight-rail__card--resources,
  .path-insight-rail__card--topics {
    grid-column: span 12;
  }

  .path-insight-rail__spotlight,
  .path-insight-rail__metrics {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .path-insight-rail__resource-columns {
    grid-template-columns: 1fr;
  }
}
</style>
