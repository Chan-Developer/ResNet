<template>
  <div class="dashboard-page" v-loading="loading">
    <section class="dashboard-hero">
      <div class="hero-main">
        <div class="hero-kicker">Data Insights</div>
        <h2>诊断数据看板</h2>
        <p class="hero-desc">展示准确率、区域预警与趋势变化，支持导出 CSV 报表。</p>
      </div>
      <div class="hero-actions">
        <el-select v-if="isAdmin" v-model="scope" class="scope-select" size="default" @change="handleScopeChange">
          <el-option value="me" label="个人看板" />
          <el-option value="all" label="全局看板" />
        </el-select>
        <el-select v-model="days" class="days-select" size="default" @change="fetchData">
          <el-option :value="7" label="近 7 天" />
          <el-option :value="30" label="近 30 天" />
          <el-option :value="90" label="近 90 天" />
        </el-select>
        <el-select
          v-model="cropName"
          clearable
          placeholder="作物筛选"
          class="filter-select"
          size="default"
          @change="fetchData"
        >
          <el-option v-for="item in cropOptions" :key="item" :label="item" :value="item" />
        </el-select>
        <el-select
          v-model="label"
          clearable
          placeholder="病害筛选"
          class="filter-select"
          size="default"
          @change="fetchData"
        >
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
      <article class="chart-card chart-card-main">
        <div class="card-head">
          <h3>区域病害量</h3>
          <span class="sub-text">{{ selectedRegionLabel }} · {{ summary?.start_date }} ~ {{ summary?.end_date }}</span>
        </div>
        <div class="region-picker-row">
          <el-select v-model="regionCode" class="region-select" size="default" @change="fetchData">
            <el-option v-for="item in regionOptions" :key="item" :label="item" :value="item" />
          </el-select>
        </div>
        <div v-if="!distribution.length" class="empty">该区域暂无病害建档数据</div>
        <div v-else class="bar-wrap">
          <div class="bar-scroll">
            <svg viewBox="0 0 760 300" preserveAspectRatio="none" class="bar-chart" role="img" aria-label="区域病害量柱状图">
              <defs>
                <linearGradient id="diseaseBarGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stop-color="#c4869b" />
                  <stop offset="100%" stop-color="#a6667d" />
                </linearGradient>
              </defs>
              <line x1="56" y1="24" x2="56" y2="246" class="axis-line" />
              <line x1="56" y1="246" x2="720" y2="246" class="axis-line" />

              <g v-for="tick in yTicks" :key="`tick-${tick.value}`">
                <line
                  x1="56"
                  :y1="tick.y"
                  x2="720"
                  :y2="tick.y"
                  class="grid-line"
                />
                <text x="48" :y="tick.y + 4" class="y-label">{{ tick.value }}</text>
              </g>

              <g v-for="bar in diseaseBars" :key="bar.label">
                <rect
                  :x="bar.x"
                  :y="bar.y"
                  :width="bar.width"
                  :height="bar.height"
                  rx="6"
                  class="bar-rect"
                />
                <text :x="bar.x + bar.width / 2" :y="bar.y - 8" class="bar-value">{{ bar.value }}</text>
                <text :x="bar.x + bar.width / 2" y="270" class="x-label">{{ bar.shortName }}</text>
              </g>
            </svg>
          </div>
          <div class="bar-foot">
            <span>病害类别数：{{ diseaseBarSource.length }}</span>
            <span>总病例数：{{ diseaseTotalCount }}</span>
            <span>峰值病例数：{{ diseasePeakCount }}</span>
          </div>
        </div>
      </article>

      <article class="chart-card chart-card-side">
        <div class="card-head">
          <h3>区域病害预警</h3>
          <span class="sub-text">仅展示有预警区域</span>
        </div>
        <div v-if="!alertRegions.length" class="empty">暂无区域预警数据</div>
        <div v-else class="region-list">
          <div
            v-for="region in alertRegions"
            :key="region.region_code"
            class="region-item"
            :class="{ alert: region.has_alert }"
          >
            <div class="region-summary">
              <span class="region-name">{{ region.region_code }}</span>
              <span class="region-value">
                {{ region.total_count }} 例（{{ (region.ratio * 100).toFixed(1) }}%）
              </span>
            </div>
            <div class="region-bar">
              <div class="region-fill" :style="{ width: `${Math.max(region.ratio * 100, 3)}%` }"></div>
            </div>
            <div class="region-badges">
              <span class="pill warn" :class="{ active: region.has_alert }">
                {{ region.has_alert ? '有预警' : '无预警' }}
              </span>
              <span class="pill unread">{{ region.has_unread_alert ? '有未读' : '无未读' }}</span>
            </div>
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

const FIXED_REGION_OPTIONS = ['区域1', '区域2', '区域3', '区域4', '区域5']

type Summary = {
  period_days: number
  start_date: string
  end_date: string
  prediction_count: number
  confirmed_count: number
  avg_confidence?: number | null
  accuracy?: number | null
}

