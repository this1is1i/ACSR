<template>
  <aside class="conversation-rail card glass" data-testid="conversation-rail" data-area="chat">
    <div class="rail-heading">
      <h3>协作会话</h3>
      <div class="search-bar">
        <input
          v-model="searchQuery"
          type="text"
          class="search-input"
          placeholder="搜索联系人..."
          @keydown.enter="emit('search', searchQuery)"
          @input="emit('search', searchQuery)"
        />
      </div>
    </div>

    <section v-if="searchResults.length" class="rail-panel search-results-panel">
      <div class="panel-header">
        <span>搜索结果</span>
        <small>{{ searchResults.length }} 位</small>
      </div>
      <div class="conversation-list">
        <div
          v-for="user in searchResults"
          :key="user.id"
          class="recommendation-item"
        >
          <div class="conversation-avatar">{{ displayInitial(user.username) }}</div>
          <div class="conversation-copy">
            <div class="conversation-row">
              <strong>{{ user.username }}</strong>
            </div>
            <p class="rec-bio">{{ user.researchInterests || user.bio || '暂无简介' }}</p>
            <button
              type="button"
              class="btn-start-chat"
              @click.stop="emit('startChatUser', user)"
            >
              开始对话
            </button>
          </div>
        </div>
      </div>
    </section>

    <section v-if="showRecommendations" class="rail-panel recommendations-panel">
      <div class="panel-header">
        <span>推荐合作者</span>
        <small>{{ recommendations.length }} 位</small>
      </div>
      <div v-if="recommendations.length" class="conversation-list">
        <div
          v-for="rec in recommendations"
          :key="rec.userId"
          class="recommendation-item"
        >
          <div class="conversation-avatar">{{ displayInitial(rec.username) }}</div>
          <div class="conversation-copy">
            <div class="conversation-row">
              <strong>{{ rec.username }}</strong>
            </div>
            <p class="rec-bio">{{ rec.bio || '暂无简介' }}</p>
            <div class="topic-chips">
              <span v-for="tag in rec.commonInterests" :key="tag" class="topic-chip">{{ tag }}</span>
            </div>
            <button
              type="button"
              class="btn-start-chat"
              @click.stop="emit('startChat', rec)"
            >
              开始对话
            </button>
          </div>
        </div>
      </div>
      <p v-else class="empty-copy">暂未找到匹配的合作者，完善研究兴趣标签可提高匹配度</p>
    </section>

    <section class="rail-panel contacts-panel">
      <div class="panel-header">
        <span>会话列表</span>
        <small>{{ contacts.length }} 条</small>
      </div>

      <div v-if="contacts.length" class="conversation-list">
        <button
          v-for="contact in contacts"
          :key="contact.id"
          type="button"
          class="conversation-item"
          :class="{ active: selectedContactId === contact.id }"
          :data-testid="`conversation-item-${contact.id}`"
          @click="emit('select', contact.id)"
        >
          <div class="conversation-avatar">{{ displayInitial(contact.name) }}</div>
          <div class="conversation-copy">
            <div class="conversation-row">
              <strong>{{ contact.name }}</strong>
              <span v-if="contact.unreadCount" class="conversation-badge">{{ contact.unreadCount }}</span>
            </div>
            <p>{{ contact.lastMessage || '等待第一条协作消息' }}</p>
            <small :class="{ online: isOnline(contact.id) }">{{ isOnline(contact.id) ? '在线协作中' : '异步协作中' }}</small>
          </div>
        </button>
      </div>
      <p v-else class="empty-copy">还没有协作会话</p>
    </section>
  </aside>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  contacts: {
    type: Array,
    default: () => [],
  },
  selectedContactId: {
    type: [String, Number],
    default: null,
  },
  onlineSet: {
    type: Object,
    default: () => new Set(),
  },
  recommendations: {
    type: Array,
    default: () => [],
  },
  showRecommendations: {
    type: Boolean,
    default: false,
  },
  searchResults: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['select', 'startChat', 'search', 'startChatUser'])

const searchQuery = ref('')

function displayInitial(name) {
  return (name || 'U').charAt(0).toUpperCase()
}

