<template>
  <div id="login-page" @mousemove="onMouseMove">
    <!-- Left Panel: Animated Characters -->
    <div class="left-panel">
      <div class="logo">
        <svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
          <path d="M12 2L15 9H9L12 2Z" />
          <path d="M12 22L9 15H15L12 22Z" />
          <path d="M2 12L9 9V15L2 12Z" />
          <path d="M22 12L15 15V9L22 12Z" />
        </svg>
        <span>ResearchLab</span>
      </div>

      <div class="characters-wrapper">
        <div class="characters-scene">
          <!-- Purple -->
          <div class="character char-purple" ref="charPurple">
            <div class="eyes" ref="purpleEyes" style="left:45px;top:40px;gap:28px">
              <div class="eyeball" ref="purpleEyeL" style="width:18px;height:18px"><div class="pupil" ref="purplePupilL" style="width:7px;height:7px"></div></div>
              <div class="eyeball" ref="purpleEyeR" style="width:18px;height:18px"><div class="pupil" ref="purplePupilR" style="width:7px;height:7px"></div></div>
            </div>
          </div>
          <!-- Black -->
          <div class="character char-black" ref="charBlack">
            <div class="eyes" ref="blackEyes" style="left:26px;top:32px;gap:20px">
              <div class="eyeball" ref="blackEyeL" style="width:16px;height:16px"><div class="pupil" ref="blackPupilL" style="width:6px;height:6px"></div></div>
              <div class="eyeball" ref="blackEyeR" style="width:16px;height:16px"><div class="pupil" ref="blackPupilR" style="width:6px;height:6px"></div></div>
            </div>
          </div>
          <!-- Orange -->
          <div class="character char-orange" ref="charOrange">
            <div class="eyes" ref="orangeEyes" style="left:82px;top:90px;gap:28px">
              <div class="bare-pupil" ref="orangePupilL"></div>
              <div class="bare-pupil" ref="orangePupilR"></div>
            </div>
            <div class="orange-mouth" ref="orangeMouth" style="left:90px;top:120px"></div>
          </div>
          <!-- Yellow -->
          <div class="character char-yellow" ref="charYellow">
            <div class="eyes" ref="yellowEyes" style="left:52px;top:40px;gap:20px">
              <div class="bare-pupil" ref="yellowPupilL"></div>
              <div class="bare-pupil" ref="yellowPupilR"></div>
            </div>
            <div class="yellow-mouth" ref="yellowMouth" style="left:40px;top:88px"></div>
          </div>
        </div>
      </div>

      <div class="footer-links">
        <a href="#">隐私政策</a>
        <a href="#">服务条款</a>
        <a href="#">联系我们</a>
      </div>
    </div>

    <!-- Right Panel: Form -->
    <div class="right-panel">
      <div class="form-container">
        <div class="sparkle-icon">
          <svg viewBox="0 0 24 24" fill="none"><path d="M12 2L13.5 9H10.5L12 2Z" fill="#1a1a2e"/><path d="M12 22L10.5 15H13.5L12 22Z" fill="#1a1a2e"/><path d="M2 12L9 10.5V13.5L2 12Z" fill="#1a1a2e"/><path d="M22 12L15 13.5V10.5L22 12Z" fill="#1a1a2e"/></svg>
        </div>

        <div class="form-header">
          <h1>{{ isRegister ? '创建账户' : '欢迎回来！' }}</h1>
          <p>{{ isRegister ? '开启您的研究之旅' : '请输入您的登录信息' }}</p>
        </div>

        <form @submit.prevent="handleSubmit">
          <div class="form-group">
            <label :class="{ 'error-label': errors.username }">用户名</label>
            <div class="input-wrapper">
              <input type="text" v-model="form.username" placeholder="请输入用户名"
                :class="{ error: errors.username }"
                @focus="onFieldFocus" @blur="onFieldBlur" @input="onFieldInput" />
            </div>
          </div>

          <div class="form-group">
            <label :class="{ 'error-label': errors.password }">密码</label>
            <div class="input-wrapper">
              <input :type="showPwd ? 'text' : 'password'" v-model="form.password"
                placeholder="••••••••" :class="{ error: errors.password }"
                @focus="isPwdFocused = true; updateCharacters()"
                @blur="isPwdFocused = false; updateCharacters()"
                @input="onFieldInput" />
              <button type="button" class="toggle-password" @click="togglePassword">
                <svg v-if="!showPwd" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
              </button>
            </div>
          </div>

          <div v-if="isRegister" class="form-group">
            <label>研究方向（选填）</label>
            <div class="input-wrapper">
              <input type="text" v-model="form.researchInterests"
                placeholder="机器学习, 深度学习, 自然语言处理"
                @focus="onFieldFocus" @blur="onFieldBlur" @input="onFieldInput" />
            </div>
            <p class="interest-hint">用逗号分隔多个研究方向，用于初始化个性化推荐</p>
          </div>

          <div class="error-msg" v-if="errorMsg">{{ errorMsg }}</div>

          <button type="submit" class="btn-login" :disabled="submitting">
            <span class="btn-text">{{ isRegister ? (submitting ? '创建中...' : '注册') : (submitting ? '登录中...' : '登录') }}</span>
            <div class="btn-hover-content">
              <span>{{ isRegister ? '注册' : '登录' }}</span>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
            </div>
          </button>
        </form>

        <div class="signup-link">
          {{ isRegister ? '已有账户？' : '还没有账户？' }}
          <a href="#" @click.prevent="toggleMode">{{ isRegister ? '登录' : '注册' }}</a>
        </div>

        <div class="guest-link">
          <a href="#" @click.prevent="goGuest">游客模式</a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { login, register } from '@/api/user'
