<template>
  <aside class="conversation-rail card glass" data-testid="conversation-rail">
    <div class="rail-heading">
      <p class="rail-eyebrow">Workspace Rail</p>
      <h3>协作会话</h3>
      <p>联系人、论文线索和路径推进都在同一个工作台侧栏里。</p>
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
      <p v-else class="empty-copy">还没有协作会话，选择知识图谱节点后也会在这里显示。</p>
    </section>

    <section class="rail-panel">
      <div class="panel-header">
        <span>主题焦点</span>
        <small>{{ inferredTopics.length ? '自动提炼' : '等待消息' }}</small>
      </div>
      <div v-if="inferredTopics.length" class="topic-chips">
        <span v-for="topic in inferredTopics" :key="topic" class="topic-chip">{{ topic }}</span>
      </div>
      <p v-else class="empty-copy">选择会话后，系统会从消息中提炼当前主题。</p>
    </section>

    <section class="rail-panel">
      <div class="panel-header">
        <span>论文线索</span>
        <small>来自对话内容</small>
      </div>
      <ul v-if="paperSignals.length" class="signal-list">
        <li v-for="paper in paperSignals" :key="paper">{{ paper }}</li>
      </ul>
      <p v-else class="empty-copy">当前对话里还没有识别到明确的论文线索。</p>
    </section>

    <section class="rail-panel">
      <div class="panel-header">
        <span>协作路径</span>
        <small>从同步到落地</small>
      </div>
      <ol class="path-list">
        <li v-for="step in collaborationPath" :key="step.label" :class="{ active: step.active }">
          <strong>{{ step.label }}</strong>
          <span>{{ step.detail }}</span>
        </li>
      </ol>
    </section>
  </aside>
</template>

<script setup>
import { computed } from 'vue'

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

const topicPatterns = [
  'Actor-Critic',
  'PPO',
  'Transformer',
  'Diffusion',
  'Graph Neural Network',
  '强化学习',
  '图神经网络',
  '知识图谱',
]

const selectedContact = computed(() => props.contacts.find(contact => contact.id == props.selectedContactId) || null)

const selectedMessages = computed(() => {
  if (props.selectedContactId == null) return []
  return props.messages[props.selectedContactId] || []
})

const conversationText = computed(() => [
  selectedContact.value?.lastMessage,
  ...selectedMessages.value.map(message => message.content),
].filter(Boolean).join(' '))

const inferredTopics = computed(() => {
  const text = conversationText.value.toLowerCase()
  return topicPatterns
    .filter(topic => text.includes(topic.toLowerCase()))
    .slice(0, 5)
})

const paperSignals = computed(() => {
  const explicitMentions = []

  for (const message of selectedMessages.value) {
    const content = message.content || ''
    for (const match of content.matchAll(/([A-Za-z][A-Za-z0-9-]*(?:\s+[A-Za-z][A-Za-z0-9-]*){0,4})\s*论文/gi)) {
      explicitMentions.push(match[1].trim())
    }
  }

  return [...new Set([...explicitMentions, ...inferredTopics.value.filter(topic => /^[A-Za-z0-9-]+$/.test(topic))])].slice(0, 4)
})

const collaborationPath = computed(() => {
  const messageCount = selectedMessages.value.length
  const firstPaper = paperSignals.value[0]
  const firstTopic = inferredTopics.value[0]

  return [
    {
      label: '建立协作线程',
      detail: selectedContact.value ? `${selectedContact.value.name} 已加入当前工作区。` : '选择一个联系人开始协作。',
      active: !!selectedContact.value,
    },
    {
      label: '共享论文线索',
      detail: firstPaper ? `${firstPaper} 已进入当前对话。` : '等待消息中出现论文引用。',
      active: !!firstPaper,
    },
    {
      label: '推进下一步',
      detail: firstTopic && messageCount > 1 ? `${firstTopic} 的下一步已经开始协同。` : '继续同步实验、写作或阅读分工。',
      active: !!firstTopic && messageCount > 1,
    },
  ]
})

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
