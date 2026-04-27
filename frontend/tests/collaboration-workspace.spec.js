import { expect, test } from '@playwright/test'

async function seedSession(page) {
  await page.addInitScript(() => {
    localStorage.setItem('token', 'workspace-token')
    localStorage.setItem('userId', '7')
    localStorage.setItem('userInfo', JSON.stringify({
      id: 7,
      username: 'Ada',
      role: 'RESEARCHER',
      roleLabel: '研究者',
    }))
  })
}

async function stubCommunityWorkspace(page) {
  await page.route(/\/api\/community\/posts(?:\?.*)?$/, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        code: 200,
        message: 'success',
        data: [
          {
            id: 11,
            title: '组会：Actor-Critic 复现实验',
            content: '这周集中同步 PPO 与 Actor-Critic 的实验路径，顺便共享两篇入门论文。',
            replyCount: 3,
            likeCount: 8,
            createTime: '2026-04-26T10:30:00Z',
            statusName: 'APPROVED',
            statusLabel: '已发布',
            author: {
              username: 'Ada',
              roleLabel: '研究者',
            },
            paper: {
              title: 'Practical PPO for Collaborative Research',
              venue: 'NeurIPS',
              year: 2025,
              citationCount: 128,
            },
          },
          {
            id: 12,
            title: '论文精读协作',
            content: '想找同学一起拆解图神经网络与强化学习结合的阅读顺序。',
            replyCount: 1,
            likeCount: 4,
            createTime: '2026-04-25T08:15:00Z',
            statusName: 'APPROVED',
            statusLabel: '已发布',
            author: {
              username: 'Grace',
              roleLabel: '学生',
            },
            paper: null,
          },
        ],
      }),
    })
  })

  await page.route(/\/api\/community\/posts\/11\/comments$/, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        code: 200,
        message: 'success',
        data: [
          {
            id: 99,
            content: '我们先对照 PPO baseline 看看。',
            createTime: '2026-04-26T12:00:00Z',
            likeCount: 0,
            author: {
              username: 'Grace',
            },
            replies: [],
          },
        ],
      }),
    })
  })
}

async function stubMessagingWorkspace(page, sentMessages) {
  await page.route(/\/api\/message\/conversations$/, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        {
          contactId: 12,
          unreadCount: 2,
          lastMessage: '关于 Actor-Critic 路径我们同步一下',
          contact: {
            id: 12,
            nickname: 'Grace',
          },
        },
      ]),
    })
  })

  await page.route(/\/api\/message\/chat\/12$/, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        {
          id: 1,
          senderId: 12,
          receiverId: 7,
          content: '我们先看那篇 PPO 论文，再补 Actor-Critic 的实验路径。',
          createTime: '2026-04-26T10:00:00Z',
          isRead: false,
        },
        {
          id: 2,
          senderId: 7,
          receiverId: 12,
          content: '好的，我把协作路径整理成三步发你。',
          createTime: '2026-04-26T10:05:00Z',
          isRead: true,
        },
      ]),
    })
  })

  await page.route(/\/api\/message\/mark-read\/1$/, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ code: 200, message: 'success', data: true }),
    })
  })

  await page.route(/\/api\/message\/send(?:\?.*)?$/, async (route) => {
    const url = new URL(route.request().url())
    sentMessages.push({
      receiverId: url.searchParams.get('receiverId'),
      content: url.searchParams.get('content'),
    })

    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ code: 200, message: 'success', data: true }),
    })
  })
}

test('community reframes the feed as a collaboration workspace with a contextual discussion rail', async ({ page }) => {
  await seedSession(page)
  await stubCommunityWorkspace(page)

  await page.goto('/community')

  await expect(page.getByTestId('community-collaboration-workspace')).toBeVisible()
  await expect(page.getByTestId('discussion-context-rail')).toContainText('Practical PPO for Collaborative Research')
  await expect(page.getByTestId('discussion-context-rail')).toContainText('Actor-Critic')
  await expect(page.getByText('组会：Actor-Critic 复现实验')).toBeVisible()

  await page.getByRole('button', { name: '查看评论' }).first().click()

  await expect(page.getByText('我们先对照 PPO baseline 看看。')).toBeVisible()
})

test('messaging becomes a collaboration workspace without breaking the existing conversation flow', async ({ page }) => {
  const sentMessages = []

  await seedSession(page)
  await stubMessagingWorkspace(page, sentMessages)

  await page.goto('/messages')

  await expect(page.getByTestId('chat-collaboration-workspace')).toBeVisible()
  await expect(page.getByTestId('conversation-rail')).toContainText('Grace')
  await expect(page.getByTestId('conversation-item-12')).toBeVisible()

  await page.getByTestId('conversation-item-12').click()

  await expect(page.getByText('我们先看那篇 PPO 论文，再补 Actor-Critic 的实验路径。')).toBeVisible()
  await expect(page.getByTestId('conversation-rail')).toContainText('Actor-Critic')
  await expect(page.getByTestId('conversation-rail')).toContainText('PPO')

  await page.getByPlaceholder('输入消息，按 Enter 发送').fill('我刚把实验分工同步到协作路径里。')
  await page.getByRole('button', { name: '发送' }).click()

  await expect(page.locator('.bubble').filter({ hasText: '我刚把实验分工同步到协作路径里。' })).toBeVisible()
  await expect.poll(() => sentMessages).toEqual([
    {
      receiverId: '12',
      content: '我刚把实验分工同步到协作路径里。',
    },
  ])
})
