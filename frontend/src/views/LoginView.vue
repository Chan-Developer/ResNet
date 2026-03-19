<template>
  <div class="login-wrapper">
    <!-- 装饰浮动元素 -->
    <div class="deco deco-1"></div>
    <div class="deco deco-2"></div>
    <div class="deco deco-3"></div>
    <div class="deco deco-4"></div>
    <div class="deco deco-5"></div>

    <div class="login-card">
      <div class="card-header">
        <div class="brand-icon">PC</div>
        <h2 class="brand-title">PlantCare</h2>
        <p class="brand-sub">智能植物病害识别系统</p>
      </div>

      <div class="tab-bar">
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'login' }"
          @click="activeTab = 'login'"
        >登录</button>
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'register' }"
          @click="activeTab = 'register'"
        >注册</button>
      </div>

      <!-- 登录表单 -->
      <form v-if="activeTab === 'login'" novalidate @submit.prevent="handleLogin" class="form">
        <div class="field">
          <label>用户名</label>
          <div class="input-wrap">
            <span class="input-icon">U</span>
            <input v-model="loginForm.username" placeholder="请输入用户名" />
          </div>
        </div>
        <div class="field">
          <label>密码</label>
          <div class="input-wrap">
            <span class="input-icon">P</span>
            <input v-model="loginForm.password" type="password" placeholder="请输入密码" />
          </div>
        </div>
        <button type="submit" class="submit-btn" :disabled="loading">
          <span v-if="loading" class="spinner"></span>
          {{ loading ? '登录中...' : '登录' }}
        </button>
      </form>

      <!-- 注册表单 -->
      <form v-else novalidate @submit.prevent="handleRegister" class="form">
        <div class="field">
          <label>用户名</label>
          <div class="input-wrap">
            <span class="input-icon">U</span>
            <input v-model="regForm.username" placeholder="请输入用户名" />
          </div>
        </div>
        <div class="field">
          <label>邮箱</label>
          <div class="input-wrap">
            <span class="input-icon">M</span>
            <input
              v-model="regForm.email"
              type="text"
              inputmode="email"
              autocapitalize="off"
              spellcheck="false"
              placeholder="请输入邮箱"
            />
          </div>
        </div>
        <div class="field">
          <label>密码</label>
          <div class="input-wrap">
            <span class="input-icon">P</span>
            <input v-model="regForm.password" type="password" placeholder="请输入密码" />
          </div>
        </div>
        <button type="submit" class="submit-btn" :disabled="loading">
          <span v-if="loading" class="spinner"></span>
          {{ loading ? '注册中...' : '注册' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { login, register } from '../api/auth'
import { useUserStore } from '../stores/user'
import { useRouter } from 'vue-router'

const userStore = useUserStore()
const router = useRouter()

const activeTab = ref('login')
const loading = ref(false)

const loginForm = reactive({ username: '', password: '' })
const regForm = reactive({ username: '', email: '', password: '' })

function isValidEmail(email: string) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

async function handleLogin() {
  if (loading.value) return
  const username = loginForm.username.trim()
  if (!username || !loginForm.password) {
    ElMessage.warning('请填写完整')
    return
  }
  loading.value = true
  try {
    const payload = {
      username,
      password: loginForm.password,
    }
    const res: any = await login(payload)
    userStore.setToken(res.data.access_token)
    await userStore.fetchUser()
    router.push('/predict')
    ElMessage.success('登录成功')
  } catch { /* handled by interceptor */ } finally {
    loading.value = false
  }
}

async function handleRegister() {
  if (loading.value) return
  const username = regForm.username.trim()
  const email = regForm.email.trim()
  if (!username || !email || !regForm.password) {
    ElMessage.warning('请填写完整')
    return
  }
  if (!isValidEmail(email)) {
    ElMessage.warning('请输入正确的邮箱地址')
    return
  }
  loading.value = true
  try {
    const payload = {
      username,
      email,
      password: regForm.password,
    }
    await register(payload)
    ElMessage.success('注册成功，请登录')
    activeTab.value = 'login'
    loginForm.username = payload.username
    loginForm.password = payload.password
  } catch { /* handled by interceptor */ } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background:
    radial-gradient(ellipse at 30% 20%, rgba(215, 161, 173, 0.28) 0%, transparent 55%),
    radial-gradient(ellipse at 70% 80%, rgba(157, 191, 182, 0.22) 0%, transparent 55%),
    radial-gradient(ellipse at 50% 50%, rgba(167, 199, 231, 0.12) 0%, transparent 60%),
    var(--bg);
  position: relative;
  overflow: hidden;
}

/* 装饰浮动 */
.deco {
  position: absolute;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--pink-light), var(--lavender-light));
  opacity: 0.35;
  animation: float 7s ease-in-out infinite;
  pointer-events: none;
}
.deco-1 { top: 10%; left: 8%; animation-delay: 0s; }
.deco-2 { top: 20%; right: 12%; animation-delay: 1.5s; width: 36px; height: 36px; }
.deco-3 { bottom: 15%; left: 15%; animation-delay: 3s; width: 54px; height: 54px; }
.deco-4 { bottom: 25%; right: 8%; animation-delay: 2s; width: 32px; height: 32px; }
.deco-5 { top: 50%; left: 5%; animation-delay: 4s; width: 28px; height: 28px; }

