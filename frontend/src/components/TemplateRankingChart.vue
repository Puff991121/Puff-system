<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { init, use, type ECharts } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { getOrderTemplateRanking, type OrderTemplateRankingItem } from '@/api/orders'

use([BarChart, GridComponent, TooltipComponent, CanvasRenderer])

const loading = ref(true)
const failed = ref(false)
const ranking = ref<OrderTemplateRankingItem[]>([])
const chartRef = ref<HTMLDivElement>()
const chartHeight = computed(() => Math.max(220, ranking.value.length * 44 + 40))
let chart: ECharts | undefined
let resizeObserver: ResizeObserver | undefined
let disposed = false

const renderChart = () => {
  if (!chartRef.value || disposed || !ranking.value.length) return
  chart ??= init(chartRef.value)
  const labelWidth = Math.min(240, Math.max(80, chartRef.value.clientWidth * 0.28))

  chart.setOption({
    grid: { top: 8, right: 64, bottom: 24, left: 0, containLabel: true },
    tooltip: {
      trigger: 'item',
      renderMode: 'richText',
      confine: true,
      formatter: '{b}\n订单数：{c} 单',
    },
    xAxis: {
      type: 'value',
      minInterval: 1,
      axisLabel: { color: '#929c97', fontSize: 10 },
      splitLine: { lineStyle: { color: '#edeee9', type: 'dashed' } },
    },
    yAxis: {
      type: 'category',
      inverse: true,
      data: ranking.value.map((item) => item.template),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: {
        color: '#3d4c45',
        fontSize: 12,
        margin: 16,
        width: labelWidth,
        overflow: 'truncate',
        formatter: (value: string, index: number) => `${ranking.value[index].rank}.  ${value}`,
      },
    },
    series: [{
      name: '订单数',
      type: 'bar',
      barWidth: 18,
      showBackground: true,
      backgroundStyle: { color: '#f2f5f0', borderRadius: [0, 4, 4, 0] },
      itemStyle: { borderRadius: [0, 4, 4, 0] },
      label: {
        show: true,
        position: 'right',
        distance: 10,
        color: '#3d4c45',
        fontSize: 12,
        formatter: '{c} 单',
      },
      data: ranking.value.map((item) => ({
        name: `第 ${item.rank} 名 · ${item.template}`,
        value: item.count,
        itemStyle: { color: ['#16352d', '#169a6c', '#51bc91'][item.rank - 1] || '#8fc8b0' },
      })),
    }],
  }, true)
}

const loadRanking = async () => {
  loading.value = true
  failed.value = false
  try {
    const result = await getOrderTemplateRanking()
    if (disposed) return
    ranking.value = result.data.items
    await nextTick()
    renderChart()
  } catch {
    failed.value = true
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (chartRef.value) {
    resizeObserver = new ResizeObserver(() => {
      chart?.resize()
      renderChart()
    })
    resizeObserver.observe(chartRef.value)
  }
  void loadRanking()
})

onBeforeUnmount(() => {
  disposed = true
  resizeObserver?.disconnect()
  chart?.dispose()
})
</script>

<template>
  <section v-loading="loading" class="panel template-ranking-panel">
    <div class="panel-title">
      <div><span>模板销量 TOP 10</span><small>按累计订单数排名 · 相同模板合并统计</small></div>
      <em class="ranking-badge">累计订单</em>
    </div>
    <div class="ranking-chart-wrap" :style="{ height: `${chartHeight}px` }">
      <div ref="chartRef" class="ranking-chart" aria-hidden="true"></div>
      <div v-if="!loading && failed" class="chart-empty ranking-state" role="status">
        <span>模板排名加载失败</span><el-button text type="primary" @click="loadRanking">重新加载</el-button>
      </div>
      <div v-else-if="!loading && !ranking.length" class="chart-empty ranking-state" role="status">
        <span>暂无订单数据</span><small>新增订单后，将自动统计模板销量排名</small>
      </div>
    </div>
    <ol v-if="ranking.length && !failed" class="visually-hidden" aria-label="模板销量前十排名">
      <li v-for="item in ranking" :key="item.template" :value="item.rank">
        {{ item.template }}，{{ item.count }} 单
      </li>
    </ol>
  </section>
</template>

<style scoped>
.template-ranking-panel {
  min-width: 0;
  padding: 22px;
}

.ranking-badge {
  flex-shrink: 0;
  padding: 6px 10px;
  border: 1px solid #dce9df;
  border-radius: 6px;
  color: var(--green-600);
  background: #f1f7f1;
  font-size: 10px;
  font-style: normal;
}

.ranking-chart-wrap {
  position: relative;
}

.ranking-chart {
  width: 100%;
  height: 100%;
}

.ranking-state {
  align-content: center;
  gap: 8px;
}

.ranking-state small {
  font-size: 11px;
}

@media (max-width: 760px) {
  .template-ranking-panel {
    padding: 18px 14px;
  }

  .panel-title {
    gap: 12px;
  }
}
</style>
