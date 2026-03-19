<template>
  <div class="role-page">
    <section class="role-hero">
      <div>
        <div class="hero-kicker">Role & Permission</div>
        <h2>角色与权限配置</h2>
        <p class="hero-desc">按角色定义可执行操作，前后端统一按权限码控制页面访问和接口调用。</p>
      </div>
      <button class="ghost-btn" :disabled="loading" @click="fetchData">
        {{ loading ? '刷新中...' : '刷新配置' }}
      </button>
    </section>

    <section class="summary-grid">
      <div class="summary-card">
        <span class="summary-label">角色数量</span>
        <strong>{{ roles.length }}</strong>
      </div>
      <div class="summary-card">
        <span class="summary-label">权限项</span>
        <strong>{{ permissionCatalog.length }}</strong>
      </div>
      <div class="summary-card">
        <span class="summary-label">可编辑角色</span>
        <strong>{{ editableRoles }}</strong>
      </div>
    </section>

    <section class="role-grid">
      <article
        v-for="role in roles"
        :key="role.role"
        class="role-card"
        :class="{ readonly: !role.editable }"
      >
        <header class="role-head">
          <div>
            <h3>{{ role.label }}</h3>
            <p class="role-key">{{ role.role }}</p>
          </div>
          <span class="role-badge" :class="role.role">
            {{ role.editable ? '可编辑' : '系统内置' }}
          </span>
        </header>

        <div class="permission-list">
          <label
            v-for="item in permissionCatalog"
            :key="`${role.role}-${item.code}`"
            class="permission-item"
          >
            <input
              type="checkbox"
              :checked="hasPermission(role.role, item.code)"
              :disabled="!role.editable || savingRole === role.role"
              @change="togglePermission(role.role, item.code, ($event.target as HTMLInputElement).checked)"
            />
            <div class="permission-copy">
              <div class="permission-title">{{ item.name }}</div>
              <div class="permission-desc">{{ item.description }}</div>
              <div class="permission-code">{{ item.code }}</div>
            </div>
          </label>
        </div>

        <footer class="role-actions">
          <button
            class="save-btn"
            :disabled="!role.editable || savingRole === role.role || !hasChanges(role)"
            @click="handleSave(role)"
          >
            {{ savingRole === role.role ? '保存中...' : '保存权限' }}
          </button>
        </footer>
      </article>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getAdminPermissions, getAdminRoles, updateAdminRolePermissions } from '../api/admin'

type PermissionItem = {
  code: string
  name: string
  description: string
}

type RoleItem = {
  role: 'admin' | 'expert' | 'user'
  label: string
  permissions: string[]
  editable: boolean
}

const loading = ref(false)
const savingRole = ref<string>('')
const permissionCatalog = ref<PermissionItem[]>([])
const roles = ref<RoleItem[]>([])
const drafts = reactive<Record<string, string[]>>({})

const editableRoles = computed(() => roles.value.filter((role) => role.editable).length)

function normalizeCodes(codes: string[]) {
  return [...new Set(codes)].sort()
}

function hasPermission(role: string, code: string) {
  return (drafts[role] || []).includes(code)
}

function togglePermission(role: string, code: string, checked: boolean) {
  const current = new Set(drafts[role] || [])
  if (checked) current.add(code)
  else current.delete(code)
  drafts[role] = [...current]
}

function syncDrafts(roleList: RoleItem[]) {
  Object.keys(drafts).forEach((key) => delete drafts[key])
  roleList.forEach((role) => {
    drafts[role.role] = [...role.permissions]
  })
}

function hasChanges(role: RoleItem) {
  const left = normalizeCodes(role.permissions).join(',')
  const right = normalizeCodes(drafts[role.role] || []).join(',')
  return left !== right
}

async function fetchData() {
  loading.value = true
  try {
    const [permissionRes, roleRes]: any = await Promise.all([
      getAdminPermissions(),
      getAdminRoles(),
    ])
    permissionCatalog.value = Array.isArray(permissionRes.data) ? permissionRes.data : []
    roles.value = Array.isArray(roleRes.data) ? roleRes.data : []
    syncDrafts(roles.value)
  } catch { /* handled by interceptor */ } finally {
    loading.value = false
  }
}

async function handleSave(role: RoleItem) {
  if (!role.editable) return
  savingRole.value = role.role
  try {
    const payload = normalizeCodes(drafts[role.role] || [])
    const res: any = await updateAdminRolePermissions(role.role, payload)
    roles.value = roles.value.map((item) => (item.role === role.role ? res.data : item))
    drafts[role.role] = [...res.data.permissions]
    ElMessage.success(`${role.label} 权限已更新`)
  } catch { /* handled by interceptor */ } finally {
    savingRole.value = ''
  }
}

onMounted(fetchData)
</script>

<style scoped>
.role-page {
  max-width: 1120px;
  margin: 0 auto;
  padding: 32px 24px 40px;
}

.role-hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 24px;
  border-radius: 24px;
  background:
    radial-gradient(circle at top right, rgba(167, 199, 231, 0.24), transparent 36%),
    radial-gradient(circle at bottom left, rgba(215, 161, 173, 0.2), transparent 36%),
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

.role-hero h2 {
  margin: 8px 0 6px;
  font-size: 28px;
  color: var(--text-primary);
}

.hero-desc {
  margin: 0;
  line-height: 1.7;
  color: var(--text-secondary);
}

.ghost-btn {
  border: none;
  border-radius: 14px;
  padding: 11px 16px;
  background: var(--lavender-light);
  color: var(--text-primary);
  font-family: inherit;
  font-weight: 700;
  cursor: pointer;
}

.ghost-btn:disabled {
  opacity: 0.52;
  cursor: not-allowed;
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

.role-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 16px;
}

.role-card {
  border-radius: 22px;
  border: 1px solid rgba(228, 217, 223, 0.92);
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.92), rgba(249, 246, 247, 0.88));
  box-shadow: var(--shadow-soft);
  padding: 18px;
}

.role-card.readonly {
  opacity: 0.88;
}

.role-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.role-head h3 {
  margin: 0;
  font-size: 20px;
}

.role-key {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--text-muted);
}

.role-badge {
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 800;
}

.role-badge.admin {
  background: rgba(167, 199, 231, 0.24);
  color: #2f5f86;
}

.role-badge.expert {
  background: rgba(242, 199, 178, 0.35);
  color: #9a3412;
}

.role-badge.user {
  background: var(--lavender-light);
  color: var(--text-secondary);
}

.permission-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.permission-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.66);
  border: 1px solid rgba(235, 224, 230, 0.9);
}

.permission-copy {
  min-width: 0;
}

.permission-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-primary);
}

.permission-desc {
  margin-top: 3px;
  font-size: 12px;
  color: var(--text-secondary);
}

.permission-code {
  margin-top: 4px;
  font-size: 11px;
  color: var(--text-muted);
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
}

.role-actions {
  margin-top: 14px;
}

.save-btn {
  width: 100%;
  border: none;
  border-radius: 14px;
  padding: 11px 16px;
  background: linear-gradient(135deg, var(--pink-deep), #8c6e79);
  color: #fff;
  font-family: inherit;
  font-weight: 700;
  cursor: pointer;
}

.save-btn:disabled {
  opacity: 0.52;
  cursor: not-allowed;
}

@media (max-width: 900px) {
  .summary-grid {
    grid-template-columns: 1fr;
  }

  .role-hero {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
