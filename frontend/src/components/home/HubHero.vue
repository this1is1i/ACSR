<template>
  <section class="hub-hero card glass" data-testid="home-hub-hero">
    <div class="hub-hero__content">
      <div class="hub-hero__copy">
        <p class="hub-hero__eyebrow">Research Hub</p>
        <h1 class="hub-hero__title">欢迎回来，{{ userName }}</h1>
        <p class="hub-hero__headline">{{ pathSummary.headline }}</p>
        <p class="hub-hero__description">
          个性化推荐与学习路径同步刷新，帮助你从下一篇论文直接衔接到下一步研究节点。
        </p>

        <div v-if="pathSummary.focusAreas.length" class="hub-hero__chips">
          <span v-for="area in pathSummary.focusAreas" :key="area.id" class="hub-hero__chip">
            {{ area.name }}
          </span>
        </div>
      </div>

      <div class="hub-hero__actions">
        <button class="btn" type="button" @click="$emit('explore')">继续探索</button>
        <button class="btn secondary" type="button" @click="$emit('viewPath')">查看学习路径</button>
      </div>
    </div>

    <div class="hub-hero__metrics">
      <template v-if="loading">
        <el-skeleton :rows="4" animated />
      </template>
      <template v-else>
        <article v-for="metric in metrics" :key="metric.label" class="hub-hero__metric">
          <span>{{ metric.label }}</span>
          <strong>{{ metric.value }}</strong>
          <small>{{ metric.caption }}</small>
        </article>
      </template>
    </div>
  </section>
</template>

<script setup>
defineEmits(['explore', 'viewPath'])

defineProps({
  userName: {
    type: String,
    default: '研究者',
  },
  loading: {
    type: Boolean,
    default: false,
  },
  metrics: {
    type: Array,
    default: () => [],
  },
  pathSummary: {
    type: Object,
    default: () => ({
      headline: '根据推荐结果继续推进你的研究主线',
      focusAreas: [],
    }),
  },
})
</script>

<style scoped>
.hub-hero {
  display: grid;
  gap: var(--space-6);
  padding: clamp(1.5rem, 2.8vw, 2.5rem);
  background:
    radial-gradient(circle at top right, rgba(55, 213, 255, 0.16), transparent 28%),
    linear-gradient(145deg, rgba(124, 140, 255, 0.16), rgba(7, 17, 31, 0.12)),
    var(--color-bg-panel);
}

.hub-hero__content {
  display: flex;
  justify-content: space-between;
  gap: var(--space-6);
}

.hub-hero__copy {
  display: grid;
  gap: var(--space-3);
  max-width: 46rem;
}

.hub-hero__eyebrow {
  font-size: 0.78rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--color-accent-secondary);
}

.hub-hero__title {
  font-size: clamp(2rem, 3vw, 3rem);
}

.hub-hero__headline {
  font-size: 1.05rem;
  line-height: 1.7;
  color: var(--color-text-primary);
}

.hub-hero__description {
  max-width: 42rem;
  line-height: 1.7;
}

.hub-hero__chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.hub-hero__chip {
  padding: 0.45rem 0.8rem;
  border: 1px solid var(--color-border-subtle);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.04);
  color: var(--color-text-primary);
}

.hub-hero__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  align-items: flex-start;
  gap: var(--space-3);
}

.hub-hero__metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--space-4);
}

.hub-hero__metric {
  display: grid;
  gap: var(--space-2);
  padding: var(--space-4);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.04);
}

.hub-hero__metric span,
.hub-hero__metric small {
  color: var(--color-text-secondary);
}

.hub-hero__metric strong {
  font-size: 1.55rem;
  color: var(--color-text-primary);
}

@media (max-width: 1120px) {
  .hub-hero__content {
    flex-direction: column;
  }

  .hub-hero__actions {
    justify-content: flex-start;
  }

  .hub-hero__metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 680px) {
  .hub-hero__metrics {
    grid-template-columns: 1fr;
  }
}
</style>
