<template>
  <aside class="path-insight-rail card glass" data-testid="path-insight-rail">
    <div class="path-insight-rail__header">
      <div>
        <p class="path-insight-rail__eyebrow">Path Immersion</p>
        <h2>学习路径洞察</h2>
        <p>{{ summary.headline }}</p>
      </div>
    </div>

    <template v-if="loading">
      <el-skeleton :rows="10" animated />
    </template>

    <template v-else>
      <section class="path-insight-rail__spotlight">
        <span class="path-insight-rail__label">当前主线</span>
        <strong>{{ summary.topic }}</strong>
        <p>{{ summary.nextStepCaption }}</p>
      </section>

      <div class="path-insight-rail__metrics">
        <article class="path-insight-rail__metric">
          <span>完成度</span>
          <strong>{{ summary.completionPercent }}%</strong>
          <small>{{ summary.estimatedHoursLabel }}</small>
        </article>
        <article class="path-insight-rail__metric">
          <span>当前聚焦</span>
          <strong>{{ activeNodeLabel }}</strong>
          <small>{{ activeNodeMeta }}</small>
        </article>
      </div>

      <section v-if="summary.focusAreas.length" class="path-insight-rail__section">
        <h3>聚焦主题</h3>
        <div class="path-insight-rail__chips">
          <span v-for="step in summary.focusAreas" :key="step.id" class="path-insight-rail__chip">
            {{ step.name }}
          </span>
        </div>
      </section>

      <section v-if="summary.resourcePapers.length" class="path-insight-rail__section">
        <h3>路径关键论文</h3>
        <div class="path-insight-rail__stack">
          <article
            v-for="paper in summary.resourcePapers.slice(0, 3)"
            :key="paper.id"
            class="path-insight-rail__item"
          >
            <strong>{{ paper.name }}</strong>
            <small>{{ getPathStepMeta(paper) }}</small>
          </article>
        </div>
      </section>

      <section v-if="recommendations.length" class="path-insight-rail__section">
        <h3>关联推荐资产</h3>
        <div class="path-insight-rail__stack">
          <article
            v-for="paper in recommendations.slice(0, 2)"
            :key="paper.paperId || paper.id"
            class="path-insight-rail__item"
          >
            <strong>{{ paper.title }}</strong>
            <small>{{ paper.reason || recommendationMeta(paper) }}</small>
          </article>
        </div>
      </section>

      <section v-if="summary.steps.length" class="path-insight-rail__section">
        <h3>路径检查点</h3>
        <ol class="path-insight-rail__route">
          <li v-for="step in summary.steps.slice(0, 4)" :key="step.id" class="path-insight-rail__route-item">
            <span class="path-insight-rail__index">{{ step.index }}</span>
            <div>
              <strong>{{ step.name }}</strong>
              <small>{{ formatMastery(step.mastery) }}</small>
            </div>
          </li>
        </ol>
      </section>
    </template>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { formatMastery, getPathStepMeta } from '@/utils/path'

const props = defineProps({
  loading: {
    type: Boolean,
    default: false,
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
  position: sticky;
  top: var(--space-7);
  display: grid;
  gap: var(--space-4);
  align-self: start;
  padding: clamp(1.35rem, 2vw, 1.8rem);
}

.path-insight-rail__header,
.path-insight-rail__section,
.path-insight-rail__spotlight,
.path-insight-rail__metric,
.path-insight-rail__item {
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

.path-insight-rail__label {
  display: inline-flex;
  width: fit-content;
  padding: 0.32rem 0.72rem;
  border-radius: 999px;
  background: rgba(55, 213, 255, 0.12);
  color: var(--color-accent-secondary);
}

.path-insight-rail__spotlight {
  padding: var(--space-4);
  border: 1px solid rgba(124, 140, 255, 0.22);
  border-radius: var(--radius-lg);
  background:
    linear-gradient(135deg, rgba(124, 140, 255, 0.14), rgba(55, 213, 255, 0.06)),
    rgba(255, 255, 255, 0.03);
}

.path-insight-rail__spotlight strong,
.path-insight-rail__metric strong,
.path-insight-rail__item strong,
.path-insight-rail__route-item strong {
  color: var(--color-text-primary);
}

.path-insight-rail__metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-3);
}

.path-insight-rail__metric,
.path-insight-rail__item {
  padding: var(--space-4);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.03);
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
.path-insight-rail__route {
  display: grid;
  gap: var(--space-3);
}

.path-insight-rail__route {
  margin: 0;
  padding: 0;
  list-style: none;
}

.path-insight-rail__route-item {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: var(--space-3);
  align-items: center;
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.03);
}

.path-insight-rail__index {
  width: 2rem;
  height: 2rem;
  display: grid;
  place-items: center;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  color: var(--color-text-primary);
}

@media (max-width: 1200px) {
  .path-insight-rail {
    position: static;
  }
}

@media (max-width: 640px) {
  .path-insight-rail__metrics {
    grid-template-columns: 1fr;
  }
}
</style>