import { useUserStore } from '@/store/userStore'

const router = useRouter()
const userStore = useUserStore()

const isRegister = ref(false)
const showPwd = ref(false)
const isPwdFocused = ref(false)
const submitting = ref(false)
const errorMsg = ref('')
const errors = reactive({ username: false, password: false })

const form = reactive({ username: '', password: '', researchInterests: '' })

// ── Animation state ────────────────────────────────────────────
let mouseX = 0, mouseY = 0, isTyping = false, isLookingAtEachOther = false
let isPurpleBlinking = false, isBlackBlinking = false, isPurplePeeking = false
let isLoginError = false
let typingTimer = null, errorRecoverTimer = null

const charPurple = ref(null), charBlack = ref(null), charOrange = ref(null), charYellow = ref(null)
const purpleEyes = ref(null), purpleEyeL = ref(null), purpleEyeR = ref(null)
const purplePupilL = ref(null), purplePupilR = ref(null)
const blackEyes = ref(null), blackEyeL = ref(null), blackEyeR = ref(null)
const blackPupilL = ref(null), blackPupilR = ref(null)
const orangeEyes = ref(null), orangePupilL = ref(null), orangePupilR = ref(null)
const orangeMouth = ref(null)
const yellowEyes = ref(null), yellowPupilL = ref(null), yellowPupilR = ref(null)
const yellowMouth = ref(null)

function goGuest() {
  router.push('/search')
}

function toggleMode() {
  isRegister.value = !isRegister.value
  errorMsg.value = ''
  errors.username = false
  errors.password = false
}

function togglePassword() {
  showPwd.value = !showPwd.value
  if (showPwd.value && form.password.length > 0) schedulePeek()
  updateCharacters()
}

function onFieldFocus() { setTyping(true) }
function onFieldBlur() { setTyping(false) }
function onFieldInput() { updateCharacters() }
function onMouseMove(e) { mouseX = e.clientX; mouseY = e.clientY; if (!isTyping && !isLoginError) updateCharacters() }

function setTyping(typing) {
  isTyping = typing
  if (typing) {
    isLookingAtEachOther = true
    clearTimeout(typingTimer)
    typingTimer = setTimeout(() => { isLookingAtEachOther = false; updateCharacters() }, 800)
  } else {
    isLookingAtEachOther = false
  }
  updateCharacters()
}

// ── Blink scheduling ───────────────────────────────────────────
function scheduleBlinkPurple() {
  setTimeout(() => {
    isPurpleBlinking = true; updateCharacters()
    setTimeout(() => { isPurpleBlinking = false; updateCharacters(); scheduleBlinkPurple() }, 150)
  }, Math.random() * 4000 + 3000)
}
function scheduleBlinkBlack() {
  setTimeout(() => {
    isBlackBlinking = true; updateCharacters()
    setTimeout(() => { isBlackBlinking = false; updateCharacters(); scheduleBlinkBlack() }, 150)
  }, Math.random() * 4000 + 3000)
}

