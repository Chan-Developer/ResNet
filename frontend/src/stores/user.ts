import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { getMe } from '../api/auth'

type UserRole = 'admin' | 'expert' | 'user'
type UserInfo = {
  id: number
  username: string
  email: string
  role: UserRole | string
  is_active: boolean
  permissions: string[]
}

function normalizeRole(role: unknown): UserRole | string {
  if (typeof role !== 'string') return 'user'
  const normalized = role.trim().toLowerCase()
  if (normalized === 'admin' || normalized === 'expert' || normalized === 'user') {
    return normalized
  }
  return normalized || 'user'
}

function decodeBase64Url(input: string): string {
  try {
    const normalized = input.replace(/-/g, '+').replace(/_/g, '/')
    const padding = '='.repeat((4 - (normalized.length % 4)) % 4)
    return atob(normalized + padding)
  } catch {
    return ''
  }
}

function roleFromToken(token: string): string {
  if (!token || token.split('.').length < 2) return ''
  const payloadPart = token.split('.')[1]
  const decoded = decodeBase64Url(payloadPart)
  if (!decoded) return ''
  try {
    const payload = JSON.parse(decoded) as { role?: string }
    return normalizeRole(payload.role)
  } catch {
    return ''
  }
}

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref<UserInfo | null>(null)
  const currentRole = computed(() => {
    if (userInfo.value) {
      const apiRole = normalizeRole(userInfo.value.role)
      if (apiRole === 'admin' || apiRole === 'expert' || apiRole === 'user') {
        return apiRole
      }
    }
    const jwtRole = roleFromToken(token.value)
    if (jwtRole === 'admin' || jwtRole === 'expert' || jwtRole === 'user') {
      return jwtRole
    }
    return 'user'
  })
  const isAdmin = computed(() => currentRole.value === 'admin')
  const permissions = computed(() => userInfo.value?.permissions ?? [])

  function setToken(t: string) {
    token.value = t
    localStorage.setItem('token', t)
  }

  function logout() {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
    if (window.location.pathname !== '/login') {
      window.location.replace('/login')
    }
  }

  async function fetchUser() {
    try {
      const res: any = await getMe()
      userInfo.value = {
        ...res.data,
        role: normalizeRole(res.data?.role),
        permissions: Array.isArray(res.data?.permissions) ? res.data.permissions : [],
      }
    } catch {
      logout()
    }
  }

  function hasPermission(permission: string) {
    if (isAdmin.value) return true
    return permissions.value.includes(permission)
  }

  // auto-fetch on init
  if (token.value) {
    fetchUser()
  }

  return { token, userInfo, currentRole, isAdmin, permissions, hasPermission, setToken, logout, fetchUser }
})
