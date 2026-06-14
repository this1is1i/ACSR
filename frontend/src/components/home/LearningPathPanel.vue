<template>
  <section class="learning-path-panel card" data-testid="learning-path-panel" data-area="learning">
    <div class="panel-header">
      <div>
        <p class="panel-header__eyebrow">Learning Path</p>
        <h2>学习路径</h2>
      </div>
    </div>

    <template v-if="loading">
      <el-skeleton :rows="8" animated />
    </template>

    <template v-else>
      <!-- 空状态：未选择学习目标 -->
      <div v-if="!currentTargetTopic" class="path-empty-state">
        <p class="path-empty-state__icon">🎯</p>
        <strong>请选择要学习的目标</strong>
        <p class="path-empty-state__hint">
          前往<router-link to="/knowledge-graph">知识图谱页面</router-link>，在「切换目标专题」中选择一个研究方向
        </p>
      </div>

      <template v-else>
        <div class="path-overview">
          <div class="path-overview__topic">
            <span class="path-overview__label">当前主题</span>
            <h3>{{ summary.topic }}</h3>
            <p>{{ summary.isComplete ? '当前路径已完成' : (summary.nextStep ? `下一节点：${summary.nextStep.name}` : '继续浏览论文以生成下一节点') }}</p>
          </div>

          <div class="path-overview__progress">
            <div class="path-overview__progress-copy">
              <span>路径完成度</span>
              <strong>{{ summary.completionPercent }}%</strong>
            </div>
            <el-progress :percentage="summary.completionPercent" :show-text="false" :stroke-width="10" />
          </div>
        </div>

        <div class="path-metrics">
          <article class="path-metric">
            <span>基础掌握</span>
            <strong>{{ summary.masteredFoundations }}/{{ summary.foundationCount || 0 }}</strong>
            <small>已掌握的基础节点</small>
          </article>
          <article class="path-metric">
            <span>预计投入</span>
            <strong>{{ summary.estimatedHoursLabel }}</strong>
            <small>完成当前路径所需时间</small>
          </article>
          <article class="path-metric">
            <span>关键论文</span>
            <strong>{{ summary.paperCount }}</strong>
            <small>沿主线串联的必读论文</small>
          </article>
        </div>

        <div class="path-next-step">
          <span>下一节点</span>
          <strong>{{ summary.isComplete ? '当前路径已完成' : (summary.nextStep?.name || '继续完善兴趣画像') }}</strong>
          <small>{{ summary.nextStepCaption }}</small>
        </div>

        <ol class="path-route">
          <li
            v-for="step in summary.steps.slice(0, 6)"
            :key="step.id"
            class="path-route__item"
            :class="`path-route__item--${step.status}`"
          >
            <span class="path-route__index">{{ step.index }}</span>
            <div class="path-route__copy">
              <strong>{{ step.name }}</strong>
              <small>{{ getPathStepMeta(step) }}</small>
            </div>
            <span class="path-route__mastery">{{ formatMastery(step.mastery) }}</span>
          </li>
        </ol>

        <div v-if="summary.resourcePapers.length" class="path-papers">
          <h3>路径关键论文</h3>
          <div v-for="paper in summary.resourcePapers.slice(0, 2)" :key="paper.id" class="path-paper">
            <strong>{{ paper.name }}</strong>
            <small>{{ getPathStepMeta(paper) }}</small>
          </div>
        </div>
      </template>
    </template>
  </section>
</template>

<script setup>
import { formatMastery, getPathStepMeta } from '@/utils/path'

defineProps({
  loading: {
    type: Boolean,
    default: false,
  },
  summary: {
    type: Object,
    default: () => ({
      topic: '个性化学习路径',
      completionPercent: 0,
      masteredFoundations: 0,
      foundationCount: 0,
      estimatedHoursLabel: '待估算',
      paperCount: 0,
      isComplete: false,
      nextStepCaption: '',
      steps: [],
      resourcePapers: [],
    }),
  },
  currentTargetTopic: {
    type: String,
    default: '',
  },
})
</script>

<style scoped>
.learning-path-panel {
  display: grid;
  gap: var(--space-4);
  padding: clamp(1.35rem, 2vw, 1.8rem);
}

.learning-path-panel[data-area="learning"] {
  border-left: 3px solid var(--color-area-learning);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-4);
}

.panel-header__eyebrow {
  margin-bottom: var(--space-2);
  font-size: 0.78rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--color-accent-secondary);
}

.path-overview {
  display: grid;
  gap: var(--space-4);
  padding: var(--space-4);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.03);
}

.path-overview__label {
  display: inline-flex;
  margin-bottom: var(--space-2);
  padding: 0.3rem 0.65rem;
  border-radius: 999px;
  background: rgba(55, 213, 255, 0.1);
  color: var(--color-accent-secondary);
}

.path-overview__progress-copy,
.path-next-step,
.path-metric,
.path-paper {
  display: grid;
  gap: var(--space-2);
}

.path-overview__progress-copy strong,
.path-next-step strong,
.path-metric strong {
  color: var(--color-text-primary);
}

.path-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-3);
}

.path-metric {
  padding: var(--space-4);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.03);
}

.path-next-step {
  padding: var(--space-4);
  border: 1px solid rgba(55, 213, 255, 0.18);
  border-radius: var(--radius-lg);
  background: linear-gradient(135deg, rgba(124, 140, 255, 0.12), rgba(55, 213, 255, 0.04));
}

.path-route {
  display: grid;
  gap: var(--space-3);
  margin: 0;
  padding: 0;
  list-style: none;
}

.path-route__item {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.03);
}

.path-route__item--mastered {
  border-color: rgba(52, 211, 153, 0.28);
}

.path-route__item--active {
  border-color: rgba(124, 140, 255, 0.34);
}

.path-route__item--up-next {
  border-color: rgba(251, 191, 36, 0.28);
}

.path-route__index {
  width: 2rem;
  height: 2rem;
  display: grid;
  place-items: center;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  color: var(--color-text-primary);
}

.path-route__copy {
  min-width: 0;
  display: grid;
  gap: 0.2rem;
}

.path-route__copy strong,
.path-paper strong {
  color: var(--color-text-primary);
}

.path-route__mastery {
  color: var(--color-accent-secondary);
  font-weight: 600;
}

.path-papers {
  display: grid;
  gap: var(--space-3);
}

.path-paper {
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.03);
}

.path-empty-state {
  display: grid;
  gap: var(--space-3);
  justify-items: center;
  text-align: center;
  padding: var(--space-8) var(--space-4);
}

.path-empty-state__icon {
  font-size: 2rem;
  margin: 0;
}

.path-empty-state strong {
  font-size: 1.1rem;
  color: var(--color-text-primary);
}

.path-empty-state__hint {
  color: var(--color-text-muted);
  font-size: 0.85rem;
  line-height: 1.5;
  max-width: 24ch;
}

.path-empty-state__hint a {
  color: var(--color-accent-secondary);
  text-decoration: underline;
}

@media (max-width: 960px) {
  .panel-header {
    flex-direction: column;
  }

  .path-metrics {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .path-route__item {
    grid-template-columns: auto 1fr;
  }

  .path-route__mastery {
    grid-column: 2;
  }
}
</style>
