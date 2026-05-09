<template>
  <section class="admin-kpi-grid" data-testid="admin-kpi-grid">
    <template v-if="loading">
      <article v-for="index in 4" :key="index" class="admin-kpi-grid__card card" data-area="admin">
        <el-skeleton :rows="3" animated />
      </article>
    </template>

    <template v-else>
      <article
        v-for="item in items"
        :key="item.label"
        class="admin-kpi-grid__card card"
        :class="item.tone ? `admin-kpi-grid__card--${item.tone}` : ''"
      >
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <small>{{ item.caption }}</small>
      </article>
    </template>
  </section>
</template>

<script setup>
defineProps({
  loading: {
    type: Boolean,
    default: false,
  },
  items: {
    type: Array,
    default: () => [],
  },
})
</script>

<style scoped>
.admin-kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--space-4);
}

.admin-kpi-grid__card {
  display: grid;
  gap: var(--space-2);
  padding: clamp(1.15rem, 2vw, 1.45rem);
  background: rgba(255, 255, 255, 0.04);
}

.admin-kpi-grid__card[data-area="admin"] {
  border-left: 3px solid var(--color-area-admin);
}

.admin-kpi-grid__card span,
.admin-kpi-grid__card small {
  color: var(--color-text-secondary);
}

.admin-kpi-grid__card strong {
  font-size: clamp(1.45rem, 2.5vw, 2rem);
  color: var(--color-text-primary);
}

.admin-kpi-grid__card--danger {
  border-color: rgba(251, 113, 133, 0.3);
}

.admin-kpi-grid__card--success {
  border-color: rgba(52, 211, 153, 0.28);
}

.admin-kpi-grid__card--accent {
  border-color: rgba(55, 213, 255, 0.3);
}

@media (max-width: 1100px) {
  .admin-kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 680px) {
  .admin-kpi-grid {
    grid-template-columns: 1fr;
  }
}
</style>
