import request from './request'

export type ConsultMessage = {
  role: 'user' | 'assistant'
  content: string
}

export type ConsultPayload = {
  question: string
  history?: ConsultMessage[]
}

export function submitDiseaseConsult(payload: ConsultPayload) {
  const apiPath = String(import.meta.env.VITE_CONSULT_API_PATH || '/consult').trim() || '/consult'
  return request.post(apiPath, payload)
}
