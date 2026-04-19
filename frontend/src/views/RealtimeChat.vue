<template>
  <div class="chat-root">
    <Sidebar />
    <main class="main-content">
      <header class="header"><h2>💬 实时私信</h2><p class="hint">通过 WebSocket/STOMP 与后端实时通信</p></header>

      <div class="chat-panel">
        <aside class="contacts">
          <div class="contacts-header">联系人</div>
          <div class="contact" v-for="c in contacts" :key="c.id" :class="{ active: selected === c.id }" @click="selectContact(c.id)">
            <div class="avatar">{{ c.name.charAt(0) }}</div>
            <div class="meta">
              <div class="name">{{ c.name }}</div>
              <div class="status" :class="{ online: onlineSet.has(c.id) }">{{ onlineSet.has(c.id) ? '在线' : '离线' }}</div>
            </div>
          </div>
        </aside>

        <section class="chat-area">
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

      <div class="ws-status">连接: <span :class="{ online: connected }">{{ connected ? '已连接' : '未连接' }}</span></div>
    </main>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import Sidebar from '@/components/Sidebar.vue'
import { getConversations, getChatHistory, sendMessageRest, markMessageRead } from '@/api/message'
import { getKnowledgeGraph } from '@/api/recommend'

const contacts = ref([])
const messages = reactive({}) // { contactId: [{id, from, to, content, time, isRead}] }
const onlineSet = ref(new Set())
const selected = ref(null)
const draft = ref('')
const connected = ref(false)
let stompClient = null
const messagesEl = ref(null)

// get user id from token if present (backend expects numeric id)
const token = localStorage.getItem('token') || ''
const meId = localStorage.getItem('userId') ? Number(localStorage.getItem('userId')) : 1

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
        return { id, name: user.nickname || user.name || `用户${id}`, unreadCount: c.unreadCount || 0, lastMessage: c.lastMessage || '', isRealUser: true }
      })
    } else {
      // fallback: use knowledge graph nodes as mock contacts, mark as not real users (don't allow send)
      try {
        const kg = await getKnowledgeGraph()
        const kgd = kg.data || kg || {}
        const nodes = kgd.nodes || []
        contacts.value = nodes.map(n => ({ id: n.id, name: n.name, unreadCount: 0, lastMessage: '', isRealUser: false }))
        ElMessage.info('当前没有真实联系人，已使用知识图谱节点作为展示（不能发送）')
      } catch(e) { console.error('fallback kg failed', e) }
    }
  } catch (e) {
    console.error('loadConversations failed', e)
  }
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
        try { await markMessageRead(msg.id); msg.isRead = true } catch (e) { console.error('markRead failed', e) }
      }
    }
  } catch (e) {
    console.error('load history failed', e)
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
          try { const d = JSON.parse(msg.body); handleIncoming(d) } catch(e) { console.error(e) }
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
      onStompError: e => { console.error('STOMP error', e) },
      onDisconnect: () => { connected.value = false }
    })

    stompClient = client
    if (client.activate) client.activate()
  } catch (e) {
    console.error('Failed to load stomp/sockjs', e)
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
    console.error('persist failed', e)
    // remove optimistic message
    const arr = messages[selected.value]
    const idx = arr.findIndex(m => m.id === tmpId)
    if (idx >= 0) arr.splice(idx, 1)
    ElMessage.error('消息发送失败：对方不存在或服务器错误')
    return
  }

  // send via STOMP if available
  if (stompClient && connected.value) {
    try { stompClient.publish({ destination: '/app/send-private', body: JSON.stringify({ token, receiverId: String(selected.value), content: text }) }) } catch (e) { console.error(e) }
  }
}

onMounted(() => { connect(); loadConversations() })
onBeforeUnmount(() => { if (stompClient && stompClient.deactivate) stompClient.deactivate(); connected.value = false })
</script>

<style scoped>
.main-content { margin-left:260px; padding:28px }
.header { padding:18px; margin-bottom:18px }
.chat-panel { display:flex; gap:18px }
.contacts { width:280px; background:var(--bg-card); padding:12px; border-radius:12px }
.contacts-header { font-weight:700; margin-bottom:8px }
.contact { display:flex; gap:10px; padding:10px; border-radius:10px; cursor:pointer; align-items:center; transition:transform .12s ease, background .12s }
.contact:hover { transform: translateX(4px) }
.contact.active { background: rgba(99,102,241,0.14) }
.avatar { width:42px; height:42px; border-radius:10px; background:linear-gradient(135deg,var(--primary),var(--accent)); display:flex; align-items:center; justify-content:center; color:white; font-weight:700 }
.meta { flex:1; overflow:hidden }
.meta .name { font-weight:600; display:flex; align-items:center; gap:8px }
.badge { background:#ff4d4f; color:white; font-size:12px; padding:2px 8px; border-radius:999px }
.meta .preview { font-size:13px; color:var(--text-secondary); white-space:nowrap; overflow:hidden; text-overflow:ellipsis }
.meta .status { font-size:12px; color:var(--text-secondary) }
.meta .status.online { color:#10b981 }
.contact .last { font-size:12px; color:var(--text-secondary) }
.chat-area { flex:1; display:flex; flex-direction:column; background:var(--bg-card); border-radius:12px; padding:12px }
.messages { flex:1; overflow:auto; padding:12px; display:flex; flex-direction:column; gap:10px }
.msg { display:flex; flex-direction:column; max-width:70%; animation: fadeInUp .18s ease }
.msg.in { align-items:flex-start }
.msg.out { align-items:flex-end; margin-left:auto }
.bubble { padding:10px 14px; border-radius:12px; background: rgba(255,255,255,0.04); backdrop-filter: blur(4px); box-shadow: var(--shadow) }
.msg.out .bubble { background: linear-gradient(135deg,var(--primary),var(--accent)); color:white }
.time { font-size:11px; color:var(--text-secondary); margin-top:6px; display:flex; gap:8px; align-items:center }
.time .read { font-size:12px; color:rgba(255,255,255,0.75) }
.bubble.new { transform: translateY(6px); opacity:0; animation: popIn .22s forwards }
.composer { display:flex; gap:8px; padding:12px; border-top:1px solid var(--border); align-items:center }
.composer input { flex:1; padding:12px 14px; border-radius:10px; border:1px solid var(--border); background:transparent; color:var(--text-primary); outline:none }
.btn.primary { background:var(--primary); color:white; padding:10px 16px; border-radius:10px }
.ws-status { margin-top:12px; color:var(--text-secondary) }
.ws-status .online { color:#10b981 }
.empty { padding:40px; text-align:center; color:var(--text-secondary) }
.badge.pulse { position:relative }
.badge.pulse::after { content:''; position:absolute; left:50%; top:50%; width:100%; height:100%; transform:translate(-50%,-50%); border-radius:999px; box-shadow: 0 0 0 0 rgba(255,77,79,0.5); animation: pulse 1.8s infinite }
@keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(255,77,79,0.35) } 70% { box-shadow: 0 0 0 12px rgba(255,77,79,0) } 100% { box-shadow: 0 0 0 0 rgba(255,77,79,0) } }
@keyframes popIn { to { transform:none; opacity:1 } }
@keyframes fadeInUp { from { opacity:0; transform: translateY(6px) } to { opacity:1; transform:none } }
</style>