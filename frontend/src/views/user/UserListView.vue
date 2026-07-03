<script setup lang="ts">
import { ref } from 'vue'
import { Plus, Search } from '@element-plus/icons-vue'

const keyword = ref('')
const users = [
  { name: '林映雪', account: 'linyx', email: 'lin@example.com', role: '超级管理员', status: true, createdAt: '2026-06-21' },
  { name: '顾北辰', account: 'gubeichen', email: 'gu@example.com', role: '运营人员', status: true, createdAt: '2026-06-25' },
  { name: '苏明月', account: 'sumingyue', email: 'su@example.com', role: '访客', status: false, createdAt: '2026-06-28' },
]
</script>

<template>
  <div class="page-enter">
    <div class="page-heading"><div><h2>用户管理</h2><p>管理后台账号、角色与使用状态。</p></div><el-button type="primary" :icon="Plus" size="large">新增用户</el-button></div>
    <section class="panel resource-panel">
      <div class="toolbar"><el-input v-model="keyword" :prefix-icon="Search" placeholder="搜索姓名、账号或邮箱" clearable /><el-select placeholder="全部角色"><el-option label="超级管理员" value="admin" /><el-option label="运营人员" value="operator" /></el-select><el-select placeholder="全部状态"><el-option label="启用" value="active" /><el-option label="停用" value="disabled" /></el-select></div>
      <el-table :data="users">
        <el-table-column label="用户" min-width="180"><template #default="scope"><div class="user-cell"><span>{{ scope.row.name.slice(0, 1) }}</span><div><strong>{{ scope.row.name }}</strong><small>@{{ scope.row.account }}</small></div></div></template></el-table-column>
        <el-table-column prop="email" label="邮箱" min-width="200" /><el-table-column prop="role" label="角色" /><el-table-column label="状态"><template #default="scope"><span class="status-dot" :class="{ off: !scope.row.status }">{{ scope.row.status ? '启用' : '停用' }}</span></template></el-table-column><el-table-column prop="createdAt" label="创建日期" /><el-table-column label="操作" align="right"><template #default><el-button link type="primary">编辑</el-button><el-button link>更多</el-button></template></el-table-column>
      </el-table>
      <div class="pagination"><span>共 3 条记录</span><el-pagination layout="prev, pager, next" :total="3" /></div>
    </section>
  </div>
</template>
