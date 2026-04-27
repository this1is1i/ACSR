import { expect, test } from '@playwright/test'

test('search workspace leads into a path-aware reading canvas', async ({ page }) => {
  await page.route('**/api/paper/search**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        code: 200,
        message: 'success',
        data: [
          {
            id: 1,
            title: 'Attention Is All You Need',
            authors: '["Ashish Vaswani","Noam Shazeer"]',
            venue: 'NeurIPS',
            year: 2017,
            abstrakt: 'Transformer paper abstract',
            keywords: '["Transformer","Attention","Sequence Modeling"]',
            citations: 51234,
            downloads: 2048,
          },
        ],
      }),
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
          title: 'Attention Is All You Need',
          authors: '["Ashish Vaswani","Noam Shazeer"]',
          venue: 'NeurIPS',
          year: 2017,
          abstrakt: 'Transformer paper abstract',
          keywords: '["Transformer","Attention","Sequence Modeling"]',
        },
      }),
    })
  })

  await page.goto('/search')
  await page.getByPlaceholder('输入关键词、论文标题、作者姓名或DOI...').fill('Transformer')
  await page.getByRole('button', { name: '智能搜索' }).click()

  await expect(page.getByTestId('search-filter-rail')).toBeVisible()
  await expect(page.getByTestId('search-result-card-1')).toBeVisible()

  await page.locator('.filter-select').nth(0).selectOption({ label: '近三年' })
  await page.locator('.filter-select').nth(1).selectOption({ label: '会议论文' })
  await page.locator('.filter-select').nth(2).selectOption({ label: '自然语言处理' })
  await page.locator('.filter-select').nth(3).selectOption({ label: '影响力' })
  await page.locator('.filter-tag').nth(1).click()

  await expect(page.getByTestId('search-result-card-1')).toContainText('研究路径')
  await expect(page.getByTestId('search-result-card-1')).toContainText('Transformer')

  await page.getByRole('button', { name: '📖 查看详情' }).click()

  await expect(page).toHaveURL(/\/paper\/1$/)
  await expect(page.getByTestId('paper-reading-canvas')).toBeVisible()
  await expect(page.getByTestId('paper-path-rail')).toContainText('Transformer')
  await expect(page.getByTestId('paper-path-rail')).toContainText('近三年')
  await expect(page.getByTestId('paper-path-rail')).toContainText('神经网络')
})
