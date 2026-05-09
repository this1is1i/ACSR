const COMPLETED_THRESHOLD = 0.7

function asNumber(value, fallback = 0) {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : fallback
}

function getGroupLabel(group) {
  return {
    foundation: '基础能力',
    intermediate: '进阶主题',
    target: '目标专题',
    paper: '关键论文',
  }[group] || '学习节点'
}

function getStepStatus(mastery) {
  if (mastery >= COMPLETED_THRESHOLD) return 'mastered'
  if (mastery >= 0.35) return 'active'
  return 'up-next'
}

export function formatMastery(mastery) {
  return `${Math.round(asNumber(mastery) * 100)}%`
}

export function getPathStepMeta(step) {
  const fragments = [getGroupLabel(step.group)]

  if (step.type === 'paper' && step.year) {
    fragments.push(`${step.year}`)
  }

  fragments.push(`${formatMastery(step.mastery)} 掌握度`)
  return fragments.join(' · ')
}

export function buildLearningPathSummary(visualization = {}) {
  const knowledge = visualization?.knowledge || {}
  const learningPath = knowledge.learningPath || {}
  const nodes = Array.isArray(knowledge.pathNodes) ? knowledge.pathNodes
    : Array.isArray(knowledge.nodes) ? knowledge.nodes : []
  const route = Array.isArray(learningPath.route) ? learningPath.route : []
  const nodeMap = new Map(nodes.map((node) => [String(node.id), node]))

  const steps = route
    .map((id, index) => {
      const node = nodeMap.get(String(id))
      if (!node) return null

      const mastery = asNumber(node.mastery)
      return {
        ...node,
        mastery,
        index: index + 1,
        status: getStepStatus(mastery),
      }
    })
    .filter(Boolean)

  const coverage = asNumber(
    learningPath.coverage,
    steps.length ? steps.reduce((total, step) => total + step.mastery, 0) / steps.length : 0
  )
  const estimatedHours = asNumber(learningPath.estimatedHours)
  const completionPercent = Math.round(coverage * 100)
  const nextStep = steps.find((step) => step.mastery < COMPLETED_THRESHOLD) || null
  const isComplete = steps.length > 0 && nextStep === null
  const foundationSteps = steps.filter((step) => step.group === 'foundation')
  const resourcePapers = steps.filter((step) => step.type === 'paper')
  const focusAreas = steps
    .filter((step) => step.type !== 'paper' && step.group !== 'foundation')
    .slice(0, 3)

  return {
    topic: learningPath.topic || '个性化学习路径',
    headline: learningPath.topic
      ? `围绕 ${learningPath.topic} 组织你的下一轮研究推进`
      : '根据推荐结果继续推进你的研究主线',
    estimatedHours,
    estimatedHoursLabel: estimatedHours ? `${estimatedHours} 小时` : '待估算',
    coverage,
    completionPercent,
    isComplete,
    steps,
    nextStep,
    nextStepCaption: isComplete
      ? '当前路径已完成，可切换到新的研究主题继续推进。'
      : nextStep
        ? getPathStepMeta(nextStep)
        : '继续浏览论文以生成下一节点',
    masteredFoundations: foundationSteps.filter((step) => step.mastery >= COMPLETED_THRESHOLD).length,
    foundationCount: foundationSteps.length,
    resourcePapers,
    paperCount: resourcePapers.length,
    focusAreas,
  }
}
