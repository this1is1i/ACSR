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
