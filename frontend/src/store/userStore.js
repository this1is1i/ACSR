import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getProfile } from '@/api/user'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(null)

  function setToken(t) {
    token.value = t
    localStorage.setItem('token', t)
  }

  function clearToken() {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
  }

  async function fetchProfile() {
    const res = await getProfile()
    userInfo.value = res.data
  }

  const isLoggedIn = () => !!token.value

  return { token, userInfo, setToken, clearToken, fetchProfile, isLoggedIn }
})
