<template>
  <div class="admin-root page-root">
    <Sidebar />
    <main class="main-content">
      <AdminCockpitHero
        :headline="cockpitHeadline"
        :description="cockpitDescription"
        :chips="heroChips"
        :signals="heroSignals"
        :actions="dashboardActions"
        @select-tab="focusTab"
      />

      <AdminKpiGrid :items="kpiItems" :loading="dashboardLoading" />

        <div class="admin-workspace">
          <section ref="operationsSection" class="admin-operations card glass" data-testid="admin-operations">
            <div class="admin-operations__intro">
              <h2>执行面板</h2>
            </div>

            <el-tabs v-model="activeTab" class="admin-tabs">
              <el-tab-pane label="帖子审核" name="posts">
                <div class="toolbar">
                  <el-select v-model="postStatusFilter" placeholder="筛选状态" style="width: 180px" @change="loadPosts">
                    <el-option label="全部" value="" />
                    <el-option label="待审核" value="PENDING" />
                    <el-option label="已发布" value="APPROVED" />
                    <el-option label="已驳回" value="REJECTED" />
                  </el-select>
                </div>
                <div class="admin-table-wrap">
                  <el-table :data="adminPosts" v-loading="loadingPosts" border>
                    <el-table-column prop="title" label="标题" min-width="180" />
                    <el-table-column prop="author.username" label="作者" min-width="120" />
                    <el-table-column prop="statusLabel" label="状态" width="100" />
                    <el-table-column prop="reviewComment" label="审核备注" min-width="180" />
                    <el-table-column label="查看" width="80">
                      <template #default="{ row }">
                        <el-button size="small" text type="primary" @click="openPostPreview(row)">查看</el-button>
                      </template>
                    </el-table-column>
                    <el-table-column label="操作" width="220">
                      <template #default="{ row }">
                        <template v-if="row.status === 0 || row.status === 'PENDING'">
                          <el-button size="small" type="success" @click="updatePostStatus(row, 'APPROVED')">通过</el-button>
                          <el-button size="small" type="danger" @click="updatePostStatus(row, 'REJECTED')">驳回</el-button>
                        </template>
                        <template v-else>
                          <el-button size="small" type="warning" @click="updatePostStatus(row, 'PENDING')">撤回</el-button>
                        </template>
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
              </el-tab-pane>

            <el-tab-pane label="论文导入" name="papers">
              <div class="import-card">
                <p class="import-tip">输入 JSON 数组。<code>authors</code> 和 <code>keywords</code> 支持 JSON 数组或逗号分隔字符串。</p>
                <textarea v-model="paperImportText" class="json-editor" rows="16" />
                <div class="toolbar">
                  <el-button type="primary" :loading="importingPapers" @click="submitPaperImport">导入论文</el-button>
                </div>
              </div>
            </el-tab-pane>

            <el-tab-pane label="账号权限" name="users">
              <div class="admin-table-wrap">
                <el-table :data="adminUsers" v-loading="loadingUsers" border>
                  <el-table-column prop="username" label="用户名" min-width="120" />
                  <el-table-column prop="email" label="邮箱" min-width="180" />
                  <el-table-column prop="roleLabel" label="当前角色" width="120" />
                  <el-table-column prop="researchInterests" label="研究方向" min-width="180" />
                  <el-table-column label="修改角色" width="220">
                    <template #default="{ row }">
                      <div class="role-action">
                        <el-select v-model="roleDrafts[row.id]" style="width: 130px">
                          <el-option label="学生" value="STUDENT" />
                          <el-option label="研究者" value="RESEARCHER" />
                          <el-option label="管理员" value="ADMIN" />
                        </el-select>
                        <el-button size="small" type="primary" @click="saveUserRole(row)">保存</el-button>
                      </div>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </el-tab-pane>

            <el-tab-pane label="模型训练" name="training">
              <div class="training-card">
                <p class="import-tip">触发 Python 侧 Actor-Critic 模型训练。训练在后台异步执行，完成后自动热重载模型权重并写入训练日志。</p>
                <div class="toolbar" style="justify-content: flex-start; gap: 16px; align-items: flex-end;">
                  <div>
                    <label style="display:block;font-size:13px;color:var(--text-secondary);margin-bottom:6px;">训练轮数（留空使用默认 300 轮）</label>
                    <el-input-number v-model="trainingEpisodes" :min="1" :max="2000" placeholder="300" style="width: 200px" />
                  </div>
                  <el-button type="primary" :loading="trainingLoading" :disabled="trainingPolling" @click="doTriggerTraining">
                    {{ trainingPolling ? '训练中...' : '实时训练' }}
                  </el-button>
                </div>
                <div v-if="trainingStatusText" class="training-status">{{ trainingStatusText }}</div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </section>
      </div>

      <el-dialog v-model="postPreviewVisible" title="帖子内容预览" width="640px">
        <div v-if="previewPost" class="post-preview">
          <div class="post-preview__meta">
            <span class="post-preview__author">作者：{{ previewPost.author?.username || '未知' }}</span>
            <el-tag size="small">{{ previewPost.statusLabel }}</el-tag>
          </div>
          <h3 class="post-preview__title">{{ previewPost.title }}</h3>
          <div class="post-preview__content">{{ previewPost.content }}</div>
        </div>
      </el-dialog>

      <el-dialog v-model="trainingResultVisible" title="训练完成" width="480px">
        <div v-if="trainingResult" class="training-result">
          <div class="result-row"><span class="result-label">最优奖励 (Best Reward)</span> <strong>{{ trainingResult.best_reward?.toFixed(4) }}</strong></div>
          <div class="result-row"><span class="result-label">训练轮数</span> <strong>{{ trainingResult.last_episode }}</strong></div>
          <div class="result-row"><span class="result-label">模型版本</span> <strong>{{ trainingResult.model_version }}</strong></div>
          <div class="result-row"><span class="result-label">训练耗时</span> <strong>{{ trainingDuration }}</strong></div>
        </div>
      </el-dialog>
    </main>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import Sidebar from '@/components/Sidebar.vue'
