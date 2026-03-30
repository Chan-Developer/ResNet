<template>
  <div class="model-page">
    <section class="page-hero">
      <div>
        <div class="hero-kicker">Model Runtime</div>
        <h2>模型版本管理</h2>
        <p class="hero-desc">维护模型版本清单，支持在线切换激活版本并查看当前运行时加载状态。</p>
      </div>
      <button class="ghost-btn" :disabled="loading" @click="refreshAll">
        {{ loading ? '刷新中...' : '刷新数据' }}
      </button>
    </section>

    <section class="summary-grid">
      <div class="summary-card">
        <span class="summary-label">版本总数</span>
        <strong>{{ versions.length }}</strong>
      </div>
      <div class="summary-card">
        <span class="summary-label">激活版本</span>
        <strong>{{ activeVersionCode }}</strong>
      </div>
      <div class="summary-card">
        <span class="summary-label">运行设备</span>
        <strong>{{ runtime.device || '--' }}</strong>
      </div>
    </section>

    <section class="panel-shell runtime-shell">
      <div class="panel-head">
        <div>
          <h3>当前运行时</h3>
          <p>用于快速确认当前推理实际加载的模型文件与类别文件来源。</p>
        </div>
      </div>
      <div class="runtime-grid">
        <div class="runtime-item">
          <span>loaded</span>
          <strong>{{ runtime.loaded ? 'true' : 'false' }}</strong>
        </div>
        <div class="runtime-item">
          <span>class_count</span>
          <strong>{{ runtime.class_count }}</strong>
        </div>
        <div class="runtime-item wide">
          <span>model_path</span>
          <code>{{ runtime.model_path || '--' }}</code>
        </div>
        <div class="runtime-item wide">
          <span>class_names_source</span>
          <code>{{ runtime.class_names_source || '--' }}</code>
        </div>
      </div>
    </section>

    <section class="panel-shell editor-shell">
      <div class="panel-head">
        <div>
          <h3>{{ editingId ? '编辑模型版本' : '新增模型版本' }}</h3>
          <p>路径支持绝对路径或相对项目根目录路径；激活时会即时加载并生效。</p>
        </div>
      </div>

      <div class="form-grid">
        <label>
          <span>version_code</span>
          <input v-model.trim="form.version_code" placeholder="如 v2026-03" />
        </label>
        <label>
          <span>display_name</span>
          <input v-model.trim="form.display_name" placeholder="如 ResNet50 阶段二" />
        </label>
        <label>
          <span>model_path</span>
          <input v-model.trim="form.model_path" placeholder="如 /abs/model.pth 或 relative/model.pth" />
        </label>
        <label>
          <span>class_names_path（可选）</span>
          <input v-model.trim="form.class_names_path" placeholder="留空则用系统默认类别来源" />
        </label>
      </div>

      <label class="full-line">
        <span>description</span>
        <textarea v-model.trim="form.description" rows="3" placeholder="版本说明" />
      </label>

      <label class="full-line">
        <span>metrics_json（JSON，可选）</span>
        <textarea v-model="form.metricsText" rows="4" placeholder='{"val_acc": 0.982, "f1": 0.975}' />
      </label>

      <div class="action-row">
        <button class="save-btn" :disabled="submitting" @click="submitForm">
          {{ submitting ? '提交中...' : editingId ? '保存版本' : '新增版本' }}
        </button>
        <button class="text-btn" :disabled="submitting" @click="resetForm">清空</button>
      </div>
    </section>

    <section class="panel-shell list-shell">
      <div class="panel-head">
        <div>
          <h3>版本列表</h3>
          <p>激活版本会用于在线推理，切换成功后无需重启服务。</p>
        </div>
      </div>

      <div v-if="!versions.length && !loading" class="empty-state">暂无模型版本。</div>

      <article v-for="item in versions" :key="item.id" class="model-item" :class="{ active: item.is_active }">
        <header class="item-header">
          <div>
            <h4>{{ item.display_name }}</h4>
            <div class="meta-line">
              <span>{{ item.version_code }}</span>
              <span>{{ item.is_active ? '激活中' : '未激活' }}</span>
              <span>{{ item.is_runtime_loaded ? '已加载' : '未加载' }}</span>
              <span>{{ formatDate(item.updated_at) }}</span>
            </div>
          </div>
          <div class="item-actions">
            <button class="mini-btn" :disabled="activatingId === item.id || item.is_active" @click="activateItem(item)">
              {{ activatingId === item.id ? '切换中...' : item.is_active ? '当前版本' : '激活' }}
            </button>
            <button class="mini-btn" @click="editItem(item)">编辑</button>
            <button class="mini-btn danger" :disabled="deletingId === item.id" @click="removeItem(item)">
              {{ deletingId === item.id ? '删除中...' : '删除' }}
            </button>
          </div>
        </header>

        <p class="item-desc">{{ item.description || '暂无说明' }}</p>

        <div class="meta-line">
          <span>model: {{ item.model_path }}</span>
        </div>
        <div class="meta-line">
          <span>class_names: {{ item.class_names_path || '--' }}</span>
        </div>

        <div class="metric-list" v-if="metricEntries(item).length">
          <span v-for="entry in metricEntries(item)" :key="`${item.id}-${entry.key}`" class="metric-chip">
            {{ entry.key }}: {{ entry.value }}
          </span>
        </div>
      </article>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  activateModelVersion,
  createModelVersion,
  deleteModelVersion,
  getModelRuntimeInfo,
  getModelVersions,
  updateModelVersion,
} from '../api/admin'

