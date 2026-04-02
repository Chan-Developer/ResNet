<template>
  <div class="followup-page">
    <section class="followup-hero">
      <div>
        <div class="hero-kicker">复查工作流</div>
        <h2>复查计划与疗效评估</h2>
        <p class="hero-desc">创建复查计划，定期上传复查图片，系统自动比较历史变化并生成分析说明。</p>
      </div>
      <button class="ghost-btn" :disabled="loadingPlans" @click="refreshAll">
        {{ loadingPlans ? '刷新中...' : '刷新数据' }}
      </button>
    </section>

    <section class="layout-grid">
      <article class="panel create-panel">
        <h3>新建复查计划</h3>
        <label class="field-label">计划名称</label>
        <input v-model="createForm.title" class="field-input" placeholder="例如：番茄晚疫病一周复查" />

        <label class="field-label">关联病例编号（可选）</label>
        <input v-model="createForm.caseIdText" class="field-input" placeholder="例如：1024" />

        <label class="field-label">病害类型（可选）</label>
        <input
          v-model="createForm.targetLabel"
          class="field-input"
          placeholder="不填则自动使用最近一次建档病例病害类型"
        />

        <label class="field-label">复查频率（天）</label>
        <input v-model.number="createForm.frequencyDays" class="field-input" type="number" min="1" max="90" />

        <label class="field-label">计划备注（可选）</label>
        <textarea v-model="createForm.notes" class="field-input textarea" rows="3" placeholder="记录处理措施与观察重点"></textarea>

        <button class="primary-btn" :disabled="creatingPlan" @click="handleCreatePlan">
          {{ creatingPlan ? '创建中...' : '创建计划' }}
        </button>
      </article>

      <article class="panel list-panel">
        <div class="panel-head">
          <h3>我的复查计划</h3>
          <select v-model="statusFilter" class="status-filter" @change="fetchPlans">
            <option value="">全部状态</option>
            <option value="active">进行中</option>
            <option value="paused">已暂停</option>
            <option value="completed">已完成</option>
            <option value="cancelled">已取消</option>
          </select>
        </div>
        <div v-if="!plans.length && !loadingPlans" class="empty-state">暂无复查计划。</div>
        <div v-else class="plan-list">
          <button
            v-for="plan in plans"
            :key="plan.id"
            class="plan-item"
            :class="{ active: selectedPlanId === plan.id }"
            @click="selectPlan(plan.id)"
          >
            <div class="plan-line">
              <strong>{{ plan.title }}</strong>
              <span class="status-pill" :class="plan.status">{{ statusText(plan.status) }}</span>
            </div>
            <div class="plan-meta">病害类型：{{ plan.target_display_name }}</div>
            <div class="plan-meta">下次复查：{{ plan.next_review_date }}</div>
            <div class="plan-meta">最近效果：{{ effectText(plan.latest_effect) }}</div>
          </button>
        </div>
      </article>
    </section>

    <section v-if="selectedPlan" class="detail-grid">
      <article class="panel detail-panel">
        <div class="panel-head">
          <h3>计划详情</h3>
          <div class="panel-actions">
            <select
              v-model="selectedPlanStatus"
              class="status-filter"
              @change="handleUpdatePlanStatus"
            >
              <option value="active">进行中</option>
              <option value="paused">已暂停</option>
              <option value="completed">已完成</option>
              <option value="cancelled">已取消</option>
            </select>
            <button class="danger-btn" :disabled="deletingPlan" @click="handleDeletePlan">
              {{ deletingPlan ? '删除中...' : '删除计划' }}
            </button>
          </div>
        </div>
        <div class="summary-grid">
          <div class="summary-card">
            <span>总复查次数</span>
            <strong>{{ evaluation.total_checkins }}</strong>
          </div>
          <div class="summary-card">
            <span>改善次数</span>
            <strong>{{ evaluation.improved_count }}</strong>
          </div>
          <div class="summary-card">
            <span>稳定次数</span>
            <strong>{{ evaluation.stable_count }}</strong>
          </div>
          <div class="summary-card">
            <span>加重次数</span>
            <strong>{{ evaluation.worse_count }}</strong>
          </div>
        </div>
        <div class="meta-list">
          <div>当前效果：{{ effectText(evaluation.latest_effect) }}</div>
        </div>
      </article>

      <article class="panel upload-panel">
        <h3>上传复查图片</h3>
        <input type="file" accept="image/*" @change="onFileChange" />
        <label class="field-label">备注（可选）</label>
        <textarea v-model="uploadNote" class="field-input textarea" rows="2" placeholder="记录本次处理和田间情况"></textarea>
        <button class="primary-btn" :disabled="uploading || !uploadFile" @click="handleUploadCheckin">
          {{ uploading ? '上传中...' : '上传并分析' }}
        </button>
      </article>
    </section>

    <section v-if="selectedPlan" class="panel checkin-panel">
      <h3>复查记录</h3>
      <div v-if="!checkins.length && !loadingCheckins" class="empty-state">暂无复查记录。</div>
      <div v-else class="checkin-list">
        <article v-for="item in checkins" :key="item.id" class="checkin-item">
          <div class="checkin-top">
            <strong>{{ item.top1_display_name }}</strong>
            <span class="status-pill" :class="item.effect_status">{{ effectText(item.effect_status) }}</span>
          </div>
          <div class="checkin-meta">
            <span>首位置信度：{{ toPercent(item.top1_confidence) }}</span>
            <span>病害变化：{{ signedPercent(item.target_confidence_delta) }}</span>
            <span>康复情况：{{ recoveryText(item.effect_status) }}</span>
            <span>{{ formatDate(item.created_at) }}</span>
          </div>
          <p class="checkin-summary">{{ item.llm_summary }}</p>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  createFollowupPlan,
  deleteFollowupPlan,
  getFollowupEvaluation,
  listFollowupCheckins,
  listFollowupPlans,
  type FollowupPlanStatus,
  updateFollowupPlan,
  uploadFollowupCheckin,
} from '../api/followup'