import AdminCockpitHero from '@/components/admin/AdminCockpitHero.vue'
import AdminKpiGrid from '@/components/admin/AdminKpiGrid.vue'
import { getAdminPosts, importAdminPapers, updateAdminPostStatus } from '@/api/admin'
import { getAdminUsers, updateUserRole } from '@/api/user'
import { triggerTraining, getModelInfo } from '@/api/recommend'

const activeTab = ref('posts')
const postStatusFilter = ref('')
const adminPosts = ref([])
const adminPostOverview = ref([])
const loadingPosts = ref(false)
const adminUsers = ref([])
const loadingUsers = ref(false)
const importingPapers = ref(false)
const roleDrafts = ref({})
const operationsSection = ref(null)
const postPreviewVisible = ref(false)
const previewPost = ref(null)
const lastSyncedAt = ref(null)
const lastImportSummary = ref(null)
const trainingEpisodes = ref(null)
const trainingLoading = ref(false)
const trainingPolling = ref(false)
const trainingStatusText = ref('')
const trainingResultVisible = ref(false)
const trainingResult = ref(null)
const trainingDuration = ref('')
let trainingPollTimer = null
let trainingStartTime = null
const paperImportText = ref(`[
  {
    "aminerId": "aminer_999",
    "title": "A Survey of Graph Neural Networks for Recommendation",
    "abstract": "Graph Neural Networks have emerged as a powerful paradigm...",
    "authors": ["Zhang San", "Li Si"],
    "keywords": ["Graph Neural Networks", "Recommender Systems"],
    "venue": "WWW 2025",
    "year": 2025,
    "citationCount": 42
  }
]`)

