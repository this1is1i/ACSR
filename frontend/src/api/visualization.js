import request from '@/utils/request'
import { getRecommendations } from './recommend'

export const getVisualizationData = () => request.get('/visualization/data')

export async function getPathSurfaceData(recommendationCount = 4) {
  const [visualizationResult, recommendationResult] = await Promise.allSettled([
    getVisualizationData(),
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
