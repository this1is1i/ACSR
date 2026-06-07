<template>
  <div class="edit-root">
    <Sidebar />
    <main class="main-content">
      <!-- 基本信息卡片 -->
      <section class="edit-section card">
        <h3>编辑资料</h3>
        <form @submit.prevent="save">
          <div class="form-row">
            <label>用户名</label>
            <input type="text" v-model="form.username" disabled />
          </div>
          <div class="form-row">
            <label>邮箱</label>
            <input type="email" v-model="form.email" placeholder="请输入邮箱地址" />
          </div>
          <div class="form-row">
            <label>头像</label>
            <div class="avatar-upload">
              <div class="avatar-preview" @click="triggerFileInput" :title="uploading ? '上传中...' : '点击上传头像'">
                <img v-if="previewUrl" :src="previewUrl" alt="avatar" class="avatar-img" />
                <span v-else class="avatar-placeholder">{{ form.username ? form.username.charAt(0) : 'U' }}</span>
                <div class="avatar-overlay" v-if="!uploading">
                  <span>📷</span>
                </div>
                <div class="avatar-overlay uploading" v-else>
                  <span>⏳</span>
                </div>
              </div>
              <input ref="fileInput" type="file" accept="image/*" @change="onFileChange" hidden />
              <div class="avatar-actions">
                <button type="button" class="btn secondary btn-sm" @click="triggerFileInput" :disabled="uploading">
                  {{ uploading ? '上传中...' : '选择图片' }}
                </button>
                <span class="avatar-hint">支持 JPG/PNG，建议 200x200</span>
              </div>
            </div>
          </div>
          <div class="form-row">
            <label>个人简介</label>
            <textarea v-model="form.bio" rows="4" placeholder="介绍一下你的研究方向与兴趣..."></textarea>
          </div>
          <div class="form-row">
            <label>研究方向（点击选择）</label>
            <div v-if="keywordsLoading" class="tags-loading">加载关键词中...</div>
            <div v-else class="tags-container">
              <button
                v-for="kw in hotKeywords" :key="kw.label"
                type="button" class="tag-pill"
                :class="{ selected: selectedKeywords.includes(kw.label) }"
                @click="toggleKeyword(kw.label)"
              >{{ kw.label }}</button>
              <button type="button" class="tag-pill tag-more" @click="dialogVisible = true">···</button>
            </div>
            <span class="interest-hint">已选: {{ selectedKeywords.length > 0 ? selectedKeywords.join(', ') : '无' }}</span>
          </div>

          <el-dialog v-model="dialogVisible" title="选择研究方向" width="560px" :z-index="3000">
            <div class="dialog-search">
              <input v-model="keywordSearch" placeholder="搜索关键词..." class="search-input" />
            </div>
            <div class="dialog-tags">
              <button
                v-for="kw in filteredKeywords" :key="kw.label"
                type="button" class="tag-pill dialog-pill"
                :class="{ selected: selectedKeywords.includes(kw.label) }"
                @click="toggleKeyword(kw.label)"
              >{{ kw.label }} <span class="freq">{{ kw.frequency }}</span></button>
            </div>
            <div v-if="filteredKeywords.length === 0" class="dialog-empty">无匹配关键词</div>
          </el-dialog>
          <div class="form-actions">
            <button type="button" class="btn secondary" @click="$router.back()">取消</button>
            <button type="submit" class="btn primary" :disabled="uploading">保存</button>
          </div>
        </form>
      </section>

      <!-- 修改密码卡片 -->
      <section class="edit-section card">
        <h3>修改密码</h3>
        <form @submit.prevent="changePassword">
          <div class="form-row">
            <label>原密码</label>
            <input type="password" v-model="pwdForm.oldPassword" placeholder="请输入原密码" />
          </div>
          <div class="form-row">
            <label>新密码</label>
            <input type="password" v-model="pwdForm.newPassword" placeholder="至少6位字符" />
          </div>
          <div class="form-row">
            <label>确认新密码</label>
            <input type="password" v-model="pwdForm.confirmPassword" placeholder="再次输入新密码" />
          </div>
          <div v-if="pwdError" class="pwd-error">{{ pwdError }}</div>
          <div class="form-actions">
            <button type="submit" class="btn primary" :disabled="pwdSubmitting">
              {{ pwdSubmitting ? '修改中...' : '修改密码' }}
            </button>
          </div>
        </form>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import Sidebar from '@/components/Sidebar.vue'
import { getProfile, updateProfile } from '@/api/user'
import request from '@/utils/request'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/userStore'