const dashboardLoading = computed(() => loadingPosts.value || loadingUsers.value)
const postCounts = computed(() => adminPostOverview.value.reduce((summary, post) => {
  if (post.statusName === 'PENDING') summary.pending += 1
  if (post.statusName === 'APPROVED') summary.approved += 1
  if (post.statusName === 'REJECTED') summary.rejected += 1
  return summary
}, { pending: 0, approved: 0, rejected: 0 }))
const roleCounts = computed(() => adminUsers.value.reduce((summary, user) => {
  const role = user.role || 'UNKNOWN'
  summary[role] = (summary[role] || 0) + 1
  return summary
}, { ADMIN: 0, RESEARCHER: 0, STUDENT: 0 }))
const pendingRoleChanges = computed(() => adminUsers.value.filter(user => (
  roleDrafts.value[user.id] && roleDrafts.value[user.id] !== user.role
)).length)
const paperDraftState = computed(() => {
  try {
    const parsed = JSON.parse(paperImportText.value)
    return {
      isValid: Array.isArray(parsed),
      count: Array.isArray(parsed) ? parsed.length : 0,
      message: Array.isArray(parsed) ? '导入载荷已就绪' : '需使用 JSON 数组',
    }
  } catch {
    return {
      isValid: false,
      count: 0,
      message: 'JSON 语法需要修正',
    }
  }
})
const totalBacklog = computed(() => postCounts.value.pending + pendingRoleChanges.value)
const syncStatusLabel = computed(() => (
  lastSyncedAt.value
    ? `已于 ${lastSyncedAt.value.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })} 更新`
    : '等待同步'
))
const cockpitHeadline = computed(() => (
  postCounts.value.pending
    ? `当前有 ${postCounts.value.pending} 条帖子待审核，建议先处理内容发布风险，再切换到导入与权限治理。`
    : '审核队列已稳定，可直接关注论文导入节奏与账号权限矩阵。'
))
const cockpitDescription = computed(() => (
  `已加载 ${adminUsers.value.length} 个账号与 ${adminPostOverview.value.length} 条帖子`
))
const heroChips = computed(() => ([
  `${postCounts.value.pending} 条待审核帖子`,
  paperDraftState.value.isValid ? `${paperDraftState.value.count} 篇导入草稿` : paperDraftState.value.message,
  `${roleCounts.value.ADMIN || 0} 位管理员值守`,
]))
const heroSignals = computed(() => ([
  {
    label: '待处理事项',
    value: `${totalBacklog.value} 项`,
    caption: postCounts.value.pending ? '优先清理审核队列' : '当前没有新增阻塞项',
  },
  {
    label: '内容态势',
    value: postCounts.value.pending ? '审核高峰' : '队列平稳',
    caption: `已发布 ${postCounts.value.approved} · 已驳回 ${postCounts.value.rejected}`,
  },
]))
const dashboardActions = computed(() => ([
  {
    tab: 'posts',
    label: '进入帖子审核',
    detail: postCounts.value.pending ? `${postCounts.value.pending} 条待处理` : '查看审核历史',
  },
  {
    tab: 'papers',
    label: '进入论文导入',
    detail: paperDraftState.value.isValid ? `${paperDraftState.value.count} 篇草稿已就绪` : paperDraftState.value.message,
  },
  {
    tab: 'users',
    label: '进入账号权限',
    detail: pendingRoleChanges.value ? `${pendingRoleChanges.value} 项角色变更待保存` : '查看当前角色矩阵',
  },
]))
const kpiItems = computed(() => ([
  {
    label: '待审核帖子',
    value: `${postCounts.value.pending} 条`,
    caption: '优先处理发布前的内容与备注校验',
    tone: postCounts.value.pending ? 'danger' : 'accent',
  },
  {
    label: '已发布帖子',
    value: `${postCounts.value.approved} 条`,
    caption: '已通过审核并处于线上展示状态',
    tone: 'success',
  },
  {
    label: '在管账号',
    value: `${adminUsers.value.length} 个`,
    caption: `管理员 ${roleCounts.value.ADMIN || 0} · 研究者 ${roleCounts.value.RESEARCHER || 0} · 学生 ${roleCounts.value.STUDENT || 0}`,
    tone: 'accent',
  },
]))
onMounted(async () => {
  await Promise.all([loadPosts(), loadUsers()])
})

