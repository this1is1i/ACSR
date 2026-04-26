const USER_INFO_KEY = 'userInfo'

export function getStoredToken() {
  return localStorage.getItem('token') || ''
}

export function getStoredUserInfo() {
  try {
    return JSON.parse(localStorage.getItem(USER_INFO_KEY) || 'null')
  } catch {
    return null
  }
}

export function setStoredToken(token) {
  if (token) localStorage.setItem('token', token)
  else localStorage.removeItem('token')
}

export function setStoredUserInfo(userInfo) {
  if (userInfo) localStorage.setItem(USER_INFO_KEY, JSON.stringify(userInfo))
  else localStorage.removeItem(USER_INFO_KEY)
}

export function clearStoredAuth() {
  localStorage.removeItem('token')
  localStorage.removeItem(USER_INFO_KEY)
}
