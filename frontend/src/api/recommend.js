import request from '@/utils/request'

export const getRecommendations = (k = 10) =>
  request.get('/recommend', { params: { k } })

export const recordClick = (paperId, source = 'recommend') =>
  request.post('/behavior/click', { paperId, source })

export const recordFavorite = (paperId, source = 'recommend') =>
  request.post('/behavior/favorite', { paperId, source })

export const recordRead = (paperId, duration, source = 'detail') =>
  request.post('/behavior/read', { paperId, duration, source })

export const getKnowledgeGraph = () =>
  request.get('/knowledge/graph')

export const getActivityHistory = (limit = 20) =>
  request.get('/behavior/history', { params: { limit } })

export const clearActivityHistory = () =>
  request.delete('/behavior/history')

export const triggerTraining = (episodes) =>
  request.post('/recommend/train', null, { params: episodes ? { episodes } : {} })

export const getModelInfo = () =>
  request.get('/recommend/model/info')
