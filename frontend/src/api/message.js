import request from '@/utils/request'

export const getConversations = () => request.get('/message/conversations')
export const getChatHistory = (contactId) => request.get(`/message/chat/${contactId}`)
export const sendMessageRest = (receiverId, content) => request.post('/message/send', null, { params: { receiverId, content } })
export const markMessageRead = (messageId) => request.post(`/message/mark-read/${messageId}`)
export const getRecommendedCollaborators = () => request.get('/message/recommended-collaborators')
export const searchUsers = (q) => request.get('/user/search', { params: { q } })