function isOnline(contactId) {
  return typeof props.onlineSet?.has === 'function' && (props.onlineSet.has(contactId) || props.onlineSet.has(Number(contactId)))
}
</script>

<style scoped>
.conversation-rail {
  height: 100%;
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  overflow: hidden;
}

.conversation-rail[data-area="chat"] {
  border-left: 3px solid var(--color-area-chat);
}

.rail-heading {
  padding: 1rem;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-subtle);
  background: rgba(255, 255, 255, 0.02);
  flex-shrink: 0;
}

.search-bar {
  margin-top: 0.75rem;
}

.search-input {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border-radius: 8px;
  border: 1px solid var(--color-border-subtle);
  background: rgba(255, 255, 255, 0.05);
  color: var(--color-text-primary);
  outline: none;
  font-size: 0.85rem;
}

.search-input::placeholder {
  color: var(--color-text-secondary);
}

.search-input:focus {
  border-color: var(--color-border-strong);
}

.search-results-panel {
  flex-shrink: 0;
  max-height: 40%;
  overflow-y: auto;
  border-left: 3px solid var(--color-accent-secondary);
}

.rail-panel {
  padding: 1rem;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-subtle);
  background: rgba(255, 255, 255, 0.02);
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.recommendations-panel {
  flex: 0 0 auto;
  max-height: 45%;
  overflow-y: auto;
}

.contacts-panel {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.rail-eyebrow {
  margin-bottom: 0.35rem;
  font-size: 0.72rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--color-accent-secondary);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  align-items: center;
  margin-bottom: 0.75rem;
  color: var(--color-text-primary);
  flex-shrink: 0;
}

.conversation-list,
.topic-chips,
.signal-list,
.path-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.conversation-item,
.signal-list li,
.path-list li {
  padding: 0.85rem 0.9rem;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-subtle);
  background: var(--bg-card);
}

.conversation-item {
  display: flex;
  gap: 0.85rem;
  text-align: left;
  cursor: pointer;
  transition: transform 0.16s ease, border-color 0.16s ease, background 0.16s ease;
}

.conversation-item:hover,
.conversation-item.active {
  transform: translateX(2px);
  border-color: var(--color-border-strong);
  background: linear-gradient(135deg, rgba(124, 140, 255, 0.18), rgba(55, 213, 255, 0.08));
}

.conversation-avatar {
  width: 2.5rem;
  height: 2.5rem;
  flex: 0 0 auto;
  border-radius: var(--radius-md);
  display: grid;
  place-items: center;
  color: #fff;
  font-weight: 700;
  background: linear-gradient(135deg, var(--primary), var(--accent));
}

.conversation-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  overflow: hidden;
}

.conversation-row {
  display: flex;
  justify-content: space-between;
  gap: 0.5rem;
  align-items: center;
}

.conversation-copy p {
  color: var(--color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conversation-copy small,
.signal-list li,
.path-list span,
.empty-copy {
  color: var(--color-text-secondary);
}

.conversation-badge,
.topic-chip {
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  border: 1px solid var(--color-border-subtle);
  background: rgba(124, 140, 255, 0.12);
}

.conversation-badge {
  color: var(--color-text-primary);
}

.topic-chips {
  flex-direction: row;
  flex-wrap: wrap;
}

.topic-chip {
  color: var(--color-text-primary);
}

.conversation-copy .online {
  color: #34d399;
}

.path-list {
  padding-left: 1.1rem;
  margin: 0;
}

.path-list li.active {
  border-color: var(--color-border-strong);
  box-shadow: var(--shadow-glow);
}

.recommendations-panel {
  border-left: 3px solid var(--color-area-chat);
}

.recommendation-item {
  padding: 0.85rem 0.9rem;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-subtle);
  background: var(--bg-card);
  display: flex;
  gap: 0.85rem;
}

.rec-bio {
  font-size: 0.82rem;
  color: var(--color-text-secondary);
  margin: 0.25rem 0 0.5rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.btn-start-chat {
  margin-top: 0.5rem;
  padding: 0.35rem 0.85rem;
  border-radius: 8px;
  border: none;
  background: linear-gradient(135deg, var(--primary), var(--accent));
  color: #fff;
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.16s ease;
}

.btn-start-chat:hover {
  opacity: 0.85;
}
</style>
