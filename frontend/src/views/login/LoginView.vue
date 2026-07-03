<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { login } from '@/api/auth'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
})

const submit = async () => {
  if (!form.username || !form.password) return

  loading.value = true

  try {
    const result = await login(form)

    userStore.setToken(result.access_token)

    await router.push('/dashboard')
  } finally {
    loading.value = false
  }
}
</script>
<template>
  <main class="login-page">
    <section class="login-art">
      <div class="login-brand"><span>P</span><strong>Puff Admin</strong></div>
      <div class="art-copy"><span>CONTROL YOUR FLOW</span>
        <h1>把复杂的业务，<br />收进清晰的秩序里。</h1>
        <p>一个为团队效率而生的现代管理系统。</p>
      </div>
      <div class="orbit orbit-one"></div>
      <div class="orbit orbit-two"></div>
    </section>
    <section class="login-form-wrap">
      <form class="login-card" @submit.prevent="submit"><span class="kicker">WELCOME BACK</span>
        <h2>登录管理后台</h2>
        <p>请输入你的管理员账号继续</p><label>账号<el-input v-model="form.username" size="large" /></label><label>密码<el-input
            v-model="form.password" type="password" show-password size="large" /></label>
        <br>
        <el-button native-type="submit" type="primary" size="large" :loading="loading">登录</el-button>
      </form>
    </section>
  </main>
</template>