const router = useRouter()
const userStore = useUserStore()
const form = ref({ username: '', email: '', avatar: '', bio: '', researchInterests: '' })
const previewUrl = ref('')
const fileInput = ref(null)
const uploading = ref(false)

// ── Password change state ───────────────────────────────────────
const pwdForm = reactive({ oldPassword: '', newPassword: '', confirmPassword: '' })
const pwdError = ref('')
const pwdSubmitting = ref(false)

// ── Common CS research keywords (fallback when Neo4j unavailable) ─
const FALLBACK_KEYWORDS = [
  'Machine Learning', 'Deep Learning', 'Reinforcement Learning',
  'Natural Language Processing', 'Computer Vision', 'Graph Neural Networks',
  'Knowledge Graph', 'Recommendation System', 'Transfer Learning',
  'Data Mining', 'Bayesian Inference', 'Transformer',
  'Federated Learning', 'Representation Learning', 'Neural Networks',
  'Generative Models', 'Optimization', 'Information Retrieval',
  'Computational Linguistics', 'Time Series', 'Causal Inference',
  'Multi-Agent Systems', 'Meta Learning', 'Few-Shot Learning'
]

// ── Keyword selector state ──────────────────────────────────────
const keywords = ref([])
const keywordsLoading = ref(false)
const selectedKeywords = ref([])
const dialogVisible = ref(false)
const keywordSearch = ref('')

const hotKeywords = computed(() => keywords.value.slice(0, 6))
const filteredKeywords = computed(() => {
  if (!keywordSearch.value) return keywords.value
  const q = keywordSearch.value.toLowerCase()
  return keywords.value.filter(k => k.label.toLowerCase().includes(q))
})

function toggleKeyword(label) {
  const idx = selectedKeywords.value.indexOf(label)
  if (idx >= 0) {
    selectedKeywords.value = selectedKeywords.value.filter(k => k !== label)
  } else {
    selectedKeywords.value = [...selectedKeywords.value, label]
  }
  form.value.researchInterests = selectedKeywords.value.join(', ')
}

async function fetchKeywords() {
  if (keywords.value.length > 0) return
  keywordsLoading.value = true
  try {
    const res = await request.get('/knowledge/keywords')
    const data = Array.isArray(res) ? res : (res?.data || [])
    if (data.length > 0) {
      keywords.value = data
      return
    }
  } catch {
    // Neo4j 不可用，使用硬编码关键词
  } finally {
    keywordsLoading.value = false
  }
  // 回退：使用硬编码常用科研关键词
  keywords.value = FALLBACK_KEYWORDS.map(k => ({ label: k, frequency: 0 }))
}

function initSelectedFromProfile(interests) {
  if (!interests) return
  selectedKeywords.value = interests.split(',').map(s => s.trim()).filter(Boolean)
}

async function load() {
  try {
    const res = await getProfile()
    const data = res.data || res
    form.value.username = data.username || ''
    form.value.email = data.email || ''
    form.value.avatar = data.avatar || ''
    form.value.bio = data.bio || ''
    form.value.researchInterests = data.researchInterests || ''
    if (data.avatar) previewUrl.value = data.avatar
    initSelectedFromProfile(data.researchInterests)
  } catch (e) {
    ElMessage.error('加载用户信息失败')
  }
}

function triggerFileInput() {
  if (uploading.value) return
  fileInput.value?.click()
}

async function onFileChange(e) {
  const file = e.target.files?.[0]
  if (!file) return

  const reader = new FileReader()
  reader.onload = (ev) => { previewUrl.value = ev.target.result }
  reader.readAsDataURL(file)

  uploading.value = true
  try {
    const fd = new FormData()
    fd.append('file', file)
    const res = await request.post('/user/avatar', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
      rawResponse: true
    })
    const data = res.data?.data || res.data || {}
    form.value.avatar = data.avatarUrl || ''
    ElMessage.success('头像上传成功')
  } catch (e) {
    ElMessage.error('头像上传失败')
    previewUrl.value = form.value.avatar || ''
  } finally {
    uploading.value = false
    if (fileInput.value) fileInput.value.value = ''
  }
}

