---
name: testing
description: >
  Use this skill when writing, reviewing, or organizing tests of any kind —
  unit tests, integration tests, API end-to-end tests, or UI end-to-end (E2E)
  tests. Trigger on requests to write a test, add a spec file, set up test
  data, use Playwright for browser E2E, write API E2E tests in Vitest, create
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

**UI E2E tests (Playwright)** — use for critical browser user journeys,
authentication and authorization flows through the UI, and features where the
browser experience itself is part of the behavior.

**API E2E tests (Vitest)** — use when there is no browser in scope but you still
need end-to-end confidence at the public HTTP boundary. These tests call a
running local API the way a real consumer would.

**Integration tests (Vitest)** — use for service layer interactions, database
operations, cross-component data flow, and in-process API coverage. If the test
bypasses the real HTTP boundary by importing handlers or app internals directly,
it is usually integration, not E2E.

**Unit tests (Vitest)** — use for complex business logic, pure utility functions,
and edge cases that would be expensive to test via integration or E2E paths.

When in doubt: choose the highest real boundary that proves the behavior without
building more harness than the scenario needs.

- Browser journey: UI E2E
- Public API contract: API E2E
- Service or module collaboration: integration
- Isolated logic: unit

If the repository already groups unit and integration tests under one Vitest
project, that is fine operationally. Keep the test intent explicit in naming,
helpers, and file organization. API E2E tests should usually live in a separate
Vitest project or config because they need a running server, longer setup, and
different lifecycle rules.

Read `./references/philosophy.md` for detailed guidance on when each test type
is appropriate and how to think about test coverage decisions.

## Unit Tests

Unit tests do not need a database. Use factory functions and direct data
generators to build test inputs.

```typescript
async function setUp(overrides = {}) {
  const user = generateUser(overrides);
  const service = new UserValidator();
  return { user, service };
}

test("should reject user with missing email", async () => {
  const { user, service } = await setUp({ email: null });
  const result = service.validate(user);
  expect(result.isValid).toBe(false);
});
```

Read `./references/unit-testing.md` for factory function patterns, data
generation, and file organization rules.

See `./examples/unit-test.ts` for a complete copyable unit test file.

## Integration Tests

Integration tests use TestContext for all data that requires a database. Keep
initial data setup in one `ctx.setupEnv()` call so shorthand IDs, merge
behavior, and selectors stay consistent.

```typescript
const MODULE_BASE_DATA = {
  orgs: [{ _id: "O1" }],
  users: [{ _id: "U1", orgId: "O1" }],
  userDetails: [{ _id: "U1" }],
};

async function setUp(ctx: TestContext, testData: DataGenObject = {}) {
  const { selector } = await ctx.setupEnv({
    baseData: MODULE_BASE_DATA,
    testData,
  });
  const service = createServiceUnderTest();
  return { selector, service };
}
```

Read `./references/integration-testing.md` for service layer patterns, TestContext
usage rules, key-based merge overrides, and data setup conventions.

Read `./references/test-context-system.md` for the full TestContext system
including shorthand IDs, the 8-module architecture, and the DB-agnostic adapter
pattern.

See `./examples/integration-test.ts` for a complete integration test file.

## API E2E Tests (Vitest)

API E2E tests call the API over HTTP as a real client would. No browser, no
page objects, and no direct handler imports.

```typescript
import { expect, inject, test } from 'vitest'

async function setUp(ctx: TestContext, testData: DataGenObject = {}) {
  const { selector } = await ctx.setupEnv({
    baseData: MODULE_BASE_DATA,
    testData,
  })

  return { selector, apiBaseUrl: inject('apiBaseUrl') }
}

test('should return user through the public API', async ({ ctx }) => {
  const { selector, apiBaseUrl } = await setUp(ctx)
  const user = selector.getUser('U1')

  const response = await fetch(`${apiBaseUrl}/api/users/${user._id}`)

  expect(response.status).toBe(200)
  await expect(response.json()).resolves.toMatchObject({ id: user._id })
})
```

Prefer Node's built-in `fetch`.
Playwright can also call APIs, but default API-only E2E coverage to Vitest.
If the repository already starts the API outside the test process, target that
running local endpoint instead of inventing a new boot path.

Read `./references/e2e-api.md` for project structure rules, startup patterns,
and the boundary between API E2E and integration tests.

See `./examples/api-e2e-test.ts` for a complete API E2E file.

## UI E2E Tests (Playwright)

All UI E2E tests live in a `spec/` folder and end with `.spec.ts`. No locators
in test files — all page interactions go through page objects.

