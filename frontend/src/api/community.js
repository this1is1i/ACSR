import request from '@/utils/request'

export const getCommunityPosts = (filter = 'latest') =>
  request.get('/community/posts', { params: { filter } })

export const searchPosts = (keyword) =>
  request.get('/community/posts/search', { params: { keyword } })

export const getMyPosts = () =>
  request.get('/community/posts/my')

export const createCommunityPost = (data) =>
  request.post('/community/posts', data)

export const updatePost = (postId, data) =>
  request.put(`/community/posts/${postId}`, data)

export const deletePost = (postId) =>
  request.delete(`/community/posts/${postId}`)

export const getPostComments = (postId) =>
  request.get(`/community/posts/${postId}/comments`)

export const createPostComment = (postId, data) =>
  request.post(`/community/posts/${postId}/comments`, data)

export const togglePostLike = (postId) =>
  request.post(`/community/posts/${postId}/like`)
