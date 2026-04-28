/**
 * API E2E test example — User endpoint
 *
 * Shows the standard API E2E pattern:
 * - Runs in Vitest, not Playwright
 * - Uses TestContext for initial DB state
 * - Reads `apiBaseUrl` from Vitest `inject()`
 * - Calls the public API over HTTP with `fetch`
 * - Asserts consumer-visible behavior at the HTTP boundary
 *
 * Place this file at: tests/api/users.e2e.test.ts
 */

import { expect, inject, test } from 'vitest'
import type { TestContext } from '@data/test-context'
import type { DataGenObject } from '@data/test-context/types'

declare module 'vitest' {
  export interface ProvidedContext {
    apiBaseUrl: string
  }
}

const MODULE_BASE_DATA = {
  orgs: [{ _id: 'O1' }],
  users: [{ _id: 'U1', orgId: 'O1' }],
  userDetails: [{ _id: 'U1' }],
}

async function setUp(ctx: TestContext, testData: DataGenObject = {}) {
  const { selector } = await ctx.setupEnv({
    baseData: MODULE_BASE_DATA,
    testData,
  })

  return { selector, apiBaseUrl: inject('apiBaseUrl') }
}

test('should return user by id through the public API', async ({ ctx }) => {
  const { selector, apiBaseUrl } = await setUp(ctx)
  const user = selector.getUser('U1')

  const response = await fetch(`${apiBaseUrl}/api/users/${user._id}`)

  expect(response.status).toBe(200)

  const body = await response.json()
  expect(body).toMatchObject({
    id: user._id,
  })
})

test('should return 404 for missing user through the public API', async ({ ctx }) => {
  const { apiBaseUrl } = await setUp(ctx)

  const response = await fetch(`${apiBaseUrl}/api/users/non-existent-id`)

  expect(response.status).toBe(404)
})
