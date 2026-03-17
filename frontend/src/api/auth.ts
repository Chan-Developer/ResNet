import request from './request'

export function register(data: { username: string; email: string; password: string }) {
  return request.post('/auth/register', data)
}

export function login(data: { username: string; password: string }) {
  return request.post('/auth/login', data)
}

export function getMe() {
  return request.get('/auth/me')
}