async function loadPosts() {
  loadingPosts.value = true
  try {
    const res = await getAdminPosts(postStatusFilter.value)
    adminPosts.value = res.data || []
    if (!postStatusFilter.value) {
      adminPostOverview.value = adminPosts.value
    }
    lastSyncedAt.value = new Date()
  } finally {
    loadingPosts.value = false
  }
}

async function loadPostOverview() {
  const res = await getAdminPosts()
  adminPostOverview.value = res.data || []
  lastSyncedAt.value = new Date()
}

async function loadUsers() {
  loadingUsers.value = true
  try {
    const res = await getAdminUsers()
    adminUsers.value = res.data || []
    roleDrafts.value = Object.fromEntries(adminUsers.value.map(user => [user.id, user.role]))
    lastSyncedAt.value = new Date()
  } finally {
    loadingUsers.value = false
  }
}

function openPostPreview(row) {
  previewPost.value = row
  postPreviewVisible.value = true
}

function focusTab(tabName) {
  activeTab.value = tabName
  nextTick(() => {
    operationsSection.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  })
}

async function updatePostStatus(row, status) {
  let reviewComment = ''
  if (status !== 'PENDING') {
    reviewComment = await ElMessageBox.prompt(
      status === 'REJECTED' ? '请输入驳回原因' : '可选填写审核备注',
      status === 'REJECTED' ? '驳回帖子' : '通过帖子',
      {
        inputValue: row.reviewComment || '',
        confirmButtonText: '确认',
        cancelButtonText: '取消',
      }
    ).then(result => result.value).catch(() => null)

    if (reviewComment === null) return
  }

  await updateAdminPostStatus(row.id, { status, reviewComment })
  ElMessage.success('帖子状态已更新')
  await loadPosts()

  if (postStatusFilter.value) {
    const [overviewRefresh] = await Promise.allSettled([loadPostOverview()])
    if (overviewRefresh.status === 'rejected') {
      ElMessage.warning('帖子状态已更新，总览同步稍后重试')
    }
  }
}

async function submitPaperImport() {
  let parsed
  try {
    parsed = JSON.parse(paperImportText.value)
  } catch {
    ElMessage.error('请输入合法的 JSON 数组')
    return
  }

  // Normalize: convert comma-separated string fields to arrays
  if (Array.isArray(parsed)) {
    parsed = parsed.map(p => ({
      ...p,
      authors: typeof p.authors === 'string'
        ? p.authors.split(',').map(s => s.trim()).filter(Boolean)
        : (p.authors || []),
      keywords: typeof p.keywords === 'string'
        ? p.keywords.split(',').map(s => s.trim()).filter(Boolean)
        : (p.keywords || [])
    }))
  }

  importingPapers.value = true
  try {
    const res = await importAdminPapers({ papers: parsed })
    lastImportSummary.value = {
      count: res.data?.importedCount || 0,
      at: new Date(),
    }
    ElMessage.success(`成功导入 ${res.data?.importedCount || 0} 篇论文`)
  } finally {
    importingPapers.value = false
  }
}

async function saveUserRole(user) {
  await updateUserRole(user.id, { role: roleDrafts.value[user.id] })
  ElMessage.success('用户角色已更新')
  await loadUsers()
}

async function doTriggerTraining() {
  trainingLoading.value = true
  try {
    const res = await triggerTraining(trainingEpisodes.value || undefined)
    if (res.code === 0 || res.data) {
      ElMessage.success('训练已在后台启动')
      trainingStartTime = Date.now()
      startTrainingPoll()
    } else {
      ElMessage.error(res.message || '触发训练失败')
    }
  } catch (e) {
    ElMessage.error('触发训练失败，请检查 Python 推荐服务是否运行')
  } finally {
    trainingLoading.value = false
  }
}

