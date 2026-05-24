import request from '@/utils/request'

export const getPaperById = (id) => request.get(`/paper/${id}`)
export const downloadPaperTxt = (id) =>
  request.get(`/paper/${id}/download/txt`, { responseType: 'blob', rawResponse: true })
export const getPaperByAminerId = (aminerId) => request.get(`/paper/aminer/${aminerId}`)
export const searchPapers = (keyword, limit = 20, filters = {}) => {
  const params = { keyword, limit }
  if (filters.yearFrom) params.yearFrom = filters.yearFrom
  if (filters.sortBy) params.sortBy = filters.sortBy
  return request.get('/paper/search', { params })
}
