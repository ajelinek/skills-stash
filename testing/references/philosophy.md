# Testing Philosophy

## Test Priority Order

Prefer E2E > Integration > Unit.

This is not about coverage percentage — it is about confidence. A test that
exercises the real browser, the real network layer, and the real database
proves more than one that exercises only a service class in isolation.

Only drop down to a cheaper test type when the more expensive one is genuinely
impractical for the scenario at hand.

## When to Write Each Type

### E2E Tests (Playwright)

Write E2E tests for:

- Critical user journeys that span multiple pages or application layers
- Authentication and authorization flows
- Workflows a user would actually perform from a browser
- Features where correctness depends on the full stack working together

Do not write E2E tests for:
- Pure data transformation logic that has no UI surface
- Scenarios that would require mocking the browser environment

### Integration Tests (Vitest)

Write integration tests for:

- Service layer methods that read from or write to a real database
- API endpoint handlers where you can spin up a real DB connection
- Cross-component data flows where multiple services interact
- Business logic that requires real relationship data to be meaningful

Do not write integration tests for:
- Logic that is already fully covered by E2E tests at lower cost
- Things that can be tested with a pure function without a database

### Unit Tests (Vitest)

Write unit tests for:

- Complex, branching business logic with many discrete paths
- Pure utility and helper functions with clear inputs and outputs
- Edge cases that would be expensive or slow to reproduce in integration or E2E
- Parsers, formatters, validators, and calculators

Do not write unit tests for:
- Code that simply delegates to other services (the delegation is not the behavior)
- Things that can only be verified by checking real database state

## Avoiding Mocks

Mocks are a design smell in most test suites. They couple tests to
implementation details instead of behavior, and they can pass even when the
real integration is broken.

**Use real implementations.** If your service calls a database, use a real test
database. If it calls an internal module, use the real module.

**The only acceptable mock targets** are external services you genuinely cannot
control in a test environment — payment processors, third-party APIs with no
sandbox, or email providers without a test mode. Even then, prefer a test mode
or sandbox endpoint over a mock when one exists.

## Test Data Principles

### Generate fresh data per test

Each test should create its own data. Tests that share data become order-dependent
and fail in surprising ways when one test's mutation affects another.

### Only specify what matters

When using TestContext or factory functions, only provide the values the test
actually depends on. Let generators create realistic random values for everything
else. This makes tests resilient to schema changes and easier to read.

```typescript
// Good: only the relationship matters
const baseData = {
  orgs: [{ _id: 'O1' }],
  users: [{ _id: 'U1', orgId: 'O1' }],
  userDetails: [{ _id: 'U1' }],
}

// Bad: over-specifying data generators can handle
const baseData = {
  orgs: [{ _id: 'O1', name: 'Test Org', createdAt: '2024-01-01' }],
  users: [{ _id: 'U1', orgId: 'O1', email: 'test@example.com', firstName: 'John' }],
  userDetails: [{ _id: 'U1', bio: 'Test bio' }],
}
```

### Data is additive

Test data setup only adds data — it never cleans up between tests. Global
setup handles truncation and schema recreation. Individual test setups only
insert the data they need. Tests do not delete their own data afterward.

## Test Structure

Every test follows Given-When-Then:

- **Given**: the `setUp()` call that creates the starting state
- **When**: the action being tested (one action per test)
- **Then**: the assertions that verify the result

Keep this structure clear and explicit. Do not mix setup and assertions.
Do not perform multiple distinct actions in a single test.

## File Organization

- Unit and integration tests live in `__tests__/` folders next to the code
  they test
- Test files are named `[module-name].test.ts` or `[module-name].test.tsx`
- E2E tests live in `tests/spec/` organized by feature area
- Page objects live in `tests/page-objects/`
- One concept per file — when a test file grows large, split by sub-feature
