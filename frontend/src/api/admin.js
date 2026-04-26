import request from '@/utils/request'

export const getAdminPosts = (status) =>
  request.get('/admin/posts', { params: status ? { status } : {} })

export const updateAdminPostStatus = (postId, data) =>
  request.put(`/admin/posts/${postId}/status`, data)

export const importAdminPapers = (data) =>
  request.post('/admin/papers/import', data)