type ModelVersionItem = {
  id: number
  version_code: string
  display_name: string
  description: string
  model_path: string
  class_names_path: string
  metrics_json: Record<string, unknown>
  is_active: boolean
  is_runtime_loaded: boolean
  created_at?: string
  updated_at?: string
}

type RuntimeInfo = {
  active_version_id: number | null
  active_version_code: string | null
  model_path: string
  class_names_source: string
  class_count: number
  device: string
  loaded: boolean
}

const loading = ref(false)
const submitting = ref(false)
const activatingId = ref<number | null>(null)
const deletingId = ref<number | null>(null)
const editingId = ref<number | null>(null)

const versions = ref<ModelVersionItem[]>([])
const runtime = ref<RuntimeInfo>({
  active_version_id: null,
  active_version_code: null,
  model_path: '',
  class_names_source: '',
  class_count: 0,
  device: '',
  loaded: false,
})

const form = reactive({
  version_code: '',
  display_name: '',
  description: '',
  model_path: '',
  class_names_path: '',
  metricsText: '',
})

const activeVersionCode = computed(() => runtime.value.active_version_code || '--')

function formatDate(value?: string) {
  if (!value) return '--'
  const date = new Date(value)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

function metricEntries(item: ModelVersionItem) {
  if (!item.metrics_json || typeof item.metrics_json !== 'object') return []
  return Object.entries(item.metrics_json)
    .filter(([key]) => key)
    .map(([key, value]) => ({ key, value: String(value) }))
}

function resetForm() {
  editingId.value = null
  form.version_code = ''
  form.display_name = ''
  form.description = ''
  form.model_path = ''
  form.class_names_path = ''
  form.metricsText = ''
}

function editItem(item: ModelVersionItem) {
  editingId.value = item.id
  form.version_code = item.version_code
  form.display_name = item.display_name
  form.description = item.description || ''
  form.model_path = item.model_path || ''
  form.class_names_path = item.class_names_path || ''
  form.metricsText = item.metrics_json && Object.keys(item.metrics_json).length
    ? JSON.stringify(item.metrics_json, null, 2)
    : ''
}

function parseMetricsText() {
  if (!form.metricsText.trim()) return {}
  try {
    const parsed = JSON.parse(form.metricsText)
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
      ElMessage.warning('metrics_json 必须是 JSON 对象')
      return null
    }
    return parsed
  } catch {
    ElMessage.warning('metrics_json 不是合法 JSON')
    return null
  }
}

async function refreshAll() {
  loading.value = true
  try {
    const [versionsRes, runtimeRes]: any = await Promise.all([
      getModelVersions(),
      getModelRuntimeInfo(),
    ])
    versions.value = Array.isArray(versionsRes.data) ? versionsRes.data : []
    runtime.value = runtimeRes?.data || runtime.value
  } catch {
    versions.value = []
  } finally {
    loading.value = false
  }
}

async function submitForm() {
  if (!form.version_code.trim() || !form.display_name.trim() || !form.model_path.trim()) {
    ElMessage.warning('version_code、display_name、model_path 不能为空')
    return
  }
  const metrics = parseMetricsText()
  if (metrics === null) return

  submitting.value = true
  const payload = {
    version_code: form.version_code.trim(),
    display_name: form.display_name.trim(),
    description: form.description.trim(),
    model_path: form.model_path.trim(),
    class_names_path: form.class_names_path.trim(),
    metrics_json: metrics,
  }

  try {
    if (editingId.value) {
      await updateModelVersion(editingId.value, payload)
      ElMessage.success('模型版本已更新')
    } else {
      await createModelVersion(payload)
      ElMessage.success('模型版本已新增')
    }
    resetForm()
    await refreshAll()
  } finally {
    submitting.value = false
  }
}

async function activateItem(item: ModelVersionItem) {
  if (item.is_active) return
  const confirmed = window.confirm(`确认激活版本 ${item.version_code} 吗？`)
  if (!confirmed) return

  activatingId.value = item.id
  try {
    await activateModelVersion(item.id)
    ElMessage.success('模型版本已激活')
    await refreshAll()
  } finally {
    activatingId.value = null
  }
}

