import { test, expect } from '@playwright/test'

test('homepage recommendation read action records click and opens detail route', async ({ page }) => {
  let clickPayload = null

  await page.addInitScript(() => {
    localStorage.setItem('token', 'test-token')
    localStorage.setItem('userInfo', JSON.stringify({ id: 1, username: 'tester', role: 'USER' }))
  })

  await page.route(/\/api\/recommend(?:\?.*)?$/, async (route) => {
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
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        code: 200,
        message: 'success',
        data: {
          knowledge: {
            learningPath: {
              topic: 'Shared Recommendation Flow',
              estimatedHours: 12,
              coverage: 0.5,
              route: [],
            },
            nodes: [],
          },
        },
      }),
    })
  })

  await page.route(/\/api\/behavior\/click$/, async (route) => {
    clickPayload = route.request().postDataJSON()
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ code: 200, message: 'success', data: null }),
    })
  })

  await page.route('**/api/paper/1', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        code: 200,
        message: 'success',
        data: {
          id: 1,
          title: 'Shared Recommendation Flow Paper',
          authors: '["Tester"]',
          venue: 'NeurIPS',
          year: 2024,
          abstrakt: 'Shared detail route abstract',
          keywords: '["Recommendation"]',
        },
      }),
    })
  })

  await page.goto('/home')
  await expect(page.getByTestId('home-hub-hero')).toBeVisible()
  await expect(page.getByTestId('recommendation-stream')).toBeVisible()
  await expect(page.getByRole('heading', { name: '推荐流' })).toBeVisible()
  await expect(page.getByTestId('recommendation-stream').getByText('当前主线：Shared Recommendation Flow')).toBeVisible()
  await expect(page.getByText('Shared Recommendation Flow Paper')).toBeVisible()
  await expect(page.getByRole('button', { name: '下载 TXT' })).toHaveCount(0)

  await page.getByRole('button', { name: '阅读' }).click()

  await expect.poll(() => clickPayload).toEqual({ paperId: 1, source: 'recommend' })
  await expect(page).toHaveURL(/\/paper\/1$/)
  await expect(page.getByTestId('paper-reading-canvas')).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Shared Recommendation Flow Paper' })).toBeVisible()
})
