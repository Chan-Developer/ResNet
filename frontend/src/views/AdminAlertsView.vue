<template>
  <div class="alert-page">
    <section class="alert-hero">
      <div>
        <div class="hero-kicker">Region Warning Center</div>
        <h2>区域病害预警</h2>
        <p class="hero-desc">系统会按区域和病害类型监测增长率，超过阈值后自动生成预警并推送管理员处理。</p>
      </div>
      <div class="hero-actions">
        <select v-model="status" class="status-select" @change="fetchAlerts">
          <option value="unread">仅看未读</option>
          <option value="all">全部预警</option>
          <option value="read">仅看已读</option>
        </select>
        <button class="ghost-btn" :disabled="loading" @click="refreshAll">
          {{ loading ? '刷新中...' : '刷新数据' }}
        </button>
      </div>
    </section>

    <section class="summary-grid">
      <div class="summary-card">
        <span class="summary-label">预警总数</span>
        <strong>{{ summary.total_count }}</strong>
      </div>
      <div class="summary-card">
        <span class="summary-label">未读预警</span>
        <strong>{{ summary.unread_count }}</strong>
      </div>
      <div class="summary-card">
        <span class="summary-label">当前列表</span>
        <strong>{{ alerts.length }}</strong>
      </div>
    </section>

    <section class="panel-shell">
      <div v-if="!alerts.length && !loading" class="empty-state">
        暂无预警记录。
      </div>

      <article
        v-for="item in alerts"
        :key="item.id"
        class="alert-row"
        :class="{ unread: item.status === 'unread' }"
      >
        <div class="alert-main">
          <div class="title-line">
            <strong>{{ item.display_name }}</strong>
            <span class="pill">{{ item.region_code }}</span>
            <span class="pill status" :class="item.status">
              {{ item.status === 'unread' ? '未读' : '已读' }}
            </span>
          </div>
          <p class="message">{{ item.message }}</p>
          <div class="meta-line">
            <span>本期 {{ item.current_count }} 例</span>
            <span>上期 {{ item.previous_count }} 例</span>
            <span>增长率 {{ formatPercent(item.growth_rate) }}</span>
            <span>阈值 {{ formatPercent(item.threshold) }}</span>
            <span>{{ formatDate(item.created_at) }}</span>
          </div>
        </div>
        <button
          v-if="item.status === 'unread'"
          class="read-btn"
          :disabled="savingId === item.id"
          @click="markRead(item)"
        >
          {{ savingId === item.id ? '处理中...' : '标记已读' }}
        </button>
      </article>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getRegionAlerts, getRegionAlertSummary, markRegionAlertRead, type RegionAlertStatus } from '../api/alert'

type AlertItem = {
  id: number
  region_code: string
  display_name: string
  current_count: number
  previous_count: number
  growth_rate: number
  threshold: number
  status: 'unread' | 'read'
  message: string
  created_at?: string
}

type AlertSummary = {
  unread_count: number
  total_count: number
}

const loading = ref(false)
const savingId = ref<number | null>(null)
const status = ref<RegionAlertStatus>('unread')
const alerts = ref<AlertItem[]>([])
const summary = ref<AlertSummary>({ unread_count: 0, total_count: 0 })

function formatPercent(value: number) {
  return `${(value * 100).toFixed(1)}%`
}

function formatDate(value?: string) {
  if (!value) return '--'
  const date = new Date(value)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

async function fetchAlerts() {
  loading.value = true
  try {
    const res: any = await getRegionAlerts({ status: status.value, limit: 100 })
    alerts.value = Array.isArray(res.data) ? res.data : []
  } catch {
    alerts.value = []
  } finally {
    loading.value = false
  }
}

async function fetchSummary() {
  try {
    const res: any = await getRegionAlertSummary()
    summary.value = {
      unread_count: Number(res?.data?.unread_count || 0),
      total_count: Number(res?.data?.total_count || 0),
    }
  } catch {
    summary.value = { unread_count: 0, total_count: 0 }
  }
}

async function refreshAll() {
  await Promise.all([fetchAlerts(), fetchSummary()])
}

async function markRead(item: AlertItem) {
  savingId.value = item.id
  try {
    await markRegionAlertRead(item.id)
    ElMessage.success('已标记为已读')
    await refreshAll()
  } finally {
    savingId.value = null
  }
}

onMounted(refreshAll)
</script>

<style scoped>
.alert-page {
  max-width: 1120px;
  margin: 0 auto;
  padding: 32px 24px 40px;
}

.alert-hero {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  padding: 24px;
  border-radius: 24px;
  background:
    radial-gradient(circle at top right, rgba(252, 165, 165, 0.22), transparent 34%),
    radial-gradient(circle at bottom left, rgba(167, 199, 231, 0.2), transparent 38%),
    linear-gradient(135deg, rgba(255, 255, 255, 0.94), rgba(251, 244, 246, 0.9));
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

.alert-hero h2 {
  margin: 8px 0 6px;
  font-size: 28px;
  color: var(--text-primary);
}

.hero-desc {
  margin: 0;
  line-height: 1.7;
  color: var(--text-secondary);
}

.hero-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-select {
  border-radius: 12px;
  border: 1px solid #e0d2da;
  padding: 10px 12px;
  font-family: inherit;
  color: var(--text-primary);
}

.ghost-btn {
  border: none;
  border-radius: 12px;
  padding: 10px 14px;
  background: var(--lavender-light);
  color: var(--text-primary);
  font-family: inherit;
  font-weight: 700;
  cursor: pointer;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin: 18px 0 22px;
}

.summary-card {
  padding: 18px 20px;
  border-radius: 20px;
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
  font-size: 30px;
  color: var(--text-primary);
}

.panel-shell {
  padding: 18px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid var(--card-border);
  box-shadow: var(--shadow-soft);
}

.alert-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
  padding: 14px;
  border-radius: 16px;
  border: 1px solid rgba(229, 219, 225, 0.9);
  background: rgba(255, 255, 255, 0.75);
}

.alert-row + .alert-row {
  margin-top: 10px;
}

.alert-row.unread {
  border-color: rgba(236, 72, 153, 0.34);
  background: linear-gradient(135deg, rgba(254, 242, 242, 0.66), rgba(255, 255, 255, 0.8));
}

.title-line {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.pill {
  padding: 3px 9px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  background: var(--lavender-light);
  color: var(--text-secondary);
}

.pill.status.unread {
  background: rgba(251, 207, 232, 0.8);
  color: #9d174d;
}

.pill.status.read {
  background: rgba(209, 250, 229, 0.8);
  color: #065f46;
}

.message {
  margin: 8px 0;
  line-height: 1.7;
  color: var(--text-secondary);
}

.meta-line {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  color: var(--text-muted);
  font-size: 12px;
}

.read-btn {
  border: none;
  border-radius: 12px;
  padding: 10px 14px;
  font-family: inherit;
  font-weight: 700;
  background: linear-gradient(135deg, var(--pink-deep), #8c6e79);
  color: #fff;
  cursor: pointer;
  white-space: nowrap;
}

.read-btn:disabled,
.ghost-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.empty-state {
  text-align: center;
  padding: 36px 0;
  color: var(--text-muted);
}
</style>
