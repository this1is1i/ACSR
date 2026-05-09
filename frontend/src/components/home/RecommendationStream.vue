<template>
  <section class="recommendation-stream card" data-testid="recommendation-stream">
    <div class="stream-header">
      <div>
        <p class="stream-header__eyebrow">Recommendation Stream</p>
        <h2>推荐流</h2>
        <p>围绕当前研究主线持续刷新推荐，保留原有阅读与收藏行为记录。</p>
      </div>
      <button class="btn secondary" type="button" @click="$emit('explore')">补充检索</button>
    </div>

    <div class="stream-highlights">
      <span class="stream-pill">当前主线：{{ focusTopic || '个性化推荐' }}</span>
      <span class="stream-pill">{{ items.length }} 篇待阅读</span>
    </div>

    <RecommendList :items="items" :loading="loading" variant="stream" />
  </section>
</template>

<script setup>
import RecommendList from '@/components/RecommendList.vue'

defineEmits(['explore'])

defineProps({
  items: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
  focusTopic: {
    type: String,
    default: '',
  },
})
</script>

<style scoped>
.recommendation-stream {
  display: grid;
  gap: var(--space-4);
  padding: clamp(1.35rem, 2vw, 1.8rem);
  overflow: hidden;
}

.stream-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-4);
}

.stream-header__eyebrow {
  margin-bottom: var(--space-2);
  font-size: 0.78rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--color-accent-secondary);
}

.stream-highlights {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.stream-pill {
  padding: 0.45rem 0.8rem;
  border-radius: 999px;
  border: 1px solid var(--color-border-subtle);
  background: rgba(124, 140, 255, 0.08);
  color: var(--color-text-primary);
}

@media (max-width: 720px) {
  .stream-header {
    flex-direction: column;
  }
}
</style>
