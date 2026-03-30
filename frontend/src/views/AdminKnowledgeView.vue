<template>
  <div class="knowledge-page">
    <section class="page-hero">
      <div>
        <div class="hero-kicker">Knowledge Center</div>
        <h2>知识库管理</h2>
        <p class="hero-desc">维护诊断知识条目，支持按标签与作物筛选，并可直接新增、编辑和删除。</p>
      </div>
      <button class="ghost-btn" :disabled="loading" @click="fetchKnowledgeList">
        {{ loading ? '刷新中...' : '刷新列表' }}
      </button>
    </section>

    <section class="summary-grid">
      <div class="summary-card">
        <span class="summary-label">知识条目</span>
        <strong>{{ knowledgeList.length }}</strong>
      </div>
      <div class="summary-card">
        <span class="summary-label">病害条目</span>
        <strong>{{ diseasedCount }}</strong>
      </div>
      <div class="summary-card">
        <span class="summary-label">健康条目</span>
        <strong>{{ healthyCount }}</strong>
      </div>
    </section>

    <section class="panel-shell filter-shell">
      <div class="panel-head">
        <div>
          <h3>筛选条件</h3>
          <p>按关键字、标签、作物和病害类型快速定位目标知识条目。</p>
        </div>
      </div>
      <div class="filter-grid">
        <label>
          <span>关键字</span>
          <input v-model.trim="filters.keyword" placeholder="标题/内容/来源" />
        </label>
        <label>
          <span>标签键</span>
          <input v-model.trim="filters.label_key" placeholder="如 Tomato___Late_blight" />
        </label>
        <label>
          <span>作物名</span>
          <input v-model.trim="filters.crop_name" placeholder="如 Tomato" />
        </label>
        <label>
          <span>病害家族</span>
          <input v-model.trim="filters.disease_family" placeholder="如 blight" />
        </label>
        <label>
          <span>健康状态</span>
          <select v-model="filters.health_status">
            <option value="">全部</option>
            <option value="diseased">diseased</option>
            <option value="healthy">healthy</option>
          </select>
        </label>
      </div>
      <div class="action-row">
        <button class="ghost-btn" :disabled="loading" @click="fetchKnowledgeList">查询</button>
        <button class="text-btn" :disabled="loading" @click="resetFilters">重置筛选</button>
      </div>
    </section>

    <section class="panel-shell editor-shell">
      <div class="panel-head">
        <div>
          <h3>{{ editingId ? '编辑知识条目' : '新增知识条目' }}</h3>
          <p>标签留空时可作为通用建议条目使用。</p>
        </div>
      </div>

      <div class="form-grid">
        <label>
          <span>label_key</span>
          <input v-model.trim="form.label_key" placeholder="可选" />
        </label>
        <label>
          <span>crop_name</span>
          <input v-model.trim="form.crop_name" placeholder="可选" />
        </label>
        <label>
          <span>disease_family</span>
          <input v-model.trim="form.disease_family" placeholder="可选" />
        </label>
        <label>
          <span>health_status</span>
          <select v-model="form.health_status">
            <option value="diseased">diseased</option>
            <option value="healthy">healthy</option>
          </select>
        </label>
        <label>
          <span>source_type</span>
          <input v-model.trim="form.source_type" />
        </label>
        <label>
          <span>source_name</span>
          <input v-model.trim="form.source_name" />
        </label>
      </div>

      <label class="full-line">
        <span>title</span>
        <input v-model.trim="form.title" placeholder="知识标题" />
      </label>

      <label class="full-line">
        <span>content</span>
        <textarea v-model.trim="form.content" rows="4" placeholder="知识内容" />
      </label>

      <div class="form-grid">
        <label>
          <span>url</span>
          <input v-model.trim="form.url" placeholder="可选" />
        </label>
        <label>
          <span>tags_json（逗号分隔）</span>
          <input v-model="form.tagsText" placeholder="tomato, blight, diseased" />
        </label>
      </div>

      <div class="action-row">
        <button class="save-btn" :disabled="submitting" @click="submitForm">
          {{ submitting ? '提交中...' : editingId ? '保存修改' : '新增条目' }}
        </button>
        <button class="text-btn" :disabled="submitting" @click="resetForm">清空</button>
      </div>
    </section>

    <section class="panel-shell list-shell">
      <div class="panel-head">
        <div>
          <h3>知识条目列表</h3>
          <p>共 {{ knowledgeList.length }} 条，按更新时间倒序展示。</p>
        </div>
      </div>

      <div v-if="!knowledgeList.length && !loading" class="empty-state">暂无知识条目。</div>

      <article v-for="item in knowledgeList" :key="item.id" class="knowledge-item">
        <header class="item-header">
          <div>
            <h4>{{ item.title }}</h4>
            <div class="meta-line">
              <span>#{{ item.id }}</span>
              <span>{{ item.source_name }}</span>
              <span>{{ item.health_status }}</span>
              <span>{{ formatDate(item.updated_at) }}</span>
            </div>
          </div>
          <div class="item-actions">
            <button class="mini-btn" @click="editItem(item)">编辑</button>
            <button class="mini-btn danger" :disabled="deletingId === item.id" @click="removeItem(item)">
              {{ deletingId === item.id ? '删除中...' : '删除' }}
            </button>
          </div>
        </header>

        <p class="item-content">{{ item.content }}</p>

        <div class="meta-line">
          <span>label: {{ item.label_key || '--' }}</span>
          <span>crop: {{ item.crop_name || '--' }}</span>
          <span>family: {{ item.disease_family || '--' }}</span>
        </div>

        <div class="tag-list">
          <span v-for="tag in item.tags_json" :key="`${item.id}-${tag}`" class="tag-chip">{{ tag }}</span>
          <span v-if="!item.tags_json.length" class="tag-chip muted">无标签</span>
        </div>
      </article>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  createKnowledgeChunk,
  deleteKnowledgeChunk,
  getKnowledgeChunks,
  updateKnowledgeChunk,
} from '../api/admin'

