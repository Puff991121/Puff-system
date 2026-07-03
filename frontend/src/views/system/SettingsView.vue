<script setup lang="ts">
import { reactive } from 'vue'
import { ElMessage } from 'element-plus'
const form = reactive({ name: 'Puff Admin', description: '简洁、可靠的业务管理后台', email: 'admin@puff.dev', timezone: 'Asia/Shanghai', notifications: true })
const save = () => ElMessage.success('设置已保存')
</script>

<template>
  <div class="page-enter settings-page">
    <div class="page-heading"><div><h2>系统设置</h2><p>调整系统基本信息与通知偏好。</p></div></div>
    <section class="panel settings-panel">
      <div class="settings-copy"><span>01</span><div><h3>基本信息</h3><p>这些信息会展示在管理端的标题与通知邮件中。</p></div></div>
      <el-form :model="form" label-position="top">
        <el-form-item label="系统名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="系统描述"><el-input v-model="form.description" type="textarea" :rows="3" /></el-form-item>
        <div class="form-grid"><el-form-item label="管理员邮箱"><el-input v-model="form.email" /></el-form-item><el-form-item label="默认时区"><el-select v-model="form.timezone"><el-option label="中国标准时间 (UTC+8)" value="Asia/Shanghai" /></el-select></el-form-item></div>
        <el-form-item label="异常通知"><el-switch v-model="form.notifications" /><span class="field-help">系统出现异常时向管理员发送邮件</span></el-form-item>
        <el-button type="primary" size="large" @click="save">保存设置</el-button>
      </el-form>
    </section>
  </div>
</template>
