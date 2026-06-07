<template>
  <div class="profile-root page-root">
    <div class="bg-animation"></div>
    <Sidebar />
    <main class="main-content">
      <header class="header">
        <div class="page-title">
          <h2>👤 研究身份与资产</h2>
        </div>
        <div class="header-actions">
          <button class="btn secondary" @click="logout">退出登录</button>
        </div>
      </header>

      <div class="profile-hero card glass animate-fade-up">
                <div class="profile-content">
          <div class="profile-avatar-large">{{ profile.avatar ? '' : (profile.username ? profile.username.charAt(0) : 'U') }}
            <img v-if="profile.avatar" :src="profile.avatar" alt="avatar" class="avatar-img" />
          </div>
          <div class="profile-info">
            <div class="profile-name">{{ profile.username || '用户' }}</div>
            <div class="profile-title">{{ profile.bio || '—' }}</div>
            <div class="profile-tags">
              <span v-for="(tag, idx) in (profile.researchInterests ? profile.researchInterests.split(',') : [])" :key="idx" class="profile-tag">{{ tag }}</span>
            </div>
          </div>

          <div class="profile-actions">
            <button class="profile-btn btn primary" @click="router.push('/profile/edit')">编辑资料</button>
          </div>
        </div>
      </div>

      <div class="profile-grid">
        <div class="profile-card card animate-fade-up" data-area="profile">
          <div class="card-header">
            <div class="card-title">
              <div class="card-icon">⭐</div>
              我的收藏
            </div>
            <button class="edit-btn btn secondary" @click="viewAllCollections">查看全部</button>
          </div>

          <div class="collection-list" v-if="collectionsLoading">
            <div class="empty-hint">加载中...</div>
          </div>
          <div class="collection-list" v-else-if="collections.length">
            <div v-for="(c, idx) in pagedCollections" :key="idx" class="collection-item" @click="c.id && router.push(`/paper/${c.id}`)">
              <div class="collection-thumb">📄</div>
              <div class="collection-info">
                <div class="collection-title">{{ c.title }}</div>
                <div class="collection-meta">{{ c.meta }}</div>
              </div>
            </div>
          </div>
          <div class="collection-list" v-else>
            <div class="empty-hint">还没有收藏论文</div>
          </div>
          <div v-if="collections.length > collectionsPageSize" class="history-pagination">
            <el-pagination background :current-page="collectionsPage" :page-size="collectionsPageSize" :total="collections.length" layout="prev, pager, next" @current-change="collectionsPage = $event" />
          </div>
        </div>

        <div class="profile-card card animate-fade-up" data-area="profile">
          <div class="card-header">
            <div class="card-title">
              <div class="card-icon">🕐</div>
              最近活动
            </div>
            <button class="edit-btn btn secondary" @click="doClearHistory">清空</button>
          </div>

          <div class="history-list" v-if="historyLoading">
            <div class="empty-hint">加载中...</div>
          </div>
          <div class="history-list" v-else-if="history.length">
            <div v-for="(h, idx) in pagedHistory" :key="idx" class="history-item">
              <div class="history-icon">{{ h.icon }}</div>
              <div class="history-text">{{ h.text }}</div>
              <div class="history-time">{{ h.time }}</div>
            </div>
          </div>
          <div class="history-list" v-else>
            <div class="empty-hint">暂无活动记录</div>
          </div>
          <div v-if="history.length > historyPageSize" class="history-pagination">
            <el-pagination background :current-page="historyPage" :page-size="historyPageSize" :total="history.length" layout="prev, pager, next" @current-change="historyPage = $event" />
          </div>
        </div>
      </div>

      <div class="profile-card card animate-fade-up my-papers-card">
        <div class="card-header">
          <div class="card-title">
            <div class="card-icon">📄</div>
            我的论文
          </div>
          <div class="claims-tabs">
            <button :class="['tab-btn', { active: claimsTab === 'pending' }]" @click="claimsTab = 'pending'">
              待确认 ({{ pendingClaims.length }})
            </button>
            <button :class="['tab-btn', { active: claimsTab === 'confirmed' }]" @click="claimsTab = 'confirmed'">
              已确认 ({{ confirmedClaims.length }})
            </button>
          </div>
        </div>

        <div v-if="claimsLoading" class="empty-hint">加载中...</div>

        <div v-else-if="claimsTab === 'pending'">
          <div v-if="pendingClaims.length" class="claims-list">
            <div v-for="claim in pendingClaims" :key="claim.claimId" class="claim-item">
              <div class="claim-thumb">📄</div>
              <div class="claim-info" @click="claim.paperId && router.push(`/paper/${claim.paperId}`)">
                <div class="claim-title">{{ claim.title }}</div>
                <div class="claim-meta">{{ [claim.venue, claim.year].filter(Boolean).join(' · ') || '—' }}</div>
                <div class="claim-authors">{{ claim.authors }}</div>
              </div>
              <div class="claim-actions">
                <button class="btn primary sm" @click.stop="doConfirmClaim(claim.paperId)">确认</button>
                <button class="btn secondary sm" @click.stop="doDenyClaim(claim.paperId)">否认</button>
              </div>
            </div>
          </div>
          <div v-else class="empty-hint">没有待确认的论文</div>
        </div>

        <div v-else>
          <div v-if="confirmedClaims.length" class="claims-list">
            <div v-for="claim in confirmedClaims" :key="claim.claimId" class="claim-item"
                 @click="claim.paperId && router.push(`/paper/${claim.paperId}`)">
              <div class="claim-thumb">✅</div>
              <div class="claim-info">
                <div class="claim-title">{{ claim.title }}</div>
                <div class="claim-meta">{{ [claim.venue, claim.year].filter(Boolean).join(' · ') || '—' }}</div>
                <div class="claim-authors">{{ claim.authors }}</div>
              </div>
            </div>
          </div>
          <div v-else class="empty-hint">还没有已确认的论文</div>
        </div>
      </div>

      <div class="profile-card card animate-fade-up my-posts-card">
        <div class="card-header">
          <div class="card-title">
            <div class="card-icon">📝</div>
            我的帖子
          </div>
          <span class="post-count-badge" v-if="myPosts.length">共 {{ myPosts.length }} 篇</span>
        </div>

        <div v-if="myPostsLoading" class="empty-hint">加载中...</div>
        <div v-else-if="myPosts.length" class="myposts-list">
          <div v-for="post in pagedMyPosts" :key="post.id" class="mypost-item">
            <div class="mypost-info">
              <div class="mypost-title">{{ post.title || '(无标题)' }}</div>
              <div class="mypost-meta">
                <el-tag size="small" :type="post.statusName === 'APPROVED' ? 'success' : post.statusName === 'REJECTED' ? 'danger' : 'warning'">
                  {{ post.statusLabel }}
                </el-tag>
                <span class="mypost-time">{{ formatRelativeTime(post.createTime) }}</span>
              </div>
              <div class="mypost-content-preview">{{ post.content?.slice(0, 80) }}{{ post.content?.length > 80 ? '...' : '' }}</div>
            </div>
            <div class="mypost-actions">
              <button class="btn sm secondary" @click="openEditPostDialog(post)">编辑</button>
              <button class="btn sm danger" @click="doDeletePost(post)">删除</button>
            </div>
          </div>
          <div v-if="myPosts.length > myPostsPageSize" class="history-pagination">
            <el-pagination background :current-page="myPostsPage" :page-size="myPostsPageSize" :total="myPosts.length" layout="prev, pager, next" @current-change="myPostsPage = $event" />
          </div>
        </div>
        <div v-else class="empty-hint">还没有发布帖子</div>
      </div>

      <!-- Edit post dialog -->
      <div class="dialog-overlay" v-if="editPostVisible" @click.self="editPostVisible = false">
        <div class="dialog-card">
          <h3>编辑帖子</h3>
          <input v-model="editPostForm.title" class="dialog-input" placeholder="帖子标题（可选）" maxlength="200" />
          <textarea v-model="editPostForm.content" class="dialog-textarea" rows="5" placeholder="帖子内容" maxlength="5000"></textarea>
          <div class="dialog-actions">
            <button class="btn secondary" @click="editPostVisible = false">取消</button>
            <button class="btn primary" @click="doUpdatePost">保存</button>
          </div>
        </div>
      </div>

      <!-- Interests edit dialog -->
      <div class="dialog-overlay" v-if="interestsEditVisible" @click.self="interestsEditVisible = false">
        <div class="dialog-card">
          <h3>管理研究兴趣</h3>
          <p class="dialog-desc">用逗号分隔多个研究方向</p>
          <input v-model="interestsEditValue" class="dialog-input" placeholder="例如：深度学习, 强化学习, 计算机视觉" @keyup.enter="saveInterests" />
          <div class="dialog-actions">
            <button class="btn secondary" @click="interestsEditVisible = false">取消</button>
            <button class="btn primary" @click="saveInterests">保存</button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import Sidebar from '@/components/Sidebar.vue'
