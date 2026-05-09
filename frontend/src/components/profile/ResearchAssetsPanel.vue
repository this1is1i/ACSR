<template>
  <article class="research-assets-panel card glass animate-fade-up" data-testid="research-assets-panel" data-area="profile">
    <div class="research-assets-panel__header">
      <div>
        <p class="research-assets-panel__eyebrow">Research Assets</p>
        <h3>研究资产总览</h3>
        <p>把推荐流、学习路径与个人画像放在同一张研究工作台里。</p>
      </div>
      <button class="btn secondary" type="button" @click="$emit('viewPath')">查看路径</button>
    </div>

    <template v-if="loading">
      <el-skeleton :rows="10" animated />
    </template>

    <template v-else>
      <section class="research-assets-panel__hero">
        <div class="research-assets-panel__identity">
          <span class="research-assets-panel__label">研究主线</span>
          <strong>{{ summary.topic }}</strong>
          <p>{{ profile.username || '研究者' }} 正沿着这条路径推进当前主题。</p>
        </div>
        <div class="research-assets-panel__metrics">
          <article class="research-assets-panel__metric">
            <span>路径完成度</span>
            <strong>{{ summary.completionPercent }}%</strong>
            <small>{{ summary.estimatedHoursLabel }}</small>
          </article>
          <article class="research-assets-panel__metric">
            <span>下一节点</span>
            <strong>{{ summary.isComplete ? '当前路径已完成' : (summary.nextStep?.name || '待生成') }}</strong>
            <small>{{ summary.nextStepCaption }}</small>
          </article>
          <article class="research-assets-panel__metric">
            <span>推荐资产</span>
            <strong>{{ recommendations.length }} 篇</strong>
            <small>按当前研究主线同步刷新</small>
          </article>
        </div>
      </section>

      <div class="research-assets-panel__grid">
        <section class="research-assets-panel__section">
          <h4>学习路径检查点</h4>
          <ol class="research-assets-panel__route">
            <li
              v-for="step in summary.steps.slice(0, 4)"
              :key="step.id"
              class="research-assets-panel__route-item"
            >
              <span class="research-assets-panel__index">{{ step.index }}</span>
              <div>
                <strong>{{ step.name }}</strong>
                <small>{{ formatMastery(step.mastery) }}</small>
              </div>
            </li>
          </ol>
        </section>

        <section class="research-assets-panel__section">
          <h4>推荐资产</h4>
          <div class="research-assets-panel__stack">
            <article
              v-for="paper in recommendations.slice(0, 2)"
              :key="paper.paperId || paper.id"
              class="research-assets-panel__item"
            >
              <strong>{{ paper.title }}</strong>
              <small>{{ paper.reason || recommendationMeta(paper) }}</small>
            </article>
          </div>
        </section>

        <section class="research-assets-panel__section">
          <h4>兴趣分布</h4>
          <div class="research-assets-panel__chips">
            <span
              v-for="interest in interests.slice(0, 4)"
              :key="interest.name"
              class="research-assets-panel__chip"
            >
              {{ interest.name }} · {{ interest.percent }}%
            </span>
          </div>
        </section>

        <section v-if="summary.resourcePapers.length" class="research-assets-panel__section">
          <h4>路径关键论文</h4>
          <div class="research-assets-panel__stack">
            <article
              v-for="paper in summary.resourcePapers.slice(0, 2)"
              :key="paper.id"
              class="research-assets-panel__item"
            >
              <strong>{{ paper.name }}</strong>
              <small>{{ getPathStepMeta(paper) }}</small>
            </article>
          </div>
        </section>
      </div>
    </template>
  </article>
</template>

<script setup>
import { formatMastery, getPathStepMeta } from '@/utils/path'

defineEmits(['viewPath'])

defineProps({
  loading: {
    type: Boolean,
    default: false,
  },
  profile: {
    type: Object,
    default: () => ({}),
  },
  summary: {
    type: Object,
    default: () => ({
      topic: '个性化学习路径',
      completionPercent: 0,
      estimatedHoursLabel: '待估算',
      nextStepCaption: '',
      steps: [],
      resourcePapers: [],
      nextStep: null,
      isComplete: false,
    }),
  },
  recommendations: {
    type: Array,
    default: () => [],
  },
  interests: {
    type: Array,
    default: () => [],
  },
})

function recommendationMeta(paper) {
  const parts = [paper.venue, paper.year].filter(Boolean)
  return parts.join(' · ') || '推荐资产'
}
</script>

<style scoped>
.research-assets-panel {
  grid-column: 1 / -1;
  display: grid;
  gap: var(--space-5);
  padding: clamp(1.4rem, 2vw, 1.85rem);
}

.research-assets-panel[data-area="profile"] {
  border-left: 3px solid var(--color-area-profile);
}

.research-assets-panel__header,
.research-assets-panel__hero,
.research-assets-panel__identity,
.research-assets-panel__metric,
.research-assets-panel__section,
.research-assets-panel__item {
  display: grid;
  gap: var(--space-2);
}

.research-assets-panel__header {
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: start;
  gap: var(--space-4);
}

.research-assets-panel__eyebrow {
  margin-bottom: var(--space-2);
  font-size: 0.78rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--color-accent-secondary);
}

.research-assets-panel__hero {
  padding: var(--space-5);
  border: 1px solid rgba(124, 140, 255, 0.2);
  border-radius: var(--radius-xl);
  background:
    linear-gradient(135deg, rgba(124, 140, 255, 0.12), rgba(55, 213, 255, 0.05)),
    rgba(255, 255, 255, 0.03);
}

.research-assets-panel__label {
  display: inline-flex;
  width: fit-content;
  padding: 0.34rem 0.74rem;
  border-radius: 999px;
  background: rgba(55, 213, 255, 0.12);
  color: var(--color-accent-secondary);
}

.research-assets-panel__identity strong,
.research-assets-panel__metric strong,
.research-assets-panel__item strong,
.research-assets-panel__route-item strong {
  color: var(--color-text-primary);
}

.research-assets-panel__metrics,
.research-assets-panel__grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-3);
}

.research-assets-panel__metric,
.research-assets-panel__section,
.research-assets-panel__item,
.research-assets-panel__route-item {
  padding: var(--space-4);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.03);
}

.research-assets-panel__section {
  align-content: start;
}

.research-assets-panel__section:nth-child(1) {
  grid-column: span 2;
}

.research-assets-panel__route,
.research-assets-panel__stack {
  display: grid;
  gap: var(--space-3);
}

.research-assets-panel__route {
  margin: 0;
  padding: 0;
  list-style: none;
}

.research-assets-panel__route-item {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  align-items: center;
  gap: var(--space-3);
  padding: 0.85rem 1rem;
}

.research-assets-panel__index {
  width: 2rem;
  height: 2rem;
  display: grid;
  place-items: center;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  color: var(--color-text-primary);
}

.research-assets-panel__chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.research-assets-panel__chip {
  padding: 0.5rem 0.82rem;
  border-radius: 999px;
  border: 1px solid rgba(124, 140, 255, 0.22);
  background: rgba(124, 140, 255, 0.12);
  color: var(--color-text-primary);
}

@media (max-width: 1100px) {
  .research-assets-panel__metrics,
  .research-assets-panel__grid {
    grid-template-columns: 1fr;
  }

  .research-assets-panel__section:nth-child(1) {
    grid-column: auto;
  }
}

@media (max-width: 720px) {
  .research-assets-panel__header {
    grid-template-columns: 1fr;
  }
}
</style>
