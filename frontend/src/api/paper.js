import request from '@/utils/request'

export const getPaperList = (params) => request.get('/paper/list', { params })
export const getPaperById = (id) => request.get(`/paper/${id}`)
export const searchPapers = (keyword, limit = 20) =>
  request.get('/paper/search', { params: { keyword, limit } })