function schedulePeek() {
  if (form.password.length > 0 && showPwd.value) {
    setTimeout(() => {
      if (form.password.length > 0 && showPwd.value) {
        isPurplePeeking = true; updateCharacters()
        setTimeout(() => { isPurplePeeking = false; updateCharacters(); schedulePeek() }, 800)
      }
    }, Math.random() * 3000 + 2000)
  }
}

// ── Mouse tracking helpers ─────────────────────────────────────
function calcPosition(el) {
  if (!el) return { faceX: 0, faceY: 0, bodySkew: 0 }
  const rect = el.getBoundingClientRect()
  const cx = rect.left + rect.width / 2
  const cy = rect.top + rect.height / 3
  return { faceX: Math.max(-15, Math.min(15, (mouseX - cx) / 20)), faceY: Math.max(-10, Math.min(10, (mouseY - cy) / 30)), bodySkew: Math.max(-6, Math.min(6, -(mouseX - cx) / 120)) }
}
function calcPupilOffset(el, maxDist) {
  if (!el) return { x: 0, y: 0 }
  const rect = el.getBoundingClientRect()
  const cx = rect.left + rect.width / 2, cy = rect.top + rect.height / 2
  const dx = mouseX - cx, dy = mouseY - cy
  const dist = Math.min(Math.sqrt(dx * dx + dy * dy), maxDist)
  const angle = Math.atan2(dy, dx)
  return { x: Math.cos(angle) * dist, y: Math.sin(angle) * dist }
}