async function save() {
  try {
    await updateProfile({
      email: form.value.email,
      avatar: form.value.avatar,
      bio: form.value.bio,
      researchInterests: form.value.researchInterests
    })
    ElMessage.success('保存成功')
    await userStore.fetchProfile()
    router.push('/profile')
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

async function changePassword() {
  pwdError.value = ''
  if (!pwdForm.oldPassword) {
    pwdError.value = '请输入原密码'
    return
  }
  if (!pwdForm.newPassword || pwdForm.newPassword.length < 6) {
    pwdError.value = '新密码至少需要6位字符'
    return
  }
  if (pwdForm.newPassword !== pwdForm.confirmPassword) {
    pwdError.value = '两次输入的新密码不一致'
    return
  }
  pwdSubmitting.value = true
  try {
    await request.put('/user/password', {
      oldPassword: pwdForm.oldPassword,
      newPassword: pwdForm.newPassword
    })
    ElMessage.success('密码修改成功，请重新登录')
    pwdForm.oldPassword = ''
    pwdForm.newPassword = ''
    pwdForm.confirmPassword = ''
    // 清除登录态，跳转登录页
    userStore.clearToken()
    router.push('/login')
  } catch (e) {
    const msg = e?.response?.data?.message || '密码修改失败'
    pwdError.value = msg
  } finally {
    pwdSubmitting.value = false
  }
}

onMounted(() => { load(); fetchKeywords() })
</script>

<style scoped>
.main-content {
  max-width: 820px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}
.edit-section {
  padding: 28px 32px;
}
.edit-section h3 {
  margin-bottom: 20px;
  font-size: 18px;
  font-weight: 700;
}
.form-row { display:flex; flex-direction:column; gap:8px; margin-bottom:16px }
.form-row label { font-weight:600; font-size:14px }
.form-row input, .form-row textarea {
  padding:12px; border-radius:8px; border:1px solid var(--border);
  background:transparent; color:var(--text-primary); font-family:inherit;
}
.form-row input:disabled { opacity:0.5; cursor:not-allowed }
.form-actions { display:flex; gap:12px; justify-content:flex-end; margin-top:16px }

.avatar-upload { display:flex; align-items:center; gap:16px }
.avatar-preview {
  width:80px; height:80px; border-radius:50%; overflow:hidden; cursor:pointer;
  position:relative; background:linear-gradient(135deg, var(--primary), var(--secondary));
  display:flex; align-items:center; justify-content:center;
  flex-shrink:0;
}
.avatar-placeholder { color:#fff; font-size:32px; font-weight:600 }
.avatar-img { width:100%; height:100%; object-fit:cover }
.avatar-overlay {
  position:absolute; inset:0; border-radius:50%;
  background:rgba(0,0,0,0.3); display:flex; align-items:center; justify-content:center;
  opacity:0; transition:opacity 0.2s; font-size:24px;
}
.avatar-overlay.uploading { opacity:1; background:rgba(0,0,0,0.5) }
.avatar-preview:hover .avatar-overlay { opacity:1 }
.avatar-actions { display:flex; flex-direction:column; gap:4px }
.avatar-hint { font-size:12px; color:var(--text-secondary) }
.btn-sm { padding:6px 14px; font-size:13px }

/* ── Password ─────────────────────────────────────────────────── */
.pwd-error {
  padding:10px 14px; font-size:13px; color:#dc2626;
  background:rgba(220,38,38,0.08); border:1px solid rgba(220,38,38,0.2);
  border-radius:10px; margin-bottom:12px;
}

/* ── Keyword Tags ────────────────────────────────────────────── */
.tags-loading { font-size:13px; color:var(--text-secondary); padding:8px 0 }
.tags-container { display:flex; flex-wrap:wrap; gap:8px }
.tag-pill {
  display:inline-flex; align-items:center; gap:4px;
  padding:6px 14px; border-radius:20px; border:1.5px solid var(--border);
  background:var(--bg-secondary, #f8f8f8); color:var(--text-secondary, #555);
  font-size:13px; font-family:inherit; cursor:pointer; transition:all 0.2s;
  user-select:none; white-space:nowrap;
}
.tag-pill:hover { border-color:#5b21b6; color:#5b21b6; background:#f5f0ff }
.tag-pill.selected {
  border-color:#5b21b6; background:#5b21b6; color:#fff;
}
.tag-pill .freq { font-size:10px; opacity:0.5; margin-left:2px }
.tag-more { font-weight:700; letter-spacing:1px; min-width:36px; justify-content:center }
.interest-hint { font-size:11px; color:var(--text-secondary); margin-top:4px }
.dialog-search { margin-bottom:16px }
.search-input {
  width:100%; height:40px; padding:0 14px; border:1.5px solid var(--border);
  border-radius:20px; font-size:14px; font-family:inherit; outline:none;
  background:var(--bg-primary); color:var(--text-primary);
}
.search-input:focus { border-color:#5b21b6 }
.dialog-tags { display:flex; flex-wrap:wrap; gap:8px; max-height:360px; overflow-y:auto }
.dialog-pill { font-size:13px }
.dialog-empty { text-align:center; color:var(--text-secondary); padding:32px 0; font-size:14px }
</style>
