<template>
  <div class="recommend-list">
    <el-skeleton :rows="4" animated v-if="loading" />
    <template v-else>
      <el-empty v-if="!items.length" description="暂无推荐，请先浏览一些论文" />
      <PaperCard
        v-for="item in items"
        :key="item.paperId || item.id"
        :paper="item"
        source="recommend"
      />
    </template>
  </div>
</template>

<script setup>
import PaperCard from './PaperCard.vue'

defineProps({
  items: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
})
</script>

<style scoped>
.recommend-list { max-width: 860px; margin: 0 auto; }
</style>
