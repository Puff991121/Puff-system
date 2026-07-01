<script setup lang="ts">
import { Calendar, Coin, ShoppingCart, UserFilled } from '@element-plus/icons-vue'
import MetricCard from '@/components/MetricCard.vue'

const metrics = [
  { label: '总用户数', value: '12,860', trend: '+12.5%', positive: true, icon: UserFilled, accent: '#19a974' },
  { label: '今日订单', value: '1,024', trend: '+8.2%', positive: true, icon: ShoppingCart, accent: '#e59b37' },
  { label: '本月收入', value: '¥ 386,240', trend: '+18.7%', positive: true, icon: Coin, accent: '#3c82f6' },
  { label: '待处理事项', value: '24', trend: '-3.1%', positive: false, icon: Calendar, accent: '#e26a55' },
]

const orders = [
  { id: '#PF-20260701-08', customer: '林映雪', product: '企业专业版', amount: '¥ 2,899', status: '已完成' },
  { id: '#PF-20260701-07', customer: '顾北辰', product: '团队协作版', amount: '¥ 1,299', status: '处理中' },
  { id: '#PF-20260701-06', customer: '苏明月', product: '企业专业版', amount: '¥ 2,899', status: '已完成' },
  { id: '#PF-20260701-05', customer: '周予安', product: '基础版', amount: '¥ 399', status: '待支付' },
]

const bars = [48, 62, 55, 78, 68, 84, 76, 92, 87, 95, 82, 100]
</script>

<template>
  <div class="dashboard page-enter">
    <div class="welcome-row">
      <div><p class="kicker">WEDNESDAY · 01 JULY</p><h2>早上好，管理员。</h2><p>这里是今天的业务运行概况，一切看起来都很稳。</p></div>
      <el-button type="primary" size="large">导出数据</el-button>
    </div>
    <div class="metric-grid"><MetricCard v-for="item in metrics" :key="item.label" v-bind="item" /></div>
    <div class="dashboard-grid">
      <section class="panel chart-panel">
        <div class="panel-title"><div><span>收入趋势</span><small>最近 12 个月</small></div><el-select model-value="2026" style="width: 100px"><el-option label="2026" value="2026" /></el-select></div>
        <div class="chart-area">
          <div class="chart-y"><span>40万</span><span>30万</span><span>20万</span><span>10万</span><span>0</span></div>
          <div class="bars"><div v-for="(bar, index) in bars" :key="index" class="bar-column"><div class="bar-track"><i :style="{ height: `${bar}%` }"></i></div><span>{{ index + 1 }}月</span></div></div>
        </div>
      </section>
      <section class="panel activity-panel">
        <div class="panel-title"><div><span>实时动态</span><small>系统最新事件</small></div><button>查看全部</button></div>
        <div class="activity-list">
          <div><i class="green"></i><p><strong>新增企业用户</strong><span>上海未名科技完成注册</span><small>3 分钟前</small></p></div>
          <div><i class="amber"></i><p><strong>订单等待处理</strong><span>订单 #PF-20260701-07</span><small>12 分钟前</small></p></div>
          <div><i class="blue"></i><p><strong>系统版本更新</strong><span>后台已升级至 v0.1.0</span><small>1 小时前</small></p></div>
        </div>
      </section>
    </div>
    <section class="panel table-panel">
      <div class="panel-title"><div><span>最近订单</span><small>今日最新交易记录</small></div><button>查看全部 →</button></div>
      <el-table :data="orders">
        <el-table-column prop="id" label="订单编号" min-width="180" /><el-table-column prop="customer" label="客户" /><el-table-column prop="product" label="产品" /><el-table-column prop="amount" label="金额" />
        <el-table-column label="状态"><template #default="scope"><el-tag :type="scope.row.status === '已完成' ? 'success' : scope.row.status === '处理中' ? 'warning' : 'info'" effect="light" round>{{ scope.row.status }}</el-tag></template></el-table-column>
      </el-table>
    </section>
  </div>
</template>
