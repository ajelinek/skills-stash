---
name: testing
description: >
  Use this skill when writing, reviewing, or organizing tests of any kind —
  unit tests, integration tests, or end-to-end (E2E) tests. Trigger on requests
  to write a test, add a spec file, set up test data, use Playwright, create
  page objects, configure a TestContext, implement a setUp function, or decide
  what kind of test to write for a given feature. Also trigger when fixing
  failing tests, improving test coverage, or refactoring test structure.
---

# Testing

Use this skill to write tests that prove real behavior, stay maintainable under
change, and run reliably without flakiness.

The core principle: test real things. Prefer tests that exercise actual code
paths over tests that verify mocks. Prefer tests that a user would recognize as
proving the feature works over tests that verify internal implementation details.

## Test Type Selection

Choose the right test type before writing anything:

**E2E tests (Playwright)** — use for critical user journeys, authentication and
authorization flows, and features spanning multiple layers of the stack. These
give the highest confidence that the system works end to end.

**Integration tests (Vitest)** — use for service layer interactions, database
operations, cross-component data flow, and API integrations where a full browser
isn't needed.

**Unit tests (Vitest)** — use for complex business logic, pure utility functions,
and edge cases that would be expensive to test via integration or E2E paths.

When in doubt: prefer E2E over integration, prefer integration over unit.
A test that exercises more of the real stack is more valuable than one that
exercises less.

Read `./references/philosophy.md` for detailed guidance on when each test type
is appropriate and how to think about test coverage decisions.

## Unit Tests

Unit tests do not need a database. Use factory functions and direct data
generators to build test inputs.

```typescript
async function setUp(overrides = {}) {
  const user = generateUser(overrides)
  const service = new UserValidator()
  return { user, service }
}

test('should reject user with missing email', async () => {
  const { user, service } = await setUp({ email: null })
  const result = service.validate(user)
  expect(result.isValid).toBe(false)
})
```

Read `./references/unit-testing.md` for factory function patterns, data
generation, and file organization rules.

See `./examples/unit-test.ts` for a complete copyable unit test file.

## Integration Tests

Integration tests use TestContext for all data that requires a database. The
`ctx.setupEnv()` call is the only way to seed initial data — never create data
outside of it for initial setup.

```typescript
const MODULE_BASE_DATA = {
  orgs: [{ _id: 'O1' }],
  users: [{ _id: 'U1', orgId: 'O1' }],
  userDetails: [{ _id: 'U1' }],
}

async function setUp(ctx: TestContext, testData: DataGenObject = {}) {
  const { selector } = await ctx.setupEnv(MODULE_BASE_DATA, testData)
  const service = new UserService(ctx.db)
  return { selector, service }
}
```

Read `./references/integration-testing.md` for service layer patterns, TestContext
usage rules, and data setup conventions.

Read `./references/test-context-system.md` for the full TestContext system
including shorthand IDs, the 8-module architecture, and the DB-agnostic adapter
pattern.

See `./examples/integration-test.ts` for a complete integration test file.

## E2E Tests (Playwright)

All E2E tests live in a `spec/` folder and end with `.spec.ts`. No locators in
test files — all page interactions go through page objects.

```typescript
// tests/spec/auth/login.spec.ts
import { test } from '@e2e/fixtures'
import { LoginPage } from '../../page-objects/LoginPage'

async function setUp(page: Page, ctx: TestContext) {
  const baseData = {
    orgs: [{ _id: 'O1' }],
    users: [{ _id: 'U1', orgId: 'O1' }],
    userDetails: [{ _id: 'U1' }],
  }
  const { selector, authUser } = await ctx.setupEnv(baseData, {}, page, 'U1', apiBasedLogin)
  return { loginPage: new LoginPage(page), authUser, selector }
}

test('should login and view dashboard @auth @happyPath @TS1', async ({ page, ctx }) => {
  const { loginPage, authUser } = await setUp(page, ctx)
  await loginPage.navigateTo()
  await expect(page.getByText(authUser.firstName)).toBeVisible()
})
```

Read `./references/e2e-playwright.md` for file structure rules, the tagging
system, TestContext fixture usage, and Playwright-specific conventions.

Read `./references/page-object-model.md` for the Page Object Pattern including
`@step` decorators, selector priority order, and structure rules.

See `./examples/e2e-test.spec.ts` for a complete spec file.
See `./examples/page-object.ts` for a complete page object class.

## TestContext System

**If the project does not already have a TestContext, stop and ask the user
before creating one.** The system requires significant upfront implementation
work. Use `./examples/test-context-implementation.md` as the build guide.

If a TestContext already exists, use it for all tests that need a database:

- Never call `TestContext.create()` directly in test files — always use the
  `ctx` fixture or a `setUp` helper
- Pass all initial data through `ctx.setupEnv()` in one atomic call
- Use shorthand IDs (`U1`, `O1`, `G1`) — the IdProvider resolves them to real
  database IDs
- Only specify IDs and relationships in test data; let generators handle names,
  emails, and other non-critical fields

Read `./references/test-context-system.md` for the complete system rules,
shorthand ID conventions, and the 8-module architecture.

## Test Structure Rules

These rules apply to all test types:

- **One behavior per test** — each test proves one thing
- **Given-When-Then structure** — setUp (Given), action (When), assertions (Then)
- **No `beforeEach` for data setup** — use `setUp()` functions called inside each test
- **No `describe` blocks** — keep test files flat; organize by feature into separate files
- **No conditional logic in tests** — be specific; test one concrete path
- **No hardcoded numeric IDs** — use shorthand IDs and let the system generate real ones
- **Flat, independent tests** — each test must be runnable in isolation

## Tagging (E2E Tests)

Every E2E test must include at least one feature tag and one test type tag at
the end of its description, plus a unique `@TS#` identifier:

```typescript
test('should create service and notify members @service-management @create @TS12')
test('should handle invalid credentials @auth @errorPath @TS13')
test('should display empty state when no results @dashboard @empty-state @TS14')
```

Read `./references/e2e-playwright.md` for the full tag catalog.

## Anti-Patterns

Read `./references/anti-patterns.md` for a consolidated list of forbidden
patterns across all test types. The most critical ones:

- No mocks for code you own — test real implementations
- No `beforeEach` for data setup or state
- No locators in test files — page objects only
- No `TestContext.create()` calls directly in tests
- No duplicate shorthand IDs between `baseData` and `testData`
- No hardcoded waits (`page.waitForTimeout()`)
- No commented-out tests — fix failing tests or delete them

## Quality Bar

Before committing tests:

- Each test proves one concrete behavior
- Tests run independently in any order
- No shared mutable state between tests
- TestContext shorthand IDs are unique within each `setupEnv()` call
- E2E tests have both a feature tag and a type tag with a `@TS#` number
- Page objects use `@step` on every action and assertion method
- No locators exist outside page object files
- All assertions are on real data, not mocked return values