type PlanItem = {
  id: number
  title: string
  target_display_name: string
  target_label: string
  status: FollowupPlanStatus
  latest_effect: 'improved' | 'stable' | 'worse' | 'unknown'
  next_review_date: string
}

type CheckinItem = {
  id: number
  top1_display_name: string
  top1_confidence: number
  target_confidence: number
  target_confidence_delta: number
  effect_status: 'improved' | 'stable' | 'worse' | 'unknown'
  llm_summary: string
  created_at?: string
}

type Evaluation = {
  total_checkins: number
  improved_count: number
  stable_count: number
  worse_count: number
  latest_effect: 'improved' | 'stable' | 'worse' | 'unknown'
  effect_score?: number
  avg_target_confidence_delta?: number
}

const loadingPlans = ref(false)
const loadingCheckins = ref(false)
const creatingPlan = ref(false)
const uploading = ref(false)
const deletingPlan = ref(false)
const statusFilter = ref<string>('')
const selectedPlanId = ref<number>(0)
const selectedPlanStatus = ref<FollowupPlanStatus>('active')
const uploadFile = ref<File | null>(null)
const uploadNote = ref('')
const plans = ref<PlanItem[]>([])
const checkins = ref<CheckinItem[]>([])
const evaluation = ref<Evaluation>({
  total_checkins: 0,
  improved_count: 0,
  stable_count: 0,
  worse_count: 0,
  latest_effect: 'unknown',
})

const createForm = reactive({
  title: '',
  caseIdText: '',
  targetLabel: '',
  frequencyDays: 7,
  notes: '',
})

const selectedPlan = computed(() => plans.value.find((item) => item.id === selectedPlanId.value) || null)

function dedupeById<T extends { id: number }>(items: T[]) {
  const map = new Map<number, T>()
  for (const item of items) {
    if (!map.has(item.id)) {
      map.set(item.id, item)
    }
  }
  return Array.from(map.values())
}

function toPercent(value?: number) {
  if (typeof value !== 'number') return '--'
  return `${(value * 100).toFixed(1)}%`
}

function signedPercent(value?: number) {
  if (typeof value !== 'number') return '--'
  const formatted = `${(value * 100).toFixed(1)}%`
  if (value > 0) return `+${formatted}`
  return formatted
}

function statusText(status: FollowupPlanStatus) {
  if (status === 'active') return '进行中'
  if (status === 'paused') return '已暂停'
  if (status === 'completed') return '已完成'
  return '已取消'
}

function effectText(status: string) {
  if (status === 'improved') return '改善'
  if (status === 'worse') return '加重'
  if (status === 'stable') return '稳定'
  return '待评估'
}

function recoveryText(status: string) {
  if (status === 'improved') return '恢复中'
  if (status === 'worse') return '出现恶化'
  if (status === 'stable') return '病情持平'
  return '待评估'
}

