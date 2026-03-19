<template>
  <div class="history-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-icon">🕘</div>
      <div>
        <h2>识别历史</h2>
        <p class="header-desc">查看你所有的植物病害识别记录</p>
      </div>
    </div>

    <!-- 历史卡片列表 -->
    <div v-loading="loading" class="history-list">
      <div v-if="records.length === 0 && !loading" class="empty-state">
        <div class="empty-icon">🍀</div>
        <p>还没有识别记录哦~</p>
        <p class="empty-hint">去「病害识别」页面上传图片试试吧</p>
      </div>

      <div
        v-for="record in records"
        :key="record.id"
        class="history-card"
      >
        <div class="card-image">
          <el-image
            :src="record.image_url"
            fit="contain"
            :preview-src-list="[record.image_url]"
            class="thumb"
          />
        </div>
        <div class="card-content">
          <div class="card-top">
            <span class="disease-tag">{{ formatName(record.top1_class) }}</span>
            <span class="time">{{ formatTime(record.created_at) }}</span>
          </div>
          <div class="card-bar">
            <ConfidenceBar :value="record.top1_confidence" />
          </div>
        </div>
        <div v-if="canDeleteHistory" class="card-action">
          <el-popconfirm title="确定要删除这条记录吗？" confirm-button-text="删除" cancel-button-text="取消" @confirm="handleDelete(record.id)">
            <template #reference>
              <button class="delete-btn" title="删除">
                <span>×</span>
              </button>
            </template>
          </el-popconfirm>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div v-if="total > 0" class="pagination-wrap">
      <el-pagination
        layout="prev, pager, next"
        :total="total"
        :page-size="pageSize"
        v-model:current-page="page"
        @current-change="fetchData"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import ConfidenceBar from '../components/ConfidenceBar.vue'
import { getHistory, deleteHistory } from '../api/history'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const loading = ref(false)
const records = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const canDeleteHistory = computed(() => userStore.hasPermission('history:delete'))

function formatName(name: string) {
  return name?.replace(/___/g, ' - ').replace(/_/g, ' ') || ''
}

function formatTime(t: string) {
  if (!t) return ''
  const d = new Date(t)
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  const hh = String(d.getHours()).padStart(2, '0')
  const mi = String(d.getMinutes()).padStart(2, '0')
  return `${mm}-${dd} ${hh}:${mi}`
}

async function fetchData() {
  loading.value = true
  try {
    const res: any = await getHistory(page.value, pageSize)
    records.value = res.data.items
    total.value = res.data.total
  } catch { /* interceptor */ } finally {
    loading.value = false
  }
}

async function handleDelete(id: number) {
  if (!canDeleteHistory.value) return
  try {
    await deleteHistory(id)
    ElMessage.success('已删除')
    if (records.value.length === 1 && page.value > 1) {
      page.value -= 1
    }
    await fetchData()
  } catch { /* interceptor */ }
}

onMounted(fetchData)
</script>

<style scoped>
.history-page {
  max-width: 800px;
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
  font-size: 13px;
  font-weight: 800;
  color: var(--pink-deep);
  background: linear-gradient(135deg, var(--sky-light), var(--lavender-light));
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

/* History Card */
.history-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 200px;
}

.history-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 18px;
  background: var(--card-bg);
  backdrop-filter: var(--glass-blur);
  border: 1px solid var(--card-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-soft);
  transition: transform 0.2s, box-shadow 0.2s;
}
.history-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-hover);
}

.card-image {
  flex-shrink: 0;
  width: 88px;
  height: 88px;
  padding: 8px;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, var(--pink-light), var(--lavender-light));
  border: 1px solid rgba(220, 210, 218, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
}
.thumb {
  width: 100%;
  height: 100%;
  border-radius: var(--radius-sm);
  display: block;
}

.thumb :deep(.el-image__inner) {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.thumb :deep(.el-image__wrapper) {
  border-radius: var(--radius-sm);
  overflow: hidden;
  background: rgba(255, 255, 255, 0.72);
}

.card-content {
  flex: 1;
  min-width: 0;
}
.card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  gap: 8px;
}
.disease-tag {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
  background: linear-gradient(135deg, var(--pink-light), var(--green-light));
  padding: 3px 12px;
  border-radius: 20px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 300px;
}
.time {
  font-size: 12px;
  color: var(--text-muted);
  white-space: nowrap;
}
.card-bar {
  width: 100%;
}

.card-action {
  flex-shrink: 0;
}
.delete-btn {
  width: 32px;
  height: 32px;
  border: 1.5px solid #fecdd3;
  border-radius: 50%;
  background: rgba(255, 228, 230, 0.4);
  color: #e11d48;
  font-size: 18px;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  line-height: 1;
}
.delete-btn:hover {
  background: #ffe4e6;
  border-color: #fda4af;
  transform: scale(1.1);
}

/* Empty */
.empty-state {
  text-align: center;
  padding: 60px 20px;
}
.empty-icon {
  font-size: 48px;
  color: var(--text-muted);
  margin-bottom: 12px;
}
.empty-state p {
  color: var(--text-muted);
  font-size: 15px;
  font-weight: 600;
  margin: 4px 0;
}
.empty-hint {
  font-size: 13px !important;
  color: var(--text-muted);
}

/* Pagination */
.pagination-wrap {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

@media (max-width: 720px) {
  .history-card {
    flex-direction: column;
    align-items: flex-start;
  }
  .card-image {
    width: 100%;
    height: 180px;
  }
  .card-top {
    flex-direction: column;
    align-items: flex-start;
  }
  .card-action {
    align-self: flex-end;
  }
}
</style>
