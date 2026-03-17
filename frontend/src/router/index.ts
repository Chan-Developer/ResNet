import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
    meta: { guest: true },
  },
  {
    path: '/',
    redirect: '/predict',
  },
  {
    path: '/predict',
    name: 'Predict',
    component: () => import('../views/PredictView.vue'),
    meta: { auth: true },
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('../views/HistoryView.vue'),
    meta: { auth: true },
  },
  {
    path: '/dataset',
    name: 'Dataset',
    component: () => import('../views/DatasetView.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.auth && !token) {
    next('/login')
  } else if (to.meta.guest && token) {
    next('/predict')
  } else {
    next()
  }
})

export default router
