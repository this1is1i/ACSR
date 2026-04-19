import request from '@/utils/request'

export const getVisualizationData = () => request.get('/visualization/data')
