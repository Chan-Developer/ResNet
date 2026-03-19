<template>
  <div class="dashboard-page" v-loading="loading">
    <section class="dashboard-hero">
      <div>
        <div class="hero-kicker">Data Insights</div>
        <h2>诊断数据看板</h2>
        <p class="hero-desc">展示准确率、病害分布和趋势变化，支持导出 CSV 报表用于答辩展示。</p>
      </div>
      <div class="hero-actions">
        <el-select v-if="isAdmin" v-model="scope" class="scope-select" size="default" @change="handleScopeChange">
          <el-option value="me" label="个人看板" />
          <el-option value="all" label="全局看板" />
        </el-select>
        <el-select v-model="days" class="days-select" size="default">
          <el-option :value="7" label="近 7 天" />
          <el-option :value="30" label="近 30 天" />
          <el-option :value="90" label="近 90 天" />
        </el-select>
        <el-select v-model="cropName" clearable placeholder="作物筛选" class="filter-select" size="default">
          <el-option v-for="item in cropOptions" :key="item" :label="item" :value="item" />
        </el-select>
        <el-select v-model="label" clearable placeholder="病害筛选" class="filter-select" size="default">
          <el-option
            v-for="item in labelOptions"
            :key="item.label"
            :label="item.display_name"
            :value="item.label"
          />
        </el-select>
        <button class="ghost-btn" :disabled="loading" @click="fetchData">
          {{ loading ? '刷新中...' : '刷新数据' }}
        </button>
        <button class="export-btn" :disabled="loading || exporting" @click="handleExport('csv')">
          {{ exporting ? '导出中...' : '下载CSV' }}
        </button>
        <button class="export-btn xlsx" :disabled="loading || exporting" @click="handleExport('xlsx')">
          {{ exporting ? '导出中...' : '下载Excel' }}
        </button>
      </div>
    </section>

    <section class="summary-grid">
      <div class="summary-card">
        <span class="summary-label">识别总数</span>
        <strong>{{ summary?.prediction_count ?? 0 }}</strong>
      </div>
      <div class="summary-card">
        <span class="summary-label">确认建档数</span>
        <strong>{{ summary?.confirmed_count ?? 0 }}</strong>
      </div>
      <div class="summary-card">
        <span class="summary-label">诊断准确率</span>
        <strong>{{ formatPercent(summary?.accuracy) }}</strong>
      </div>
      <div class="summary-card">
        <span class="summary-label">平均置信度</span>
        <strong>{{ formatPercent(summary?.avg_confidence) }}</strong>
      </div>
    </section>

    <section class="chart-grid">
      <article class="chart-card">
        <div class="card-head">
          <h3>病害分布</h3>
          <span class="sub-text">按确认建档标签统计</span>
        </div>
        <div v-if="!distribution.length" class="empty">暂无分布数据</div>
        <div v-else class="dist-list">
          <div v-for="item in distribution" :key="item.label" class="dist-item">
            <div class="dist-top">
              <span class="dist-name">{{ item.display_name }}</span>
              <span class="dist-value">{{ item.count }}（{{ (item.ratio * 100).toFixed(1) }}%）</span>
            </div>
            <div class="dist-bar">
              <div class="dist-fill" :style="{ width: `${Math.max(item.ratio * 100, 2)}%` }"></div>
            </div>
          </div>
        </div>
      </article>

      <article class="chart-card">
        <div class="card-head">
          <h3>趋势变化</h3>
          <span class="sub-text">{{ summary?.start_date }} ~ {{ summary?.end_date }}</span>
        </div>
        <div v-if="!trend.length" class="empty">暂无趋势数据</div>
        <div v-else class="line-wrap">
          <svg viewBox="0 0 680 220" preserveAspectRatio="none" class="line-chart">
            <polyline class="line predictions" :points="predictionPoints" />
            <polyline class="line confirmed" :points="confirmedPoints" />
          </svg>
          <div class="legend-row">
            <span class="legend-item"><i class="dot predictions"></i>识别量</span>
            <span class="legend-item"><i class="dot confirmed"></i>建档量</span>
          </div>
          <div class="trend-foot">
            <span>峰值识别量：{{ maxPrediction }}</span>
            <span>峰值建档量：{{ maxConfirmed }}</span>
          </div>
        </div>
      </article>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  exportDashboardCsv,
  exportDashboardXlsx,
  getDashboardFilters,
  getDashboardOverview,
} from '../api/report'
import { useUserStore } from '../stores/user'

