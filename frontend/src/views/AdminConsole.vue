<template>
  <div class="admin-root">
    <div class="bg-animation"></div>
    <Sidebar />
    <main class="main-content">
      <header class="header">
        <div class="page-title">
          <h2>🛡️ 管理员后台</h2>
          <p>统一处理帖子审核、论文导入和账号权限管理。</p>
        </div>
      </header>

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
        </el-tab-pane>
      </el-tabs>
    </main>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import Sidebar from '@/components/Sidebar.vue'
import { getAdminPosts, importAdminPapers, updateAdminPostStatus } from '@/api/admin'
import { getAdminUsers, updateUserRole } from '@/api/user'

const activeTab = ref('posts')
const postStatusFilter = ref('')
const adminPosts = ref([])
const loadingPosts = ref(false)
const adminUsers = ref([])
const loadingUsers = ref(false)
const importingPapers = ref(false)
const roleDrafts = ref({})
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

onMounted(async () => {
  await Promise.all([loadPosts(), loadUsers()])
})

async function loadPosts() {
  loadingPosts.value = true
  try {
    const res = await getAdminPosts(postStatusFilter.value)
    adminPosts.value = res.data || []
  } finally {
    loadingPosts.value = false
  }
}

async function loadUsers() {
  loadingUsers.value = true
  try {
    const res = await getAdminUsers()
    adminUsers.value = res.data || []
    roleDrafts.value = Object.fromEntries(adminUsers.value.map(user => [user.id, user.role]))
  } finally {
    loadingUsers.value = false
  }
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

.main-content { margin-left: 260px; min-height: 100vh; padding: 30px 40px; color: var(--text-primary); }
.toolbar { display: flex; justify-content: flex-end; margin-bottom: 16px; }
.import-card { padding: 20px; border-radius: 16px; background: var(--bg-card); border: 1px solid var(--design-border); }
.import-tip { color: var(--text-secondary); line-height: 1.7; margin-bottom: 14px; }
.json-editor { width: 100%; border-radius: 12px; background: rgba(15, 23, 42, 0.45); border: 1px solid rgba(148, 163, 184, 0.2); color: var(--text-primary); padding: 14px; resize: vertical; }
.role-action { display: flex; gap: 10px; align-items: center; }

@media (max-width: 980px) {
  .main-content { margin-left: 0; padding: 18px; }
}
</style>
