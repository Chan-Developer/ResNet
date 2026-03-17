<template>
  <div class="confidence-bar">
    <div class="bar-track">
      <div class="bar-fill" :style="{ width: percent + '%', background: gradient }"></div>
    </div>
    <span class="bar-label" :style="{ color: labelColor }">{{ label }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ value: number }>()

const percent = computed(() => Math.round(props.value * 10000) / 100)
const label = computed(() => `${percent.value.toFixed(1)}%`)

const gradient = computed(() => {
  if (percent.value >= 80) return 'linear-gradient(90deg, var(--green-light), var(--green-deep))'
  if (percent.value >= 50) return 'linear-gradient(90deg, var(--peach-light), var(--peach))'
  return 'linear-gradient(90deg, var(--pink-light), var(--pink-deep))'
})

const labelColor = computed(() => {
  if (percent.value >= 80) return 'var(--green-deep)'
  if (percent.value >= 50) return '#b7791f'
  return 'var(--pink-deep)'
})
</script>

<style scoped>
.confidence-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 80px;
}
.bar-track {
  flex: 1;
  height: 10px;
  background: var(--lavender-light);
  border-radius: 10px;
  overflow: hidden;
}
.bar-fill {
  height: 100%;
  border-radius: 10px;
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}
.bar-label {
  font-size: 12px;
  font-weight: 800;
  min-width: 48px;
  text-align: right;
}
</style>
