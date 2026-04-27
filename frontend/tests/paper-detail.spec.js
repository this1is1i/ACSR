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

test('restores visible search state after returning from paper detail', async ({ page }) => {
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
  await page.locator('.filter-select').nth(0).selectOption({ label: '近三年' });
  await page.locator('.filter-select').nth(1).selectOption({ label: '会议论文' });
  await page.locator('.filter-select').nth(2).selectOption({ label: '自然语言处理' });
  await page.locator('.filter-select').nth(3).selectOption({ label: '影响力' });
  await page.locator('.filter-tag').nth(1).click();
  await expect(page.locator('.filter-tag').nth(1)).toContainText('*神经网络');
  await page.getByRole('button', { name: '📖 查看详情' }).click();

  await expect(page).toHaveURL(/\/paper\/1$/);
  await expect(page.getByRole('heading', { name: 'Attention Is All You Need' })).toBeVisible();
  await expect(page.getByRole('button', { name: '下载 TXT' })).toBeVisible();

  await page.goBack();

  await expect(page).toHaveURL(/\/search$/);
  await expect(page.getByPlaceholder('输入关键词、论文标题、作者姓名或DOI...')).toHaveValue('Transformer');
  await expect(page.locator('.filter-select').nth(0)).toHaveValue('近三年');
  await expect(page.locator('.filter-select').nth(1)).toHaveValue('会议论文');
  await expect(page.locator('.filter-select').nth(2)).toHaveValue('自然语言处理');
  await expect(page.locator('.filter-select').nth(3)).toHaveValue('影响力');
  await expect(page.locator('.filter-tag').nth(1)).toContainText('*神经网络');
  await expect(page.getByText('Attention Is All You Need')).toBeVisible();
});

test('uses download filename from response headers', async ({ page }) => {
  await page.addInitScript(() => {
    window.__downloadRecords = [];
    const originalClick = HTMLAnchorElement.prototype.click;
    HTMLAnchorElement.prototype.click = function patchedClick() {
      window.__downloadRecords.push({ href: this.href, download: this.download });
    };
    window.__restoreAnchorClick = () => {
      HTMLAnchorElement.prototype.click = originalClick;
    };
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
          title: 'Attention/Is:All*You?Need',
          authors: '["Ashish Vaswani"]',
          venue: 'NeurIPS',
          year: 2017,
          abstrakt: 'Transformer paper abstract',
          keywords: '["Transformer","Attention"]',
        },
      }),
    });
  });

  await page.route('**/api/paper/1/download/txt', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'text/plain; charset=utf-8',
      headers: {
        'content-disposition': "attachment; filename*=UTF-8''paper-safe-title.txt",
      },
      body: 'demo content',
    });
  });

  await page.goto('/paper/1');
  await page.getByRole('button', { name: '下载 TXT' }).click();

  await expect.poll(async () => {
    return page.evaluate(() => window.__downloadRecords.length);
  }).toBe(1);

  await expect.poll(async () => {
    return page.evaluate(() => window.__downloadRecords[0]?.download ?? null);
  }).toBe('paper-safe-title.txt');
});
