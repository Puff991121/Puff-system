import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import AdminLayout from '@/layouts/AdminLayout.vue'

const routes: RouteRecordRaw[] = [
  { path: '/login', name: 'Login', component: () => import('@/views/login/LoginView.vue'), meta: { title: '登录', public: true } },
  {
    path: '/', component: AdminLayout, redirect: '/dashboard',
    children: [
      { path: 'dashboard', name: 'Dashboard', component: () => import('@/views/dashboard/DashboardView.vue'), meta: { title: '数据概览' } },
      { path: 'users', name: 'Users', component: () => import('@/views/user/UserListView.vue'), meta: { title: '用户管理' } },
      { path: 'settings', name: 'Settings', component: () => import('@/views/system/SettingsView.vue'), meta: { title: '系统设置' } },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/dashboard' },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to) => {
  document.title = `${String(to.meta.title || '管理后台')} · Puff Admin`
  // 后端登录接口就绪后，可取消下一行注释启用登录鉴权。
  // if (!to.meta.public && !localStorage.getItem('access_token')) return '/login'
})

export default router
