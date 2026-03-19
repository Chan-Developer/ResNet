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
        <small>适合深度诊断</small>
      </button>
      <button
        v-if="canBatch"
        class="mode-btn"
        :class="{ active: mode === 'batch' }"
        @click="mode = 'batch'"
      >
        <span>批量识别</span>
        <small>适合快速筛查</small>
      </button>
    </div>

    <div class="mode-tip">
      <span class="tip-chip">{{ mode === 'single' ? '智能诊断模式' : '批量筛查模式' }}</span>
      <span class="tip-text">当前已选择 {{ files.length }} 张图片</span>
    </div>

    <!-- 上传区域 -->
    <ImageUploader :key="uploaderKey" :multiple="mode === 'batch'" :limit="10" @change="onFilesChange" />

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
    <div v-if="draft" class="results-section">
      <div class="section-title">
        <h3>诊断草稿</h3>
        <span class="section-badge">待确认</span>
      </div>
      <div class="result-grid">
        <PredictionCard :result="draft" :image-url="previewUrls[0]" />
      </div>

      <div class="diagnosis-grid">
        <div class="insight-card">
          <div class="meta-row">
            <span class="meta-chip">{{ draft.crop_name }}</span>
            <span class="meta-chip" :class="draft.health_status">
              {{ draft.health_status === 'healthy' ? '健康状态' : '疑似病害' }}
            </span>
          </div>
          <h4>处置建议</h4>
          <p class="advice-summary">{{ draft.advice.summary }}</p>
          <p class="advice-overview">{{ draft.advice.condition_overview }}</p>
          <div class="sub-title">建议动作</div>
          <ul class="advice-list">
            <li v-for="(action, idx) in draft.advice.recommended_actions" :key="idx">
              {{ action }}
            </li>
          </ul>
          <div class="sub-title">不确定性提示</div>
          <p class="notice-text">{{ draft.advice.uncertainty_notice }}</p>
          <div class="sub-title">跟进建议</div>
          <p class="notice-text">{{ draft.advice.follow_up }}</p>
        </div>

        <div class="insight-card">
          <h4>知识证据</h4>
          <div
            v-for="item in draft.knowledge_evidence"
            :key="item.evidence_id"
            class="evidence-item"
          >
            <div class="evidence-top">
              <span class="evidence-id">{{ item.evidence_id }}</span>
              <span class="evidence-score">{{ formatPercent(item.score) }}</span>
            </div>
            <div class="evidence-title">{{ item.title }}</div>
            <div class="evidence-source">{{ item.source_name }}</div>
            <p class="evidence-snippet">{{ item.snippet }}</p>
          </div>
        </div>

        <div class="insight-card">
          <h4>相似病例</h4>
          <div v-if="!draft.similar_cases.length" class="empty-mini">
            暂无已确认相似病例，将主要依据知识证据给出处置建议。
          </div>
          <div
            v-for="item in draft.similar_cases"
            :key="item.case_id"
            class="case-item"
          >
            <div class="case-top">
              <span class="case-label">{{ item.display_name }}</span>
              <span class="case-score">相似度 {{ formatPercent(item.similarity) }}</span>
            </div>
            <p class="case-summary">{{ item.summary }}</p>
            <div class="case-actions">
              <span
                v-for="(action, idx) in item.reference_actions"
                :key="`${item.case_id}-${idx}`"
                class="case-action-chip"
              >
                {{ action }}
              </span>
            </div>
          </div>
        </div>

        <div class="insight-card">
          <h4>确认建档</h4>
          <p v-if="canConfirmDiagnosis" class="confirm-hint">
            只有点击确认后，诊断结果才会写入数据库并进入病例库。
          </p>
          <template v-if="canConfirmDiagnosis">
            <label class="confirm-label">确认标签</label>
            <select v-model="confirmedLabel" class="confirm-select">
              <option
                v-for="item in draft.predictions"
                :key="item.class_name"
                :value="item.class_name"
              >
                {{ item.display_name }} · {{ formatPercent(item.confidence) }}
              </option>
            </select>
            <label class="confirm-label">区域信息（可选）</label>
            <div class="location-grid">
              <input v-model="locationForm.province" class="location-input" placeholder="省份" />
              <input v-model="locationForm.city" class="location-input" placeholder="城市" />
              <input v-model="locationForm.district" class="location-input" placeholder="区县" />
              <input
                v-model="locationForm.lat"
                class="location-input"
                placeholder="纬度（可选）"
                inputmode="decimal"
              />
              <input
                v-model="locationForm.lng"
                class="location-input"
                placeholder="经度（可选）"
                inputmode="decimal"
              />
            </div>
            <button
              class="predict-btn confirm-btn"
              :disabled="confirmLoading || !!confirmedCase"
              @click="handleConfirmDiagnosis"
            >
              <span v-if="confirmLoading" class="spinner"></span>
              {{ confirmLoading ? '建档中...' : confirmedCase ? '已建档' : '确认并建档' }}
            </button>
          </template>
          <p v-else class="confirm-hint">
            当前角色不具备“确认建档”权限，请联系管理员开通。
          </p>

          <div v-if="confirmedCase" class="confirm-success">
            <div class="success-title">病例已建档 #{{ confirmedCase.case.id }}</div>
            <div class="success-text">
              已按「{{ confirmedCase.case.confirmed_display_name }}」写入数据库。
            </div>
          </div>
        </div>
      </div>
    </div>

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
    <div v-if="!results.length && !draft && !loading" class="empty-state">
      <div class="empty-icon">🍃</div>
      <p>上传植物照片开始识别吧~</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import ImageUploader from '../components/ImageUploader.vue'
