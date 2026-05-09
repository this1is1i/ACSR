<template>
  <div class="recommend-list" :class="`recommend-list--${variant}`">
    <el-skeleton :rows="variant === 'stream' ? 5 : 4" animated v-if="loading" />
    <template v-else>
      <el-empty v-if="!items.length" :description="emptyDescription" />
      <div v-else class="recommend-list__stack">
        <PaperCard
          v-for="item in items"
          :key="item.paperId || item.id"
          :paper="item"
          source="recommend"
          :variant="variant"
        />
      </div>
    </template>
  </div>
</template>

<script setup>
import PaperCard from './PaperCard.vue'

defineProps({
  items: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  variant: { type: String, default: 'default' },
  emptyDescription: { type: String, default: '暂无推荐，请先浏览一些论文' },
})
</script>

<style scoped>
.recommend-list {
  width: 100%;
}

.recommend-list--default {
  max-width: 860px;
  margin: 0 auto;
}

.recommend-list__stack {
  display: grid;
  gap: var(--space-4);
  min-width: 0;
}
</style>
