<template>
  <el-aside width="220px" class="sidebar">
    <!-- Logo 区域 -->
    <div class="logo-area">
      <div class="logo-icon">PC</div>
      <div class="logo-text">
        <span class="logo-title">PlantCare</span>
        <span class="logo-sub">植物病害识别</span>
      </div>
    </div>

    <!-- 导航菜单 -->
    <nav class="nav-list">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :class="{ active: isRouteActive(item.path) }"
      >
        <span class="nav-icon">{{ item.icon }}</span>
        <span class="nav-label">{{ item.label }}</span>
      </router-link>
    </nav>

    <!-- 底部用户区域 -->
    <div class="sidebar-footer">
      <div class="user-info" v-if="userStore.userInfo">
        <div class="avatar">{{ userStore.userInfo.username.charAt(0).toUpperCase() }}</div>
        <div class="user-meta">
          <span class="user-name">{{ userStore.userInfo.username }}</span>
          <span class="user-role">{{ roleLabel }}</span>
        </div>
      </div>
      <button class="logout-btn" @click="userStore.logout()">
        <span>退出登录</span>
      </button>
    </div>
  </el-aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from '../stores/user'

const route = useRoute()
const userStore = useUserStore()

const navItems = computed(() => {
  const baseItems: Array<{ path: string; icon: string; label: string }> = []
  baseItems.push({ path: '/dashboard', icon: '📊', label: '数据看板' })
  const isAdminRole = userStore.isAdmin
  if (userStore.hasPermission('predict:single')) {
    baseItems.push({ path: '/predict', icon: '🌿', label: '病害识别' })
  }
  if (userStore.hasPermission('history:view')) {
    baseItems.push({ path: '/history', icon: '🕘', label: '识别历史' })
  }
  if (userStore.hasPermission('dataset:view')) {
    baseItems.push({ path: '/dataset', icon: '🗂️', label: '数据集浏览' })
  }
  if (isAdminRole || userStore.hasPermission('admin:user')) {
    baseItems.push({ path: '/admin/users', icon: '👥', label: '用户管理' })
  }
  if (isAdminRole || userStore.hasPermission('admin:role')) {
    baseItems.push({ path: '/admin/roles', icon: '🛡️', label: '角色权限' })
  }
  if (isAdminRole || userStore.hasPermission('admin:alert')) {
    baseItems.push({ path: '/admin/alerts', icon: '🚨', label: '区域预警' })
  }
  return baseItems
})

function isRouteActive(path: string) {
  return route.path === path || route.path.startsWith(`${path}/`)
}

const roleLabel = computed(() => (
  userStore.currentRole === 'admin'
    ? '系统管理员'
    : userStore.currentRole === 'expert'
      ? '专家用户'
      : '诊断用户'
))
</script>

<style scoped>
.sidebar {
  background: linear-gradient(180deg, #fbf4f6 0%, #faf7f8 40%, #f1f7f5 100%);
  display: flex;
  flex-direction: column;
  border-right: 1px solid rgba(220, 210, 218, 0.6);
  padding: 0;
  overflow: hidden;
}

/* Logo */
.logo-area {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 28px 20px 24px;
}
.logo-icon {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  background: linear-gradient(135deg, var(--pink-light), var(--lavender-light));
  color: var(--pink-deep);
  font-weight: 800;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  letter-spacing: 1px;
  box-shadow: var(--shadow-soft);
}
.logo-text {
  display: flex;
  flex-direction: column;
}
.logo-title {
  font-size: 20px;
  font-weight: 800;
  background: linear-gradient(135deg, var(--pink-deep), #8e6f7c);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1.2;
}
.logo-sub {
  font-size: 11px;
  color: var(--text-muted);
  font-weight: 600;
}

/* Navigation */
.nav-list {
  flex: 1;
  padding: 8px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  overflow-y: auto;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-radius: var(--radius-sm);
  text-decoration: none;
  color: var(--text-secondary);
  font-weight: 600;
  font-size: 14px;
  transition: all 0.25s ease;
  position: relative;
  overflow: hidden;
}
.nav-item::after {
  content: '';
  position: absolute;
  left: 6px;
  top: 50%;
  width: 3px;
  height: 18px;
  border-radius: 999px;
  background: var(--pink-deep);
  transform: translateY(-50%) scaleY(0.4);
  opacity: 0;
  transition: opacity 0.25s, transform 0.25s;
}
.nav-item::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: linear-gradient(135deg, var(--pink-light), var(--lavender-light));
  opacity: 0;
  transition: opacity 0.25s;
}
.nav-item:hover::before {
  opacity: 0.6;
}
.nav-item.active::before {
  opacity: 1;
}
.nav-item.active::after {
  opacity: 1;
  transform: translateY(-50%) scaleY(1);
}
.nav-item:hover,
.nav-item.active {
  color: var(--pink-deep);
}
.nav-item.active {
  font-weight: 700;
  box-shadow: 0 2px 12px rgba(178, 106, 127, 0.14);
}
.nav-icon {
  font-size: 13px;
  width: 22px;
  height: 22px;
  border-radius: 8px;
  background: var(--lavender-light);
  color: var(--text-secondary);
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}
.nav-item.active .nav-icon {
  background: var(--pink-light);
  color: var(--pink-deep);
}
.nav-label {
  position: relative;
  z-index: 1;
}

/* Footer */
.sidebar-footer {
  padding: 16px;
  border-top: 1px solid rgba(244, 214, 236, 0.5);
}
.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}
.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--pink), var(--lavender));
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 15px;
  flex-shrink: 0;
}
.user-meta {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.user-name {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.user-role {
  font-size: 11px;
  color: var(--text-muted);
}
.logout-btn {
  width: 100%;
  padding: 8px;
  border: 1.5px solid #fecdd3;
  border-radius: var(--radius-sm);
  background: rgba(255, 228, 230, 0.4);
  color: #e11d48;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.logout-btn:hover {
  background: #ffe4e6;
  border-color: #fda4af;
}
</style>