// ── Main character update ──────────────────────────────────────
function updateCharacters() {
  if (!charPurple.value) return
  const purple = charPurple.value, black = charBlack.value, orange = charOrange.value, yellow = charYellow.value
  const purplePos = calcPosition(purple), blackPos = calcPosition(black)
  const orangePos = calcPosition(orange), yellowPos = calcPosition(yellow)

  const pwdLen = form.password.length
  const isShowingPwd = pwdLen > 0 && showPwd.value
  const isLookingAway = isPwdFocused.value && !showPwd.value

  // ── Purple body ──
  if (isShowingPwd) { purple.style.transform = 'skewX(0deg)'; purple.style.height = '370px' }
  else if (isLookingAway) { purple.style.transform = 'skewX(-14deg) translateX(-20px)'; purple.style.height = '410px' }
  else if (isTyping) { purple.style.transform = `skewX(${(purplePos.bodySkew || 0) - 12}deg) translateX(40px)`; purple.style.height = '410px' }
  else { purple.style.transform = `skewX(${purplePos.bodySkew}deg)`; purple.style.height = '370px' }

  // Purple eyes
  purpleEyeL.value.style.height = isPurpleBlinking ? '2px' : '18px'
  purpleEyeR.value.style.height = isPurpleBlinking ? '2px' : '18px'
  if (isLoginError) {
    purpleEyes.value.style.left = '30px'; purpleEyes.value.style.top = '55px'
    purplePupilL.value.style.transform = 'translate(-3px, 4px)'; purplePupilR.value.style.transform = 'translate(-3px, 4px)'
  } else if (isLookingAway) {
    purpleEyes.value.style.left = '20px'; purpleEyes.value.style.top = '25px'
    purplePupilL.value.style.transform = 'translate(-5px, -5px)'; purplePupilR.value.style.transform = 'translate(-5px, -5px)'
  } else if (isShowingPwd) {
    purpleEyes.value.style.left = '20px'; purpleEyes.value.style.top = '35px'
    const p = isPurplePeeking ? 4 : -4
    purplePupilL.value.style.transform = `translate(${p}px, ${isPurplePeeking ? 5 : -4}px)`
    purplePupilR.value.style.transform = `translate(${p}px, ${isPurplePeeking ? 5 : -4}px)`
  } else if (isLookingAtEachOther) {
    purpleEyes.value.style.left = '55px'; purpleEyes.value.style.top = '65px'
    purplePupilL.value.style.transform = 'translate(3px, 4px)'; purplePupilR.value.style.transform = 'translate(3px, 4px)'
  } else {
    purpleEyes.value.style.left = (45 + purplePos.faceX) + 'px'; purpleEyes.value.style.top = (40 + purplePos.faceY) + 'px'
    const po = calcPupilOffset(purpleEyeL.value, 5)
    purplePupilL.value.style.transform = `translate(${po.x}px, ${po.y}px)`
    purplePupilR.value.style.transform = `translate(${po.x}px, ${po.y}px)`
  }

  // ── Black body ──
  if (isShowingPwd) black.style.transform = 'skewX(0deg)'
  else if (isLookingAway) black.style.transform = 'skewX(12deg) translateX(-10px)'
  else if (isLookingAtEachOther) black.style.transform = `skewX(${(blackPos.bodySkew || 0) * 1.5 + 10}deg) translateX(20px)`
  else if (isTyping) black.style.transform = `skewX(${(blackPos.bodySkew || 0) * 1.5}deg)`
  else black.style.transform = `skewX(${blackPos.bodySkew}deg)`

  // Black eyes
  blackEyeL.value.style.height = isBlackBlinking ? '2px' : '16px'
  blackEyeR.value.style.height = isBlackBlinking ? '2px' : '16px'
  if (isLoginError) {
    blackEyes.value.style.left = '15px'; blackEyes.value.style.top = '40px'
    blackPupilL.value.style.transform = 'translate(-3px, 4px)'; blackPupilR.value.style.transform = 'translate(-3px, 4px)'
  } else if (isLookingAway) {
    blackEyes.value.style.left = '10px'; blackEyes.value.style.top = '20px'
    blackPupilL.value.style.transform = 'translate(-4px, -5px)'; blackPupilR.value.style.transform = 'translate(-4px, -5px)'
  } else if (isShowingPwd) {
    blackEyes.value.style.left = '10px'; blackEyes.value.style.top = '28px'
    blackPupilL.value.style.transform = 'translate(-4px, -4px)'; blackPupilR.value.style.transform = 'translate(-4px, -4px)'
  } else if (isLookingAtEachOther) {
    blackEyes.value.style.left = '32px'; blackEyes.value.style.top = '12px'
    blackPupilL.value.style.transform = 'translate(0px, -4px)'; blackPupilR.value.style.transform = 'translate(0px, -4px)'
  } else {
    blackEyes.value.style.left = (26 + blackPos.faceX) + 'px'; blackEyes.value.style.top = (32 + blackPos.faceY) + 'px'
    const bo = calcPupilOffset(blackEyeL.value, 4)
    blackPupilL.value.style.transform = `translate(${bo.x}px, ${bo.y}px)`
    blackPupilR.value.style.transform = `translate(${bo.x}px, ${bo.y}px)`
  }

  // ── Orange body & mouth ──
  if (isShowingPwd) orange.style.transform = 'skewX(0deg)'
  else orange.style.transform = `skewX(${orangePos.bodySkew}deg)`
  if (isLoginError) {
    orangeMouth.value.style.left = (80 + orangePos.faceX) + 'px'; orangeMouth.value.style.top = '130px'
  }
  // Orange eyes
  if (isLoginError) {
    orangeEyes.value.style.left = '60px'; orangeEyes.value.style.top = '95px'
    orangePupilL.value.style.transform = 'translate(-3px, 4px)'; orangePupilR.value.style.transform = 'translate(-3px, 4px)'
  } else if (isLookingAway) {
    orangeEyes.value.style.left = '50px'; orangeEyes.value.style.top = '75px'
    orangePupilL.value.style.transform = 'translate(-5px, -5px)'; orangePupilR.value.style.transform = 'translate(-5px, -5px)'
  } else if (isShowingPwd) {
    orangeEyes.value.style.left = '50px'; orangeEyes.value.style.top = '85px'
    orangePupilL.value.style.transform = 'translate(-5px, -4px)'; orangePupilR.value.style.transform = 'translate(-5px, -4px)'
  } else {
    orangeEyes.value.style.left = (82 + orangePos.faceX) + 'px'; orangeEyes.value.style.top = (90 + orangePos.faceY) + 'px'
    const oo = calcPupilOffset(orangePupilL.value, 5)
    orangePupilL.value.style.transform = `translate(${oo.x}px, ${oo.y}px)`
    orangePupilR.value.style.transform = `translate(${oo.x}px, ${oo.y}px)`
  }

  // ── Yellow body ──
  if (isShowingPwd) yellow.style.transform = 'skewX(0deg)'
  else yellow.style.transform = `skewX(${yellowPos.bodySkew}deg)`
  // Yellow eyes & mouth
  if (isLoginError) {
    yellowEyes.value.style.left = '35px'; yellowEyes.value.style.top = '45px'
    yellowPupilL.value.style.transform = 'translate(-3px, 4px)'; yellowPupilR.value.style.transform = 'translate(-3px, 4px)'
    yellowMouth.value.style.left = '30px'; yellowMouth.value.style.top = '92px'; yellowMouth.value.style.transform = 'rotate(-8deg)'
  } else if (isLookingAway) {
    yellowEyes.value.style.left = '20px'; yellowEyes.value.style.top = '30px'
    yellowPupilL.value.style.transform = 'translate(-5px, -5px)'; yellowPupilR.value.style.transform = 'translate(-5px, -5px)'
    yellowMouth.value.style.left = '15px'; yellowMouth.value.style.top = '78px'; yellowMouth.value.style.transform = 'rotate(0deg)'
  } else if (isShowingPwd) {
    yellowEyes.value.style.left = '20px'; yellowEyes.value.style.top = '35px'
    yellowPupilL.value.style.transform = 'translate(-5px, -4px)'; yellowPupilR.value.style.transform = 'translate(-5px, -4px)'
    yellowMouth.value.style.left = '10px'; yellowMouth.value.style.top = '88px'; yellowMouth.value.style.transform = 'rotate(0deg)'
  } else {
    yellowEyes.value.style.left = (52 + yellowPos.faceX) + 'px'; yellowEyes.value.style.top = (40 + yellowPos.faceY) + 'px'
    const yo = calcPupilOffset(yellowPupilL.value, 5)
    yellowPupilL.value.style.transform = `translate(${yo.x}px, ${yo.y}px)`
    yellowPupilR.value.style.transform = `translate(${yo.x}px, ${yo.y}px)`
    yellowMouth.value.style.left = (40 + yellowPos.faceX) + 'px'; yellowMouth.value.style.top = (88 + yellowPos.faceY) + 'px'
    yellowMouth.value.style.transform = 'rotate(0deg)'
  }
}

