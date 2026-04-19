const { test, expect } = require('@playwright/test');

test('design pages load', async ({ page }) => {
  await page.goto('/design/index.html');
  await expect(page).toHaveTitle(/科研推荐系统/);
  await page.goto('/design/search.html');
  await expect(page).toHaveTitle(/智能搜索/);
});