import PredictionCard from '../components/PredictionCard.vue'
import { diagnoseSingle, predictBatch, confirmDiagnosis } from '../api/predict'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const mode = ref<'single' | 'batch'>('single')
const topK = ref(5)
const maxTopK = 20
const loading = ref(false)
const confirmLoading = ref(false)
const files = ref<File[]>([])
const previewUrls = ref<string[]>([])
const results = ref<any[]>([])
const draft = ref<any | null>(null)
const confirmedLabel = ref('')
const confirmedCase = ref<any | null>(null)
const locationForm = reactive({
  province: '',
  city: '',
  district: '',
  lat: '',
  lng: '',
})
const uploaderKey = ref(0)
const canBatch = computed(() => userStore.hasPermission('predict:batch'))
const canConfirmDiagnosis = computed(() => userStore.hasPermission('diagnosis:confirm'))

function formatPercent(value: number) {
  return `${(value * 100).toFixed(1)}%`
}

function resetPredictState() {
  results.value = []
  draft.value = null
  confirmedLabel.value = ''
  confirmedCase.value = null
  locationForm.province = ''
  locationForm.city = ''
  locationForm.district = ''
  locationForm.lat = ''
  locationForm.lng = ''
}

function toOptionalText(value: string) {
  const text = value.trim()
  return text || undefined
}

function toOptionalNumber(value: string) {
  const text = value.trim()
  if (!text) return undefined
  const parsed = Number(text)
  return Number.isFinite(parsed) ? parsed : undefined
}

function onFilesChange(newFiles: File[]) {
  previewUrls.value.forEach((u) => URL.revokeObjectURL(u))
  files.value = newFiles
  previewUrls.value = newFiles.map((f) => URL.createObjectURL(f))
  resetPredictState()
}

async function handlePredict() {
  if (!files.value.length) return
  loading.value = true
  resetPredictState()
  try {
    if (mode.value === 'single') {
      const res: any = await diagnoseSingle(files.value[0], topK.value)
      draft.value = res.data
      confirmedLabel.value = res.data.best_prediction?.class_name || ''
    } else {
      if (!canBatch.value) {
        ElMessage.warning('当前角色无批量识别权限')
        return
      }
      const res: any = await predictBatch(files.value, topK.value)
      results.value = res.data
    }
  } catch {
    ElMessage.error('识别失败')
  } finally {
    loading.value = false
  }
}

async function handleConfirmDiagnosis() {
  if (!canConfirmDiagnosis.value) {
    ElMessage.warning('当前角色无确认建档权限')
    return
  }
  if (!draft.value?.draft_token) return
  confirmLoading.value = true
  try {
    const res: any = await confirmDiagnosis({
      draft_token: draft.value.draft_token,
      confirmed_label: confirmedLabel.value,
      province: toOptionalText(locationForm.province),
      city: toOptionalText(locationForm.city),
      district: toOptionalText(locationForm.district),
      lat: toOptionalNumber(locationForm.lat),
      lng: toOptionalNumber(locationForm.lng),
    })
    confirmedCase.value = res.data
    ElMessage.success('病例已建档')
  } catch {
    ElMessage.error('建档失败')
  } finally {
    confirmLoading.value = false
  }
}

watch(mode, () => {
  previewUrls.value.forEach((u) => URL.revokeObjectURL(u))
  files.value = []
  previewUrls.value = []
  resetPredictState()
  uploaderKey.value += 1
})

