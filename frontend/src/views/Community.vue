<template>
  <div class="community-root" data-testid="community-collaboration-workspace">
    <div class="bg-animation"></div>
    <Sidebar />
    <main class="main-content">
      <PageHeader
        eyebrow="Future Lab"
        title="科研社区工作台"
        description="聚焦帖子、评论与审核后的社区互动，不再让说明性设计卡片占据主界面。"
      />

      <div class="workspace-grid">
        <section class="workspace-main">
          <section class="post-creator card">
            <div class="creator-header">
              <div class="creator-avatar">{{ userStore.userInfo?.username?.charAt(0)?.toUpperCase() || 'U' }}</div>
              <div class="creator-form">
                <input v-model="postForm.title" class="creator-title" placeholder="帖子标题（可选）" maxlength="200" />
                <textarea
                  v-model="postForm.content"
                  class="creator-input"
                  rows="4"
                  maxlength="5000"
                  placeholder="分享你的科研观点、论文推荐或研究心得..."
                />
                <input v-model="postForm.paperId" class="creator-title" placeholder="关联论文 ID（可选）" />
              </div>
            </div>
            <div class="creator-actions">
              <span class="creator-hint">{{ publishHint }}</span>
              <button class="post-btn btn" :disabled="submitting" @click="submitPost">
                {{ submitting ? '提交中...' : '发布动态' }}
              </button>
            </div>
          </section>

          <section class="feed-section">
            <div class="feed-tabs">
              <button class="feed-tab" :class="{ active: activeTab === 'latest' }" @click="activeTab = 'latest'">最新</button>
              <button class="feed-tab" :class="{ active: activeTab === 'hot' }" @click="activeTab = 'hot'">热门</button>
            </div>

            <div v-if="loading" class="empty-state">社区内容加载中...</div>
            <div v-else-if="!posts.length" class="empty-state">还没有社区帖子，发一条试试。</div>

            <article v-for="post in posts" :key="post.id" class="post-card">
              <div class="post-header">
                <div class="post-author">
                  <div class="author-avatar">{{ post.author?.username?.charAt(0)?.toUpperCase() || 'U' }}</div>
                  <div class="author-info">
                    <h4>{{ post.author?.username || '未知用户' }}</h4>
                    <p>{{ post.author?.roleLabel || '' }}</p>
                  </div>
                </div>
                <div class="post-meta">
                  <el-tag size="small" :type="statusTagType(post.statusName)">{{ post.statusLabel }}</el-tag>
                  <span class="post-time">{{ formatTime(post.createTime) }}</span>
                </div>
              </div>

              <h3 v-if="post.title" class="post-title">{{ post.title }}</h3>
              <div class="post-content">{{ post.content }}</div>

              <div v-if="post.paper" class="post-paper">
                <div class="paper-title-small">📄 {{ post.paper.title }}</div>
                <div class="paper-meta-small">
                  {{ post.paper.venue || '未指定 venue' }} · {{ post.paper.year || '未知年份' }} · 被引 {{ post.paper.citationCount || 0 }}
                </div>
              </div>

              <div v-if="post.reviewComment && post.statusName !== 'APPROVED'" class="review-note">
                审核备注：{{ post.reviewComment }}
              </div>

              <div class="post-actions">
                <span class="post-stat">回复 {{ post.replyCount }}</span>
                <span class="post-stat">点赞 {{ post.likeCount }}</span>
                <button class="comment-btn" @click="openComments(post)">查看评论</button>
              </div>
            </article>
          </section>
        </section>
      </div>
    </main>

    <el-dialog v-model="commentDialogVisible" width="720px" destroy-on-close>
      <template #title>
        <div class="dialog-title">
          <div>{{ selectedPost?.title || '帖子评论' }}</div>
          <span class="dialog-subtitle">{{ selectedPost?.author?.username || '' }}</span>
        </div>
      </template>

      <div class="comment-panel">
        <div v-if="commentsLoading" class="empty-state">评论加载中...</div>
        <div v-else-if="!comments.length" class="empty-state">还没有评论，来发表第一条回复。</div>

        <CommunityCommentTree
          v-for="comment in comments"
          :key="comment.id"
          :comment="comment"
          @reply="setReplyTarget"
        />

        <div class="comment-editor">
          <div v-if="replyTarget" class="reply-target">
            正在回复 {{ replyTarget.author?.username || '该用户' }}
            <button class="clear-reply" @click="replyTarget = null">取消</button>
          </div>
          <textarea
            v-model="commentForm.content"
            class="creator-input"
            rows="3"
            maxlength="2000"
            placeholder="写下你的评论..."
          />
          <div class="comment-submit">
            <button class="post-btn btn" :disabled="commentSubmitting" @click="submitComment">
              {{ commentSubmitting ? '提交中...' : '发表评论' }}
            </button>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import Sidebar from '@/components/Sidebar.vue'
import CommunityCommentTree from '@/components/CommunityCommentTree.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import { createCommunityPost, createPostComment, getCommunityPosts, getPostComments } from '@/api/community'
import { useUserStore } from '@/store/userStore'

const userStore = useUserStore()
const activeTab = ref('latest')
const loading = ref(false)
const submitting = ref(false)
const commentDialogVisible = ref(false)
const commentsLoading = ref(false)
const commentSubmitting = ref(false)
const selectedPost = ref(null)
const posts = ref([])
const comments = ref([])
const replyTarget = ref(null)
const postForm = ref({
  title: '',
  content: '',
  paperId: '',
})
const commentForm = ref({
  content: '',
})