import { getProfile, updateProfile, getFavorites } from '@/api/user'
import { getActivityHistory, clearActivityHistory } from '@/api/recommend'
import { getClaimedPapers, confirmClaim, denyClaim } from '@/api/claim'
import { getMyPosts, updatePost, deletePost } from '@/api/community'
import { useUserStore } from '@/store/userStore'

const router = useRouter()
const userStore = useUserStore()

const profile = ref({ id: null, username: '', avatar: '', email: '', bio: '', researchInterests: '' })
const collectionsLoading = ref(false)
const historyLoading = ref(false)

const collections = ref([])
const collectionsPage = ref(1)
const collectionsPageSize = ref(4)
const pagedCollections = computed(() => {
  const start = (collectionsPage.value - 1) * collectionsPageSize.value
  return collections.value.slice(start, start + collectionsPageSize.value)
})
const history = ref([])
const historyPage = ref(1)
const historyPageSize = ref(4)
const claimsLoading = ref(false)
const pendingClaims = ref([])
const confirmedClaims = ref([])
const claimsTab = ref('pending')
const myPostsLoading = ref(false)
const myPosts = ref([])
const myPostsPage = ref(1)
const myPostsPageSize = ref(4)
const editPostVisible = ref(false)
const editingPost = ref(null)
const editPostForm = ref({ title: '', content: '' })
const pagedMyPosts = computed(() => {
  const start = (myPostsPage.value - 1) * myPostsPageSize.value
  return myPosts.value.slice(start, start + myPostsPageSize.value)
})
const pagedHistory = computed(() => {
  const start = (historyPage.value - 1) * historyPageSize.value
  return history.value.slice(start, start + historyPageSize.value)
})
const interestsEditVisible = ref(false)
const interestsEditValue = ref('')

