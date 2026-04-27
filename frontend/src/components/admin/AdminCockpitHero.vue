<template>
  <section class="admin-cockpit-hero card glass" data-testid="admin-cockpit-hero">
    <div class="admin-cockpit-hero__copy">
      <p class="admin-cockpit-hero__eyebrow">Admin Cockpit</p>
      <h2>控制台总览</h2>
      <p class="admin-cockpit-hero__headline">{{ headline }}</p>
      <p class="admin-cockpit-hero__description">{{ description }}</p>

      <div v-if="chips.length" class="admin-cockpit-hero__chips">
        <span v-for="chip in chips" :key="chip" class="admin-cockpit-hero__chip">
          {{ chip }}
        </span>
      </div>
    </div>

    <div class="admin-cockpit-hero__side">
      <div class="admin-cockpit-hero__signals">
        <article v-for="signal in signals" :key="signal.label" class="admin-cockpit-hero__signal">
          <span>{{ signal.label }}</span>
          <strong>{{ signal.value }}</strong>
          <small>{{ signal.caption }}</small>
        </article>
      </div>

      <div class="admin-cockpit-hero__actions">
        <button
          v-for="action in actions"
          :key="action.label"
          class="btn"
          type="button"
          @click="$emit('select-tab', action.tab)"
        >
          {{ action.label }}
        </button>
      </div>
    </div>
  </section>
</template>

<script setup>
defineEmits(['select-tab'])

defineProps({
  headline: {
    type: String,
    default: '统一查看审核压力、导入准备度与权限矩阵，再进入具体管理工作流。',
  },
  description: {
    type: String,
    default: '保持原有帖子审核、论文导入与账号权限管理接口不变，用驾驶舱摘要先建立全局态势。',
  },
  chips: {
    type: Array,
    default: () => [],
  },
  signals: {
    type: Array,
    default: () => [],
  },
  actions: {
    type: Array,
    default: () => [],
  },
})
</script>

<style scoped>
.admin-cockpit-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(320px, 0.95fr);
  gap: var(--space-6);
  padding: clamp(1.5rem, 2.8vw, 2.4rem);
  background:
    radial-gradient(circle at top right, rgba(55, 213, 255, 0.16), transparent 30%),
    linear-gradient(140deg, rgba(124, 140, 255, 0.16), rgba(7, 17, 31, 0.12)),
    var(--color-bg-panel);
}

.admin-cockpit-hero__copy,
.admin-cockpit-hero__side,
.admin-cockpit-hero__signal {
  display: grid;
  gap: var(--space-3);
}

.admin-cockpit-hero__eyebrow {
  font-size: 0.78rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--color-accent-secondary);
}

.admin-cockpit-hero__headline {
  font-size: 1.05rem;
  line-height: 1.75;
  color: var(--color-text-primary);
}

.admin-cockpit-hero__description {
  max-width: 42rem;
  line-height: 1.7;
}

.admin-cockpit-hero__chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.admin-cockpit-hero__chip {
  padding: 0.46rem 0.82rem;
  border: 1px solid rgba(124, 140, 255, 0.22);
  border-radius: 999px;
  background: rgba(124, 140, 255, 0.12);
  color: var(--color-text-primary);
}

.admin-cockpit-hero__signals {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-3);
}

.admin-cockpit-hero__signal {
  padding: var(--space-4);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.04);
}

.admin-cockpit-hero__signal span,
.admin-cockpit-hero__signal small {
  color: var(--color-text-secondary);
}

.admin-cockpit-hero__signal strong {
  color: var(--color-text-primary);
  font-size: 1.35rem;
}

.admin-cockpit-hero__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
}

@media (max-width: 1220px) {
  .admin-cockpit-hero {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 780px) {
  .admin-cockpit-hero__signals {
    grid-template-columns: 1fr;
  }
}
</style>