function startTrainingPoll() {
  trainingPolling.value = true
  trainingStatusText.value = '模型训练中，请稍候...'
  trainingPollTimer = setInterval(async () => {
    try {
      const res = await getModelInfo()
      const info = res.data || res
      if (info && !info.is_training) {
        clearInterval(trainingPollTimer)
        trainingPollTimer = null
        trainingPolling.value = false
        trainingStatusText.value = ''
        const elapsed = Math.round((Date.now() - trainingStartTime) / 1000)
        const mins = Math.floor(elapsed / 60)
        const secs = elapsed % 60
        trainingDuration.value = `${mins}分${secs}秒`
        trainingResult.value = info
        trainingResultVisible.value = true
        ElMessage.success('模型训练完成，权重已热重载')
      }
    } catch {
      // 静默重试
    }
  }, 2000)
}
</script>

<style scoped>
.main-content {
  display: grid;
  gap: var(--space-6);
}

.admin-header-status {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
}

.admin-header-status__item {
  display: grid;
  gap: 0.2rem;
  min-width: 9rem;
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  background: var(--bg-hover);
}

.admin-header-status__item span {
  color: var(--color-text-secondary);
}

.admin-header-status__item strong,
.admin-operations__intro h2 {
  color: var(--color-text-primary);
}

.admin-workspace {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
}

.admin-operations {
  display: grid;
  gap: var(--space-5);
  min-width: 0;
  padding: clamp(1.25rem, 2vw, 1.65rem);
}

.admin-operations__intro {
  display: grid;
  gap: var(--space-2);
}

.admin-operations__eyebrow {
  font-size: 0.78rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--color-accent-secondary);
}

.toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 16px;
}

.import-card {
  padding: 20px;
  border-radius: 16px;
  background: var(--bg-card);
  border: 1px solid var(--design-border);
}

.import-tip {
  color: var(--text-secondary);
  line-height: 1.7;
  margin-bottom: 14px;
}

.json-editor {
  width: 100%;
  border-radius: 12px;
  background: var(--bg-card);
  border: 1px solid var(--design-border);
  color: var(--text-primary);
  padding: 14px;
  resize: vertical;
}

.role-action {
  display: flex;
  gap: 10px;
  align-items: center;
}

.admin-table-wrap {
  max-width: 100%;
  overflow-x: auto;
}

:deep(.admin-tabs .el-tabs__header) {
  margin-bottom: var(--space-5);
}

:deep(.admin-tabs .el-tabs__item) {
  color: var(--color-text-secondary);
}

:deep(.admin-tabs .el-tabs__item.is-active) {
  color: var(--color-text-primary);
}

:deep(.admin-tabs .el-tabs__active-bar) {
  background: linear-gradient(135deg, var(--primary), var(--accent));
}

:deep(.admin-tabs .el-table) {
  --el-table-border-color: var(--color-border-subtle);
  --el-table-header-bg-color: var(--bg-hover);
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-text-color: var(--color-text-primary);
  --el-table-header-text-color: var(--color-text-secondary);
  min-width: 760px;
}

@media (max-width: 1180px) {
  .admin-workspace {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 980px) {
  .admin-header-status {
    width: 100%;
  }
}

.post-preview__meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.post-preview__author {
  color: var(--color-text-secondary, #94a3b8);
  font-size: 14px;
}
.post-preview__title {
  font-size: 18px;
  margin-bottom: 16px;
  color: var(--color-text-primary, #f8fafc);
}
.post-preview__content {
  padding: 16px;
  border-radius: 8px;
  background: var(--bg-hover);
  color: var(--color-text-secondary);
  line-height: 1.8;
  white-space: pre-wrap;
  max-height: 400px;
  overflow-y: auto;
}

@media (max-width: 680px) {
  .toolbar {
    justify-content: stretch;
  }

  .toolbar > * {
    width: 100%;
  }
}

.training-card {
  padding: 20px;
  border-radius: 16px;
  background: var(--bg-card);
  border: 1px solid var(--design-border);
}
.training-status {
  margin-top: 16px;
  padding: 10px 14px;
  border-radius: 10px;
  background: rgba(99,102,241,0.1);
  color: #6366f1;
  font-size: 13px;
}
.training-result .result-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid var(--design-border);
}
.training-result .result-row:last-child {
  border-bottom: none;
}
.result-label {
  color: var(--text-secondary);
  font-size: 14px;
}
</style>
