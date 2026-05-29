<template>
  <div class="edit-root">
    <Sidebar />
    <main class="main-content card">
      <h3>编辑资料</h3>
      <form @submit.prevent="save">
        <div class="form-row">
          <label>用户名</label>
          <input type="text" v-model="form.username" disabled />
        </div>
        <div class="form-row">
          <label>邮箱</label>
          <input type="email" v-model="form.email" />
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
          <textarea v-model="form.bio" rows="4"></textarea>
        </div>
        <div class="form-row">
          <label>研究方向（点击选择）</label>
          <div v-if="keywordsLoading" class="tags-loading">加载关键词中...</div>
          <div v-else-if="keywords.length > 0" class="tags-container">
            <button
              v-for="kw in hotKeywords" :key="kw.label"
              type="button" class="tag-pill"
              :class="{ selected: selectedKeywords.includes(kw.label) }"
              @click="toggleKeyword(kw.label)"
            >{{ kw.label }}</button>
            <button type="button" class="tag-pill tag-more" @click="dialogVisible = true">···</button>
          </div>
          <div v-else class="tags-fallback">
            <input type="text" v-model="form.researchInterests" />
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
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
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
    keywords.value = res || []
  } catch {
    keywords.value = []
  } finally {
    keywordsLoading.value = false
  }
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

  // Show local preview immediately
  const reader = new FileReader()
  reader.onload = (ev) => { previewUrl.value = ev.target.result }
  reader.readAsDataURL(file)

  // Upload to server
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
    // Reset file input so re-selecting the same file triggers change
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

onMounted(() => { load(); fetchKeywords() })
</script>

<style scoped>
.main-content { max-width:820px }
.form-row { display:flex; flex-direction:column; gap:8px; margin-bottom:14px }
.form-row label { font-weight:600 }
.form-row input, .form-row textarea { padding:12px; border-radius:8px; border:1px solid var(--border); background:transparent; color:var(--text-primary) }
.form-actions { display:flex; gap:12px; justify-content:flex-end; margin-top:12px }

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
.tags-fallback input {
  width:100%; padding:12px; border-radius:8px; border:1px solid var(--border);
  background:transparent; color:var(--text-primary);
}
</style>