// ── Error animation ────────────────────────────────────────────
const shakeIds = ['purple-eyes','black-eyes','orange-eyes','yellow-eyes','yellow-mouth','orange-mouth']

function triggerLoginError() {
  if (errorRecoverTimer) { clearTimeout(errorRecoverTimer); errorRecoverTimer = null }
  isLoginError = true; isPwdFocused.value = false
  updateCharacters()
  orangeMouth.value?.classList.add('visible')
  setTimeout(() => {
    shakeIds.forEach(id => {
      const el = document.getElementById(id) || (id === 'purple-eyes' ? purpleEyes.value : id === 'black-eyes' ? blackEyes.value : id === 'orange-eyes' ? orangeEyes.value : id === 'yellow-eyes' ? yellowEyes.value : id === 'yellow-mouth' ? yellowMouth.value : orangeMouth.value)
      if (el) { el.classList.remove('shake-head'); void el.offsetHeight; el.classList.add('shake-head') }
    })
  }, 350)
  errorRecoverTimer = setTimeout(() => {
    isLoginError = false; errorRecoverTimer = null
    orangeMouth.value?.classList.remove('visible')
    shakeIds.forEach(id => {
      const el = document.getElementById(id) || (id === 'purple-eyes' ? purpleEyes.value : id === 'black-eyes' ? blackEyes.value : id === 'orange-eyes' ? orangeEyes.value : id === 'yellow-eyes' ? yellowEyes.value : id === 'yellow-mouth' ? yellowMouth.value : orangeMouth.value)
      if (el) el.classList.remove('shake-head')
    })
    updateCharacters()
  }, 2500)
}

