import request from './request'

export type FollowupPlanStatus = 'active' | 'paused' | 'completed' | 'cancelled'

export function listFollowupPlans(params?: { status?: FollowupPlanStatus }) {
  return request.get('/followup/plans', { params })
}

export function createFollowupPlan(data: {
  title?: string
  case_id?: number
  target_label?: string
  notes?: string
  frequency_days?: number
  start_date?: string
}) {
  return request.post('/followup/plans', data)
}

export function updateFollowupPlan(
  planId: number,
  data: { status?: FollowupPlanStatus; frequency_days?: number; notes?: string },
) {
  return request.patch(`/followup/plans/${planId}`, data)
}

export function listFollowupCheckins(planId: number, params?: { limit?: number }) {
  return request.get(`/followup/plans/${planId}/checkins`, { params })
}

export function getFollowupEvaluation(planId: number) {
  return request.get(`/followup/plans/${planId}/evaluation`)
}

export function uploadFollowupCheckin(
  planId: number,
  file: File,
  data?: { top_k?: number; note?: string },
) {
  const form = new FormData()
  form.append('file', file)
  if (typeof data?.top_k === 'number') {
    form.append('top_k', String(data.top_k))
  }
  if (data?.note) {
    form.append('note', data.note)
  }
  return request.post(`/followup/plans/${planId}/checkins`, form)
}
