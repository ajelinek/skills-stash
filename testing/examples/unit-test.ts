/**
 * Unit test example — UserValidator
 *
 * Shows the standard unit test pattern:
 * - setUp() function called inside each test (not in beforeEach)
 * - Factory functions for test data (no TestContext needed)
 * - One behavior per test
 * - Descriptive test names using should/when pattern
 *
 * Place this file at: src/validators/__tests__/UserValidator.test.ts
 */

import { describe, expect, test } from 'vitest'
import { generateUser } from '@data/generators'
import { UserValidator } from '../UserValidator'

// ── Setup ──────────────────────────────────────────────────────────────────

interface SetUpOptions {
  email?: string | null
  firstName?: string
  lastName?: string
  orgId?: string | null
}

async function setUp(overrides: SetUpOptions = {}) {
  const user = generateUser(overrides)
  const validator = new UserValidator()
  return { user, validator }
}

// ── Tests ──────────────────────────────────────────────────────────────────

test('should accept a valid user', async () => {
  const { user, validator } = await setUp()

  const result = validator.validate(user)

  expect(result.isValid).toBe(true)
  expect(result.errors).toHaveLength(0)
})

test('should reject user with missing email', async () => {
  const { user, validator } = await setUp({ email: null })

  const result = validator.validate(user)

  expect(result.isValid).toBe(false)
  expect(result.errors).toContain('email is required')
})

test('should reject user with missing firstName', async () => {
  const { user, validator } = await setUp({ firstName: '' })

  const result = validator.validate(user)

  expect(result.isValid).toBe(false)
  expect(result.errors).toContain('firstName is required')
})

test('should reject user not belonging to an org', async () => {
  const { user, validator } = await setUp({ orgId: null })

  const result = validator.validate(user)

  expect(result.isValid).toBe(false)
  expect(result.errors).toContain('orgId is required')
})

test('should reject user with malformed email', async () => {
  const { user, validator } = await setUp({ email: 'not-an-email' })

  const result = validator.validate(user)

  expect(result.isValid).toBe(false)
  expect(result.errors).toContain('email must be a valid email address')
})

test('should collect multiple errors when multiple fields are invalid', async () => {
  const { user, validator } = await setUp({ email: null, firstName: '' })

  const result = validator.validate(user)

  expect(result.isValid).toBe(false)
  expect(result.errors).toHaveLength(2)
})