// ── Form submit ────────────────────────────────────────────────
async function handleSubmit() {
  errorMsg.value = ''
  errors.username = false
  errors.password = false

  if (!form.username || form.username.trim().length < 2) {
    errors.username = true
    errorMsg.value = '请输入有效用户名（至少2个字符）。'
    triggerLoginError()
    return
  }
  if (!form.password || form.password.length < 6) {
    errors.password = true
    errorMsg.value = '密码至少需要6个字符。'
    triggerLoginError()
    return
  }

  submitting.value = true
  try {
    if (isRegister.value) {
      const regRes = await register({
        username: form.username.trim(),
        password: form.password,
        researchInterests: form.researchInterests.trim()
      })
      userStore.setAuth(regRes.data)
      ElMessage.success('注册成功！欢迎加入。')
      router.push('/home')
      return
    } else {
      const res = await login({ username: form.username.trim(), password: form.password })
      userStore.setAuth(res.data)
      ElMessage.success('登录成功')
      router.push(res.data.role === 'ADMIN' ? '/admin' : '/home')
    }
  } catch (e) {
    const msg = e?.response?.data?.message || '登录失败，请检查用户名和密码。'
    errorMsg.value = msg
    errors.username = true
    errors.password = true
    triggerLoginError()
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  await nextTick()
  scheduleBlinkPurple()
  scheduleBlinkBlack()
  updateCharacters()
})

onBeforeUnmount(() => {
  if (typingTimer) clearTimeout(typingTimer)
  if (errorRecoverTimer) clearTimeout(errorRecoverTimer)
})
</script>

<style scoped>
* { margin: 0; padding: 0; box-sizing: border-box; }

#login-page {
  display: grid; grid-template-columns: 1fr 1fr; height: 100vh;
  font-family: "Inter", -apple-system, BlinkMacSystemFont, sans-serif;
}

