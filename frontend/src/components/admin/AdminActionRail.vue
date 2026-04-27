<template>
  <aside class="admin-action-rail card glass" data-testid="admin-action-rail">
    <div class="admin-action-rail__header">
      <p class="admin-action-rail__eyebrow">Action Rail</p>
      <h2>高优先级动作</h2>
      <p>先判断态势，再切换到对应执行面板，维持现有管理接口与操作节奏。</p>
    </div>

    <div class="admin-action-rail__actions">
      <button
        v-for="action in actions"
        :key="action.label"
        class="admin-action-rail__action"
        type="button"
        @click="$emit('select-tab', action.tab)"
      >
        <strong>{{ action.label }}</strong>
        <small>{{ action.detail }}</small>
      </button>
    </div>

    <section class="admin-action-rail__section">
      <h3>治理状态</h3>
      <div class="admin-action-rail__status-list">
        <article
          v-for="status in statuses"
          :key="status.label"
          class="admin-action-rail__status"
          :class="status.tone ? `admin-action-rail__status--${status.tone}` : ''"
        >
          <span>{{ status.label }}</span>
          <strong>{{ status.value }}</strong>
          <small>{{ status.detail }}</small>
        </article>
      </div>
    </section>

    <section v-if="notes.length" class="admin-action-rail__section">
      <h3>接口约束</h3>
      <ul class="admin-action-rail__notes">
        <li v-for="note in notes" :key="note">{{ note }}</li>
      </ul>
    </section>
  </aside>
</template>

<script setup>
defineEmits(['select-tab'])

defineProps({
  actions: {
    type: Array,
    default: () => [],
  },
  statuses: {
    type: Array,
    default: () => [],
  },
  notes: {
    type: Array,
    default: () => [],
  },
})
</script>

<style scoped>
.admin-action-rail {
  position: sticky;
  top: var(--space-7);
  display: grid;
  gap: var(--space-4);
  align-self: start;
  padding: clamp(1.25rem, 2vw, 1.65rem);
}

.admin-action-rail__header,
.admin-action-rail__section,
.admin-action-rail__status,
.admin-action-rail__action {
  display: grid;
  gap: var(--space-2);
}

.admin-action-rail__eyebrow {
  font-size: 0.78rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--color-accent-secondary);
}

.admin-action-rail__actions,
.admin-action-rail__status-list {
  display: grid;
  gap: var(--space-3);
}

.admin-action-rail__action,
.admin-action-rail__status {
  padding: var(--space-4);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.04);
  text-align: left;
}

.admin-action-rail__action {
  cursor: pointer;
  transition:
    transform 0.16s ease,
    border-color 0.16s ease,
    background 0.16s ease;
}

.admin-action-rail__action:hover {
  transform: translateY(-1px);
  border-color: var(--color-border-strong);
  background: rgba(124, 140, 255, 0.08);
}

.admin-action-rail__status--danger {
  border-color: rgba(251, 113, 133, 0.3);
}

.admin-action-rail__status--success {
  border-color: rgba(52, 211, 153, 0.28);
}

.admin-action-rail__status--accent {
  border-color: rgba(55, 213, 255, 0.3);
}

.admin-action-rail__action strong,
.admin-action-rail__status strong {
  color: var(--color-text-primary);
}

.admin-action-rail__action small,
.admin-action-rail__status span,
.admin-action-rail__status small {
  color: var(--color-text-secondary);
}

.admin-action-rail__notes {
  display: grid;
  gap: var(--space-2);
  margin: 0;
  padding-left: 1.1rem;
  color: var(--color-text-secondary);
}

@media (max-width: 1180px) {
  .admin-action-rail {
    position: static;
  }
}
</style>