async function fetchFavorites() {
  collectionsLoading.value = true
  try {
    const res = await getFavorites()
    const data = res.data || res
    collections.value = (data || []).map(p => ({
      id: p.id,
      title: p.title || 'Untitled',
      meta: [p.authors, p.venue, p.year].filter(Boolean).join(' · ') || '—'
    }))
  } catch (e) {
    console.debug('Failed to load favorites', e)
    collections.value = []
  } finally {
    collectionsLoading.value = false
  }
}

async function fetchHistory() {
  historyLoading.value = true
  try {
    const res = await getActivityHistory(20)
    const data = res.data || res
    const actionIcons = { click: '👁️', favorite: '⭐', read: '📖' }
    const actionLabels = { click: '浏览了', favorite: '收藏了', read: '阅读了' }
    history.value = (data || []).map(item => {
      const action = item.action || 'click'
      return {
        icon: actionIcons[action] || '📌',
        text: `${actionLabels[action] || '查看了'}《${item.paper_title || 'Unknown'}》`,
        time: formatRelativeTime(item.timestamp)
      }
    })
  } catch (e) {
    console.debug('Failed to load history', e)
    history.value = []
  } finally {
    historyLoading.value = false
  }
}

async function fetchClaims(status) {
  try {
    const res = await getClaimedPapers(status)
    const data = res.data || res
    if (status === 0) {
      pendingClaims.value = data || []
    } else {
      confirmedClaims.value = data || []
    }
  } catch (e) {
    console.debug('Failed to load claims', e)
  }
}

