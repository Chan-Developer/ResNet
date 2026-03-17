import request from './request'

export function getCategories() {
  return request.get('/dataset/categories')
}

export function getCategoryImages(name: string, page = 1, size = 20) {
  return request.get(`/dataset/categories/${encodeURIComponent(name)}/images`, {
    params: { page, size },
  })
}
