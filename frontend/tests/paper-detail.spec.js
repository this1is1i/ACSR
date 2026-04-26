import { test, expect } from '@playwright/test'

test('renders backend-shaped paper detail payload safely', async ({ page }) => {
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
          keywords: '["Transformer","Attention"]',
        },
      }),
    });
  });

  await page.goto('/paper/1');

  await expect(page.getByRole('heading', { name: 'Attention Is All You Need' })).toBeVisible();
  await expect(page.getByText('Ashish Vaswani, Noam Shazeer · NeurIPS · 2017')).toBeVisible();
  await expect(page.getByText('Transformer paper abstract')).toBeVisible();
  await expect(page.locator('.tag')).toHaveText(['Transformer', 'Attention']);
  await expect(page.getByRole('heading', { name: 'DOI' })).toHaveCount(0);
});

test('restores search keyword and result after returning from paper detail', async ({ page }) => {
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
            authors: '["Ashish Vaswani"]',
            venue: 'NeurIPS',
            year: 2017,
            abstrakt: 'Transformer paper abstract',
            keywords: '["NLP"]',
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
          authors: '["Ashish Vaswani"]',
          venue: 'NeurIPS',
          year: 2017,
          abstrakt: 'Transformer paper abstract',
          keywords: '["Transformer","Attention"]',
        },
      }),
    });
  });

  await page.goto('/search');
  await page.getByPlaceholder('输入关键词、论文标题、作者姓名或DOI...').fill('Transformer');
  await page.getByRole('button', { name: '智能搜索' }).click();
  await expect(page.getByText('Attention Is All You Need')).toBeVisible();
  await page.getByRole('button', { name: '📖 查看详情' }).click();

  await expect(page).toHaveURL(/\/paper\/1$/);
  await expect(page.getByRole('heading', { name: 'Attention Is All You Need' })).toBeVisible();
  await expect(page.getByRole('button', { name: '下载 TXT' })).toBeVisible();

  await page.getByRole('button', { name: '← 返回搜索' }).click();

  await expect(page).toHaveURL(/\/search/);
  await expect(page.getByPlaceholder('输入关键词、论文标题、作者姓名或DOI...')).toHaveValue('Transformer');
  await expect(page.getByText('Attention Is All You Need')).toBeVisible();
});
