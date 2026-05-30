import request from '@/utils/request'
import { getRecommendations } from './recommend'

export const getVisualizationData = (targetTopic) => {
  const params = {}
  if (targetTopic) params.targetTopic = targetTopic
  return request.get('/visualization/data', { params })
}

export async function getPathSurfaceData(recommendationCount = 4, targetTopic) {
  const [visualizationResult, recommendationResult] = await Promise.allSettled([
    getVisualizationData(targetTopic),
    getRecommendations(recommendationCount),
  ])

  return {
    visualization: visualizationResult.status === 'fulfilled'
      ? (visualizationResult.value?.data || {})
      : {},
    recommendations: recommendationResult.status === 'fulfilled'
      ? (recommendationResult.value?.data?.recommendations || [])
      : [],
  }
}
