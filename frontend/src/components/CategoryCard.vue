<template>
  <div class="category-card" @click="$emit('click')">
    <div class="card-emoji">{{ initial }}</div>
    <div class="card-info">
      <h4>{{ category.display_name }}</h4>
      <span class="card-count">{{ category.count }} 张</span>
    </div>
    <div class="card-arrow">›</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  category: { name: string; display_name: string; count: number }
}>()
defineEmits(['click'])

const initial = computed(() => {
  const text = props.category.display_name || props.category.name || ''
  return text.trim().charAt(0).toUpperCase() || 'P'
})
</script>

<style scoped>
.category-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: var(--card-bg);
  backdrop-filter: var(--glass-blur);
  border: 1.5px solid var(--card-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.25s ease;
  box-shadow: var(--shadow-soft);
}
.category-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-hover);
  border-color: var(--pink);
}

.card-emoji {
  font-size: 16px;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--green-light), var(--peach-light));
  border-radius: var(--radius-sm);
  flex-shrink: 0;
  font-weight: 800;
  color: var(--green-deep);
}

.card-info {
  flex: 1;
  min-width: 0;
}
.card-info h4 {
  margin: 0 0 2px;
  font-size: 13px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.3;
}
.card-count {
  font-size: 11px;
  color: var(--text-muted);
  font-weight: 600;
}

.card-arrow {
  font-size: 20px;
  color: var(--text-muted);
  font-weight: 300;
  transition: transform 0.2s;
}
.category-card:hover .card-arrow {
  transform: translateX(3px);
  color: var(--pink-deep);
}
</style>
