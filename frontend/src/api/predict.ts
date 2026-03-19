import request from './request'

export function predictSingle(file: File, topK = 5) {
  const form = new FormData()
  form.append('file', file)
  return request.post(`/predict?top_k=${topK}`, form)
}

export function diagnoseSingle(file: File, topK = 5) {
  const form = new FormData()
  form.append('file', file)
  return request.post(`/predict/diagnose?top_k=${topK}`, form)
}

export function predictBatch(files: File[], topK = 5) {
  const form = new FormData()
  files.forEach((f) => form.append('files', f))
  return request.post(`/predict/batch?top_k=${topK}`, form)
}

export function confirmDiagnosis(data: { draft_token: string; confirmed_label?: string }) {
  return request.post('/case/confirm', data)
}
