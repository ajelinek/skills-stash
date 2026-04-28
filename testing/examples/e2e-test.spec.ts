/**
 * UI E2E test example — Dashboard navigation
 *
 * Shows the standard UI E2E spec file pattern:
 * - Import from @e2e/fixtures (never from @playwright/test directly)
 * - setUp() function called inside each test (not beforeEach)
 * - testData can override MODULE_BASE_DATA by reusing the same shorthand key
 * - All page interactions via page objects only
 * - Single-line assertions in the test using page.getBy*() or expect()
 * - Tags at the end of test description: feature + type + @TS#
 * - No describe blocks
 *
 * Place this file at: tests/spec/dashboard/navigation.spec.ts
 */

import { expect } from '@playwright/test'
import { test } from '@e2e/fixtures'
import { apiBasedLogin } from '@e2e/utils/authentication'
import { DashboardPage } from '../../page-objects/DashboardPage'
import type { Page } from '@playwright/test'
import type { TestContext } from '@data/test-context'
import type { DataGenObject } from '@data/test-context/types'

// ── Setup ──────────────────────────────────────────────────────────────────

async function setUp(page: Page, ctx: TestContext, testData: DataGenObject = {}) {
  const baseData = {
    orgs: [{ _id: 'O1' }],
    users: [{ _id: 'U1', orgId: 'O1' }],
    userDetails: [{ _id: 'U1' }],
  }

  const { selector } = await ctx.setupEnv({
    baseData,
    testData,
    page,
    authShortId: 'U1',
    loginFn: apiBasedLogin,
  })

  const dashboardPage = new DashboardPage(page)

  return { dashboardPage, selector }
}

// ── Tests ──────────────────────────────────────────────────────────────────

test(
  'should display dashboard after login @dashboard @happyPath @TS100',
  async ({ page, ctx }) => {
    const { dashboardPage } = await setUp(page, ctx)

    await dashboardPage.navigateTo()

    await dashboardPage.verifyLoaded()
    await expect(page).toHaveURL(/\/dashboard/)
  }
)

test(
  'should navigate to user settings from dashboard @dashboard @navigation @TS101',
  async ({ page, ctx }) => {
    const { dashboardPage } = await setUp(page, ctx)

    await dashboardPage.navigateTo()
    await dashboardPage.openUserMenu()
    await dashboardPage.clickSettings()

    await expect(page).toHaveURL(/\/settings/)
  }
)

test(
  'should show empty state when no services exist @dashboard @empty-state @TS102',
  async ({ page, ctx }) => {
    // U1 has no services — base data is sufficient
    const { dashboardPage } = await setUp(page, ctx)

    await dashboardPage.navigateTo()

    await expect(page.getByText('No services yet')).toBeVisible()
  }
)

test(
  'should display service in list after creation @dashboard @create @TS103',
  async ({ page, ctx }) => {
    const { dashboardPage, selector } = await setUp(page, ctx, {
      userGroups: [{ _id: 'G1', orgId: 'O1' }],
      activities: [{ _id: 'A1', orgId: 'O1' }],
      services: [{ _id: 'S1', userGroupId: 'G1', activityId: 'A1', performedByUserId: 'U1' }],
    })

    const service = selector.getService('S1')

    await dashboardPage.navigateTo()

    await dashboardPage.verifyServiceRow(service.name)
  }
)
