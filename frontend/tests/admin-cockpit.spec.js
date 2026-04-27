import { expect, test } from '@playwright/test'

async function seedAdminSession(page) {
  await page.addInitScript(() => {
    window.localStorage.setItem('token', 'admin-cockpit-token')
    window.localStorage.setItem('userInfo', JSON.stringify({
      id: 1,
      username: 'admin',
      role: 'ADMIN',
      roleLabel: '管理员',
    }))
  })
}

async function stubAdminApis(page, options = {}) {
  const allPosts = [
    {
      id: 101,
      title: '待审核的图谱帖子',
      status: 'PENDING',
      statusLabel: '待审核',
      reviewComment: '',
      author: { username: 'Ada' },
    },
    {
      id: 102,
      title: '已发布的推荐帖子',
      status: 'APPROVED',
      statusLabel: '已发布',
      reviewComment: '内容完整',
      author: { username: 'Grace' },
    },
    {
      id: 103,
      title: '需要驳回的论文导入帖',
      status: 'REJECTED',
      statusLabel: '已驳回',
      reviewComment: '缺少来源',
      author: { username: 'Linus' },
    },
  ]

  let unfilteredRequestCount = 0

  await page.route(/\/api\/admin\/posts(?:\?.*)?$/, async (route) => {
    const requestUrl = new URL(route.request().url())
    const status = requestUrl.searchParams.get('status')

    if (!status) {
      unfilteredRequestCount += 1
      if (options.failOverviewAfterInitialLoad && unfilteredRequestCount > 1) {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ code: 500, message: 'overview failed', data: null }),
        })
        return
      }
    }

    const data = status ? allPosts.filter((post) => post.status === status) : allPosts

    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        code: 200,
        message: 'success',
        data,
      }),
    })
  })

  await page.route(/\/api\/admin\/posts\/\d+\/status$/, async (route) => {
    const requestUrl = new URL(route.request().url())
    const postId = Number(requestUrl.pathname.match(/\/api\/admin\/posts\/(\d+)\/status$/)?.[1])
    const payload = route.request().postDataJSON()
    const target = allPosts.find((post) => post.id === postId)

    if (target) {
      target.status = payload.status
      target.statusLabel = payload.status === 'APPROVED' ? '已发布' : '已驳回'
      target.reviewComment = payload.reviewComment || ''
    }

    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ code: 200, message: 'success', data: true }),
    })
  })

  await page.route(/\/api\/admin\/users$/, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        code: 200,
        message: 'success',
        data: [
          {
            id: 1,
            username: 'admin',
            email: 'admin@example.com',
            role: 'ADMIN',
            roleLabel: '管理员',
            researchInterests: '治理,平台运营',
          },
          {
            id: 2,
            username: 'ada',
            email: 'ada@example.com',
            role: 'RESEARCHER',
            roleLabel: '研究者',
            researchInterests: '强化学习',
          },
          {
            id: 3,
            username: 'student01',
            email: 'student01@example.com',
            role: 'STUDENT',
            roleLabel: '学生',
            researchInterests: '图神经网络',
          },
        ],
      }),
    })
  })
}

test('admin console lands on a cockpit summary before the existing operational tabs', async ({ page }) => {
  await seedAdminSession(page)
  await stubAdminApis(page)

  await page.goto('/admin')

  const hero = page.getByTestId('admin-cockpit-hero')
  const kpiGrid = page.getByTestId('admin-kpi-grid')
  const operations = page.getByTestId('admin-operations')

  await expect(hero).toBeVisible()
  await expect(hero).toContainText('控制台总览')
  await expect(kpiGrid).toContainText('待审核帖子')
  await expect(kpiGrid).toContainText('在管账号')
  await expect(page.getByText('高优先级动作')).toHaveCount(0)
  await expect(operations).toBeVisible()
  await expect(page.getByText('待审核的图谱帖子')).toBeVisible()

  const heroBox = await hero.boundingBox()
  const operationsBox = await operations.boundingBox()
  expect(heroBox).not.toBeNull()
  expect(operationsBox).not.toBeNull()
  expect(heroBox.y).toBeLessThan(operationsBox.y)
})

