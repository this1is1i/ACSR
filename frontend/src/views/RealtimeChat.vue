<template>
  <div class="chat-root" data-testid="chat-collaboration-workspace">
    <Sidebar />
    <main class="main-content">
      <header class="workspace-header card glass">
        <div>
          <h2>协作消息工作台</h2>
        </div>
      </header>

      <div class="chat-panel">
        <ConversationRail
          :contacts="contacts"
          :selected-contact-id="selected"
          :messages="messages"
          :online-set="onlineSet"
          :recommendations="recommendations"
          :show-recommendations="showRecommendations"
          :search-results="searchResults"
          @select="selectContact"
          @start-chat="startChatWithRecommended"
          @search="handleSearch"
          @start-chat-user="startChatWithUser"
        />

        <section class="chat-area card glass">
          <div class="thread-header">
            <div>
              <p class="workspace-eyebrow">Shared Thread</p>
              <h3>{{ selectedContact ? `${selectedContact.name} 协作线程` : '选择一个协作线程' }}</h3>
              <p class="thread-summary">{{ selectedSummary }}</p>
            </div>
            <div class="thread-pills">
              <span class="thread-pill" :class="{ online: selectedContact && onlineSet.has(selectedContact.id) }">
                {{ selectedContact ? (onlineSet.has(selectedContact.id) ? '在线协作中' : '异步协作中') : '等待选择联系人' }}
              </span>
              <span class="thread-pill" :class="{ online: connected }">{{ connected ? '实时同步已连接' : '离线消息模式' }}</span>
            </div>
          </div>

          <div class="messages" ref="messagesEl">
            <div v-if="!selected" class="empty">请选择联系人开始聊天</div>
            <div v-else>
              <div v-for="(m, idx) in conversationFor(selected)" :key="idx" :class="['msg', m.from === meId ? 'out' : 'in']">
                <div class="bubble">{{ m.content }}</div>
                <div class="time">{{ m.time }}</div>
              </div>
            </div>
          </div>

          <div class="composer">
            <input v-model="draft" @keydown.enter.prevent="sendMessage" placeholder="输入消息，按 Enter 发送" />
            <button class="btn primary" @click="sendMessage">发送</button>
          </div>
        </section>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, ref, reactive, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import Sidebar from '@/components/Sidebar.vue'
import ConversationRail from '@/components/chat/ConversationRail.vue'
import { getConversations, getChatHistory, sendMessageRest, markMessageRead, getRecommendedCollaborators, searchUsers } from '@/api/message'
import { getKnowledgeGraph } from '@/api/recommend'
import { useUserStore } from '@/store/userStore'

const contacts = ref([])
const messages = reactive({}) // { contactId: [{id, from, to, content, time, isRead}] }
const onlineSet = ref(new Set())
const selected = ref(null)
const draft = ref('')
const connected = ref(false)
let stompClient = null
const messagesEl = ref(null)

// get user id from token if present (backend expects numeric id)
const userStore = useUserStore()
const recommendations = ref([])
const showRecommendations = ref(false)
const searchResults = ref([])
let searchTimer = null
const token = localStorage.getItem('token') || ''
const meId = userStore.userInfo?.id || Number(localStorage.getItem('userId')) || 1

const selectedContact = computed(() => contacts.value.find(contact => contact.id == selected.value) || null)
const selectedSummary = computed(() => {
  if (!selectedContact.value) return '选择左侧会话开始协作'
  if (selectedContact.value.lastMessage) return selectedContact.value.lastMessage
  return '当前会话还没有消息，发送第一条协作信息开始同步。'
})

function conversationFor(id) {
  return messages[id] || []
}

