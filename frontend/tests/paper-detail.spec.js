import { test, expect } from '@playwright/test'

test('navigates from search results to standalone paper detail page', async ({ page }) => {
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
            authors: ['Ashish Vaswani'],
            venue: 'NeurIPS',
            year: 2017,
            abstract: 'Transformer paper abstract',
            tags: ['NLP'],
          },
        ],
      }),
    });
  });

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
          authors: ['Ashish Vaswani'],
          venue: 'NeurIPS',
          year: 2017,
          abstract: 'Transformer paper abstract',
          doi: '10.5555/attention',
          keywords: ['Transformer', 'Attention'],
        },
      }),
    });
  });

  await page.goto('/search');
  await page.getByPlaceholder('输入关键词、论文标题、作者姓名或DOI...').fill('Transformer');
  await page.getByRole('button', { name: '智能搜索' }).click();
  await page.getByRole('button', { name: '📖 查看详情' }).click();

  await expect(page).toHaveURL(/\/paper\/1$/);
  await expect(page.getByRole('heading', { name: 'Attention Is All You Need' })).toBeVisible();
  await expect(page.getByRole('button', { name: '下载 TXT' })).toBeVisible();
})
