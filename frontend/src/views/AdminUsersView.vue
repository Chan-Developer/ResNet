<template>
  <div class="admin-page">
    <section class="admin-hero">
      <div>
        <div class="hero-kicker">Access Control</div>
        <h2>用户角色与权限管理</h2>
        <p class="hero-desc">集中管理账号角色、启用状态，确保病例审核和系统入口按权限开放。</p>
      </div>
      <div class="hero-badge">仅管理员可见</div>
    </section>

    <section class="summary-grid">
      <div class="summary-card">
        <span class="summary-label">用户总数</span>
        <strong>{{ users.length }}</strong>
      </div>
      <div class="summary-card">
        <span class="summary-label">管理员</span>
        <strong>{{ adminCount }}</strong>
      </div>
      <div class="summary-card">
        <span class="summary-label">停用账号</span>
        <strong>{{ disabledCount }}</strong>
      </div>
    </section>

    <section class="panel-shell">
      <div class="panel-head">
        <div>
          <h3>账号列表</h3>
          <p>当前账号不能修改自己的角色或启用状态，避免管理员把自己锁死。</p>
        </div>
        <button class="ghost-btn" :disabled="loading" @click="fetchUsers">
          {{ loading ? '刷新中...' : '刷新列表' }}
        </button>
      </div>

      <div v-if="!users.length && !loading" class="empty-state">
        暂无用户数据。
      </div>

      <div v-else class="user-list">
        <article
          v-for="user in users"
          :key="user.id"
          class="user-row"
          :class="{ current: user.id === currentUserId }"
        >
          <div class="user-main">
            <div class="avatar">{{ user.username.charAt(0).toUpperCase() }}</div>
            <div class="user-copy">
              <div class="user-line">
                <strong>{{ user.username }}</strong>
                <span class="pill" :class="user.role">
                  {{ user.role === 'admin' ? '管理员' : user.role === 'expert' ? '专家用户' : '普通用户' }}
                </span>
                <span class="pill" :class="user.is_active ? 'active' : 'inactive'">
                  {{ user.is_active ? '启用中' : '已停用' }}
                </span>
                <span v-if="user.id === currentUserId" class="self-tag">当前账号</span>
              </div>
              <div class="user-meta">{{ user.email }}</div>
              <div class="user-meta">创建于 {{ formatTime(user.created_at) }}</div>
            </div>
          </div>

          <div class="user-controls">
            <label class="control-item">
              <span>角色</span>
              <select v-model="drafts[user.id].role" :disabled="isSelf(user)">
                <option value="user">普通用户</option>
                <option value="expert">专家用户</option>
                <option value="admin">管理员</option>
              </select>
            </label>
            <label class="control-item">
              <span>状态</span>
              <select v-model="drafts[user.id].is_active" :disabled="isSelf(user)">
                <option :value="true">启用</option>
                <option :value="false">停用</option>
              </select>
            </label>
            <button
              class="save-btn"
              :disabled="savingId === user.id || !hasChanges(user) || isSelf(user)"
              @click="handleSave(user)"
            >
              {{ savingId === user.id ? '保存中...' : '保存修改' }}
            </button>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getAdminUsers, updateAdminUser } from '../api/admin'
import { useUserStore } from '../stores/user'

type UserRow = {
  id: number
  username: string
  email: string
  role: 'admin' | 'expert' | 'user'
  is_active: boolean
  created_at?: string
}

const userStore = useUserStore()
const loading = ref(false)
const savingId = ref<number | null>(null)
const users = ref<UserRow[]>([])
const drafts = reactive<Record<number, { role: 'admin' | 'expert' | 'user'; is_active: boolean }>>({})

const currentUserId = computed(() => userStore.userInfo?.id ?? 0)
const adminCount = computed(() => users.value.filter((user) => user.role === 'admin').length)
const disabledCount = computed(() => users.value.filter((user) => !user.is_active).length)

function isSelf(user: UserRow) {
  return user.id === currentUserId.value
}

