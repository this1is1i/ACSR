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
          <label>研究方向（逗号分隔）</label>
          <input type="text" v-model="form.researchInterests" />
        </div>
        <div class="form-actions">
          <button type="button" class="btn secondary" @click="$router.back()">取消</button>
          <button type="submit" class="btn primary" :disabled="uploading">保存</button>
        </div>
      </form>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Sidebar from '@/components/Sidebar.vue'
import { getProfile, updateProfile } from '@/api/user'
import request from '@/utils/request'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'

const router = useRouter()
const form = ref({ username: '', email: '', avatar: '', bio: '', researchInterests: '' })
const previewUrl = ref('')
const fileInput = ref(null)
const uploading = ref(false)

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
    router.push('/profile')
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

onMounted(load)
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
</style>