async function loadConversations() {
  try {
    const res = await getConversations()
    const data = res.data || res || []
    if (Array.isArray(data) && data.length) {
      contacts.value = data.map(c => {
        const user = c.contact || {}
        const id = user.id || c.contactId
        return { id, name: user.nickname || user.username || user.name || `用户${id}`, unreadCount: c.unreadCount || 0, lastMessage: c.lastMessage || '', isRealUser: true }
      })
    } else {
      // fallback: use knowledge graph nodes as mock contacts, mark as not real users (don't allow send)
      try {
        const kg = await getKnowledgeGraph()
        const kgd = kg.data || kg || {}
        const nodes = kgd.nodes || []
        contacts.value = nodes.map(n => ({ id: n.id, name: n.name, unreadCount: 0, lastMessage: '', isRealUser: false }))
        ElMessage.info('当前没有真实联系人，已使用知识图谱节点作为展示（不能发送）')
      } catch(e) { console.debug('fallback kg failed', e) }
    }
  } catch (e) {
    console.debug('loadConversations failed', e)
  }
}

async function loadRecommendations() {
  if (!userStore.hasRole('RESEARCHER')) return
  showRecommendations.value = true
  try {
    const res = await getRecommendedCollaborators()
    const data = res.data || res || []
    recommendations.value = Array.isArray(data) ? data : []
  } catch (e) {
    console.debug('loadRecommendations failed', e)
  }
}

async function handleSearch(query) {
  if (!query || !query.trim()) {
    searchResults.value = []
    return
  }
  clearTimeout(searchTimer)
  searchTimer = setTimeout(async () => {
    try {
      const res = await searchUsers(query.trim())
      const data = res.data || res || []
      searchResults.value = Array.isArray(data) ? data : []
    } catch (e) {
      console.debug('searchUsers failed', e)
    }
  }, 300)
}

async function startChatWithUser(user) {
  const greeting = `你好！我是${userStore.userInfo?.username || '一位研究者'}，通过搜索找到你，希望可以一起交流探讨！`
  try {
    await sendMessageRest(user.id, greeting)
    ElMessage.success('已发送协作邀请')
  } catch (e) {
    console.debug('send greeting failed', e)
    ElMessage.error('发送邀请失败')
    return
  }
  searchResults.value = []
  await loadConversations()
  await loadRecommendations()
  selectContact(user.id)
}

async function startChatWithRecommended(rec) {
  const greeting = `你好！我是${userStore.userInfo?.username || '一位研究者'}，发现我们在${rec.commonInterests?.join('、') || '研究'}方面有共同兴趣，希望可以一起交流探讨！`
  try {
    await sendMessageRest(rec.userId, greeting)
    ElMessage.success('已发送协作邀请')
  } catch (e) {
    console.debug('send greeting failed', e)
    ElMessage.error('发送邀请失败')
    return
  }
  await loadConversations()
  await loadRecommendations()
  selectContact(rec.userId)
}

async function selectContact(id) {
  selected.value = id
  // load history from backend
  try {
    const res = await getChatHistory(id)
    const hist = res.data || res || []
    messages[id] = hist.map(m => ({ id: m.id, from: m.senderId, to: m.receiverId, content: m.content, time: m.createTime ? new Date(m.createTime).toLocaleString() : (m.time || new Date().toLocaleTimeString()), isRead: !!m.isRead }))

    // update contact metadata
    const contact = contacts.value.find(c => c.id == id)
    if (contact) {
      contact.unreadCount = 0
      contact.lastMessage = messages[id].length ? messages[id][messages[id].length - 1].content : contact.lastMessage
    }

    // mark unread messages as read
    for (const msg of messages[id]) {
      if (msg.to === meId && !msg.isRead) {
        try { await markMessageRead(msg.id); msg.isRead = true } catch (e) { console.debug('markRead failed', e) }
      }
    }
  } catch (e) {
    console.debug('load history failed', e)
  }

  nextTick(() => { scrollToBottom() })
}

function scrollToBottom() {
  const el = messagesEl.value
  if (el) { el.scrollTop = el.scrollHeight }
}

