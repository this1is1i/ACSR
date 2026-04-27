export const SEARCH_STATE_KEY = 'search-paper-state'
export const SEARCH_RESTORE_PENDING_KEY = 'search-paper-restore-pending'
export const SEARCH_DEFAULT_FILTERS = {
  time: '全部时间',
  type: '全部类型',
  field: '全部领域',
  sort: '相关度',
}

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

export function getStoredSearchState() {
  if (typeof window === 'undefined') return null

  const rawState = window.sessionStorage.getItem(SEARCH_STATE_KEY)
  if (!rawState) return null

  try {
    const parsed = JSON.parse(rawState)
    return parsed && typeof parsed === 'object' ? parsed : null
  } catch {
    return null
  }
}

export function getActiveFilterLabels(filters = {}, defaults = SEARCH_DEFAULT_FILTERS) {
  return Object.entries(defaults).flatMap(([key, defaultValue]) => {
    const value = sanitizeString(filters?.[key])
    if (!value || value === defaultValue) return []
    return [value]
  })
}

export function getActiveTagLabels(tags = []) {
  return toStringArray(tags).flatMap((tag) => {
    const normalized = sanitizeString(tag)
    if (!normalized.startsWith('*')) return []

    const label = sanitizeString(normalized.slice(1))
    return label ? [label] : []
  })
}

export function summarizeSearchContext(filters = {}, tags = []) {
  return {
    activeFilters: getActiveFilterLabels(filters),
    activeTags: getActiveTagLabels(tags),
  }
}

export function buildPaperPathContext(paper, options = {}) {
  const { searchState = getStoredSearchState(), hasSearchContext = false } = options
  const keywords = Array.isArray(paper?.keywordsList)
    ? paper.keywordsList
    : toStringArray(paper?.keywords || paper?.tags)
  const query = hasSearchContext ? sanitizeString(searchState?.keyword) : ''
  const activeFilters = hasSearchContext ? getActiveFilterLabels(searchState?.filters) : []
  const activeTags = hasSearchContext ? getActiveTagLabels(searchState?.tags) : []
  const resultCount = hasSearchContext && Array.isArray(searchState?.results)
    ? searchState.results.length
    : 0
  const anchors = [...new Set([query, ...activeTags, ...keywords].filter(Boolean))].slice(0, 4)

  const nextSteps = anchors.length
    ? anchors.map((anchor, index) => ({
        title: index === 0 && query ? `回到 ${anchor} 检索结果` : `延伸阅读：${anchor}`,
        detail: index === 0 && query
          ? `${resultCount} 篇相关结果仍保留在当前检索路径中`
          : '继续围绕这个主题筛选、比对并沉淀阅读线索',
      }))
    : [{
        title: '独立阅读模式',
        detail: '当前页面未绑定检索路径，可从这篇论文开始建立新的研究方向',
      }]

  return {
    modeLabel: hasSearchContext ? '来自辅助检索工作区' : '独立阅读模式',
    description: hasSearchContext
      ? '保留你的检索词、筛选条件与主题标签，帮助你在阅读中持续保持路径感。'
      : '通过独立详情路由进入阅读画布，适合直接查阅、下载和做进一步研究。',
    query,
    activeFilters,
    activeTags,
    resultCount,
    anchors,
    nextSteps,
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
