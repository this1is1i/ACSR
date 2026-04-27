import { test, expect } from '@playwright/test'

async function seedSession(page, userInfo) {
  await page.addInitScript(({ userInfo: seededUser }) => {
    window.localStorage.setItem('token', 'playwright-token')
    window.localStorage.setItem('userInfo', JSON.stringify(seededUser))
  }, { userInfo })
}

test('regular users get the shared shell foundations without management navigation', async ({ page }) => {
  await seedSession(page, {
    id: 7,
    username: 'researcher',
    role: 'RESEARCHER',
    roleLabel: '研究者',
  })

  await page.goto('/search')

  const designTokens = await page.evaluate(() => {
    const styles = window.getComputedStyle(document.documentElement)
    return {
      canvas: styles.getPropertyValue('--color-bg-canvas').trim(),
      sidebarWidth: styles.getPropertyValue('--shell-sidebar-width').trim(),
    }
  })

  expect(designTokens.canvas).not.toBe('')
  expect(designTokens.sidebarWidth).not.toBe('')
  await expect(page.getByText('探索', { exact: true })).toBeVisible()
  await expect(page.getByText('协作', { exact: true })).toBeVisible()
  await expect(page.getByText('管理', { exact: true })).toHaveCount(0)
})

test('admins can see the management navigation group in the shared shell', async ({ page }) => {
  await seedSession(page, {
    id: 1,
    username: 'admin',
    role: 'ADMIN',
    roleLabel: '管理员',
  })

  await page.goto('/search')

  await expect(page.getByText('管理', { exact: true })).toBeVisible()
  await expect(page.getByRole('link', { name: '管理员后台' })).toBeVisible()
})

test('shared shell tokens resolve from a single source of truth', async ({ page }) => {
  await seedSession(page, {
    id: 7,
    username: 'researcher',
    role: 'RESEARCHER',
    roleLabel: '研究者',
  })

  await page.goto('/search')

  const tokenSnapshot = await page.evaluate(() => {
    const styles = window.getComputedStyle(document.documentElement)
    return {
      primary: styles.getPropertyValue('--primary').trim(),
      accentPrimary: styles.getPropertyValue('--color-accent-primary').trim(),
      accent: styles.getPropertyValue('--accent').trim(),
      accentSecondary: styles.getPropertyValue('--color-accent-secondary').trim(),
    }
  })

  expect(tokenSnapshot.primary).toBe(tokenSnapshot.accentPrimary)
  expect(tokenSnapshot.accent).toBe(tokenSnapshot.accentSecondary)
})

test('mobile shell keeps the page content below the sidebar', async ({ page }) => {
  await page.setViewportSize({ width: 900, height: 1200 })
  await seedSession(page, {
    id: 7,
    username: 'researcher',
    role: 'RESEARCHER',
    roleLabel: '研究者',
  })

  await page.goto('/search')

  const sidebarBox = await page.locator('.sidebar').boundingBox()
  const mainBox = await page.locator('.search-root > main.main-content').boundingBox()

  expect(sidebarBox).not.toBeNull()
  expect(mainBox).not.toBeNull()
  expect(sidebarBox.x).toBeGreaterThanOrEqual(0)
  expect(mainBox.y).toBeGreaterThanOrEqual(sidebarBox.y + sidebarBox.height - 1)
})

test('theme toggle keeps the html dark class in sync with the selected theme', async ({ page }) => {
  await seedSession(page, {
    id: 1,
    username: 'admin',
    role: 'ADMIN',
    roleLabel: '管理员',
  })

  await page.goto('/admin')
  await page.getByRole('button', { name: '切换浅色' }).click()

  const themeState = await page.evaluate(() => ({
    theme: document.documentElement.getAttribute('data-theme'),
    isDark: document.documentElement.classList.contains('dark'),
  }))

  expect(themeState.theme).toBe('light')
  expect(themeState.isDark).toBe(false)
})

test('legacy workspace surfaces still receive the shared border token', async ({ page }) => {
  await seedSession(page, {
    id: 7,
    username: 'researcher',
    role: 'RESEARCHER',
    roleLabel: '研究者',
  })

  await page.goto('/search')
  await page.locator('.search-container').waitFor()

  const borderState = await page.evaluate(() => {
    const rootStyles = window.getComputedStyle(document.documentElement)
    const container = document.querySelector('.search-container')
    const containerStyles = window.getComputedStyle(container)
    return {
      borderToken: rootStyles.getPropertyValue('--border').trim(),
      borderWidth: containerStyles.borderTopWidth,
      borderStyle: containerStyles.borderTopStyle,
    }
  })

  expect(borderState.borderToken).not.toBe('')
  expect(borderState.borderWidth).toBe('1px')
  expect(borderState.borderStyle).toBe('solid')
})

test('light theme keeps the shared sidebar surface readable for dark text', async ({ page }) => {
  await seedSession(page, {
    id: 1,
    username: 'admin',
    role: 'ADMIN',
    roleLabel: '管理员',
  })

  await page.goto('/admin')
  await page.getByRole('button', { name: '切换浅色' }).click()

  const sidebarSurface = await page.evaluate(() => {
    const color = window.getComputedStyle(document.querySelector('.sidebar')).backgroundColor
    const [red, green, blue] = color.match(/\d+/g).slice(0, 3).map(Number)
    return {
      color,
      averageChannel: (red + green + blue) / 3,
    }
  })

  expect(sidebarSurface.averageChannel).toBeGreaterThan(180)
})