watch(canBatch, (enabled) => {
  if (!enabled && mode.value === 'batch') {
    mode.value = 'single'
  }
})

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
  margin-bottom: 10px;
}
.mode-btn {
  display: flex;
  align-items: flex-start;
  justify-content: center;
  flex-direction: column;
  gap: 8px;
  padding: 12px 18px;
  min-width: 160px;
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
.mode-btn small {
  font-size: 11px;
  color: var(--text-muted);
  font-weight: 600;
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
.mode-btn.active small {
  color: var(--pink-deep);
}

.mode-tip {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 18px;
}

.tip-chip {
  padding: 4px 11px;
  border-radius: 999px;
  background: linear-gradient(135deg, var(--green-light), var(--sky-light));
  color: var(--green-deep);
  font-size: 11px;
  font-weight: 800;
}

.tip-text {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 600;
}

/* Actions */
.actions-bar {
  display: flex;
  align-items: flex-end;
  gap: 16px;
  margin: 20px 0 28px;
  flex-wrap: wrap;
  padding: 14px;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.62);
  border: 1px solid rgba(232, 216, 223, 0.78);
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
.section-badge {
  font-size: 11px;
  font-weight: 700;
  color: var(--pink-deep);
  background: var(--pink-light);
  border-radius: 999px;
  padding: 4px 10px;
}
.result-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: 16px;
}

.diagnosis-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.insight-card {
  background: var(--card-bg);
  backdrop-filter: var(--glass-blur);
  border: 1px solid var(--card-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-soft);
  padding: 18px;
}

.insight-card h4 {
  margin: 0 0 14px;
  font-size: 17px;
  color: var(--text-primary);
}

.meta-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 14px;
}

.meta-chip {
  font-size: 12px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 999px;
  background: var(--lavender-light);
  color: var(--text-secondary);
}

.meta-chip.healthy {
  background: var(--green-light);
  color: var(--green-deep);
}

.meta-chip.diseased {
  background: var(--peach-light);
  color: #b45309;
}

.advice-summary {
  margin: 0 0 8px;
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
}

.advice-overview,
.notice-text,
.case-summary,
.confirm-hint,
.success-text {
  margin: 0;
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-secondary);
}

.sub-title,
.confirm-label {
  display: block;
  margin: 14px 0 8px;
  font-size: 12px;
  font-weight: 800;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.4px;
}

.advice-list {
  margin: 0;
  padding-left: 18px;
  color: var(--text-secondary);
}

.advice-list li {
  margin-bottom: 8px;
  line-height: 1.6;
}

.evidence-item,
.case-item {
  padding: 12px;
  border-radius: var(--radius-sm);
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(232, 216, 223, 0.8);
  margin-bottom: 10px;
}

.evidence-top,
.case-top {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: center;
  margin-bottom: 6px;
}

.evidence-id,
.case-label {
  font-size: 12px;
  font-weight: 800;
  color: var(--text-primary);
}

.evidence-score,
.case-score {
  font-size: 11px;
  color: var(--text-muted);
  white-space: nowrap;
}

.evidence-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-primary);
}

.evidence-source {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 4px;
}

.evidence-snippet {
  margin: 8px 0 0;
  font-size: 12px;
  line-height: 1.7;
  color: var(--text-secondary);
}

.case-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 10px;
}

.case-action-chip {
  font-size: 11px;
  font-weight: 700;
  color: var(--pink-deep);
  background: var(--pink-light);
  padding: 4px 8px;
  border-radius: 999px;
}

.empty-mini {
  font-size: 13px;
  color: var(--text-muted);
  line-height: 1.7;
}

.confirm-select {
  width: 100%;
  border: 1.5px solid #e8d8df;
  border-radius: var(--radius-sm);
  padding: 12px 14px;
  font-size: 14px;
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.9);
  outline: none;
  font-family: inherit;
}

.confirm-select:focus {
  border-color: var(--pink);
}

.location-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin-top: 10px;
}

.location-input {
  border: 1.5px solid #e8d8df;
  border-radius: var(--radius-sm);
  padding: 10px 12px;
  font-size: 13px;
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.9);
  outline: none;
  font-family: inherit;
}

.location-input:focus {
  border-color: var(--pink);
}

.confirm-btn {
  margin-top: 16px;
  width: 100%;
  justify-content: center;
}

.confirm-success {
  margin-top: 14px;
  padding: 12px;
  border-radius: var(--radius-sm);
  background: var(--green-light);
  color: var(--green-deep);
}

.success-title {
  font-size: 13px;
  font-weight: 800;
  margin-bottom: 4px;
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
  .location-grid {
    grid-template-columns: 1fr;
  }
}
</style>
