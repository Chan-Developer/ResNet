import { createRouter, createWebHistory } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../stores/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
    meta: { guest: true },
  },
  {
    path: '/',
    redirect: '/dashboard',
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../views/DashboardView.vue'),
    meta: { auth: true },
  },
  {
    path: '/predict',
    name: 'Predict',
    component: () => import('../views/PredictView.vue'),
    meta: { auth: true, permissions: ['predict:single'] },
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('../views/HistoryView.vue'),
    meta: { auth: true, permissions: ['history:view'] },
  },
  {
    path: '/followup',
    name: 'Followup',
    component: () => import('../views/FollowupView.vue'),
    meta: { auth: true, permissions: ['followup:manage'] },
  },
  {
    path: '/dataset',
    name: 'Dataset',
    component: () => import('../views/DatasetView.vue'),
    meta: { auth: true, permissions: ['dataset:view'] },
  },
  {
    path: '/admin/users',
    name: 'AdminUsers',
    component: () => import('../views/AdminUsersView.vue'),
    meta: { auth: true, permissions: ['admin:user'] },
  },
  {
    path: '/admin/roles',
    name: 'AdminRoles',
    component: () => import('../views/AdminRolesView.vue'),
    meta: { auth: true, permissions: ['admin:role'] },
  },
  {
    path: '/admin/alerts',
    name: 'AdminAlerts',
    component: () => import('../views/AdminAlertsView.vue'),
    meta: { auth: true, permissions: ['admin:alert'] },
  },
  {
    path: '/admin/knowledge',
    name: 'AdminKnowledge',
    component: () => import('../views/AdminKnowledgeView.vue'),
    meta: { auth: true, permissions: ['admin:knowledge'] },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

function firstAllowedPath(userStore: ReturnType<typeof useUserStore>) {
  if (userStore.token) return '/dashboard'
  if (userStore.hasPermission('predict:single')) return '/predict'
  if (userStore.hasPermission('followup:manage')) return '/followup'
  if (userStore.hasPermission('history:view')) return '/history'
  if (userStore.hasPermission('dataset:view')) return '/dataset'
  if (userStore.hasPermission('admin:user')) return '/admin/users'
  if (userStore.hasPermission('admin:role')) return '/admin/roles'
  if (userStore.hasPermission('admin:alert')) return '/admin/alerts'
  if (userStore.hasPermission('admin:knowledge')) return '/admin/knowledge'
  return '/login'
}

router.beforeEach(async (to) => {
  const userStore = useUserStore()

  if (userStore.token && !userStore.userInfo) {
    await userStore.fetchUser()
  }

  if (to.meta.auth && !userStore.token) {
    return '/login'
  }
  if (to.meta.guest && userStore.token) {
    return '/dashboard'
  }

  const requiredPermissions = Array.isArray(to.meta.permissions) ? to.meta.permissions : []
  if (requiredPermissions.length > 0) {
    const ok = requiredPermissions.every((permission) => userStore.hasPermission(String(permission)))
    if (!ok) {
      ElMessage.warning('暂无权限访问该页面')
      const targetPath = firstAllowedPath(userStore)
      if (targetPath !== to.path) {
        return targetPath
      }
      return false
    }
  }
})

export default router
