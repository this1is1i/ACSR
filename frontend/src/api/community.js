import request from '@/utils/request'

export const getCommunityPosts = (filter = 'latest') =>
  request.get('/community/posts', { params: { filter } })

export const createCommunityPost = (data) =>
  request.post('/community/posts', data)

export const getPostComments = (postId) =>
  request.get(`/community/posts/${postId}/comments`)

export const createPostComment = (postId, data) =>
  request.post(`/community/posts/${postId}/comments`, data)
