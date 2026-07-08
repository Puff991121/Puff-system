import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import AdminLayout from '@/layouts/AdminLayout.vue'

const routes: RouteRecordRaw[] = [
  { path: '/login', name: 'Login', component: () => import('@/views/login/LoginView.vue'), meta: { title: '登录', public: true } },
  {
    path: '/', component: AdminLayout, redirect: '/dashboard',
    children: [
      { path: 'dashboard', name: 'Dashboard', component: () => import('@/views/dashboard/DashboardView.vue'), meta: { title: '数据概览' } },
      { path: 'orders', name: 'Orders', component: () => import('@/views/order/OrderListView.vue'), meta: { title: '订单管理' } },
      { path: 'expenses', name: 'Expenses', component: () => import('@/views/expense/ExpenseListView.vue'), meta: { title: '消费记录' } },
      { path: 'assets', name: 'Assets', component: () => import('@/views/asset/AssetManagementView.vue'), meta: { title: '资产管理' } },
      { path: 'account-data', name: 'AccountData', component: () => import('@/views/account/AccountDataView.vue'), meta: { title: '账号数据' } },
      { path: 'settings', name: 'Settings', component: () => import('@/views/system/SettingsView.vue'), meta: { title: '系统设置' } },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/dashboard' },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to) => {
  document.title = `${String(to.meta.title || '管理后台')} · Puff Admin`
  // 后端登录接口就绪后，可取消下一行注释启用登录鉴权。
  if (!to.meta.public && !localStorage.getItem('access_token')) {
    return '/login'
  }

  if (to.path === '/login' && localStorage.getItem('access_token')) {
    return '/dashboard'
  }
})

export default router
