export const SEARCH_STATE_KEY = 'search-paper-state'

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