async function connect() {
  // helper to load script fallback
  function loadScript(url, check) {
    return new Promise((resolve, reject) => {
      if (check && check()) return resolve()
      const s = document.createElement('script')
      s.src = url
      s.async = true
      s.onload = () => resolve()
      s.onerror = (e) => reject(e)
      document.head.appendChild(s)
    })
  }

  try {
    let SockJSlib, stompModule

    // try importing sockjs-client, fallback to CDN UMD
    try {
      const m = await import('sockjs-client')
      SockJSlib = m.default || m
    } catch (e) {
      await loadScript('https://cdn.jsdelivr.net/npm/sockjs-client@1.6.1/dist/sockjs.min.js', () => window.SockJS)
      SockJSlib = window.SockJS
    }

    // try importing stompjs, fallback to CDN UMD
    try {
      stompModule = await import('@stomp/stompjs')
    } catch (e) {
      await loadScript('https://cdn.jsdelivr.net/npm/@stomp/stompjs@8.1.0/bundles/stomp.umd.min.js', () => window.Stomp)
      stompModule = window.Stomp || window.StompJs || window.stomp
    }

    const Client = stompModule?.Client || stompModule?.Stomp?.Client || stompModule?.default?.Client || stompModule || (window.Stomp && window.Stomp.Client)
    if (!Client) throw new Error('STOMP client not available')

    const client = new Client({
      webSocketFactory: () => new SockJSlib('/ws-messages'),
      debug: () => {},
      reconnectDelay: 5000,
      onConnect: () => {
        connected.value = true
        client.subscribe('/user/queue/private', msg => {
          try { const d = JSON.parse(msg.body); handleIncoming(d) } catch(e) { console.debug(e) }
        })
        client.subscribe('/topic/user-status', msg => {
          try { const d = JSON.parse(msg.body); if (d?.userId) {
            if (d.status === 'online') onlineSet.value.add(Number(d.userId)); else onlineSet.value.delete(Number(d.userId))
          }} catch(e) {}
        })
        client.publish({ destination: '/app/user-online', body: JSON.stringify({ token }) })

        // refresh conversations after connect
        loadConversations()
      },
      onStompError: e => { console.debug('STOMP error', e) },
      onDisconnect: () => { connected.value = false }
    })

    stompClient = client
    if (client.activate) client.activate()
  } catch (e) {
    console.debug('Failed to load stomp/sockjs', e)
  }
}

function handleIncoming(data) {
  const from = Number(data.senderId || data.from || data.sender)
  const to = Number(data.receiverId || data.to || data.receiver)
  const other = (from === meId) ? to : from
  if (!messages[other]) messages[other] = []

  const msg = { id: data.id || data.messageId || `s_${Date.now()}`, from, to, content: data.content || data.message || '', time: data.time || new Date().toLocaleTimeString(), isRead: !!data.isRead }
  messages[other].push(msg)

  // update contact unread counts
  const contact = contacts.value.find(c => c.id == other)
  if (contact) {
    if (from !== meId) contact.unreadCount = (contact.unreadCount || 0) + 1
    contact.lastMessage = msg.content
  } else {
    // new contact discovered (assume real user when receiving a message)
    contacts.value.unshift({ id: other, name: `用户${other}`, unreadCount: from !== meId ? 1 : 0, lastMessage: msg.content, isRealUser: true })
  }

  nextTick(() => scrollToBottom())
}