/* ── Left Panel ─────────────────────────────────────────────── */
.left-panel {
  position: relative; display: flex; flex-direction: column; justify-content: space-between;
  background: linear-gradient(135deg, #d4d0dc 0%, #c8c4d0 50%, #bbb7c5 100%);
  padding: 40px 48px; overflow: hidden;
}
.left-panel::after {
  content:""; position:absolute; top:20%; right:15%; width:260px; height:260px;
  background:rgba(180,170,200,0.25); border-radius:50%; filter:blur(80px);
}
.left-panel::before {
  content:""; position:absolute; bottom:15%; left:10%; width:350px; height:350px;
  background:rgba(200,195,210,0.2); border-radius:50%; filter:blur(100px);
}
.logo { display:flex; align-items:center; gap:10px; font-size:16px; font-weight:600; color:#fff; z-index:10; position:relative }
.logo svg { width:28px; height:28px; background:rgba(255,255,255,0.15); backdrop-filter:blur(8px); padding:4px; border-radius:6px }
.characters-wrapper { position:relative; z-index:10; display:flex; align-items:flex-end; justify-content:center; height:420px }
.footer-links { display:flex; gap:28px; font-size:13px; color:rgba(80,70,90,0.7); z-index:10; position:relative }
.footer-links a { color:inherit; text-decoration:none; transition:color 0.2s }
.footer-links a:hover { color:#333 }

.characters-scene { position:relative; width:480px; height:360px }
.character { position:absolute; bottom:0; transition:all 0.7s ease-in-out; transform-origin:bottom center }
.char-purple { left:60px; width:170px; height:370px; background:#6c3ff5; border-radius:10px 10px 0 0; z-index:1 }
.char-black { left:220px; width:115px; height:290px; background:#2d2d2d; border-radius:8px 8px 0 0; z-index:2 }
.char-orange { left:0; width:230px; height:190px; background:#ff9b6b; border-radius:115px 115px 0 0; z-index:3 }
.char-yellow { left:290px; width:135px; height:215px; background:#e8d754; border-radius:68px 68px 0 0; z-index:4 }
.eyes { position:absolute; display:flex; transition:all 0.7s ease-in-out }
.eyeball { border-radius:50%; background:white; display:flex; align-items:center; justify-content:center; transition:height 0.15s ease; overflow:hidden }
.pupil { border-radius:50%; background:#2d2d2d; transition:transform 0.1s ease-out }
.bare-pupil { width:12px; height:12px; border-radius:50%; background:#2d2d2d; transition:transform 0.7s ease-in-out }
.yellow-mouth { position:absolute; width:50px; height:4px; background:#2d2d2d; border-radius:2px; transition:all 0.7s ease-in-out }
.orange-mouth { position:absolute; width:28px; height:14px; border:3px solid #2d2d2d; border-top:none; border-radius:0 0 14px 14px; opacity:0; transition:all 0.7s ease-in-out }
.orange-mouth.visible { opacity:1 }

@keyframes shakeHead {
  0%,100%{translate:0 0} 10%{translate:-9px 0} 20%{translate:7px 0} 30%{translate:-6px 0}
  40%{translate:5px 0} 50%{translate:-4px 0} 60%{translate:3px 0} 70%{translate:-2px 0}
  80%{translate:1px 0} 90%{translate:-0.5px 0}
}
.eyes.shake-head, .yellow-mouth.shake-head, .orange-mouth.shake-head {
  animation:shakeHead 0.8s cubic-bezier(0.36,0.07,0.19,0.97) both;
}

/* ── Right Panel ────────────────────────────────────────────── */
.right-panel { display:flex; align-items:center; justify-content:center; background:#fff; padding:40px }
.form-container { width:100%; max-width:400px }
.sparkle-icon { display:flex; justify-content:center; margin-bottom:24px }
.sparkle-icon svg { width:32px; height:32px }
.form-header { text-align:center; margin-bottom:36px }
.form-header h1 { font-size:28px; font-weight:700; color:#1a1a2e; letter-spacing:-0.5px; margin-bottom:6px }
.form-header p { font-size:14px; color:#888 }
.form-group { margin-bottom:20px }
.form-group label { display:block; font-size:13px; font-weight:500; color:#333; margin-bottom:8px }
.form-group label.error-label { color:#dc2626 }
.form-group .input-wrapper { position:relative }
.form-group input {
  width:100%; height:48px; border:none; border-bottom:1.5px solid #e0e0e0;
  padding:0 40px 0 0; font-size:15px; font-family:inherit; color:#1a1a2e;
  background:transparent; outline:none; transition:border-color 0.3s;
}
.form-group input:focus { border-bottom-color:#5b21b6 }
.form-group input::placeholder { color:#ccc }
.form-group input.error { border-bottom-color:#dc2626 }
.interest-hint { font-size:11px; color:#999; margin-top:4px; padding-left:2px }
.toggle-password {
  position:absolute; right:0; top:50%; transform:translateY(-50%);
  background:none; border:none; cursor:pointer; color:#666; padding:6px; transition:color 0.2s;
}
.toggle-password:hover { color:#333 }
.error-msg {
  padding:10px 14px; font-size:13px; color:#dc2626;
  background:rgba(220,38,38,0.08); border:1px solid rgba(220,38,38,0.2);
  border-radius:10px; margin-bottom:16px;
}
.btn-login {
  position:relative; width:100%; height:50px; border-radius:25px;
  border:1.5px solid #1a1a2e; background:#1a1a2e; color:#fff;
  font-size:15px; font-weight:600; font-family:inherit; cursor:pointer;
  overflow:hidden; margin-bottom:14px; transition:all 0.3s;
}
.btn-login:disabled { opacity:0.7; cursor:not-allowed }
.btn-login .btn-text { display:inline-block; transition:all 0.3s }
.btn-login .btn-hover-content {
  position:absolute; inset:0; display:flex; align-items:center; justify-content:center;
  gap:8px; background:#5b21b6; color:#fff; opacity:0; transition:all 0.3s; border-radius:25px;
}
.btn-login:hover:not(:disabled) .btn-text { transform:translateX(40px); opacity:0 }
.btn-login:hover:not(:disabled) .btn-hover-content { opacity:1 }
.signup-link { text-align:center; font-size:13px; color:#888; margin-top:32px }
.signup-link a { color:#1a1a2e; font-weight:600; text-decoration:none }
.signup-link a:hover { text-decoration:underline }
.guest-link { text-align:center; margin-top:16px }
.guest-link a { color:#6366f1; font-size:13px; text-decoration:none; padding:8px 24px; border:1px solid rgba(99,102,241,0.3); border-radius:20px; transition:all 0.2s }
.guest-link a:hover { background:rgba(99,102,241,0.1); border-color:#6366f1 }

@media (max-width:900px) {
  #login-page { grid-template-columns:1fr }
  .left-panel { display:none }
}
@media (max-width:480px) {
  .right-panel { padding:24px }
}
</style>
