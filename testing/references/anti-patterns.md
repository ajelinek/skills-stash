# Anti-Patterns

Consolidated list of forbidden patterns across all test types. These are not
preferences — they produce tests that are brittle, misleading, or unreliable.

## Test Structure

### No `beforeEach` for data setup

`beforeEach` creates implicit state that makes it impossible to understand a
test without reading the entire file. Call `setUp()` at the start of each test.

```typescript
// Bad
beforeEach(async () => {
  await ctx.setupEnv({ baseData, testData: {} })
})

// Good
test('should do something', async ({ ctx }) => {
  const { selector } = await setUp(ctx)
  ...
})
```

### No `describe` blocks for nesting

Nested `describe` blocks with `beforeEach` hooks create hidden dependencies
and make test state nearly impossible to reason about. Organize by feature
into separate files instead.

### No conditional logic in tests

A test with an `if` statement is actually two tests — write both explicitly.
Conditional logic in tests hides which behavior is being verified.

### No test interdependence

Each test must be runnable in isolation in any order. Tests that depend on
side effects from previous tests fail unpredictably.

### No commented-out tests

Commented-out tests are dead weight. Fix the failing test or delete it.

### No `test.only` or `test.skip` in committed code

These are local development tools. Remove them before committing.

## Test Data

### No mocks for code you own

Mocking your own services couples tests to implementation details. When the
implementation changes, mocks silently pass while real behavior breaks. Use
real implementations.

```typescript
// Bad
jest.mock('../UserService')
const mockService = UserService as jest.MockedClass<typeof UserService>
mockService.prototype.findById.mockResolvedValue({ id: '123' })

// Good
const service = createServiceUnderTest()
const result = await service.findById(selector.getUser('U1')._id)
```

### No hardcoded database IDs

Hardcoded UUIDs or numeric IDs will not match what TestContext generates. Use
shorthand IDs and the selector.

```typescript
// Bad
const user = await service.findById('550e8400-e29b-41d4-a716-446655440000')

// Good
const user = selector.getUser('U1')
const result = await service.findById(user._id)
```

### No unsafe shorthand-ID overrides

Do not assume all repositories handle repeated shorthand IDs the same way.

- If the repository supports merge-by-key, repeating the same shorthand ID in
  `baseData` and `testData` is how you override a module default.
- If it does not, repeating the same shorthand ID may create duplicate data or
  insertion failures.
- Override semantics are typically replace-by-key, not deep merge.

```typescript
// Safe override when merge-by-key is supported
await ctx.setupEnv({
  baseData: { users: [{ _id: 'U1', orgId: 'O1' }] },
  testData: { users: [{ _id: 'U1', orgId: 'O1', email: 'custom@example.com' }] },
})
```

### No ad-hoc TestContext access pattern

Do not invent a new pattern for obtaining `TestContext`. Follow the
repository's existing fixture or helper pattern.

### No per-test manual data cleanup

Tests do not delete data they created as part of normal setup. Environment
reset or suite-level cleanup handles that responsibility.

### No test data pollution across tests

Do not rely on data created by another test. If you override module defaults,
do it explicitly through the repository's merge semantics.

## API E2E Specific

### No direct handler or controller imports in API E2E tests

If the test imports route handlers, controllers, or services and never talks to
a consumer-visible HTTP endpoint, it is not API E2E.

### No hidden boundary downgrade

Helpers that talk to an in-process app can be useful, but classify them
honestly. If the test is not targeting the started local server or public base
URL, it belongs in integration tests instead of API E2E.

## UI E2E / Playwright Specific

### No locators in spec files

Every `page.getByRole()`, `page.getByLabel()`, etc. call in a spec file is a
locator that belongs in a page object instead. Spec files use page object
methods and may use page object–exposed locators for single-line assertions only.

```typescript
// Bad — locator in spec file
await page.getByRole('button', { name: 'Sign in' }).click()

// Good — action on page object
await loginPage.clickSignIn()
```

### No `page.waitForTimeout()`

Hardcoded waits make tests slow and still flaky. Use Playwright's built-in
auto-waiting on locators and expect assertions.

### No fragile selectors

CSS class selectors, IDs assigned by bundlers, and XPath expressions break
without warning when the UI is restyled or rebuilt. Stick to the selector
priority order in `./page-object-model.md`.

### No explicit waits in page objects

`page.waitForSelector()` is almost always a sign that a test is racing against
an asynchronous UI update. Use Playwright's `expect()` assertions which include
built-in retry logic.

### No conditional logic in page objects

Page objects must not branch on UI state. If a button might or might not be
visible, write two different actions (or two different page objects) — do not
add `if (await button.isVisible())`.

### No `describe` blocks in E2E spec files

Same reason as integration tests: nesting creates hidden state. Keep E2E
spec files flat.

### No returning locators from page object methods

Page object methods perform operations or make assertions. They do not return
locators. Returning locators leaks implementation details to spec files.

## Page Objects

### No single-line assertion methods

Only create assertion methods in page objects for multi-step assertions that
are reused across multiple tests. Single assertions go directly in spec files.

```typescript
// Bad — single-line assertion method in page object
async verifyButtonVisible() {
  await expect(this.submitButton()).toBeVisible()
}

// Good — single-line assertion in spec file using locator directly
await expect(loginPage.submitButton()).toBeVisible()
// Wait — that exposes the locator. If the locator is private, just use:
await expect(page.getByRole('button', { name: 'Sign in' })).toBeVisible()
// Or promote it to a proper multi-step assertion method if it is truly reused.
```
