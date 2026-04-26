import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getProfile } from '@/api/user'
import { clearStoredAuth, getStoredToken, getStoredUserInfo, setStoredToken, setStoredUserInfo } from '@/utils/auth'

export const useUserStore = defineStore('user', () => {
  const token = ref(getStoredToken())
  const userInfo = ref(getStoredUserInfo())

  function setUserInfo(info) {
    userInfo.value = info || null
    setStoredUserInfo(info)
  }

  function setToken(t) {
    token.value = t
    setStoredToken(t)
  }

  function setAuth(loginResponse) {
    setToken(loginResponse.token)
    setUserInfo({
      id: loginResponse.userId,
      username: loginResponse.username,
      role: loginResponse.role,
      roleLabel: loginResponse.roleLabel,
    })
  }

  function clearToken() {
    token.value = ''
    clearStoredAuth()
    userInfo.value = null
  }

  async function fetchProfile() {
    const res = await getProfile()
    setUserInfo(res.data)
  }

  const isLoggedIn = () => !!token.value
  const hasRole = (...roles) => !!userInfo.value?.role && roles.includes(userInfo.value.role)
  const isAdmin = () => hasRole('ADMIN')

  return { token, userInfo, setToken, setUserInfo, setAuth, clearToken, fetchProfile, isLoggedIn, hasRole, isAdmin }
})
