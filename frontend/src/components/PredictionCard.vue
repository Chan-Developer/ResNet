<template>
  <div class="prediction-card">
    <div v-if="imageUrl" class="card-image">
      <el-image :src="imageUrl" fit="contain" class="preview-img" />
    </div>

    <div class="card-body">
      <!-- Best prediction -->
      <div v-if="result?.best_prediction" class="best-result">
        <div class="best-tag">
          <span class="tag-dot"></span>
          <span class="tag-name">{{ result.best_prediction.display_name }}</span>
        </div>
        <ConfidenceBar :value="result.best_prediction.confidence" />
      </div>

      <!-- Top-K list -->
      <div class="topk-list">
        <div class="topk-title">Top {{ result?.top_k }} 候选</div>
        <div
          v-for="(item, idx) in result?.predictions"
          :key="item.class_index"
          class="topk-item"
        >
          <span class="topk-rank" :class="rankClass(idx)">{{ idx + 1 }}</span>
          <span class="topk-name">{{ item.display_name }}</span>
          <ConfidenceBar :value="item.confidence" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import ConfidenceBar from './ConfidenceBar.vue'

defineProps<{
  result: any
  imageUrl?: string
}>()

function rankClass(idx: number) {
  if (idx === 0) return 'gold'
  if (idx === 1) return 'silver'
  if (idx === 2) return 'bronze'
  return ''
}
</script>

<style scoped>
.prediction-card {
  background: var(--card-bg);
  backdrop-filter: var(--glass-blur);
  border: 1px solid var(--card-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-soft);
  transition: transform 0.3s, box-shadow 0.3s;
}
.prediction-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-hover);
}

.card-image {
  background: linear-gradient(135deg, var(--pink-light), var(--lavender-light));
  padding: 16px;
  display: flex;
  justify-content: center;
}
.preview-img {
  max-height: 200px;
  border-radius: var(--radius-sm);
}

.card-body {
  padding: 20px;
}

/* Best */
.best-result {
  margin-bottom: 16px;
}
.best-tag {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.tag-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--pink-deep);
  box-shadow: 0 0 0 4px var(--pink-light);
}
.tag-name {
  font-size: 16px;
  font-weight: 800;
  color: var(--text-primary);
}

/* Top-K */
.topk-list {
  border-top: 1px solid var(--lavender-light);
  padding-top: 12px;
}
.topk-title {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-muted);
  margin-bottom: 10px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.topk-item {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}
.topk-rank {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--lavender-light);
  color: var(--text-secondary);
  font-size: 11px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.topk-rank.gold {
  background: linear-gradient(135deg, #fde68a, #fbbf24);
  color: #92400e;
}
.topk-rank.silver {
  background: linear-gradient(135deg, #e5e7eb, #d1d5db);
  color: #4b5563;
}
.topk-rank.bronze {
  background: linear-gradient(135deg, #fed7aa, #fb923c);
  color: #7c2d12;
}
.topk-name {
  min-width: 140px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
