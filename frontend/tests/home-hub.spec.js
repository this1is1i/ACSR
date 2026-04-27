import { expect, test } from '@playwright/test'

function createVisualizationPayload(overrides = {}) {
  const defaultPayload = {
    code: 200,
    message: 'success',
    data: {
      stats: {
        readTime: '42.5h',
        readCount: 128,
        activeFields: 6,
      },
      knowledge: {
        learningPath: {
          topic: 'Actor-Critic Methods',
          estimatedHours: 28,
          coverage: 0.42,
          route: ['kw_ml', 'kw_rl', 'kw_ac', 'p_a3c'],
        },
        nodes: [
          { id: 'kw_ml', name: 'Machine Learning', type: 'keyword', mastery: 0.92, depth: 0, group: 'foundation' },
          { id: 'kw_rl', name: 'Reinforcement Learning', type: 'keyword', mastery: 0.65, depth: 1, group: 'intermediate' },
          { id: 'kw_ac', name: 'Actor-Critic', type: 'keyword', mastery: 0.4, depth: 2, group: 'target' },
          { id: 'p_a3c', name: 'Asynchronous Actor-Critic (A3C)', type: 'paper', mastery: 0.1, depth: 3, group: 'paper', year: 2016 },
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
      knowledge: {
        ...defaultPayload.data.knowledge,
        ...(overrides.data?.knowledge || {}),
        learningPath: {
          ...defaultPayload.data.knowledge.learningPath,
          ...(overrides.data?.knowledge?.learningPath || {}),
        },
        nodes: overrides.data?.knowledge?.nodes || defaultPayload.data.knowledge.nodes,
      },
    },
  }
}

test('homepage hub loads recommendations with learning path data and highlights the derived path summary', async ({ page }) => {
  let recommendRequested = false
  let visualizationRequested = false
  let releaseRecommendations

  const recommendationGate = new Promise((resolve) => {
    releaseRecommendations = resolve
  })

  await page.addInitScript(() => {
    localStorage.setItem('token', 'hub-token')
    localStorage.setItem('userInfo', JSON.stringify({
      id: 7,
      username: 'researcher',
      role: 'RESEARCHER',
      roleLabel: '研究者',
    }))
  })

  await page.route(/\/api\/recommend(?:\?.*)?$/, async (route) => {
    recommendRequested = true
    await recommendationGate
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        code: 200,
        message: 'success',
        data: {
          recommendations: [
            {
              paperId: 1,
              title: 'Shared Recommendation Flow Paper',
              authors: '["Tester"]',
              venue: 'NeurIPS',
              year: 2024,
              abstrakt: 'Shared detail route abstract',
              reason: 'Because it matches your interests',
            },
          ],
        },
      }),
    })
  })

  await page.route(/\/api\/visualization\/data$/, async (route) => {
    visualizationRequested = true
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(createVisualizationPayload()),
    })
  })

  const navigation = page.goto('/home')

  await expect.poll(() => ({ recommendRequested, visualizationRequested }), {
    timeout: 3000,
  }).toEqual({ recommendRequested: true, visualizationRequested: true })

  releaseRecommendations()
  await navigation

  await expect(page.locator('[data-testid="home-hub-hero"]')).toBeVisible()
  await expect(page.locator('[data-testid="recommendation-stream"]')).toContainText('Shared Recommendation Flow Paper')
  await expect(page.locator('[data-testid="learning-path-panel"]')).toContainText('Actor-Critic Methods')
  await expect(page.locator('[data-testid="learning-path-panel"]')).toContainText('Reinforcement Learning')
})

test('homepage hub shows a completion state instead of reusing the final node as the next step', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('token', 'hub-token')
    localStorage.setItem('userInfo', JSON.stringify({
      id: 7,
      username: 'researcher',
      role: 'RESEARCHER',
      roleLabel: '研究者',
    }))
  })

  await page.route(/\/api\/recommend(?:\?.*)?$/, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        code: 200,
        message: 'success',
        data: { recommendations: [] },
      }),
    })
  })

  await page.route(/\/api\/visualization\/data$/, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(createVisualizationPayload({
        data: {
          knowledge: {
            learningPath: {
              coverage: 1,
            },
            nodes: [
              { id: 'kw_ml', name: 'Machine Learning', type: 'keyword', mastery: 0.92, depth: 0, group: 'foundation' },
              { id: 'kw_rl', name: 'Reinforcement Learning', type: 'keyword', mastery: 0.88, depth: 1, group: 'intermediate' },
              { id: 'kw_ac', name: 'Actor-Critic', type: 'keyword', mastery: 0.85, depth: 2, group: 'target' },
              { id: 'p_a3c', name: 'Asynchronous Actor-Critic (A3C)', type: 'paper', mastery: 0.9, depth: 3, group: 'paper', year: 2016 },
            ],
          },
        },
      })),
    })
  })

  await page.goto('/home')

  await expect(page.locator('[data-testid="learning-path-panel"]')).toContainText('当前路径已完成')
  await expect(page.locator('[data-testid="learning-path-panel"]')).not.toContainText('下一节点：Asynchronous Actor-Critic (A3C)')
})
