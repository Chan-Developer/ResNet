import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getMe } from '../api/auth'
import router from '../router'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref<{ id: number; username: string; email: string } | null>(null)

  function setToken(t: string) {
    token.value = t
    localStorage.setItem('token', t)
  }

  function logout() {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
    router.push('/login')
  }

  async function fetchUser() {
    try {
      const res: any = await getMe()
      userInfo.value = res.data
    } catch {
      logout()
    }
  }

  // auto-fetch on init
  if (token.value) {
    fetchUser()
  }

  return { token, userInfo, setToken, logout, fetchUser }
})