type Summary = {
  period_days: number
  start_date: string
  end_date: string
  prediction_count: number
  confirmed_count: number
  avg_confidence?: number | null
  accuracy?: number | null
}

type DistributionItem = {
  label: string
  display_name: string
  count: number
  ratio: number
}

type TrendItem = {
  date: string
  prediction_count: number
  confirmed_count: number
  accuracy?: number | null
}

const loading = ref(false)
const exporting = ref(false)
const days = ref(30)
const scope = ref<'me' | 'all'>('me')
const cropName = ref('')
const label = ref('')
const cropOptions = ref<string[]>([])
const labelOptions = ref<Array<{ label: string; display_name: string }>>([])
const summary = ref<Summary | null>(null)
const distribution = ref<DistributionItem[]>([])
const trend = ref<TrendItem[]>([])
const userStore = useUserStore()
const isAdmin = computed(() => userStore.isAdmin)

function formatPercent(value?: number | null) {
  if (value === null || value === undefined) return '--'
  return `${(value * 100).toFixed(1)}%`
}

function buildPoints(values: number[]) {
  if (!values.length) return ''
  const width = 680
  const height = 220
  const max = Math.max(...values, 1)
  const stepX = values.length > 1 ? width / (values.length - 1) : width
  return values
    .map((value, index) => {
      const x = index * stepX
      const y = height - (value / max) * (height - 16) - 8
      return `${x.toFixed(2)},${y.toFixed(2)}`
    })
    .join(' ')
}

const predictionValues = computed(() => trend.value.map((item) => item.prediction_count))
const confirmedValues = computed(() => trend.value.map((item) => item.confirmed_count))
const predictionPoints = computed(() => buildPoints(predictionValues.value))
const confirmedPoints = computed(() => buildPoints(confirmedValues.value))
const maxPrediction = computed(() => Math.max(...predictionValues.value, 0))
const maxConfirmed = computed(() => Math.max(...confirmedValues.value, 0))

async function fetchData() {
  loading.value = true
  try {
    const res: any = await getDashboardOverview({
      days: days.value,
      scope: scope.value,
      crop_name: cropName.value || undefined,
      label: label.value || undefined,
    })
    summary.value = res.data.summary
    distribution.value = Array.isArray(res.data.distribution) ? res.data.distribution : []
    trend.value = Array.isArray(res.data.trend) ? res.data.trend : []
  } catch { /* handled by interceptor */ } finally {
    loading.value = false
  }
}

async function fetchFilters() {
  try {
    const res: any = await getDashboardFilters(scope.value)
    cropOptions.value = Array.isArray(res.data?.crops) ? res.data.crops : []
    labelOptions.value = Array.isArray(res.data?.labels) ? res.data.labels : []
  } catch { /* handled by interceptor */ }
}

async function handleScopeChange() {
  cropName.value = ''
  label.value = ''
  await fetchFilters()
  await fetchData()
}

async function handleExport(type: 'csv' | 'xlsx') {
  exporting.value = true
  try {
    const params = {
      days: days.value,
      scope: scope.value,
      crop_name: cropName.value || undefined,
      label: label.value || undefined,
    }
    const blob = (type === 'xlsx'
      ? await exportDashboardXlsx(params)
      : await exportDashboardCsv(params)) as unknown as Blob
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `diagnosis_report_${new Date().toISOString().slice(0, 10)}.${type}`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    ElMessage.success(`${type.toUpperCase()} 报表已开始下载`)
  } catch { /* handled by interceptor */ } finally {
    exporting.value = false
  }
}

onMounted(async () => {
  await fetchFilters()
  await fetchData()
})
</script>

<style scoped>
.dashboard-page {
  max-width: 1120px;
  margin: 0 auto;
  padding: 32px 24px 40px;
}