@keyframes float {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  33% { transform: translateY(-14px) rotate(5deg); }
  66% { transform: translateY(8px) rotate(-3deg); }
}

/* 登录卡片 */
.login-card {
  width: 400px;
  background: rgba(255, 255, 255, 0.86);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(230, 219, 226, 0.8);
  border-radius: var(--radius-xl);
  padding: 40px 36px 36px;
  box-shadow:
    0 12px 40px rgba(88, 70, 80, 0.12),
    0 2px 8px rgba(88, 70, 80, 0.06);
  position: relative;
  z-index: 1;
}

/* Header */
.card-header {
  text-align: center;
  margin-bottom: 28px;
}
.brand-icon {
  width: 56px;
  height: 56px;
  margin: 0 auto 10px;
  border-radius: 18px;
  background: linear-gradient(135deg, var(--pink-light), var(--lavender-light));
  color: var(--pink-deep);
  font-weight: 800;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8px;
}
.brand-title {
  margin: 0;
  font-size: 28px;
  font-weight: 800;
  background: linear-gradient(135deg, var(--pink-deep), #8b6b77, var(--green-deep));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.brand-sub {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--text-muted);
  font-weight: 600;
}

/* Tab Bar */
.tab-bar {
  display: flex;
  background: var(--lavender-light);
  border-radius: var(--radius-sm);
  padding: 4px;
  margin-bottom: 24px;
}
.tab-btn {
  flex: 1;
  padding: 10px;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.25s;
  background: transparent;
  color: var(--text-secondary);
}
.tab-btn.active {
  background: #fff;
  color: var(--pink-deep);
  box-shadow: 0 2px 8px rgba(178, 106, 127, 0.16);
}

/* Form */
.form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.field label {
  display: block;
  font-size: 13px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 6px;
}
.input-wrap {
  display: flex;
  align-items: center;
  background: rgba(248, 240, 244, 0.7);
  border: 1.5px solid #e8d8df;
  border-radius: var(--radius-sm);
  padding: 0 14px;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.input-wrap:focus-within {
  border-color: var(--pink);
  box-shadow: 0 0 0 3px rgba(215, 161, 173, 0.18);
}
.input-icon {
  font-size: 12px;
  margin-right: 10px;
  flex-shrink: 0;
  width: 22px;
  height: 22px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--lavender-light);
  color: var(--text-secondary);
  font-weight: 700;
}
.input-wrap input {
  flex: 1;
  border: none;
  background: transparent;
  padding: 12px 0;
  font-size: 14px;
  color: var(--text-primary);
  outline: none;
  font-family: inherit;
}
.input-wrap input::placeholder {
  color: var(--text-muted);
}

/* Submit */
.submit-btn {
  width: 100%;
  padding: 14px;
  border: none;
  border-radius: var(--radius-sm);
  background: linear-gradient(135deg, var(--pink-deep), #9a6f7a);
  color: #fff;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 4px;
}
.submit-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(178, 106, 127, 0.28);
}
.submit-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
