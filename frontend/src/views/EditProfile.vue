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
          <label>头像 URL</label>
          <input type="text" v-model="form.avatar" />
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
          <button type="submit" class="btn primary">保存</button>
        </div>
      </form>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Sidebar from '@/components/Sidebar.vue'
import { getProfile, updateProfile } from '@/api/user'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'

const router = useRouter()
const form = ref({ username: '', email: '', avatar: '', bio: '', researchInterests: '' })

async function load() {
  try {
    const res = await getProfile()
    const data = res.data || res
    form.value.username = data.username || ''
    form.value.email = data.email || ''
    form.value.avatar = data.avatar || ''
    form.value.bio = data.bio || ''
    form.value.researchInterests = data.researchInterests || ''
  } catch (e) {
    ElMessage.error('加载用户信息失败')
  }
}

async function save() {
  try {
    await updateProfile({ email: form.value.email, avatar: form.value.avatar, bio: form.value.bio, researchInterests: form.value.researchInterests })
    ElMessage.success('保存成功')
    router.push('/profile')
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

onMounted(load)
</script>

<style scoped>
.main-content { margin-left:260px; padding:24px; max-width:820px }
.form-row { display:flex; flex-direction:column; gap:8px; margin-bottom:14px }
.form-row label { font-weight:600 }
.form-row input, .form-row textarea { padding:12px; border-radius:8px; border:1px solid var(--border); background:transparent; color:var(--text-primary) }
.form-actions { display:flex; gap:12px; justify-content:flex-end; margin-top:12px }
</style>