import request from '@/utils/request'

export const getClaimedPapers = (status = 0) =>
  request.get('/user/claimed-papers', { params: { status } })

export const confirmClaim = (paperId) =>
  request.post(`/paper/${paperId}/claim-confirm`)

export const denyClaim = (paperId) =>
  request.post(`/paper/${paperId}/claim-deny`)
