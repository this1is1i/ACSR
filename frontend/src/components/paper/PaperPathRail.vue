<template>
  <aside class="paper-path-rail card glass" data-testid="paper-path-rail">
    <section class="paper-path-rail__section">
      <p class="paper-path-rail__eyebrow">Reading Path</p>
      <h2>路径上下文</h2>
      <p>{{ pathContext.description }}</p>
    </section>

    <section class="paper-path-rail__section paper-path-rail__actions">
      <button class="back-btn" type="button" @click="emit('back')">← 返回搜索</button>
      <button class="download-btn" type="button" :disabled="downloading || !paper" @click="emit('download')">
        {{ downloading ? '下载中...' : '下载 TXT' }}
      </button>
    </section>

    <section class="paper-path-rail__section">
      <h3>当前模式</h3>
      <p class="paper-path-rail__mode">{{ pathContext.modeLabel }}</p>
      <p v-if="pathContext.query" class="paper-path-rail__query">检索词：{{ pathContext.query }}</p>
    </section>

    <section v-if="pathContext.activeFilters.length" class="paper-path-rail__section">
      <h3>已启用筛选</h3>
      <div class="paper-path-rail__chips">
        <span v-for="label in pathContext.activeFilters" :key="label" class="paper-path-rail__chip">{{ label }}</span>
      </div>
    </section>

    <section v-if="pathContext.activeTags.length" class="paper-path-rail__section">
      <h3>主题标签</h3>
      <div class="paper-path-rail__chips">
        <span
          v-for="label in pathContext.activeTags"
          :key="label"
          class="paper-path-rail__chip paper-path-rail__chip--accent"
        >
          {{ label }}
        </span>
      </div>
    </section>

    <section class="paper-path-rail__section">
      <h3>下一步阅读</h3>
      <ol class="paper-path-rail__steps">
        <li v-for="step in pathContext.nextSteps" :key="step.title" class="paper-path-rail__step">
          <strong>{{ step.title }}</strong>
          <span>{{ step.detail }}</span>
        </li>
      </ol>
    </section>
  </aside>
</template>

<script setup>
defineProps({
  paper: {
    type: Object,
    default: null,
  },
  pathContext: {
    type: Object,
    required: true,
  },
  downloading: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['back', 'download'])
</script>

<style scoped>
.paper-path-rail {
  position: sticky;
  top: var(--space-6);
  display: grid;
  gap: var(--space-5);
  align-self: start;
  padding: var(--space-6);
}

.paper-path-rail__section {
  display: grid;
  gap: var(--space-3);
}

.paper-path-rail__eyebrow {
  font-size: 0.76rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--color-accent-secondary);
}

.paper-path-rail__actions {
  grid-template-columns: 1fr;
}

.paper-path-rail__mode,
.paper-path-rail__query {
  color: var(--color-text-primary);
}

.paper-path-rail__chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.paper-path-rail__chip {
  padding: 0.5rem 0.8rem;
  border: 1px solid rgba(124, 140, 255, 0.22);
  border-radius: 999px;
  background: rgba(124, 140, 255, 0.12);
  color: var(--color-text-primary);
}

.paper-path-rail__chip--accent {
  border-color: rgba(55, 213, 255, 0.22);
  background: rgba(55, 213, 255, 0.12);
}

.paper-path-rail__steps {
  display: grid;
  gap: var(--space-3);
  margin: 0;
  padding-left: 1.2rem;
}

.paper-path-rail__step {
  display: grid;
  gap: var(--space-1);
}

.paper-path-rail__step strong {
  color: var(--color-text-primary);
}

.paper-path-rail__step span {
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.back-btn,
.download-btn {
  width: 100%;
  padding: 0.9rem 1rem;
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-md);
  color: var(--color-text-primary);
  cursor: pointer;
}

.back-btn {
  background: rgba(255, 255, 255, 0.03);
}

.download-btn {
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  border-color: transparent;
  color: #fff;
}

.download-btn:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

@media (max-width: 1120px) {
  .paper-path-rail {
    position: static;
  }
}
</style>
