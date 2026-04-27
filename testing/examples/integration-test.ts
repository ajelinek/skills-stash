/**
 * Integration test example — UserService
 *
 * Shows the standard integration test pattern:
 * - MODULE_BASE_DATA defined at module level
 * - setUp() accepts ctx and testData, calls ctx.setupEnv() once
 * - selector used to access seeded data by shorthand ID
 * - Tests receive ctx from the Vitest fixture
 *
 * Place this file at: src/services/__tests__/UserService.test.ts
 */

import { expect, test } from 'vitest'
import type { TestContext } from '@data/test-context'
import type { DataGenObject } from '@data/test-context/types'
import { UserService } from '../UserService'

// ── Base Data ──────────────────────────────────────────────────────────────
//
// Defines the minimum data every test in this module needs.
// Only IDs and relationships — generators handle everything else.

const MODULE_BASE_DATA = {
  orgs: [{ _id: 'O1' }],
  users: [{ _id: 'U1', orgId: 'O1' }],
  userDetails: [{ _id: 'U1' }],
}

// ── Setup ──────────────────────────────────────────────────────────────────

async function setUp(ctx: TestContext, testData: DataGenObject = {}) {
  const { selector, authUser } = await ctx.setupEnv(MODULE_BASE_DATA, testData)
  const service = new UserService(ctx.db)
  return { selector, authUser, service }
}

// ── Tests ──────────────────────────────────────────────────────────────────

test('should find user by id', async ({ ctx }) => {
  const { selector, service } = await setUp(ctx)

  const expectedUser = selector.getUser('U1')
  const result = await service.findById(expectedUser.id)

  expect(result).toBeDefined()
  expect(result?.id).toBe(expectedUser.id)
})

test('should return null for non-existent user', async ({ ctx }) => {
  const { service } = await setUp(ctx)

  const result = await service.findById('non-existent-id')

  expect(result).toBeNull()
})

test('should list users belonging to an org', async ({ ctx }) => {
  // Add a second user in a different org to verify filtering
  const { selector, service } = await setUp(ctx, {
    orgs: [{ _id: 'O2' }],
    users: [{ _id: 'U2', orgId: 'O2' }],
    userDetails: [{ _id: 'U2' }],
  })

  const org = selector.getOrg('O1')
  const result = await service.listByOrg(org.id)

  expect(result).toHaveLength(1)
  expect(result[0].id).toBe(selector.getUser('U1').id)
})

test('should update user firstName', async ({ ctx }) => {
  const { selector, service } = await setUp(ctx)

  const user = selector.getUser('U1')
  const updated = await service.update(user.id, { firstName: 'Updated' })

  expect(updated.firstName).toBe('Updated')
})

test('should list multiple users in the same org', async ({ ctx }) => {
  const { selector, service } = await setUp(ctx, {
    users: [{ _id: 'U2', orgId: 'O1' }],
    userDetails: [{ _id: 'U2' }],
  })

  const org = selector.getOrg('O1')
  const result = await service.listByOrg(org.id)

  // U1 from MODULE_BASE_DATA + U2 from testData = 2 users in O1
  expect(result).toHaveLength(2)
})
