import request from './request'

export type DashboardScope = 'me' | 'all'

export type DashboardParams = {
  days?: number
  scope?: DashboardScope
  crop_name?: string
  label?: string
}

export function getDashboardOverview(params: DashboardParams = {}) {
  const { days = 30, scope = 'me', crop_name, label } = params
  return request.get('/report/overview', { params: { days, scope, crop_name, label } })
}

export function getDashboardFilters(scope: DashboardScope = 'me') {
  return request.get('/report/filters', { params: { scope } })
}

export function exportDashboardCsv(params: DashboardParams = {}) {
  const { days = 30, scope = 'me', crop_name, label } = params
  return request.get('/report/export.csv', {
    params: { days, scope, crop_name, label },
    responseType: 'blob',
  })
}

export function exportDashboardXlsx(params: DashboardParams = {}) {
  const { days = 30, scope = 'me', crop_name, label } = params
  return request.get('/report/export.xlsx', {
    params: { days, scope, crop_name, label },
    responseType: 'blob',
  })
}
