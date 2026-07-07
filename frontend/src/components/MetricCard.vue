<script setup lang="ts">
import type { Component } from 'vue'

defineProps<{ label: string; value: string; icon: Component; accent: string }>()
</script>

<template>
  <article class="metric-card" :style="{ '--accent': accent }">
    <span class="metric-icon"><el-icon><component :is="icon" /></el-icon></span>
    <div class="metric-content"><strong>{{ value }}</strong><p>{{ label }}</p></div>
    <div class="metric-line"><span></span></div>
  </article>
</template>
