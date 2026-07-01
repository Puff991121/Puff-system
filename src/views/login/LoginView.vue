<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
const router = useRouter()
const loading = ref(false)
const form = reactive({ username: 'admin', password: 'admin123' })
const submit = async () => { loading.value = true; await new Promise((r) => setTimeout(r, 500)); loading.value = false; router.push('/dashboard') }
</script>

<template>
  <main class="login-page">
    <section class="login-art"><div class="login-brand"><span>P</span><strong>Puff Admin</strong></div><div class="art-copy"><span>CONTROL YOUR FLOW</span><h1>把复杂的业务，<br />收进清晰的秩序里。</h1><p>一个为团队效率而生的现代管理系统。</p></div><div class="orbit orbit-one"></div><div class="orbit orbit-two"></div></section>
    <section class="login-form-wrap"><form class="login-card" @submit.prevent="submit"><span class="kicker">WELCOME BACK</span><h2>登录管理后台</h2><p>请输入你的管理员账号继续</p><label>账号<el-input v-model="form.username" size="large" /></label><label>密码<el-input v-model="form.password" type="password" show-password size="large" /></label><div class="login-options"><el-checkbox>记住我</el-checkbox><a href="#">忘记密码？</a></div><el-button native-type="submit" type="primary" size="large" :loading="loading">登录</el-button><small>演示模式：可直接点击登录</small></form></section>
  </main>
</template>
