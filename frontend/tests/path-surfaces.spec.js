import { expect, test } from '@playwright/test'

function createVisualizationPayload(overrides = {}) {
  const defaultPayload = {
    code: 200,
    message: 'success',
    data: {
      stats: {
        readTime: '42.5h',
        readTimeChange: '18%',
        readCount: 128,
        readCountChange: '24',
        activeFields: 6,
        activeFieldsChange: 2,
        depth: 85.3,
        depthChange: '5.2',
      },
      field: {
        labels: ['深度学习', '强化学习', '图神经网络', '自然语言处理'],
        data: [35, 30, 20, 15],
      },
      knowledge: {
        learningPath: {
          topic: 'Actor-Critic Methods',
          estimatedHours: 28,
          coverage: 0.42,
          route: ['kw_ml', 'kw_rl', 'kw_ac', 'p_a3c', 'p_ppo'],
        },
        nodes: [
          { id: 'kw_ml', name: 'Machine Learning', type: 'keyword', mastery: 0.92, depth: 0, group: 'foundation' },
          { id: 'kw_rl', name: 'Reinforcement Learning', type: 'keyword', mastery: 0.65, depth: 1, group: 'intermediate' },
          { id: 'kw_ac', name: 'Actor-Critic', type: 'keyword', mastery: 0.4, depth: 2, group: 'target' },
          { id: 'p_a3c', name: 'Asynchronous Actor-Critic (A3C)', type: 'paper', mastery: 0.15, depth: 3, group: 'paper', year: 2016 },
          { id: 'p_ppo', name: 'Proximal Policy Optimization', type: 'paper', mastery: 0.05, depth: 3, group: 'paper', year: 2017 },
        ],
        edges: [
          { source: 'kw_ml', target: 'kw_rl', weight: 0.8 },
          { source: 'kw_rl', target: 'kw_ac', weight: 0.9 },
          { source: 'kw_ac', target: 'p_a3c', weight: 0.95 },
          { source: 'p_a3c', target: 'p_ppo', weight: 0.7 },
        ],
      },
    },
  }

  return {
    ...defaultPayload,
    ...overrides,
    data: {
      ...defaultPayload.data,
      ...(overrides.data || {}),
      stats: {
        ...defaultPayload.data.stats,
        ...(overrides.data?.stats || {}),
      },
      field: {
        ...defaultPayload.data.field,
        ...(overrides.data?.field || {}),
      },
      knowledge: {
        ...defaultPayload.data.knowledge,
        ...(overrides.data?.knowledge || {}),
        learningPath: {
          ...defaultPayload.data.knowledge.learningPath,
          ...(overrides.data?.knowledge?.learningPath || {}),
        },
        nodes: overrides.data?.knowledge?.nodes || defaultPayload.data.knowledge.nodes,
        edges: overrides.data?.knowledge?.edges || defaultPayload.data.knowledge.edges,
      },
    },
  }
}

function createProfilePayload(overrides = {}) {
  return {
    code: 200,
    message: 'success',
    data: {
      id: 7,
      username: 'Ada',
      avatar: '',
      email: 'ada@example.com',
      bio: '研究强化学习与智能体推理',
      researchInterests: '强化学习,图神经网络,智能体',
      ...overrides,
    },
  }
}

function createRecommendationsPayload(overrides = {}) {
  return {
    code: 200,
    message: 'success',
    data: {
      recommendations: [
        {
          paperId: 101,
          title: 'Entropy-Regularized Actor-Critic',
          authors: '["Ada Lovelace"]',
          venue: 'ICLR',
          year: 2024,
          abstrakt: 'Builds directly on actor-critic stability improvements.',
          reason: '与你当前的 Actor-Critic 学习路径强相关',
          keywords: '["Actor-Critic","Policy Optimization","Entropy"]',
        },
        {
          paperId: 102,
          title: 'Graph World Models for RL',
          authors: '["Grace Hopper"]',
          venue: 'NeurIPS',
          year: 2023,
          abstrakt: 'Connects graph representations with downstream RL planning.',
          reason: '匹配你的图谱探索与强化学习兴趣',
          keywords: '["Graph Neural Network","Reinforcement Learning"]',
        },
      ],
      ...(overrides.data || {}),
    },
  }
}

async function stubSharedApis(page, { visualization, profile, recommendations } = {}) {
  await page.addInitScript(() => {
    localStorage.setItem('token', 'path-token')
    localStorage.setItem('userInfo', JSON.stringify({
      id: 7,
      username: 'Ada',
      role: 'RESEARCHER',
      roleLabel: '研究者',
    }))
  })

  await page.route(/\/api\/visualization\/data$/, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(visualization || createVisualizationPayload()),
    })
  })

  await page.route(/\/api\/recommend(?:\?.*)?$/, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(recommendations || createRecommendationsPayload()),
    })
  })

  await page.route(/\/api\/user\/profile$/, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(profile || createProfilePayload()),
    })
  })
}

test('knowledge graph foregrounds the learning path with recommendation assets', async ({ page }) => {
  await stubSharedApis(page)

  await page.goto('/knowledge-graph')

  const rail = page.getByTestId('path-insight-rail')
  await expect(rail).toBeVisible()
  await expect(rail).toContainText('Actor-Critic Methods')
  await expect(rail).toContainText('Actor-Critic')
  await expect(rail).toContainText('Asynchronous Actor-Critic (A3C)')
  await expect(rail).toContainText('Entropy-Regularized Actor-Critic')
})

test('knowledge graph keeps the top controls compact on wide screens', async ({ page }) => {
  await page.setViewportSize({ width: 2000, height: 1200 })
  await stubSharedApis(page)

  await page.goto('/knowledge-graph')

  const mainSurface = page.locator('.viz-surface-layout__main')
  const timeFilter = page.locator('.time-filter')
  const firstStatCard = page.locator('.stats-row .stat-card').first()

  await expect(timeFilter).toBeVisible()
  await expect(firstStatCard).toBeVisible()

  const mainSurfaceBox = await mainSurface.boundingBox()
  const timeFilterBox = await timeFilter.boundingBox()
  const firstStatCardBox = await firstStatCard.boundingBox()

  expect(mainSurfaceBox).not.toBeNull()
  expect(timeFilterBox).not.toBeNull()
  expect(firstStatCardBox).not.toBeNull()
  expect(timeFilterBox.width).toBeLessThan(mainSurfaceBox.width * 0.6)
  expect(firstStatCardBox.width).toBeLessThan(280)
})

test('profile foregrounds research assets before legacy cards', async ({ page }) => {
  await stubSharedApis(page)

  await page.goto('/profile')

  const panel = page.getByTestId('research-assets-panel')
  await expect(panel).toBeVisible()
  await expect(panel).toContainText('Actor-Critic Methods')
  await expect(panel).toContainText('Entropy-Regularized Actor-Critic')
  await expect(panel).toContainText('Machine Learning')
  await expect(page.locator('.profile-grid > *').first()).toHaveAttribute('data-testid', 'research-assets-panel')
})
