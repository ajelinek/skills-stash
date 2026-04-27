/**
 * Page Object example — DashboardPage
 *
 * Shows the complete page object pattern:
 * - Selectors at the top as private arrow function properties
 * - Selector priority order: role > label > text > placeholder > alt > title > testId
 * - Actions decorated with @step
 * - Multi-step assertion methods decorated with @step
 * - No conditional logic anywhere
 * - No explicit waits
 * - No locators returned from methods
 *
 * Place this file at: tests/page-objects/DashboardPage.ts
 */

import { type Page, expect } from '@playwright/test'
import { step } from '../utils/step'

export class DashboardPage {
  constructor(private page: Page) {}

  // ── Selectors ─────────────────────────────────────────────────────────────
  //
  // Ordered: role → label → text → placeholder → alt → title → testId
  // Grouped by category. All private.

  // Navigation
  private userMenuButton = () =>
    this.page.getByRole('button', { name: 'User menu' })
  private settingsLink = () =>
    this.page.getByRole('link', { name: 'Settings' })
  private signOutLink = () =>
    this.page.getByRole('link', { name: 'Sign out' })

  // Page content
  private pageHeading = () =>
    this.page.getByRole('heading', { name: 'Dashboard' })
  private createServiceButton = () =>
    this.page.getByRole('button', { name: 'Create service' })
  private serviceRow = (serviceName: string) =>
    this.page.getByRole('row', { name: serviceName })

  // Empty state
  private emptyStateMessage = () =>
    this.page.getByText('No services yet')

  // ── Actions ───────────────────────────────────────────────────────────────

  @step('Navigate to dashboard')
  async navigateTo() {
    await this.page.goto('/dashboard')
  }

  @step('Open user menu')
  async openUserMenu() {
    await this.userMenuButton().click()
  }

  @step('Click settings')
  async clickSettings() {
    await this.openUserMenu()
    await this.settingsLink().click()
  }

  @step('Sign out')
  async signOut() {
    await this.openUserMenu()
    await this.signOutLink().click()
  }

  @step('Click create service')
  async clickCreateService() {
    await this.createServiceButton().click()
  }

  // ── Assertions ────────────────────────────────────────────────────────────
  //
  // Only multi-step assertions reused across multiple tests belong here.
  // Single-line assertions go directly in spec files.

  @step('Verify dashboard is loaded')
  async verifyLoaded() {
    await expect(this.pageHeading()).toBeVisible()
    await expect(this.createServiceButton()).toBeVisible()
  }

  @step('Verify service row is visible for {serviceName}')
  async verifyServiceRow(serviceName: string) {
    await expect(this.serviceRow(serviceName)).toBeVisible()
  }

  @step('Verify empty state is displayed')
  async verifyEmptyState() {
    await expect(this.emptyStateMessage()).toBeVisible()
    await expect(this.createServiceButton()).toBeVisible()
  }
}


// ── Usage in a spec file ───────────────────────────────────────────────────
//
// import { DashboardPage } from '../../page-objects/DashboardPage'
//
// test('should display dashboard @dashboard @happyPath @TS100', async ({ page, ctx }) => {
//   const { dashboardPage, authUser } = await setUp(page, ctx)
//   await dashboardPage.navigateTo()
//   await dashboardPage.verifyLoaded()
//   await expect(page.getByText(authUser.firstName)).toBeVisible()  // single-line → in spec
// })
