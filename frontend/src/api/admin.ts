import request from './request'

export function getAdminUsers() {
  return request.get('/admin/users')
}

export function updateAdminUser(
  userId: number,
  data: { role?: 'admin' | 'expert' | 'user'; is_active?: boolean },
) {
  return request.patch(`/admin/users/${userId}`, data)
}

export function getAdminPermissions() {
  return request.get('/admin/permissions')
}

export function getAdminRoles() {
  return request.get('/admin/roles')
}

export function updateAdminRolePermissions(role: string, permissions: string[]) {
  return request.patch(`/admin/roles/${role}/permissions`, { permissions })
}

export function getKnowledgeChunks(params?: {
  keyword?: string
  label_key?: string
  crop_name?: string
  disease_family?: string
  health_status?: string
  limit?: number
}) {
  return request.get('/admin/knowledge', { params })
}

export function createKnowledgeChunk(data: {
  label_key?: string
  crop_name?: string
  disease_family?: string
  health_status: string
  source_type: string
  source_name: string
  title: string
  content: string
  url?: string
  tags_json?: string[]
}) {
  return request.post('/admin/knowledge', data)
}

export function updateKnowledgeChunk(
  chunkId: number,
  data: {
    label_key?: string | null
    crop_name?: string | null
    disease_family?: string | null
    health_status?: string
    source_type?: string
    source_name?: string
    title?: string
    content?: string
    url?: string
    tags_json?: string[]
  },
) {
  return request.patch(`/admin/knowledge/${chunkId}`, data)
}

export function deleteKnowledgeChunk(chunkId: number) {
  return request.delete(`/admin/knowledge/${chunkId}`)
}

export function getModelVersions() {
  return request.get('/admin/model-versions')
}

export function getModelRuntimeInfo() {
  return request.get('/admin/model-versions/runtime')
}

export function createModelVersion(data: {
  version_code: string
  display_name: string
  description?: string
  model_path: string
  class_names_path?: string
  metrics_json?: Record<string, any>
}) {
  return request.post('/admin/model-versions', data)
}

export function updateModelVersion(
  versionId: number,
  data: {
    version_code?: string
    display_name?: string
    description?: string
    model_path?: string
    class_names_path?: string
    metrics_json?: Record<string, any>
  },
) {
  return request.patch(`/admin/model-versions/${versionId}`, data)
}

export function deleteModelVersion(versionId: number) {
  return request.delete(`/admin/model-versions/${versionId}`)
}

export function activateModelVersion(versionId: number) {
  return request.post(`/admin/model-versions/${versionId}/activate`)
}