async function fetchAllClaims() {
  claimsLoading.value = true
  try {
    await Promise.all([fetchClaims(0), fetchClaims(1)])
  } finally {
    claimsLoading.value = false
  }
}

async function doConfirmClaim(paperId) {
  try {
    await confirmClaim(paperId)
    ElMessage.success('已确认为您的研究成果')
    await fetchAllClaims()
  } catch (e) {
    ElMessage.error('操作失败，请重试')
  }
}

async function doDenyClaim(paperId) {
  try {
    await denyClaim(paperId)
    ElMessage.success('已否认')
    await fetchAllClaims()
  } catch (e) {
    ElMessage.error('操作失败，请重试')
  }
}

async function fetchMyPosts() {
  myPostsLoading.value = true
  try {
    const res = await getMyPosts()
    myPosts.value = (res.data || res) || []
  } catch (e) {
    console.debug('Failed to load my posts', e)
    myPosts.value = []
  } finally {
    myPostsLoading.value = false
  }
}

function openEditPostDialog(post) {
  editingPost.value = post
  editPostForm.value = { title: post.title || '', content: post.content || '' }
  editPostVisible.value = true
}

async function doUpdatePost() {
  if (!editingPost.value) return
  try {
    await updatePost(editingPost.value.id, {
      title: editPostForm.value.title?.trim() || null,
      content: editPostForm.value.content.trim(),
    })
    ElMessage.success('帖子已更新')
    editPostVisible.value = false
    editingPost.value = null
    await fetchMyPosts()
  } catch (e) {
    ElMessage.error('修改失败，请重试')
  }
}

async function doDeletePost(post) {
  try {
    await ElMessageBox.confirm('确定要删除这篇帖子吗？删除后无法恢复。', '确认删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deletePost(post.id)
    ElMessage.success('帖子已删除')
    await fetchMyPosts()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败，请重试')
    }
  }
}

function formatRelativeTime(timestamp) {
  if (!timestamp) return ''
  const now = Date.now()
  const then = new Date(timestamp).getTime()
  const diff = now - then
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}小时前`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}天前`
  return new Date(timestamp).toLocaleDateString()
}

function manageInterests() {
  interestsEditValue.value = profile.value.researchInterests || ''
  interestsEditVisible.value = true
}

async function saveInterests() {
  try {
    await updateProfile({ researchInterests: interestsEditValue.value })
    profile.value.researchInterests = interestsEditValue.value
    interestsEditVisible.value = false
    ElMessage.success('研究兴趣已更新')
  } catch (e) {
    ElMessage.error('保存失败，请重试')
  }
}

function viewAllCollections() {
  const el = document.querySelector('.collection-list')
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
}

async function doClearHistory() {
  try {
    await ElMessageBox.confirm('确定要清空所有活动记录吗？', '确认', { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' })
    await clearActivityHistory()
    history.value = []
    ElMessage.success('已清空')
  } catch (e) {
    if (e !== 'cancel') console.debug('Failed to clear history', e)
  }
}

function logout() {
  userStore.clearToken()
  ElMessage.success('已退出登录')
  router.push('/login')
}

onMounted(async () => {
  await Promise.allSettled([
    (async () => {
      try {
        const res = await getProfile()
        const data = res.data || res
        profile.value = { id: data.id, username: data.username, avatar: data.avatar, email: data.email, bio: data.bio, researchInterests: data.researchInterests }
      } catch (e) {
        console.debug('failed to load profile', e)
      }
    })(),
    fetchFavorites(),
    fetchHistory(),
    fetchAllClaims(),
    fetchMyPosts(),
  ])
})
</script>

<style scoped>
@import './Profile.css';
</style>
