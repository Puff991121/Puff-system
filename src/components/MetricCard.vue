<script setup lang="ts">
import type { Component } from 'vue'

defineProps<{ label: string; value: string; trend: string; positive?: boolean; icon: Component; accent: string }>()
</script>

<template>
  <article class="metric-card" :style="{ '--accent': accent }">
    <div class="metric-top"><span class="metric-icon"><el-icon><component :is="icon" /></el-icon></span><span class="metric-trend" :class="{ negative: !positive }">{{ trend }}</span></div>
    <strong>{{ value }}</strong><p>{{ label }}</p>
    <div class="metric-line"><span></span></div>
  </article>
</template>
