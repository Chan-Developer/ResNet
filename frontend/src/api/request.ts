import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'

const request = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

function normalizeValidationMessage(field: string | null, message: string): string {
  if (field === 'email' && message.includes('valid email address')) {
    return '邮箱格式不正确'
  }
  if (message.toLowerCase() === 'field required') {
    return field ? `${field} 不能为空` : '请求参数不完整'
  }
  return message
}

function extractErrorMessage(payload: unknown): string | null {
  if (!payload) return null
  if (typeof payload === 'string') return payload.trim() || null

  if (Array.isArray(payload)) {
    const messages = payload
      .map((item) => {
        if (typeof item === 'string') return item.trim()
        if (item && typeof item === 'object' && 'msg' in item) {
          const rawMessage = String(item.msg || '').trim()
          const locList = Array.isArray((item as any).loc) ? (item as any).loc : []
          const loc = locList.length ? locList[locList.length - 1] : null
          const message = normalizeValidationMessage(loc ? String(loc) : null, rawMessage)
          return loc && message === rawMessage ? `${String(loc)}: ${message}` : message
        }
        return ''
      })
      .filter(Boolean)
    return messages.length ? messages.join('；') : null
  }

  if (typeof payload === 'object') {
    if ('detail' in payload) {
      return extractErrorMessage((payload as any).detail)
    }
    if ('message' in payload && typeof (payload as any).message === 'string') {
      const message = (payload as any).message.trim()
      return message || null
    }
  }

  return null
}

request.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

request.interceptors.response.use(
  (resp) => {
    const data = resp.data
    if (data.code !== undefined && data.code !== 0) {
      ElMessage.error(data.message || '请求失败')
      return Promise.reject(new Error(data.message))
    }
    return data
  },
  (err) => {
    const message = extractErrorMessage(err.response?.data)
      || extractErrorMessage(err.response?.data?.detail)
      || err.message
      || '网络错误'
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      router.push('/login')
      ElMessage.warning('登录已过期，请重新登录')
    } else {
      ElMessage.error(message)
    }
    return Promise.reject(err)
  },
)

export default request