type KnowledgeItem = {
  id: number
  label_key?: string | null
  crop_name?: string | null
  disease_family?: string | null
  health_status: string
  source_type: string
  source_name: string
  title: string
  content: string
  url?: string
  tags_json: string[]
  created_at?: string
  updated_at?: string
}

const loading = ref(false)
const submitting = ref(false)
const deletingId = ref<number | null>(null)
const editingId = ref<number | null>(null)
const knowledgeList = ref<KnowledgeItem[]>([])

const filters = reactive({
  keyword: '',
  label_key: '',
  crop_name: '',
  disease_family: '',
  health_status: '',
})

const form = reactive({
  label_key: '',
  crop_name: '',
  disease_family: '',
  health_status: 'diseased',
  source_type: 'internal',
  source_name: 'PlantCare 知识库',
  title: '',
  content: '',
  url: '',
  tagsText: '',
})

const healthyCount = computed(() => knowledgeList.value.filter((item) => item.health_status === 'healthy').length)
const diseasedCount = computed(() => knowledgeList.value.filter((item) => item.health_status === 'diseased').length)

function formatDate(value?: string) {
  if (!value) return '--'
  const date = new Date(value)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

function parseTags(text: string) {
  return text
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

function resetFilters() {
  filters.keyword = ''
  filters.label_key = ''
  filters.crop_name = ''
  filters.disease_family = ''
  filters.health_status = ''
  fetchKnowledgeList()
}

function resetForm() {
  editingId.value = null
  form.label_key = ''
  form.crop_name = ''
  form.disease_family = ''
  form.health_status = 'diseased'
  form.source_type = 'internal'
  form.source_name = 'PlantCare 知识库'
  form.title = ''
  form.content = ''
  form.url = ''
  form.tagsText = ''
}

function editItem(item: KnowledgeItem) {
  editingId.value = item.id
  form.label_key = item.label_key || ''
  form.crop_name = item.crop_name || ''
  form.disease_family = item.disease_family || ''
  form.health_status = item.health_status || 'diseased'
  form.source_type = item.source_type || 'internal'
  form.source_name = item.source_name || 'PlantCare 知识库'
  form.title = item.title || ''
  form.content = item.content || ''
  form.url = item.url || ''
  form.tagsText = Array.isArray(item.tags_json) ? item.tags_json.join(', ') : ''
}

async function fetchKnowledgeList() {
  loading.value = true
  try {
    const res: any = await getKnowledgeChunks({
      keyword: filters.keyword || undefined,
      label_key: filters.label_key || undefined,
      crop_name: filters.crop_name || undefined,
      disease_family: filters.disease_family || undefined,
      health_status: filters.health_status || undefined,
      limit: 1000,
    })
    knowledgeList.value = Array.isArray(res.data) ? res.data : []
  } catch {
    knowledgeList.value = []
  } finally {
    loading.value = false
  }
}

async function submitForm() {
  if (!form.title.trim() || !form.content.trim()) {
    ElMessage.warning('标题和内容不能为空')
    return
  }

  submitting.value = true
  const payload = {
    label_key: form.label_key || '',
    crop_name: form.crop_name || '',
    disease_family: form.disease_family || '',
    health_status: form.health_status || 'diseased',
    source_type: form.source_type || 'internal',
    source_name: form.source_name || 'PlantCare 知识库',
    title: form.title.trim(),
    content: form.content.trim(),
    url: form.url || '',
    tags_json: parseTags(form.tagsText),
  }

  try {
    if (editingId.value) {
      await updateKnowledgeChunk(editingId.value, payload)
      ElMessage.success('知识条目已更新')
    } else {
      await createKnowledgeChunk(payload)
      ElMessage.success('知识条目已新增')
    }
    resetForm()
    await fetchKnowledgeList()
  } finally {
    submitting.value = false
  }
}

async function removeItem(item: KnowledgeItem) {
  const confirmed = window.confirm(`确认删除条目 #${item.id} 吗？`)
  if (!confirmed) return

  deletingId.value = item.id
  try {
    await deleteKnowledgeChunk(item.id)
    ElMessage.success('知识条目已删除')
    if (editingId.value === item.id) resetForm()
    await fetchKnowledgeList()
  } finally {
    deletingId.value = null
  }
}

onMounted(fetchKnowledgeList)
</script>

<style scoped>
.knowledge-page {
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
    radial-gradient(circle at top right, rgba(167, 199, 231, 0.24), transparent 34%),
    radial-gradient(circle at bottom left, rgba(134, 239, 172, 0.2), transparent 34%),
    linear-gradient(135deg, rgba(255, 255, 255, 0.94), rgba(247, 252, 250, 0.92));
  border: 1px solid rgba(214, 226, 220, 0.9);
  box-shadow: var(--shadow-soft);
}

.hero-kicker {
  font-size: 12px;
  font-weight: 800;
  color: #3b7d67;
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

.filter-grid,
.form-grid {
  margin-top: 14px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
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
select,
textarea {
  width: 100%;
  border: 1px solid #dfd5dc;
  border-radius: 12px;
  padding: 10px 12px;
  font-family: inherit;
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.85);
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
  background: linear-gradient(135deg, #2f8d6f, #4e9d85);
  color: #fff;
}

.text-btn {
  padding: 11px 14px;
  background: rgba(247, 243, 246, 0.8);
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

.knowledge-item {
  padding: 14px;
  border-radius: 16px;
  border: 1px solid rgba(229, 220, 226, 0.9);
  background: rgba(255, 255, 255, 0.78);
}

.knowledge-item + .knowledge-item {
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

.item-content {
  margin: 8px 0;
  line-height: 1.72;
  color: var(--text-secondary);
  white-space: pre-wrap;
}

.meta-line {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 12px;
  color: var(--text-muted);
}

.item-actions {
  display: flex;
  gap: 8px;
}

.mini-btn {
  padding: 8px 12px;
  background: rgba(243, 236, 241, 0.8);
  color: var(--text-primary);
}

.mini-btn.danger {
  background: rgba(254, 226, 226, 0.95);
  color: #b42318;
}

.tag-list {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag-chip {
  padding: 3px 9px;
  border-radius: 999px;
  background: rgba(220, 246, 237, 0.95);
  color: #1b6a55;
  font-size: 11px;
  font-weight: 700;
}

.tag-chip.muted {
  background: rgba(238, 232, 237, 0.85);
  color: var(--text-muted);
}

@media (max-width: 900px) {
  .summary-grid {
    grid-template-columns: 1fr;
  }

  .page-hero {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