test('admin cockpit quick actions switch into the preserved operational workflows', async ({ page }) => {
  await seedAdminSession(page)
  await stubAdminApis(page)

  await page.goto('/admin')

  await page.getByRole('button', { name: '进入论文导入' }).click()
  await expect(page.getByRole('tab', { name: '论文导入', exact: true })).toHaveAttribute('aria-selected', 'true')
  await expect(page.locator('.json-editor')).toBeVisible()

  await page.getByRole('button', { name: '进入账号权限' }).click()
  await expect(page.getByRole('tab', { name: '账号权限', exact: true })).toHaveAttribute('aria-selected', 'true')
  await expect(page.getByText('admin@example.com')).toBeVisible()
})

test('cockpit summary remains global when the operations table is filtered', async ({ page }) => {
  await seedAdminSession(page)
  await stubAdminApis(page)

  await page.goto('/admin')

  const kpiGrid = page.getByTestId('admin-kpi-grid')
  const pendingKpi = kpiGrid.locator('.admin-kpi-grid__card').filter({ hasText: '待审核帖子' })
  await expect(pendingKpi).toContainText('1 条')

  const statusFilter = page.getByRole('combobox').first()
  await statusFilter.scrollIntoViewIfNeeded()
  await statusFilter.focus()
  await page.keyboard.press('Enter')
  await page.keyboard.press('ArrowDown')
  await page.keyboard.press('ArrowDown')
  await page.keyboard.press('Enter')

  await expect(page.getByText('已发布的推荐帖子')).toBeVisible()
  await expect(page.getByText('待审核的图谱帖子')).toHaveCount(0)
  await expect(pendingKpi).toContainText('1 条')
})

test('filtered post workflow still updates even if cockpit overview refresh fails', async ({ page }) => {
  await seedAdminSession(page)
  await stubAdminApis(page, { failOverviewAfterInitialLoad: true })

  await page.goto('/admin')

  const statusFilter = page.getByRole('combobox').first()
  await statusFilter.scrollIntoViewIfNeeded()
  await statusFilter.focus()
  await page.keyboard.press('Enter')
  await page.keyboard.press('ArrowDown')
  await page.keyboard.press('ArrowDown')
  await page.keyboard.press('Enter')

  await expect(page.getByText('已发布的推荐帖子')).toBeVisible()
  await expect(page.getByText('待审核的图谱帖子')).toHaveCount(0)
})

test('successful moderation keeps the table updated and shows an accurate overview-sync warning', async ({ page }) => {
  await seedAdminSession(page)
  await stubAdminApis(page, { failOverviewAfterInitialLoad: true })

  await page.goto('/admin')

  const statusFilter = page.getByRole('combobox').first()
  await statusFilter.scrollIntoViewIfNeeded()
  await statusFilter.focus()
  await page.keyboard.press('Enter')
  await page.keyboard.press('ArrowDown')
  await page.keyboard.press('Enter')

  await expect(page.getByText('待审核的图谱帖子')).toBeVisible()

  await page.locator('tr', { hasText: '待审核的图谱帖子' }).getByRole('button', { name: '通过' }).evaluate((element) => {
    element.click()
  })
  await page.getByRole('button', { name: '确认' }).click()

  await expect(page.getByText('待审核的图谱帖子')).toHaveCount(0)
  await expect(page.getByText('帖子状态已更新，总览同步稍后重试')).toBeVisible()
  await expect(page.locator('.el-message--error')).toHaveCount(0)
})

test('admin console removes unfinished draft rail cards and keeps tables inside the operations panel', async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 960 })
  await seedAdminSession(page)
  await stubAdminApis(page)

  await page.goto('/admin')

  const operations = page.getByTestId('admin-operations')
  await expect(operations).toBeVisible()
  await expect(page.getByText('高优先级动作')).toHaveCount(0)
  await expect(page.getByText('接口约束')).toHaveCount(0)

  const operationsOverflows = await operations.evaluate((element) => element.scrollWidth > element.clientWidth)
  expect(operationsOverflows).toBe(false)
})
