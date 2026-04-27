<template>
  <aside class="discussion-rail card glass" data-testid="discussion-context-rail">
    <div class="rail-heading">
      <p class="rail-eyebrow">Collaboration Workspace</p>
      <h3>协作上下文</h3>
      <p>把讨论、论文与路径推进放在同一条协作轨道里。</p>
    </div>

    <section class="rail-panel">
      <div class="panel-header">
        <span>当前模式</span>
        <strong>{{ activeTabLabel }}</strong>
      </div>
      <p class="panel-copy">{{ publishHint }}</p>
      <div class="stats-grid">
        <div class="stat-chip">
          <strong>{{ posts.length }}</strong>
          <span>讨论线程</span>
        </div>
        <div class="stat-chip">
          <strong>{{ linkedPapers.length }}</strong>
          <span>关联论文</span>
        </div>
        <div class="stat-chip">
          <strong>{{ topicFocus.length }}</strong>
          <span>主题焦点</span>
        </div>
      </div>
    </section>

    <section class="rail-panel">
      <div class="panel-header">
        <span>论文线索</span>
        <small>{{ linkedPapers.length ? '实时提炼' : '等待关联' }}</small>
      </div>
      <div v-if="linkedPapers.length" class="signal-list">
        <article v-for="paper in linkedPapers" :key="paper.key" class="signal-card">
          <strong>{{ paper.title }}</strong>
          <span>{{ paper.venue || '未指定 venue' }} · {{ paper.year || '未知年份' }}</span>
        </article>
      </div>
      <p v-else class="empty-copy">当帖子关联论文后，这里会自动汇总当前协作资产。</p>
    </section>

    <section class="rail-panel">
      <div class="panel-header">
        <span>主题焦点</span>
        <small>从讨论中提炼</small>
      </div>
      <div v-if="topicFocus.length" class="topic-chips">
        <span v-for="topic in topicFocus" :key="topic" class="topic-chip">{{ topic }}</span>
      </div>
      <p v-else class="empty-copy">还没有足够明显的主题关键词。</p>
    </section>

    <section class="rail-panel">
      <div class="panel-header">
        <span>协作路径</span>
        <small>从帖子到行动</small>
      </div>
      <ol class="path-list">
        <li v-for="step in collaborationPath" :key="step.label" :class="{ active: step.active }">
          <strong>{{ step.label }}</strong>
          <span>{{ step.detail }}</span>
        </li>
      </ol>
    </section>

    <section v-if="selectedPost" class="rail-panel rail-panel--spotlight">
      <div class="panel-header">
        <span>当前讨论线程</span>
        <small>评论工作区</small>
      </div>
      <strong class="spotlight-title">{{ selectedPost.title || '无标题帖子' }}</strong>
      <p class="panel-copy">{{ selectedPost.content }}</p>
    </section>
  </aside>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  posts: {
    type: Array,
    default: () => [],
  },
  activeTab: {
    type: String,
    default: 'latest',
  },
  publishHint: {
    type: String,
    default: '',
  },
  selectedPost: {
    type: Object,
    default: null,
  },
})

const topicPatterns = [
  'Actor-Critic',
  'PPO',
  'Reinforcement Learning',
  '强化学习',
  '图神经网络',
  'Graph Neural Network',
  '知识图谱',
  'Diffusion',
  'Transformer',
]

const activeTabLabel = computed(() => (props.activeTab === 'hot' ? '热门协作流' : '最新协作流'))

const linkedPapers = computed(() => {
  const seen = new Set()

  return props.posts
    .filter(post => post.paper?.title)
    .map(post => ({
      key: `${post.paper.title}-${post.paper.year || ''}`,
      title: post.paper.title,
      venue: post.paper.venue,
      year: post.paper.year,
    }))
    .filter((paper) => {
      if (seen.has(paper.key)) return false
      seen.add(paper.key)
      return true
    })
    .slice(0, 3)
})

const topicFocus = computed(() => {
  const text = props.posts
    .flatMap(post => [post.title, post.content, post.paper?.title])
    .filter(Boolean)
    .join(' ')
    .toLowerCase()

  return topicPatterns
    .filter(topic => text.includes(topic.toLowerCase()))
    .slice(0, 6)
})

const collaborationPath = computed(() => [
  {
    label: '共享问题空间',
    detail: props.posts.length ? `已有 ${props.posts.length} 条线程正在同步研究问题。` : '等待首条讨论开启协作。',
    active: props.posts.length > 0,
  },
  {
    label: '锚定论文资产',
    detail: linkedPapers.value[0]?.title || '等待帖子关联论文。',
    active: linkedPapers.value.length > 0,
  },
  {
    label: '推进下一步行动',
    detail: topicFocus.value[0] ? `${topicFocus.value[0]} 已成为当前协作焦点。` : '等待讨论收敛为明确主题。',
    active: topicFocus.value.length > 0,
  },
])
</script>

<style scoped>
.discussion-rail {
  position: sticky;
  top: 1.5rem;
  align-self: start;
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.rail-heading,
.rail-panel {
  padding: 1rem;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-subtle);
  background: rgba(255, 255, 255, 0.02);
}

.rail-eyebrow {
  margin-bottom: 0.35rem;
  font-size: 0.72rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--color-accent-secondary);
}

.rail-heading h3 {
  margin-bottom: 0.35rem;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  align-items: center;
  margin-bottom: 0.75rem;
  color: var(--color-text-primary);
}

.panel-header small,
.panel-copy,
.signal-card span,
.path-list span,
.empty-copy {
  color: var(--color-text-secondary);
}

.stats-grid,
.topic-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
}

.stat-chip,
.topic-chip {
  padding: 0.65rem 0.8rem;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-subtle);
  background: rgba(124, 140, 255, 0.08);
}

.stat-chip {
  min-width: 5.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.signal-list,
.path-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.signal-card,
.path-list li {
  padding: 0.85rem 0.9rem;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-subtle);
  background: rgba(15, 23, 42, 0.36);
}

.signal-card {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.path-list {
  padding-left: 1.1rem;
  margin: 0;
}

.path-list li.active {
  border-color: var(--color-border-strong);
  box-shadow: var(--shadow-glow);
}

.spotlight-title {
  display: block;
  margin-bottom: 0.5rem;
}

@media (max-width: 1180px) {
  .discussion-rail {
    position: static;
  }
}
</style>