.dashboard-hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  padding: 26px;
  border-radius: 28px;
  background:
    radial-gradient(circle at top right, rgba(167, 199, 231, 0.28), transparent 32%),
    radial-gradient(circle at bottom left, rgba(215, 161, 173, 0.22), transparent 36%),
    linear-gradient(135deg, rgba(255, 255, 255, 0.94), rgba(251, 244, 246, 0.92));
  border: 1px solid rgba(220, 210, 218, 0.72);
  box-shadow: var(--shadow-soft);
}

.hero-kicker {
  font-size: 12px;
  font-weight: 800;
  color: var(--pink-deep);
  text-transform: uppercase;
  letter-spacing: 1.4px;
}

.dashboard-hero h2 {
  margin: 8px 0 6px;
  font-size: 30px;
  color: var(--text-primary);
}

.hero-desc {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.7;
}

.hero-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.days-select {
  width: 110px;
}

.scope-select {
  width: 118px;
}

.filter-select {
  width: 150px;
}

.ghost-btn,
.export-btn {
  border: none;
  border-radius: 14px;
  padding: 11px 16px;
  font-family: inherit;
  font-weight: 700;
  cursor: pointer;
}

.ghost-btn {
  background: var(--lavender-light);
  color: var(--text-primary);
}

.export-btn {
  background: linear-gradient(135deg, var(--pink-deep), #8c6e79);
  color: #fff;
}

.export-btn.xlsx {
  background: linear-gradient(135deg, var(--green-deep), #6f8f87);
}

.ghost-btn:disabled,
.export-btn:disabled {
  opacity: 0.52;
  cursor: not-allowed;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin: 18px 0 20px;
}

.summary-card {
  padding: 18px 20px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid var(--card-border);
  box-shadow: var(--shadow-soft);
}

.summary-label {
  display: block;
  font-size: 12px;
  font-weight: 700;
  color: var(--text-muted);
}

.summary-card strong {
  display: block;
  margin-top: 8px;
  font-size: 28px;
  color: var(--text-primary);
}

.chart-grid {
  display: grid;
  grid-template-columns: 1.1fr 1fr;
  gap: 16px;
}

.chart-card {
  border-radius: 22px;
  border: 1px solid rgba(228, 217, 223, 0.92);
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.92), rgba(249, 246, 247, 0.88));
  box-shadow: var(--shadow-soft);
  padding: 18px;
}

.card-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 12px;
}

.card-head h3 {
  margin: 0;
  font-size: 20px;
  color: var(--text-primary);
}

.sub-text {
  font-size: 12px;
  color: var(--text-muted);
}

.empty {
  padding: 42px 12px;
  text-align: center;
  color: var(--text-muted);
}

.dist-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.dist-item {
  padding: 10px 12px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.64);
  border: 1px solid rgba(232, 216, 223, 0.78);
}

.dist-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 6px;
}

.dist-name {
  font-size: 13px;
  color: var(--text-primary);
  font-weight: 700;
}

.dist-value {
  font-size: 12px;
  color: var(--text-muted);
}

.dist-bar {
  height: 8px;
  border-radius: 999px;
  background: #f1e9ee;
  overflow: hidden;
}

.dist-fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #dba8b4, #9dbfb6);
}

.line-wrap {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.line-chart {
  width: 100%;
  height: 240px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.68);
  border: 1px solid rgba(232, 216, 223, 0.78);
}

.line {
  fill: none;
  stroke-width: 2.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.line.predictions {
  stroke: #b26a7f;
}

.line.confirmed {
  stroke: #4f7f75;
}

.legend-row {
  display: flex;
  gap: 12px;
}

.legend-item {
  font-size: 12px;
  color: var(--text-secondary);
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.dot.predictions {
  background: #b26a7f;
}

.dot.confirmed {
  background: #4f7f75;
}

.trend-foot {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  font-size: 12px;
  color: var(--text-muted);
}

@media (max-width: 980px) {
  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .chart-grid {
    grid-template-columns: 1fr;
  }
  .dashboard-hero {
    flex-direction: column;
    align-items: flex-start;
  }
  .hero-actions {
    flex-wrap: wrap;
  }
}
</style>
