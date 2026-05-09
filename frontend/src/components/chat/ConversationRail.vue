<template>
  <aside class="conversation-rail card glass" data-testid="conversation-rail" data-area="chat">
    <div class="rail-heading">
      <h3>协作会话</h3>
    </div>

    <section class="rail-panel">
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
const props = defineProps({
  contacts: {
    type: Array,
    default: () => [],
  },
  selectedContactId: {
    type: [String, Number],
    default: null,
  },
  messages: {
    type: Object,
    default: () => ({}),
  },
  onlineSet: {
    type: Object,
    default: () => new Set(),
  },
})

const emit = defineEmits(['select'])

function displayInitial(name) {
  return (name || 'U').charAt(0).toUpperCase()
}

function isOnline(contactId) {
  return typeof props.onlineSet?.has === 'function' && (props.onlineSet.has(contactId) || props.onlineSet.has(Number(contactId)))
}
</script>

<style scoped>
.conversation-rail {
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.conversation-rail[data-area="chat"] {
  border-left: 3px solid var(--color-area-chat);
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

.panel-header {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  align-items: center;
  margin-bottom: 0.75rem;
  color: var(--color-text-primary);
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
  background: rgba(15, 23, 42, 0.36);
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
}

.conversation-row {
  display: flex;
  justify-content: space-between;
  gap: 0.5rem;
  align-items: center;
}

.conversation-copy p,
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
</style>
