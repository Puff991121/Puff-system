<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowDown, Bell, Coin, DataAnalysis, Expand, Fold, Grid, Setting, ShoppingCart, User } from '@element-plus/icons-vue'
import { useAppStore } from '@/stores/app'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()
const userStore = useUserStore()
const pageTitle = computed(() => route.meta.title as string)

const logout = () => {
  userStore.logout()
  router.push('/login')
}
</script>

<template>
  <div class="admin-shell" :class="{ 'is-collapsed': appStore.sidebarCollapsed }">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark">P</div>
        <div class="brand-copy"><strong>Puff</strong><span>CONTROL ROOM</span></div>
      </div>
      <div class="nav-label">工作台</div>
      <el-menu :default-active="route.path" router :collapse="appStore.sidebarCollapsed">
        <el-menu-item index="/dashboard"><el-icon><Grid /></el-icon><template #title>数据概览</template></el-menu-item>
        <el-menu-item index="/orders"><el-icon><ShoppingCart /></el-icon><template #title>订单管理</template></el-menu-item>
        <el-menu-item index="/assets"><el-icon><Coin /></el-icon><template #title>资产管理</template></el-menu-item>
        <el-menu-item index="/account-data"><el-icon><DataAnalysis /></el-icon><template #title>账号数据</template></el-menu-item>
        <el-menu-item index="/users"><el-icon><User /></el-icon><template #title>用户管理</template></el-menu-item>
        <el-menu-item index="/settings"><el-icon><Setting /></el-icon><template #title>系统设置</template></el-menu-item>
      </el-menu>
      <div class="sidebar-status">
        <i></i><span>所有服务运行正常</span>
      </div>
    </aside>

    <main class="main-area">
      <header class="topbar">
        <div class="topbar-left">
          <button class="icon-button" aria-label="切换侧边栏" @click="appStore.toggleSidebar">
            <el-icon><Expand v-if="appStore.sidebarCollapsed" /><Fold v-else /></el-icon>
          </button>
          <div><span class="eyebrow">PUFF / ADMIN</span><h1>{{ pageTitle }}</h1></div>
        </div>
        <div class="topbar-actions">
          <button class="icon-button notification" aria-label="通知"><el-icon><Bell /></el-icon><i></i></button>
          <el-dropdown trigger="click" @command="logout">
            <button class="profile-button">
              <span class="avatar">管</span>
              <span class="profile-copy"><strong>{{ userStore.name }}</strong><small>{{ userStore.role }}</small></span>
              <el-icon><ArrowDown /></el-icon>
            </button>
            <template #dropdown><el-dropdown-menu><el-dropdown-item command="logout">退出登录</el-dropdown-item></el-dropdown-menu></template>
          </el-dropdown>
        </div>
      </header>
      <section class="page-content"><router-view v-slot="{ Component }"><transition name="page" mode="out-in"><component :is="Component" /></transition></router-view></section>
    </main>
  </div>
</template>
