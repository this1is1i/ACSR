import request from '@/utils/request'

export const getPaperList = (params) => request.get('/paper/list', { params })
export const getPaperById = (id) => request.get(`/paper/${id}`)
export const downloadPaperTxt = (id) =>
  request.get(`/paper/${id}/download/txt`, { responseType: 'blob', rawResponse: true })
export const searchPapers = (keyword, limit = 20) =>
  request.get('/paper/search', { params: { keyword, limit } })
