<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { LegendComponent, TooltipComponent } from 'echarts/components'
import { PieChart } from 'echarts/charts'
import { CanvasRenderer } from 'echarts/renderers'
import { init, use, type ECharts } from 'echarts/core'
import { Calendar, Coin, ShoppingCart } from '@element-plus/icons-vue'
import { getAssetPage, type AssetAccount } from '@/api/assets'
import { getOrderSummary, getOrderTrend, type OrderSummary } from '@/api/orders'
import MetricCard from '@/components/MetricCard.vue'

use([PieChart, TooltipComponent, LegendComponent, CanvasRenderer])

const now = ref(new Date())
let clockTimer: ReturnType<typeof setInterval> | undefined
const selectedYear = ref(new Date().getFullYear())
const availableYears = Array.from({ length: 5 }, (_, index) => selectedYear.value - index)
const revenueLoading = ref(false)
const assetLoading = ref(false)
const summaryLoading = ref(false)
const orderSummary = ref<OrderSummary>()
const monthlyRevenue = ref(Array.from({ length: 12 }, () => 0))
const assetAccounts = ref<AssetAccount[]>([])
const assetChartRef = ref<HTMLDivElement>()
let assetChart: ECharts | undefined
let assetChartResizeObserver: ResizeObserver | undefined

const maxRevenue = computed(() => Math.max(...monthlyRevenue.value, 0))
const revenueScale = computed(() => {
  if (maxRevenue.value === 0) return 10000
  const magnitude = 10 ** Math.floor(Math.log10(maxRevenue.value))
  return Math.ceil(maxRevenue.value / magnitude) * magnitude
})
const revenueAxis = computed(() => Array.from(
  { length: 5 },
  (_, index) => revenueScale.value * (4 - index) / 4,
))
const bars = computed(() => monthlyRevenue.value.map((amount) => (
  amount === 0 ? 0 : Math.max((amount / revenueScale.value) * 100, 3)
)))

const formatCompactMoney = (value: number) => {
  if (value >= 10000) return `${Number((value / 10000).toFixed(1))}万`
  return new Intl.NumberFormat('zh-CN', { maximumFractionDigits: 0 }).format(value)
}

const formatMoney = (value: number) => new Intl.NumberFormat('zh-CN', {
  style: 'currency',
  currency: 'CNY',
  minimumFractionDigits: 2,
}).format(value)

const formatMetricMoney = (value?: string) => {
  if (value === undefined) return '--'
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(Number(value))
}

const metrics = computed(() => [
  {
    label: '总收入',
    value: formatMetricMoney(orderSummary.value?.total_amount),
    icon: Coin,
    accent: '#19a974',
  },
  {
    label: '今日订单',
    value: orderSummary.value ? new Intl.NumberFormat('zh-CN').format(orderSummary.value.today_count) : '--',
    icon: ShoppingCart,
    accent: '#e59b37',
  },
  {
    label: '本月收入',
    value: formatMetricMoney(orderSummary.value?.month_amount),
    icon: Coin,
    accent: '#3c82f6',
  },
  { label: '待处理事项', value: '24', icon: Calendar, accent: '#e26a55' },
])

const loadOrderSummary = async () => {
  summaryLoading.value = true
  try {
    const result = await getOrderSummary()
    orderSummary.value = result.data
  } finally {
    summaryLoading.value = false
  }
}

const loadRevenueTrend = async () => {
  revenueLoading.value = true
  try {
    const result = await getOrderTrend(selectedYear.value)
    const amounts = Array.from({ length: 12 }, () => 0)
    result.data.items.forEach((item) => {
      amounts[item.month - 1] = Number(item.amount)
    })
    monthlyRevenue.value = amounts
  } finally {
    revenueLoading.value = false
  }
}