type RegionDistributionItem = {
  region_code: string
  total_count: number
  ratio: number
  has_alert: boolean
  has_unread_alert: boolean
}

type DistributionItem = {
  label: string
  display_name: string
  count: number
  ratio: number
}

const loading = ref(false)
const exporting = ref(false)
const days = ref(30)
const scope = ref<'me' | 'all'>('me')
const cropName = ref('')
const label = ref('')
const regionCode = ref(FIXED_REGION_OPTIONS[0])
const regionOptions = ref<string[]>([...FIXED_REGION_OPTIONS])
const cropOptions = ref<string[]>([])
const labelOptions = ref<Array<{ label: string; display_name: string }>>([])
const summary = ref<Summary | null>(null)
const regionDistribution = ref<RegionDistributionItem[]>([])
const distribution = ref<DistributionItem[]>([])
const userStore = useUserStore()
const isAdmin = computed(() => userStore.isAdmin)
const selectedRegionLabel = computed(() => regionCode.value || '区域')
const alertRegions = computed(() => regionDistribution.value.filter((item) => item.has_alert))

function formatPercent(value?: number | null) {
  if (value === null || value === undefined) return '--'
  return `${(value * 100).toFixed(1)}%`
}

function shortDiseaseName(value: string) {
  const text = value.trim()
  if (text.length <= 8) return text
  return `${text.slice(0, 8)}…`
}

const diseaseBarSource = computed(() => distribution.value.slice(0, 8))
const diseasePeakCount = computed(() => Math.max(...diseaseBarSource.value.map((item) => item.count), 0))
const diseaseTotalCount = computed(() => diseaseBarSource.value.reduce((sum, item) => sum + item.count, 0))
const diseaseAxisMax = computed(() => {
  const max = Math.max(diseasePeakCount.value, 1)
  const step = Math.max(1, Math.ceil(max / 4))
  return step * 4
})

const yTicks = computed(() => {
  const axisMax = diseaseAxisMax.value
  const step = axisMax / 4
  const values = [0, step, step * 2, step * 3, step * 4]
  return values.map((value) => {
    const ratio = value / axisMax
    const y = 246 - ratio * 198
    return { value, y: Number(y.toFixed(2)) }
  })
})

const diseaseBars = computed(() => {
  const chartLeft = 72
  const chartWidth = 632
  const list = diseaseBarSource.value
  const band = chartWidth / Math.max(list.length, 1)
  const barWidth = Math.max(34, Math.min(64, band * 0.58))
  const axisMax = diseaseAxisMax.value
  return list.map((item, index) => {
    const x = chartLeft + index * band + (band - barWidth) / 2
    const height = (item.count / axisMax) * 198
    const y = 246 - height
    return {
      label: item.label,
      shortName: shortDiseaseName(item.display_name),
      value: item.count,
      x: Number(x.toFixed(2)),
      y: Number(y.toFixed(2)),
      width: Number(barWidth.toFixed(2)),
      height: Number(height.toFixed(2)),
    }
  })
})

async function fetchData() {
  loading.value = true
  try {
    const baseParams = {
      days: days.value,
      scope: scope.value,
      crop_name: cropName.value || undefined,
      label: label.value || undefined,
    }
    const [regionRes, alertRes]: any = await Promise.all([
      getDashboardOverview({
        ...baseParams,
        region_code: regionCode.value,
      }),
      getDashboardOverview(baseParams),
    ])
    summary.value = regionRes.data.summary
    distribution.value = Array.isArray(regionRes.data.distribution) ? regionRes.data.distribution : []
    const rawRegions = Array.isArray(alertRes.data.region_distribution) ? alertRes.data.region_distribution : []
    regionDistribution.value = rawRegions.filter((item: RegionDistributionItem) =>
      FIXED_REGION_OPTIONS.includes(item.region_code)
    )
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
  regionCode.value = FIXED_REGION_OPTIONS[0]
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
      region_code: regionCode.value,
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
  padding: 28px 20px 36px;
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

.hero-main {
  min-width: 220px;
  flex: 1 1 320px;
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
  align-items: flex-start;
  justify-content: flex-end;
  align-content: flex-start;
  flex: 1 1 520px;
  min-width: 300px;
  flex-wrap: wrap;
  gap: 10px;
}

.days-select {
  width: 118px;
}

.scope-select {
  width: 126px;
}

.filter-select {
  width: 140px;
}

.ghost-btn,
.export-btn {
  border: none;
  border-radius: 14px;
  padding: 11px 16px;
  min-width: 88px;
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
  margin: 16px 0 18px;
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
  align-items: start;
}

.chart-card {
  border-radius: 22px;
  border: 1px solid rgba(228, 217, 223, 0.92);
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.92), rgba(249, 246, 247, 0.88));
  box-shadow: var(--shadow-soft);
  padding: 16px;
}

.chart-card-main {
  align-self: center;
}