async function sendMessage() {
  if (!selected.value || !draft.value.trim()) return
  const contact = contacts.value.find(c => c.id == selected.value)
  if (!contact) { ElMessage.error('请选择有效联系人'); return }
  if (contact.isRealUser === false) { ElMessage.warning('该联系人为展示节点，无法发送消息'); return }

  const text = draft.value

  // optimistic append
  const tmpId = `tmp_${Date.now()}`
  if (!messages[selected.value]) messages[selected.value] = []
  messages[selected.value].push({ id: tmpId, from: meId, to: selected.value, content: text, time: new Date().toLocaleTimeString(), isRead: false, _tmp: true })
  contact.lastMessage = text
  draft.value = ''
  nextTick(() => scrollToBottom())

  // persist via REST
  try {
    await sendMessageRest(selected.value, text)
  } catch (e) {
    console.debug('persist failed', e)
    // remove optimistic message
    const arr = messages[selected.value]
    const idx = arr.findIndex(m => m.id === tmpId)
    if (idx >= 0) arr.splice(idx, 1)
    ElMessage.error('消息发送失败：对方不存在或服务器错误')
    return
  }

  // send via STOMP if available
  if (stompClient && connected.value) {
    try { stompClient.publish({ destination: '/app/send-private', body: JSON.stringify({ token, receiverId: String(selected.value), content: text }) }) } catch (e) { console.debug(e) }
  }
}

onMounted(() => { connect(); loadConversations(); loadRecommendations() })
onBeforeUnmount(() => { if (stompClient && stompClient.deactivate) stompClient.deactivate(); connected.value = false })
</script>

<style scoped>
.main-content {
  padding: 28px;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.workspace-header {
  margin-bottom: 18px;
  padding: 24px;
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
  flex-shrink: 0;
}

.workspace-eyebrow {
  margin-bottom: 8px;
  font-size: 12px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--color-accent-secondary);
}

.chat-panel {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: 340px minmax(0, 1fr);
  gap: 18px;
  overflow: hidden;
}

.chat-area {
  min-width: 0;
  display: flex;
  flex-direction: column;
  padding: 18px;
  height: 100%;
  overflow: hidden;
}

.thread-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  padding: 0 4px 12px;
  border-bottom: 1px solid var(--design-border);
  flex-shrink: 0;
}

.thread-header > div:first-child {
  min-width: 0;
  flex: 1;
}

.thread-header h3 {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.thread-summary {
  max-width: 56ch;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.thread-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  flex-shrink: 0;
}

.thread-pill {
  padding: 8px 12px;
  border-radius: 999px;
  border: 1px solid var(--design-border);
  background: rgba(124, 140, 255, 0.12);
  color: var(--color-text-primary);
}

.thread-pill.online { color: #10b981; }

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.msg {
  display: flex;
  flex-direction: column;
  max-width: 70%;
  animation: fadeInUp 0.18s ease;
}

.msg.in { align-items: flex-start; }

.msg.out {
  align-items: flex-end;
  margin-left: auto;
}

.bubble {
  padding: 10px 14px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(4px);
  box-shadow: var(--shadow);
}

.msg.out .bubble {
  background: linear-gradient(135deg, var(--primary), var(--accent));
  color: white;
}

.time {
  font-size: 11px;
  color: var(--text-secondary);
  margin-top: 6px;
  display: flex;
  gap: 8px;
  align-items: center;
}

.time .read {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.75);
}

.bubble.new {
  transform: translateY(6px);
  opacity: 0;
  animation: popIn 0.22s forwards;
}

.composer {
  display: flex;
  gap: 8px;
  padding: 12px;
  border-top: 1px solid var(--border);
  align-items: center;
  flex-shrink: 0;
}

.composer input {
  flex: 1;
  padding: 12px 14px;
  border-radius: 10px;
  border: 1px solid var(--border);
  background: transparent;
  color: var(--text-primary);
  outline: none;
}

.btn.primary {
  background: var(--primary);
  color: white;
  padding: 10px 16px;
  border-radius: 10px;
}

.empty {
  padding: 40px;
  text-align: center;
  color: var(--text-secondary);
}

@keyframes popIn {
  to { transform: none; opacity: 1; }
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: none; }
}

@media (max-width: 1180px) {
  .workspace-header,
  .chat-panel { grid-template-columns: 1fr; }
  .workspace-header,
  .thread-header { flex-direction: column; align-items: flex-start; }
}

@media (max-width: 980px) {
  .main-content { margin-left: 0; padding: 18px; }
}
</style>