function formatDate(value?: string) {
  if (!value) return '--'
  const date = new Date(value)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

async function fetchPlans() {
  loadingPlans.value = true
  try {
    const res: any = await listFollowupPlans(statusFilter.value ? { status: statusFilter.value as FollowupPlanStatus } : {})
    plans.value = dedupeById(Array.isArray(res.data) ? res.data : [])
    if (!plans.value.length) {
      selectedPlanId.value = 0
      checkins.value = []
      evaluation.value = {
        total_checkins: 0,
        improved_count: 0,
        stable_count: 0,
        worse_count: 0,
        latest_effect: 'unknown',
      }
      return
    }
    if (!plans.value.some((item) => item.id === selectedPlanId.value)) {
      selectedPlanId.value = plans.value[0].id
    }
    selectedPlanStatus.value = selectedPlan.value?.status || 'active'
  } finally {
    loadingPlans.value = false
  }
}

async function fetchPlanDetail() {
  if (!selectedPlanId.value) return
  loadingCheckins.value = true
  try {
    const [checkinRes, evalRes]: any = await Promise.all([
      listFollowupCheckins(selectedPlanId.value, { limit: 50 }),
      getFollowupEvaluation(selectedPlanId.value),
    ])
    checkins.value = dedupeById(Array.isArray(checkinRes.data) ? checkinRes.data : [])
    evaluation.value = evalRes.data || evaluation.value
    selectedPlanStatus.value = selectedPlan.value?.status || 'active'
  } finally {
    loadingCheckins.value = false
  }
}

async function refreshAll() {
  await fetchPlans()
  if (selectedPlanId.value) {
    await fetchPlanDetail()
  }
}

function selectPlan(planId: number) {
  selectedPlanId.value = planId
  selectedPlanStatus.value = selectedPlan.value?.status || 'active'
  fetchPlanDetail()
}

async function handleCreatePlan() {
  const caseIdText = createForm.caseIdText.trim()
  const caseId = caseIdText ? Number(caseIdText) : undefined
  if (caseIdText && !Number.isFinite(caseId)) {
    ElMessage.warning('病例ID必须是数字')
    return
  }
  creatingPlan.value = true
  try {
    const res: any = await createFollowupPlan({
      title: createForm.title.trim() || undefined,
      case_id: Number.isFinite(caseId) ? caseId : undefined,
      target_label: createForm.targetLabel.trim() || undefined,
      frequency_days: createForm.frequencyDays,
      notes: createForm.notes.trim() || undefined,
    })
    ElMessage.success('复查计划已创建')
    createForm.title = ''
    createForm.caseIdText = ''
    createForm.targetLabel = ''
    createForm.notes = ''
    createForm.frequencyDays = 7
    await fetchPlans()
    selectedPlanId.value = res.data?.id || selectedPlanId.value
    await fetchPlanDetail()
  } finally {
    creatingPlan.value = false
  }
}

function onFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  uploadFile.value = file || null
}

async function handleUploadCheckin() {
  if (!selectedPlanId.value || !uploadFile.value) return
  uploading.value = true
  try {
    await uploadFollowupCheckin(selectedPlanId.value, uploadFile.value, {
      note: uploadNote.value.trim() || undefined,
      top_k: 5,
    })
    ElMessage.success('复查上传成功，已完成趋势分析')
    uploadFile.value = null
    uploadNote.value = ''
    await fetchPlans()
    await fetchPlanDetail()
  } finally {
    uploading.value = false
  }
}

async function handleUpdatePlanStatus() {
  if (!selectedPlanId.value) return
  await updateFollowupPlan(selectedPlanId.value, { status: selectedPlanStatus.value })
  ElMessage.success('计划状态已更新')
  await fetchPlans()
  await fetchPlanDetail()
}

async function handleDeletePlan() {
  if (!selectedPlanId.value) return
  const confirmed = window.confirm('确定要删除该复查计划吗？相关复查记录也会一起删除。')
  if (!confirmed) return
  deletingPlan.value = true
  try {
    await deleteFollowupPlan(selectedPlanId.value)
    ElMessage.success('复查计划已删除')
    selectedPlanId.value = 0
    await fetchPlans()
    if (selectedPlanId.value) {
      await fetchPlanDetail()
    } else {
      checkins.value = []
      evaluation.value = {
        total_checkins: 0,
        improved_count: 0,
        stable_count: 0,
        worse_count: 0,
        latest_effect: 'unknown',
      }
    }
  } finally {
    deletingPlan.value = false
  }
}

onMounted(refreshAll)
</script>

<style scoped>
.followup-page {
  max-width: 1120px;
  margin: 0 auto;
  padding: 32px 24px 40px;
}