function formatTime(value?: string) {
  if (!value) return '--'
  const date = new Date(value)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

function hasChanges(user: UserRow) {
  const draft = drafts[user.id]
  if (!draft) return false
  return draft.role !== user.role || draft.is_active !== user.is_active
}

function syncDrafts(data: UserRow[]) {
  Object.keys(drafts).forEach((key) => delete drafts[Number(key)])
  data.forEach((user) => {
    drafts[user.id] = {
      role: user.role,
      is_active: user.is_active,
    }
  })
}

async function fetchUsers() {
  loading.value = true
  try {
    const res: any = await getAdminUsers()
    const list = Array.isArray(res.data) ? res.data : []
    syncDrafts(list)
    users.value = list
  } catch { /* handled by interceptor */ } finally {
    loading.value = false
  }
}

async function handleSave(user: UserRow) {
  const draft = drafts[user.id]
  const payload: { role?: 'admin' | 'expert' | 'user'; is_active?: boolean } = {}

  if (draft.role !== user.role) payload.role = draft.role
  if (draft.is_active !== user.is_active) payload.is_active = draft.is_active
  if (!Object.keys(payload).length) return

  savingId.value = user.id
  try {
    const res: any = await updateAdminUser(user.id, payload)
    const nextUser = res.data as UserRow
    users.value = users.value.map((item) => (item.id === user.id ? nextUser : item))
    drafts[user.id] = {
      role: nextUser.role,
      is_active: nextUser.is_active,
    }
    ElMessage.success('权限已更新')
  } catch { /* handled by interceptor */ } finally {
    savingId.value = null
  }
}

onMounted(fetchUsers)
</script>

<style scoped>
.admin-page {
  max-width: 1120px;
  margin: 0 auto;
  padding: 32px 24px 40px;
}

.admin-hero {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: flex-start;
  padding: 28px;
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
  letter-spacing: 1.6px;
}

.admin-hero h2 {
  margin: 10px 0 8px;
  font-size: 30px;
  color: var(--text-primary);
}

.hero-desc {
  margin: 0;
  max-width: 680px;
  line-height: 1.75;
  color: var(--text-secondary);
}

.hero-badge {
  white-space: nowrap;
  padding: 10px 14px;
  border-radius: 999px;
  background: rgba(79, 127, 117, 0.12);
  color: var(--green-deep);
  font-size: 12px;
  font-weight: 800;
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
  padding: 22px;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid var(--card-border);
  box-shadow: var(--shadow-soft);
}

.panel-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
  margin-bottom: 18px;
}

.panel-head h3 {
  margin: 0 0 6px;
  font-size: 22px;
}

.panel-head p {
  margin: 0;
  color: var(--text-muted);
  font-size: 13px;
}

.ghost-btn,
.save-btn {
  border: none;
  border-radius: 14px;
  font-family: inherit;
  font-weight: 700;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.ghost-btn {
  padding: 11px 16px;
  background: var(--lavender-light);
  color: var(--text-primary);
}

.save-btn {
  padding: 12px 18px;
  background: linear-gradient(135deg, var(--pink-deep), #8c6e79);
  color: #fff;
}

.ghost-btn:hover,
.save-btn:hover:not(:disabled) {
  transform: translateY(-1px);
}

.save-btn:disabled,
.ghost-btn:disabled {
  opacity: 0.52;
  cursor: not-allowed;
  transform: none;
}

.empty-state {
  padding: 48px 12px;
  text-align: center;
  color: var(--text-muted);
}

.user-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.user-row {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: center;
  padding: 18px;
  border-radius: 22px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.92), rgba(249, 246, 247, 0.88));
  border: 1px solid rgba(228, 217, 223, 0.92);
}

.user-row.current {
  box-shadow: inset 0 0 0 1px rgba(178, 106, 127, 0.24);
}

.user-main {
  display: flex;
  gap: 14px;
  align-items: center;
  min-width: 0;
}

.avatar {
  width: 48px;
  height: 48px;
  border-radius: 16px;
  background: linear-gradient(135deg, var(--pink), var(--lavender));
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 800;
  flex-shrink: 0;
}

.user-copy {
  min-width: 0;
}

.user-line {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.user-line strong {
  font-size: 16px;
  color: var(--text-primary);
}

.user-meta {
  margin-top: 6px;
  color: var(--text-secondary);
  font-size: 13px;
}

.pill,
.self-tag {
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 800;
}

.pill.admin {
  background: rgba(167, 199, 231, 0.24);
  color: #2f5f86;
}

.pill.user {
  background: var(--lavender-light);
  color: var(--text-secondary);
}

.pill.expert {
  background: rgba(242, 199, 178, 0.35);
  color: #9a3412;
}

.pill.active {
  background: rgba(157, 191, 182, 0.22);
  color: var(--green-deep);
}

.pill.inactive {
  background: rgba(255, 228, 230, 0.6);
  color: #be123c;
}

.self-tag {
  background: rgba(242, 199, 178, 0.34);
  color: #b45309;
}

.user-controls {
  display: flex;
  gap: 12px;
  align-items: flex-end;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.control-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.control-item span {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-muted);
}

.control-item select {
  min-width: 132px;
  padding: 10px 12px;
  border-radius: 14px;
  border: 1px solid rgba(220, 210, 218, 0.92);
  background: rgba(255, 255, 255, 0.88);
  color: var(--text-primary);
  font-family: inherit;
}

.control-item select:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

@media (max-width: 900px) {
  .summary-grid {
    grid-template-columns: 1fr;
  }

  .user-row,
  .panel-head,
  .admin-hero {
    flex-direction: column;
    align-items: flex-start;
  }

  .user-controls {
    width: 100%;
    justify-content: flex-start;
  }

  .save-btn {
    width: 100%;
  }
}
</style>
