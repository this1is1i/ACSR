export const SEARCH_STATE_KEY = 'search-paper-state'
export const SEARCH_RESTORE_PENDING_KEY = 'search-paper-restore-pending'

function sanitizeString(value) {
  return String(value ?? '').trim()
}

export function toStringArray(value) {
  if (Array.isArray(value)) {
    return value.map(sanitizeString).filter(Boolean)
  }

  if (typeof value === 'string') {
    const trimmed = value.trim()
    if (!trimmed) return []

    try {
      const parsed = JSON.parse(trimmed)
      if (Array.isArray(parsed)) {
        return parsed.map(sanitizeString).filter(Boolean)
      }
      if (typeof parsed === 'string') {
        return sanitizeString(parsed) ? [sanitizeString(parsed)] : []
      }
    } catch {}

    return [trimmed]
  }

  return []
}

export function normalizePaper(raw = {}) {
  const authorsList = toStringArray(raw.authors)
  const keywordsList = toStringArray(raw.keywords || raw.tags)
  const abstractText = raw.abstract || raw.abstrakt || raw.summary || ''

  return {
    ...raw,
    abstractText,
    authorsList,
    authorText: authorsList.length ? authorsList.join(', ') : '未知作者',
    keywordsList,
  }
}

function sanitizeFilename(filename) {
  return sanitizeString(filename).replace(/[<>:"/\\|?*\x00-\x1f]/g, '_')
}

export function getDownloadFilename(contentDisposition, fallback = 'paper.txt') {
  const safeFallback = sanitizeFilename(fallback) || 'paper.txt'
  if (!contentDisposition) return safeFallback

  const encodedMatch = contentDisposition.match(/filename\*\s*=\s*UTF-8''([^;]+)/i)
  if (encodedMatch?.[1]) {
    try {
      return sanitizeFilename(decodeURIComponent(encodedMatch[1])) || safeFallback
    } catch {}
  }

  const plainMatch = contentDisposition.match(/filename\s*=\s*"([^"]+)"|filename\s*=\s*([^;]+)/i)
  const plainFilename = plainMatch?.[1] || plainMatch?.[2]
  return sanitizeFilename(plainFilename) || safeFallback
}