async function removeItem(item: ModelVersionItem) {
  const confirmed = window.confirm(`确认删除版本 ${item.version_code} 吗？`)
  if (!confirmed) return

  deletingId.value = item.id
  try {
    await deleteModelVersion(item.id)
    ElMessage.success('模型版本已删除')
    if (editingId.value === item.id) resetForm()
    await refreshAll()
  } finally {
    deletingId.value = null
  }
}

onMounted(refreshAll)
</script>

<style scoped>
.model-page {
  max-width: 1140px;
  margin: 0 auto;
  padding: 32px 24px 40px;
}

.page-hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 24px;
  border-radius: 24px;
  background:
    radial-gradient(circle at top right, rgba(125, 211, 252, 0.26), transparent 34%),
    radial-gradient(circle at bottom left, rgba(190, 242, 100, 0.22), transparent 34%),
    linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(245, 250, 255, 0.92));
  border: 1px solid rgba(205, 224, 240, 0.92);
  box-shadow: var(--shadow-soft);
}

.hero-kicker {
  font-size: 12px;
  font-weight: 800;
  color: #2563eb;
  text-transform: uppercase;
  letter-spacing: 1.4px;
}

.page-hero h2 {
  margin: 8px 0 6px;
  font-size: 28px;
  color: var(--text-primary);
}

.hero-desc {
  margin: 0;
  line-height: 1.7;
  color: var(--text-secondary);
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin: 18px 0 22px;
}

.summary-card {
  padding: 18px 20px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.86);
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
  padding: 20px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid var(--card-border);
  box-shadow: var(--shadow-soft);
}

.panel-shell + .panel-shell {
  margin-top: 16px;
}

.panel-head h3 {
  margin: 0 0 6px;
  font-size: 21px;
}

.panel-head p {
  margin: 0;
  font-size: 13px;
  color: var(--text-muted);
}

.runtime-grid,
.form-grid {
  margin-top: 14px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
}

.runtime-item {
  border-radius: 12px;
  border: 1px solid rgba(220, 231, 245, 0.9);
  background: rgba(247, 251, 255, 0.88);
  padding: 10px 12px;
}

.runtime-item span {
  display: block;
  font-size: 12px;
  color: var(--text-muted);
}

.runtime-item strong,
.runtime-item code {
  display: block;
  margin-top: 6px;
  font-size: 13px;
  color: var(--text-primary);
  word-break: break-all;
}

.runtime-item.wide {
  grid-column: span 2;
}

label {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

label span {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-muted);
}

input,
textarea {
  width: 100%;
  border: 1px solid #d7dee8;
  border-radius: 12px;
  padding: 10px 12px;
  font-family: inherit;
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.86);
}

textarea {
  resize: vertical;
}

.full-line {
  margin-top: 12px;
}

.action-row {
  margin-top: 14px;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.ghost-btn,
.text-btn,
.save-btn,
.mini-btn {
  border: none;
  border-radius: 12px;
  font-family: inherit;
  font-weight: 700;
  cursor: pointer;
}

.ghost-btn {
  padding: 10px 14px;
  background: var(--lavender-light);
  color: var(--text-primary);
}

.save-btn {
  padding: 11px 16px;
  background: linear-gradient(135deg, #2563eb, #2f80ed);
  color: #fff;
}

.text-btn {
  padding: 11px 14px;
  background: rgba(239, 244, 252, 0.85);
  color: var(--text-secondary);
}

.ghost-btn:disabled,
.text-btn:disabled,
.save-btn:disabled,
.mini-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.list-shell {
  margin-top: 16px;
}

.empty-state {
  text-align: center;
  padding: 34px 0;
  color: var(--text-muted);
}

.model-item {
  padding: 14px;
  border-radius: 16px;
  border: 1px solid rgba(218, 226, 238, 0.92);
  background: rgba(255, 255, 255, 0.8);
}

.model-item.active {
  border-color: rgba(37, 99, 235, 0.32);
  box-shadow: inset 0 0 0 1px rgba(37, 99, 235, 0.24);
}

.model-item + .model-item {
  margin-top: 10px;
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
}

.item-header h4 {
  margin: 0;
  font-size: 17px;
  color: var(--text-primary);
}

.meta-line {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-muted);
}

.item-desc {
  margin: 8px 0;
  line-height: 1.68;
  color: var(--text-secondary);
}

.item-actions {
  display: flex;
  gap: 8px;
}

.mini-btn {
  padding: 8px 12px;
  background: rgba(235, 241, 252, 0.9);
  color: var(--text-primary);
}

.mini-btn.danger {
  background: rgba(254, 226, 226, 0.95);
  color: #b42318;
}

.metric-list {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.metric-chip {
  padding: 3px 9px;
  border-radius: 999px;
  background: rgba(219, 234, 254, 0.95);
  color: #1e40af;
  font-size: 11px;
  font-weight: 700;
}

@media (max-width: 900px) {
  .summary-grid {
    grid-template-columns: 1fr;
  }

  .page-hero {
    flex-direction: column;
    align-items: flex-start;
  }

  .runtime-item.wide {
    grid-column: span 1;
  }
}
</style>
