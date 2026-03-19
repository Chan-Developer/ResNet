import request from './request'

export type RegionAlertStatus = 'all' | 'unread' | 'read'

export function getRegionAlerts(params?: { status?: RegionAlertStatus; limit?: number }) {
  return request.get('/alerts/region', { params })
}

export function markRegionAlertRead(alertId: number) {
  return request.patch(`/alerts/region/${alertId}/read`)
}

export function getRegionAlertSummary() {
  return request.get('/alerts/region/summary')
}
