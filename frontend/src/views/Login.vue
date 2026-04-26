<template>
  <div class="login-container">
    <div class="login-box">
      <h2 class="title">科研推荐系统</h2>
      <p class="subtitle">Actor-Critic 强化学习驱动</p>

      <el-form :model="form" :rules="rules" ref="formRef" size="large">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名" prefix-icon="User" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="密码"
            prefix-icon="Lock" show-password @keyup.enter="handleLogin" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" class="btn-full" :loading="loading" @click="handleLogin">
            登录
          </el-button>
        </el-form-item>
        <el-form-item>
          <el-button class="btn-full" @click="handleRegister" :loading="regLoading">
            注册账号
          </el-button>
        </el-form-item>
        <div class="hint">新注册账号默认为学生用户，可由管理员升级为研究者或管理员。</div>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { login, register } from '@/api/user'
import { useUserStore } from '@/store/userStore'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref()
const loading = ref(false)
const regLoading = ref(false)

const form = reactive({ username: '', password: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, min: 6, message: '密码至少6位', trigger: 'blur' }],
}

async function handleLogin() {
  await formRef.value.validate()
  loading.value = true
  try {
    const res = await login(form)
    userStore.setAuth(res.data)
    ElMessage.success('登录成功')
    router.push(res.data.role === 'ADMIN' ? '/admin' : '/home')
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  await formRef.value.validate()
  regLoading.value = true
  try {
    await register(form)
    ElMessage.success('注册成功，请登录')
  } finally {
    regLoading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
}
.login-box {
  width: 380px;
  padding: 40px;
  background: #1c2128;
  border-radius: 12px;
  border: 1px solid #30363d;
}
.title {
  color: #e6edf3;
  text-align: center;
  margin-bottom: 4px;
  font-size: 22px;
}
.subtitle {
  color: #8b949e;
  text-align: center;
  font-size: 13px;
  margin-bottom: 28px;
}
.hint { color:#8b949e; font-size:12px; line-height:1.5; margin-top:8px; text-align:center }
.btn-full { width: 100%; }
</style>