```typescript
// tests/spec/auth/login.spec.ts
import { test } from "@e2e/fixtures";
import { LoginPage } from "../../page-objects/LoginPage";

async function setUp(page: Page, ctx: TestContext) {
  const baseData = {
    orgs: [{ _id: "O1" }],
    users: [{ _id: "U1", orgId: "O1" }],
    userDetails: [{ _id: "U1" }],
  };
  const { selector } = await ctx.setupEnv({
    baseData,
    page,
    authShortId: "U1",
    loginFn: apiBasedLogin,
  });
  return { loginPage: new LoginPage(page), selector };
}

test("should login and view dashboard @auth @happyPath @TS1", async ({
  page,
  ctx,
}) => {
  const { loginPage } = await setUp(page, ctx);
  await loginPage.navigateTo();
  await expect(page).toHaveURL(/dashboard/);
});
```

Read `./references/e2e-playwright.md` for UI E2E file structure rules, the
tagging system, TestContext fixture usage, and Playwright-specific conventions.

Read `./references/page-object-model.md` for the Page Object Pattern including
`@step` decorators, selector priority order, and structure rules.

See `./examples/e2e-test.spec.ts` for a complete spec file.
See `./examples/page-object.ts` for a complete page object class.

## TestContext System

**If the project does not already have a TestContext, stop and gather the data
model before creating one.** The system is built around your specific entities
and their relationships — it cannot be scaffolded without that knowledge.

Follow this sequence:

1. **Ask the user for the data model** — a schema file, a list of
   types/interfaces, a `schema.prisma`, SQL DDL, or even a plain prose
   description of entities and relationships.
2. **If none exists**, analyze the codebase to infer it: look for type
   definitions, Firestore collection references, Prisma/Mongoose schemas,
   migration files, and any existing test data to understand what shape
   entities already take. Present the inferred model to the user for
   confirmation before proceeding.
3. **Derive the dependency order** — which entities must be inserted before
   others — and confirm it with the user.
4. **Then** use `./examples/test-context-implementation.md` as the build guide,
   substituting your confirmed entity names and fields for every placeholder.

The full data model discovery workflow is in
`./examples/test-context-implementation.md` under **Step 0**.

If a TestContext already exists, use it for all tests that need a database:

- Prefer the repository's existing fixture or helper pattern. In UI E2E tests that
  usually means a `ctx` fixture. In backend, integration, or API E2E tests it
  may mean a local `setupTest()` helper that creates `TestContext` directly.
- Pass initial data through one `ctx.setupEnv()` call when the repository uses
  that pattern
- Use shorthand IDs (`U1`, `O1`, `G1`) — the IdProvider resolves them to real
  database IDs
- Only specify IDs and relationships in test data; let generators handle names,
  emails, and other non-critical fields
- Treat shorthand IDs as test-local aliases. Reusing `U1` across different
  tests is fine because each test gets a fresh context and fresh real IDs.
- If the repository supports key-based merge, reusing the same shorthand ID in
  `baseData` and `testData` is the standard way to override module defaults.
  The override replaces the matching seeded entity; it is not a deep merge, so
  repeat required relationship fields when needed.

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
- **No per-test teardown for seeded data** — let environment-level reset or cleanup own that responsibility

## Tagging (UI E2E Tests)

Every UI E2E test must include at least one feature tag and one test type tag
at the end of its description, plus a unique `@TS#` identifier:

```typescript
test(
  "should create service and notify members @service-management @create @TS12",
);
test("should handle invalid credentials @auth @errorPath @TS13");
test(
  "should display empty state when no results @dashboard @empty-state @TS14",
);
```

Read `./references/e2e-playwright.md` for the full tag catalog.

## Anti-Patterns

Read `./references/anti-patterns.md` for a consolidated list of forbidden
patterns across all test types. The most critical ones:

- No mocks for code you own — test real implementations
- No `beforeEach` for data setup or state
- No locators in UI E2E test files — page objects only
- No per-test teardown for seeded data
- No hardcoded waits (`page.waitForTimeout()`)
- No commented-out tests — fix failing tests or delete them

## Quality Bar

Before committing tests:

- Each test proves one concrete behavior
- Tests run independently in any order
- No shared mutable state between tests
- TestContext shorthand IDs are clear and unambiguous within each seeded test dataset
- If a key-based merge is used, overrides repeat all required fields instead of assuming deep merge
- API E2E tests hit a consumer-visible HTTP endpoint rather than imported handlers
- UI E2E tests have both a feature tag and a type tag with a `@TS#` number
- UI page objects use `@step` on every action and assertion method
- No locators exist outside UI page object files
- All assertions are on real data, not mocked return values
