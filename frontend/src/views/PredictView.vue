<template>
  <div class="predict-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-icon">AI</div>
      <div>
        <h2>植物病害识别</h2>
        <p class="header-desc">上传植物叶片照片，AI 帮你快速诊断病害类型</p>
      </div>
    </div>

    <!-- 模式切换 -->
    <div class="mode-switch">
      <button
        class="mode-btn"
        :class="{ active: mode === 'single' }"
        @click="mode = 'single'"
      >
        <span>单张识别</span>
      </button>
      <button
        class="mode-btn"
        :class="{ active: mode === 'batch' }"
        @click="mode = 'batch'"
      >
        <span>批量识别</span>
      </button>
    </div>

    <!-- 上传区域 -->
    <ImageUploader :multiple="mode === 'batch'" :limit="10" @change="onFilesChange" />

    <!-- 操作栏 -->
    <div class="actions-bar">
      <div class="topk-field">
        <label>识别数量 Top-K</label>
        <el-input-number v-model="topK" :min="1" :max="maxTopK" size="default" />
      </div>
      <button class="predict-btn" :disabled="loading || !files.length" @click="handlePredict">
        <span v-if="loading" class="spinner"></span>
        {{ loading ? '识别中...' : '开始识别' }}
      </button>
    </div>

    <!-- 结果展示 -->
    <div v-if="results.length" class="results-section">
      <div class="section-title">
        <h3>识别结果</h3>
      </div>
      <div class="result-grid">
        <PredictionCard
          v-for="(r, i) in results"
          :key="i"
          :result="r"
          :image-url="previewUrls[i]"
        />
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="!results.length && !loading" class="empty-state">
      <div class="empty-icon">·</div>
      <p>上传植物照片开始识别吧~</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, ref } from 'vue'
import { ElMessage } from 'element-plus'
import ImageUploader from '../components/ImageUploader.vue'
import PredictionCard from '../components/PredictionCard.vue'
import { predictSingle, predictBatch } from '../api/predict'

const mode = ref<'single' | 'batch'>('single')
const topK = ref(5)
const maxTopK = 20
const loading = ref(false)
const files = ref<File[]>([])
const previewUrls = ref<string[]>([])
const results = ref<any[]>([])

function onFilesChange(newFiles: File[]) {
  previewUrls.value.forEach((u) => URL.revokeObjectURL(u))
  files.value = newFiles
  previewUrls.value = newFiles.map((f) => URL.createObjectURL(f))
  results.value = []
}

async function handlePredict() {
  if (!files.value.length) return
  loading.value = true
  results.value = []
  try {
    if (mode.value === 'single') {
      const res: any = await predictSingle(files.value[0], topK.value)
      results.value = [res.data]
    } else {
      const res: any = await predictBatch(files.value, topK.value)
      results.value = res.data
    }
  } catch {
    ElMessage.error('识别失败')
  } finally {
    loading.value = false
  }
}

onBeforeUnmount(() => {
  previewUrls.value.forEach((u) => URL.revokeObjectURL(u))
})
</script>

<style scoped>
.predict-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 32px 24px;
}

/* Header */
.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 28px;
}
.header-icon {
  font-size: 16px;
  font-weight: 800;
  letter-spacing: 1px;
  color: var(--pink-deep);
  background: linear-gradient(135deg, var(--pink-light), var(--lavender-light));
  width: 64px;
  height: 64px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: var(--shadow-soft);
}
.page-header h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 800;
  color: var(--text-primary);
}
.header-desc {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--text-muted);
  font-weight: 600;
}

/* Mode Switch */
.mode-switch {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}
.mode-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border: 1.5px solid #e8d8df;
  border-radius: var(--radius-sm);
  background: rgba(255, 255, 255, 0.6);
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s;
  font-family: inherit;
}
.mode-btn:hover {
  border-color: var(--pink);
  background: var(--pink-light);
}
.mode-btn.active {
  border-color: var(--pink-deep);
  background: linear-gradient(135deg, var(--pink-light), var(--lavender-light));
  color: var(--pink-deep);
  box-shadow: 0 2px 12px rgba(178, 106, 127, 0.14);
}

/* Actions */
.actions-bar {
  display: flex;
  align-items: flex-end;
  gap: 16px;
  margin: 20px 0 28px;
  flex-wrap: wrap;
}
.topk-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.topk-field label {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-secondary);
}
.predict-btn {
  padding: 12px 32px;
  border: none;
  border-radius: var(--radius-sm);
  background: linear-gradient(135deg, var(--pink-deep), #9a6f7a);
  color: #fff;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: inherit;
}
.predict-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(178, 106, 127, 0.28);
}
.predict-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Results */
.results-section {
  animation: slideUp 0.4s ease;
}
@keyframes slideUp {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}
.section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}
.section-title h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 800;
  color: var(--text-primary);
}
.result-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: 16px;
}

/* Empty */
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-muted);
}
.empty-icon {
  font-size: 48px;
  color: var(--text-muted);
  margin-bottom: 12px;
  animation: float 4s ease-in-out infinite;
}
@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}
.empty-state p {
  font-size: 15px;
  font-weight: 600;
}

@media (max-width: 720px) {
  .actions-bar {
    flex-direction: column;
    align-items: stretch;
  }
  .result-grid {
    grid-template-columns: 1fr;
  }
}
</style>
