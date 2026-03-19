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
