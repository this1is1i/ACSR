<template>
  <aside class="search-filter-rail card glass" data-testid="search-filter-rail">
    <section class="search-filter-rail__section">
      <p class="search-filter-rail__eyebrow">Auxiliary Workspace</p>
      <h2>筛选轨道</h2>
    </section>

    <section class="search-filter-rail__section search-filter-rail__stats">
      <div class="search-filter-rail__stat">
        <span>当前检索</span>
        <strong>{{ query || '等待输入关键词' }}</strong>
      </div>
      <div class="search-filter-rail__stat">
        <span>结果规模</span>
        <strong>{{ resultCount }} 篇</strong>
      </div>
    </section>

    <section class="search-filter-rail__section">
      <div class="filter-group">
        <label class="filter-label" for="search-filter-time">时间范围</label>
        <select
          id="search-filter-time"
          class="filter-select"
          :value="filters.time"
          @change="emit('update-filter', 'time', $event.target.value)"
        >
          <option>全部时间</option>
          <option>近一年</option>
          <option>近三年</option>
          <option>近五年</option>
        </select>
      </div>

      <div class="filter-group">
        <label class="filter-label" for="search-filter-sort">排序方式</label>
        <select
          id="search-filter-sort"
          class="filter-select"
          :value="filters.sort"
          @change="emit('update-filter', 'sort', $event.target.value)"
        >
          <option>相关度</option>
          <option>引用次数</option>
          <option>发表时间</option>
          <option>影响力</option>
        </select>
      </div>
    </section>

    <section class="search-filter-rail__section">
      <div class="search-filter-rail__section-header">
        <h3>研究标签</h3>
        <button class="search-filter-rail__reset" type="button" @click="emit('reset')">重置</button>
      </div>
      <div class="filter-tags">
        <button
          v-for="(tag, index) in tags"
          :key="`${tag}-${index}`"
          class="filter-tag"
          type="button"
          @click="emit('toggle-tag', index)"
        >
          {{ tag }}
          <span class="remove">×</span>
        </button>
      </div>
    </section>

    <section v-if="activeFilters.length || activeTags.length" class="search-filter-rail__section">
      <h3>已启用条件</h3>
      <div class="search-filter-rail__active">
        <span v-for="label in activeFilters" :key="label" class="search-filter-rail__chip">{{ label }}</span>
        <span v-for="label in activeTags" :key="label" class="search-filter-rail__chip search-filter-rail__chip--accent">{{ label }}</span>
      </div>
    </section>
  </aside>
</template>

<script setup>
defineProps({
  query: {
    type: String,
    default: '',
  },
  resultCount: {
    type: Number,
    default: 0,
  },
  filters: {
    type: Object,
    default: () => ({}),
  },
  tags: {
    type: Array,
    default: () => [],
  },
  activeFilters: {
    type: Array,
    default: () => [],
  },
  activeTags: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['update-filter', 'toggle-tag', 'reset'])
</script>

<style scoped>
.search-filter-rail {
  position: sticky;
  top: var(--space-6);
  display: grid;
  gap: var(--space-5);
  align-self: start;
  padding: var(--space-6);
}

.search-filter-rail__section {
  display: grid;
  gap: var(--space-3);
}

.search-filter-rail__eyebrow {
  font-size: 0.76rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--color-accent-secondary);
}

.search-filter-rail__stats {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.search-filter-rail__stat {
  display: grid;
  gap: var(--space-2);
  padding: var(--space-4);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.03);
}

.search-filter-rail__stat span {
  font-size: 0.82rem;
  color: var(--color-text-muted);
}

.search-filter-rail__stat strong {
  color: var(--color-text-primary);
  line-height: 1.4;
}

.filter-group {
  display: grid;
  gap: var(--space-2);
}

.filter-label {
  font-size: 0.82rem;
  color: var(--color-text-secondary);
}

.filter-select {
  width: 100%;
  padding: 0.9rem 1rem;
}

.search-filter-rail__section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

.search-filter-rail__reset {
  padding: 0.45rem 0.85rem;
  border: 1px solid var(--color-border-subtle);
  border-radius: 999px;
  background: transparent;
  color: var(--color-text-secondary);
  cursor: pointer;
}

.filter-tags,
.search-filter-rail__active {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.filter-tag,
.search-filter-rail__chip {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.55rem 0.9rem;
  border: 1px solid rgba(124, 140, 255, 0.22);
  border-radius: 999px;
  background: rgba(124, 140, 255, 0.12);
  color: var(--color-text-primary);
}

.filter-tag {
  cursor: pointer;
}

.search-filter-rail__chip--accent {
  border-color: rgba(55, 213, 255, 0.22);
  background: rgba(55, 213, 255, 0.12);
}

.remove {
  color: var(--color-text-muted);
}

@media (max-width: 1120px) {
  .search-filter-rail {
    position: static;
  }

  .search-filter-rail__stats {
    grid-template-columns: 1fr;
  }
}
</style>