const renderAssetChart = () => {
  if (!assetChartRef.value) return
  assetChart ??= init(assetChartRef.value)
  const data = assetAccounts.value
    .map((item) => ({ name: item.account, value: Number(item.amount) }))
    .filter((item) => item.value > 0)

  assetChart.setOption({
    color: ['#15966c', '#51bc91', '#8fd3b8', '#e7ad4a', '#528ce5', '#85a9e8', '#d36f5c'],
    tooltip: {
      trigger: 'item',
      formatter: (params: { name: string; value: number; percent: number }) =>
        `${params.name}<br/>${formatMoney(params.value)} · ${params.percent}%`,
    },
    legend: {
      type: 'scroll',
      orient: 'vertical',
      right: 0,
      top: 'middle',
      width: '42%',
      itemWidth: 8,
      itemHeight: 8,
      itemGap: 12,
      textStyle: { color: '#697570', fontSize: 11 },
      formatter: (name: string) => {
        const item = data.find((entry) => entry.name === name)
        return `${name}  ${item ? formatCompactMoney(item.value) : ''}`
      },
    },
    series: [{
      name: '资产明细',
      type: 'pie',
      radius: ['48%', '72%'],
      center: ['31%', '50%'],
      avoidLabelOverlap: true,
      itemStyle: { borderColor: '#fff', borderWidth: 3, borderRadius: 5 },
      label: { show: false },
      emphasis: { scaleSize: 6 },
      data,
    }],
  }, true)
}

const loadAssets = async () => {
  assetLoading.value = true
  try {
    const result = await getAssetPage()
    assetAccounts.value = result.data.assets
    await nextTick()
    renderAssetChart()
  } finally {
    assetLoading.value = false
  }
}

const currentDateTime = computed(() => {
  const date = now.value
  const weekday = new Intl.DateTimeFormat('en-US', { weekday: 'long' }).format(date).toUpperCase()
  const day = String(date.getDate()).padStart(2, '0')
  const month = new Intl.DateTimeFormat('en-US', { month: 'long' }).format(date).toUpperCase()
  const time = new Intl.DateTimeFormat('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  }).format(date)

  return `${weekday} · ${day} ${month} · ${time}`
})

const greeting = computed(() => {
  const hour = now.value.getHours()

  if (hour < 11) return '早上好'
  if (hour < 18) return '中午好'
  return '晚上好'
})

onMounted(() => {
  now.value = new Date()
  clockTimer = setInterval(() => {
    now.value = new Date()
  }, 1000)
  void loadRevenueTrend()
  void loadOrderSummary()
  void loadAssets()
  if (assetChartRef.value) {
    assetChartResizeObserver = new ResizeObserver(() => assetChart?.resize())
    assetChartResizeObserver.observe(assetChartRef.value)
  }
})

onBeforeUnmount(() => {
  if (clockTimer) clearInterval(clockTimer)
  assetChartResizeObserver?.disconnect()
  assetChart?.dispose()
})

</script>

<template>
  <div class="dashboard page-enter">
    <div class="welcome-row">
      <div>
        <p class="kicker">{{ currentDateTime }}</p>
        <h2>{{ greeting }}，Puff！</h2>
      </div>
    </div>
    <div v-loading="summaryLoading" class="metric-grid">
      <MetricCard v-for="item in metrics" :key="item.label" v-bind="item" />
    </div>
    <div class="dashboard-grid">
      <section v-loading="revenueLoading" class="panel chart-panel">
        <div class="panel-title">
          <div><span>收入趋势</span><small>{{ selectedYear }} 年订单实收金额</small></div><el-select v-model="selectedYear"
            style="width: 100px" @change="loadRevenueTrend"><el-option v-for="year in availableYears" :key="year"
              :label="year" :value="year" /></el-select>
        </div>
        <div class="chart-area">
          <div class="chart-y"><span v-for="value in revenueAxis" :key="value">{{ formatCompactMoney(value) }}</span>
          </div>
          <div class="bars">
            <div v-for="(bar, index) in bars" :key="index" class="bar-column">
              <div class="bar-track" :title="`${index + 1} 月：${formatMoney(monthlyRevenue[index] ?? 0)}`"><i
                  :class="{ empty: bar === 0 }" :style="{ height: `${bar}%` }"></i></div><span>{{ index + 1 }}月</span>
            </div>
          </div>
        </div>
      </section>
      <section v-loading="assetLoading" class="panel activity-panel asset-chart-panel">
        <div class="panel-title">
          <div><span>资产明细</span><small>各资产账户余额占比</small></div>
        </div>
        <div class="asset-chart-wrap">
          <div ref="assetChartRef" class="asset-chart" role="img" aria-label="资产账户余额占比饼图"></div>
          <div v-if="!assetLoading && !assetAccounts.some((item) => Number(item.amount) > 0)" class="chart-empty">
            暂无资产数据
          </div>
        </div>
      </section>
    </div>

  </div>
</template>
