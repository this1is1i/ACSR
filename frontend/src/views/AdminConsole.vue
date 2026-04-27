<template>
  <div class="admin-root">
    <Sidebar />
    <main class="main-content">
      <PageHeader
        eyebrow="Future Lab"
        title="管理员后台"
        description="先用驾驶舱总览建立治理态势，再无缝进入帖子审核、论文导入与账号权限工作流。"
      >
        <template #actions>
          <div class="admin-header-status">
            <article class="admin-header-status__item">
              <span>最近同步</span>
              <strong>{{ syncStatusLabel }}</strong>
            </article>
            <article class="admin-header-status__item">
              <span>待处理事项</span>
              <strong>{{ totalBacklog }} 项</strong>
            </article>
          </div>
        </template>
      </PageHeader>

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
              <p class="admin-operations__eyebrow">Operations Deck</p>
              <h2>执行面板</h2>
              <p>以下保留原有的后台操作流：筛选审核、提交导入、修改角色均继续走现有接口。</p>
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
                    <el-table-column label="操作" width="220">
                      <template #default="{ row }">
                        <el-button size="small" type="success" @click="updatePostStatus(row, 'APPROVED')">通过</el-button>
                        <el-button size="small" type="danger" @click="updatePostStatus(row, 'REJECTED')">驳回</el-button>
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
              </el-tab-pane>

            <el-tab-pane label="论文导入" name="papers">
              <div class="import-card">
                <p class="import-tip">输入 JSON 数组，字段支持：<code>aminerId</code>、<code>title</code>、<code>abstract</code>、<code>authors</code>、<code>keywords</code>、<code>venue</code>、<code>year</code>、<code>citationCount</code>。</p>
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
          </el-tabs>
        </section>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import Sidebar from '@/components/Sidebar.vue'
import AdminCockpitHero from '@/components/admin/AdminCockpitHero.vue'
import AdminKpiGrid from '@/components/admin/AdminKpiGrid.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import { getAdminPosts, importAdminPapers, updateAdminPostStatus } from '@/api/admin'
import { getAdminUsers, updateUserRole } from '@/api/user'

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
const lastSyncedAt = ref(null)
const lastImportSummary = ref(null)
const paperImportText = ref(`[
  {
    "aminerId": "manual_demo_001",
    "title": "A Demo Imported Paper",
    "abstract": "This paper is imported from the admin console.",
    "authors": ["Admin User"],
    "keywords": ["demo", "admin import"],
    "venue": "Internal Workshop",
    "year": 2026,
    "citationCount": 0
  }
]`)

const dashboardLoading = computed(() => loadingPosts.value || loadingUsers.value)
const postCounts = computed(() => adminPostOverview.value.reduce((summary, post) => {
  if (post.status === 'PENDING') summary.pending += 1
  if (post.status === 'APPROVED') summary.approved += 1
  if (post.status === 'REJECTED') summary.rejected += 1
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
  `现有后台接口保持不变：已加载 ${adminUsers.value.length} 个账号与 ${adminPostOverview.value.length} 条帖子状态，导入面板继续复用当前 JSON 提交流程。`
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
  {
    label: '导入准备度',
    value: paperDraftState.value.isValid ? '可执行' : '待修正',
    caption: paperDraftState.value.isValid ? '继续使用现有导入接口' : paperDraftState.value.message,
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
  {
    label: '导入载荷',
    value: paperDraftState.value.isValid ? `${paperDraftState.value.count} 篇` : '待修正',
    caption: lastImportSummary.value
      ? `上次成功导入 ${lastImportSummary.value.count} 篇`
      : '继续通过现有 /admin/papers/import 提交',
    tone: paperDraftState.value.isValid ? 'success' : 'danger',
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

function focusTab(tabName) {
  activeTab.value = tabName
  nextTick(() => {
    operationsSection.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  })
}

async function updatePostStatus(row, status) {
  const reviewComment = await ElMessageBox.prompt(
    status === 'REJECTED' ? '请输入驳回原因' : '可选填写审核备注',
    status === 'REJECTED' ? '驳回帖子' : '通过帖子',
    {
      inputValue: row.reviewComment || '',
      confirmButtonText: '确认',
      cancelButtonText: '取消',
    }
  ).then(result => result.value).catch(() => null)

  if (reviewComment === null) return

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
</script>

<style scoped>
@import '@/style.css';

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
  background: rgba(255, 255, 255, 0.04);
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
  background: rgba(15, 23, 42, 0.45);
  border: 1px solid rgba(148, 163, 184, 0.2);
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
  --el-table-border-color: rgba(148, 163, 184, 0.18);
  --el-table-header-bg-color: rgba(15, 23, 42, 0.42);
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

@media (max-width: 680px) {
  .toolbar {
    justify-content: stretch;
  }

  .toolbar > * {
    width: 100%;
  }
}
</style>