.followup-hero {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 24px;
  border-radius: 24px;
  background:
    radial-gradient(circle at top right, rgba(167, 199, 231, 0.24), transparent 36%),
    radial-gradient(circle at bottom left, rgba(157, 191, 182, 0.22), transparent 36%),
    linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(251, 244, 246, 0.9));
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

.followup-hero h2 {
  margin: 8px 0 6px;
  font-size: 28px;
  color: var(--text-primary);
}

.hero-desc {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.7;
}

.ghost-btn,
.primary-btn {
  border: none;
  border-radius: 12px;
  padding: 10px 14px;
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
}

.ghost-btn {
  background: var(--lavender-light);
  color: var(--text-primary);
  align-self: flex-start;
}

.primary-btn {
  background: linear-gradient(135deg, var(--pink-deep), #8c6e79);
  color: #fff;
}

.layout-grid {
  margin-top: 18px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.detail-grid {
  margin-top: 16px;
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 16px;
}

.panel {
  padding: 18px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid var(--card-border);
  box-shadow: var(--shadow-soft);
}

.panel h3 {
  margin: 0 0 12px;
  font-size: 20px;
}

.field-label {
  display: block;
  margin: 10px 0 6px;
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 700;
}

.field-input {
  width: 100%;
  border: 1.5px solid #e8d8df;
  border-radius: 12px;
  padding: 10px 12px;
  font-size: 14px;
  font-family: inherit;
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.9);
  box-sizing: border-box;
}

.field-input.textarea {
  resize: vertical;
}

.field-input:focus {
  outline: none;
  border-color: var(--pink);
}

.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}

.panel-actions {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.status-filter {
  border: 1px solid #e0d2da;
  border-radius: 10px;
  padding: 8px 10px;
  font-family: inherit;
  color: var(--text-primary);
}

.danger-btn {
  border: none;
  border-radius: 10px;
  padding: 8px 12px;
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
  background: rgba(254, 226, 226, 0.9);
  color: #b91c1c;
}

.plan-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 420px;
  overflow-y: auto;
  padding-right: 4px;
}

.plan-item {
  border: 1px solid #e9dde3;
  border-radius: 14px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.72);
  text-align: left;
  font-family: inherit;
  cursor: pointer;
}

.plan-item.active {
  border-color: rgba(178, 106, 127, 0.5);
  background: linear-gradient(135deg, var(--pink-light), rgba(255, 255, 255, 0.86));
}

.plan-line {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: center;
}

.plan-meta {
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-muted);
}

.status-pill {
  border-radius: 999px;
  padding: 3px 8px;
  font-size: 11px;
  font-weight: 700;
}

.status-pill.active,
.status-pill.stable {
  background: rgba(191, 219, 254, 0.55);
  color: #1d4ed8;
}

.status-pill.paused {
  background: rgba(224, 231, 255, 0.7);
  color: #4338ca;
}

.status-pill.completed,
.status-pill.improved {
  background: rgba(209, 250, 229, 0.8);
  color: #047857;
}

.status-pill.cancelled,
.status-pill.worse {
  background: rgba(254, 226, 226, 0.9);
  color: #b91c1c;
}

.status-pill.unknown {
  background: rgba(241, 245, 249, 0.9);
  color: #475569;
}

.summary-grid {
  margin-top: 10px;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.summary-card {
  border-radius: 14px;
  padding: 12px;
  border: 1px solid #ece4e9;
  background: rgba(255, 255, 255, 0.8);
}

.summary-card span {
  font-size: 12px;
  color: var(--text-muted);
}

.summary-card strong {
  display: block;
  margin-top: 4px;
  font-size: 24px;
  color: var(--text-primary);
}

.meta-list {
  margin-top: 12px;
  display: grid;
  gap: 8px;
  color: var(--text-secondary);
}

.checkin-panel {
  margin-top: 16px;
}

.checkin-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 560px;
  overflow-y: auto;
  padding-right: 4px;
}

.checkin-item {
  border-radius: 14px;
  border: 1px solid #ece4e9;
  background: rgba(255, 255, 255, 0.82);
  padding: 12px;
}

.checkin-top {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: center;
}

.checkin-meta {
  margin-top: 6px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  font-size: 12px;
  color: var(--text-muted);
}

.checkin-summary {
  margin: 8px 0 0;
  line-height: 1.7;
  color: var(--text-secondary);
}

.empty-state {
  color: var(--text-muted);
  font-size: 13px;
  text-align: center;
  padding: 18px 0;
}

.ghost-btn:disabled,
.primary-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 920px) {
  .layout-grid,
  .detail-grid {
    grid-template-columns: 1fr;
  }
  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
