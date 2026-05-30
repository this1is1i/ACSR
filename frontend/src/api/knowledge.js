import request from '@/utils/request'

export const getKeywords = () => request.get('/knowledge/keywords')