.chart-card-side {
  align-self: start;
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

.region-picker-row {
  margin-bottom: 10px;
}

.region-select {
  width: 160px;
}

.bar-wrap {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.bar-scroll {
  width: 100%;
  overflow-x: auto;
  overflow-y: hidden;
  padding-bottom: 2px;
}

.bar-chart {
  width: 100%;
  min-width: 620px;
  height: 280px;
  border-radius: 16px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.8), rgba(252, 247, 250, 0.7)),
    repeating-linear-gradient(
      90deg,
      rgba(214, 194, 203, 0.08) 0,
      rgba(214, 194, 203, 0.08) 1px,
      transparent 1px,
      transparent 56px
    );
  border: 1px solid rgba(232, 216, 223, 0.78);
}

.axis-line {
  stroke: rgba(152, 131, 141, 0.8);
  stroke-width: 1.2;
}

.grid-line {
  stroke: rgba(199, 181, 190, 0.4);
  stroke-width: 1;
}

.y-label {
  font-size: 11px;
  fill: var(--text-muted);
  text-anchor: end;
}

.bar-rect {
  fill: url(#diseaseBarGradient);
  stroke: rgba(166, 98, 120, 0.25);
  stroke-width: 1;
  filter: drop-shadow(0 3px 6px rgba(178, 106, 127, 0.2));
}

.bar-value {
  font-size: 11px;
  fill: var(--text-primary);
  text-anchor: middle;
  font-weight: 700;
}

.x-label {
  font-size: 12px;
  fill: var(--text-secondary);
  text-anchor: middle;
  font-weight: 700;
}

.bar-foot {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  font-size: 12px;
  color: var(--text-muted);
}

.region-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.region-item {
  border-radius: 16px;
  border: 1px solid rgba(232, 216, 223, 0.78);
  background: rgba(255, 255, 255, 0.7);
  padding: 12px 14px;
}

.region-item.alert {
  border-color: rgba(231, 103, 123, 0.55);
  background: linear-gradient(135deg, rgba(255, 245, 247, 0.95), rgba(255, 255, 255, 0.75));
}

.region-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  cursor: pointer;
}

.region-name {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
}

.region-value {
  font-size: 12px;
  color: var(--text-muted);
}

.region-bar {
  margin-top: 8px;
  height: 8px;
  border-radius: 999px;
  background: #f1e9ee;
  overflow: hidden;
}

.region-fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #dba8b4, #9dbfb6);
}

.region-badges {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}

.pill {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 2px 8px;
  font-size: 12px;
  font-weight: 700;
}

.pill.warn {
  background: rgba(240, 177, 181, 0.35);
  color: #9e5a6b;
}

.pill.warn.active {
  background: rgba(233, 92, 122, 0.2);
  color: #c81f47;
  border: 1px solid rgba(227, 70, 103, 0.35);
}

.pill.unread {
  background: rgba(192, 213, 204, 0.35);
  color: #4f7f75;
}

@media (max-width: 1200px) {
  .dashboard-page {
    padding: 24px 16px 32px;
  }
  .dashboard-hero h2 {
    font-size: 28px;
  }
  .summary-card strong {
    font-size: 24px;
  }
}

@media (max-width: 980px) {
  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .chart-grid {
    grid-template-columns: 1fr;
  }
  .chart-card-main,
  .chart-card-side {
    align-self: auto;
  }
  .dashboard-hero {
    flex-direction: column;
    align-items: flex-start;
    padding: 20px;
  }
  .hero-main {
    width: 100%;
  }
  .hero-actions {
    width: 100%;
    justify-content: flex-start;
    min-width: 0;
  }
  .filter-select {
    width: 150px;
  }
}

@media (max-width: 640px) {
  .dashboard-page {
    padding: 16px 12px 24px;
  }
  .dashboard-hero {
    border-radius: 20px;
    padding: 16px;
    gap: 14px;
  }
  .hero-kicker {
    font-size: 11px;
  }
  .dashboard-hero h2 {
    font-size: 24px;
    line-height: 1.25;
  }
  .hero-desc {
    font-size: 14px;
    line-height: 1.6;
  }
  .hero-actions {
    gap: 8px;
  }
  .scope-select,
  .days-select,
  .filter-select {
    width: calc(50% - 4px);
    min-width: 132px;
  }
  .ghost-btn,
  .export-btn {
    width: calc(33.33% - 6px);
    min-width: 94px;
    padding: 10px 10px;
    font-size: 14px;
  }
  .summary-grid {
    grid-template-columns: 1fr;
    gap: 10px;
  }
  .summary-card {
    border-radius: 16px;
    padding: 14px 14px;
  }
  .summary-card strong {
    font-size: 28px;
  }
  .chart-card {
    border-radius: 18px;
    padding: 12px;
  }
  .card-head {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  .card-head h3 {
    font-size: 18px;
  }
  .sub-text {
    font-size: 11px;
  }
  .region-select {
    width: 100%;
  }
  .region-item {
    border-radius: 12px;
    padding: 10px 10px;
  }
  .region-summary {
    align-items: flex-start;
    flex-direction: column;
    gap: 4px;
  }
  .region-value {
    font-size: 11px;
  }
}
</style>