const publishHint = computed(() => {
  switch (userStore.userInfo?.role) {
    case 'ADMIN':
      return '管理员发布的帖子将直接公开。'
    case 'RESEARCHER':
      return '研究者发布的帖子将直接公开。'
    default:
      return '学生用户发帖后将进入管理员审核队列。'
  }
})

watch(activeTab, () => {
  loadPosts()
})

onMounted(async () => {
  if (!userStore.userInfo) {
    try {
      await userStore.fetchProfile()
    } catch {
      // handled globally
    }
  }
  loadPosts()
})

async function loadPosts() {
  loading.value = true
  try {
    const res = await getCommunityPosts(activeTab.value)
    posts.value = res.data || []
  } finally {
    loading.value = false
  }
}

async function submitPost() {
  if (!postForm.value.content.trim()) {
    ElMessage.warning('请输入帖子内容')
    return
  }

  submitting.value = true
  try {
    const payload = {
      title: postForm.value.title?.trim() || null,
      content: postForm.value.content.trim(),
      paperId: postForm.value.paperId ? Number(postForm.value.paperId) : null,
    }
    const res = await createCommunityPost(payload)
    postForm.value = { title: '', content: '', paperId: '' }
    ElMessage.success(res.data?.statusName === 'PENDING' ? '帖子已提交审核' : '帖子已发布')
    await loadPosts()
  } finally {
    submitting.value = false
  }
}

async function openComments(post) {
  selectedPost.value = post
  replyTarget.value = null
  commentForm.value.content = ''
  commentDialogVisible.value = true
  await loadComments(post.id)
}

async function loadComments(postId) {
  commentsLoading.value = true
  try {
    const res = await getPostComments(postId)
    comments.value = res.data || []
  } finally {
    commentsLoading.value = false
  }
}

function setReplyTarget(comment) {
  replyTarget.value = comment
}

async function submitComment() {
  if (!selectedPost.value) return
  if (!commentForm.value.content.trim()) {
    ElMessage.warning('请输入评论内容')
    return
  }

  commentSubmitting.value = true
  try {
    await createPostComment(selectedPost.value.id, {
      content: commentForm.value.content.trim(),
      parentId: replyTarget.value?.id || null,
    })
    commentForm.value.content = ''
    replyTarget.value = null
    await loadComments(selectedPost.value.id)
    await loadPosts()
  } finally {
    commentSubmitting.value = false
  }
}

function statusTagType(status) {
  if (status === 'APPROVED') return 'success'
  if (status === 'REJECTED') return 'danger'
  return 'warning'
}

function formatTime(value) {
  if (!value) return ''
  return new Date(value).toLocaleString()
}
</script>

<style scoped>
@import '@/style.css';

.main-content { margin-left: 260px; min-height: 100vh; padding: 30px 40px; color: var(--text-primary); }
.workspace-grid { display: grid; grid-template-columns: minmax(0, 1fr); gap: 24px; align-items: start; }
.workspace-main { min-width: 0; }
.post-creator,
.post-card { padding: 20px; border-radius: 16px; background: var(--bg-card); border: 1px solid var(--design-border); margin-bottom: 18px; }
.creator-header { display: flex; gap: 14px; align-items: flex-start; }
.creator-avatar,
.author-avatar { width: 48px; height: 48px; display: flex; align-items: center; justify-content: center; border-radius: 50%; background: linear-gradient(135deg, #6366f1, #8b5cf6); color: #fff; font-weight: 700; }
.creator-form { flex: 1; display: flex; flex-direction: column; gap: 10px; }
.creator-title,
.creator-input { width: 100%; border-radius: 10px; border: 1px solid rgba(148, 163, 184, 0.2); background: rgba(15, 23, 42, 0.45); color: var(--text-primary); padding: 12px 14px; }
.creator-input { resize: vertical; min-height: 100px; }
.creator-actions,
.post-actions,
.comment-submit { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-top: 14px; }
.creator-hint,
.post-time,
.post-stat,
.dialog-subtitle { color: var(--text-secondary); font-size: 13px; }
.feed-tabs { display: flex; gap: 10px; margin-bottom: 16px; }
.feed-tab { padding: 8px 12px; border-radius: 8px; background: transparent; border: 1px solid var(--design-border); color: var(--text-secondary); cursor: pointer; }
.feed-tab.active { background: linear-gradient(90deg, var(--primary), var(--secondary)); color: white; }
.post-header { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; }
.post-author { display: flex; gap: 12px; align-items: center; }
.post-meta { display: flex; gap: 10px; align-items: center; }
.author-info p,
.paper-meta-small,
.review-note { color: var(--text-secondary); font-size: 13px; }
.post-title { margin: 14px 0 8px; font-size: 20px; }
.post-content { white-space: pre-wrap; line-height: 1.7; }
.post-paper,
.review-note,
.reply-target { margin-top: 14px; padding: 12px; border-radius: 10px; background: rgba(99, 102, 241, 0.08); border: 1px solid rgba(99, 102, 241, 0.15); }
.comment-btn,
.clear-reply { background: transparent; border: 1px solid rgba(99, 102, 241, 0.35); color: var(--primary); padding: 6px 12px; border-radius: 8px; cursor: pointer; }
.empty-state { padding: 24px; text-align: center; color: var(--text-secondary); }
.dialog-title { display: flex; flex-direction: column; gap: 4px; }
.comment-panel { max-height: 70vh; overflow: auto; }
.comment-editor { margin-top: 16px; }

@media (max-width: 1180px) {
  .workspace-grid { grid-template-columns: 1fr; }
}

@media (max-width: 980px) {
  .main-content { margin-left: 0; padding: 18px; }
}
</style>
