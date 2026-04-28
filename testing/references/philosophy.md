# Testing Philosophy

## Test Priority Order

Prefer the highest-confidence boundary that matches the behavior under test.

This is not a strict `UI E2E > API E2E > Integration > Unit` ladder for every
scenario. A browser test is not automatically better than an API E2E test when
no browser behavior matters, and an API E2E test is not automatically better
than an integration test when the behavior lives entirely below the HTTP
boundary.

Use this decision order instead:

- Browser journey or visual workflow: UI E2E
- Consumer-visible HTTP behavior: API E2E
- In-process collaboration between modules or DB-backed services: integration
- Isolated branching logic or pure transforms: unit

Only drop down to a cheaper test type when the higher boundary does not add
meaningful confidence for the scenario at hand.

## When to Write Each Type

### UI E2E Tests (Playwright)

Write UI E2E tests for:

- Critical user journeys that span multiple pages or application layers
- Authentication and authorization flows
- Workflows a user would actually perform from a browser
- Features where correctness depends on the full stack working together

Do not write UI E2E tests for:
- Pure data transformation logic that has no UI surface
- Scenarios where no browser behavior matters and an API E2E test proves the
  same thing faster

### API E2E Tests (Vitest)

Write API E2E tests for:

- Public REST, GraphQL, RPC, or webhook behavior at the HTTP boundary
- Authentication, authorization, validation, routing, serialization, and error
  envelopes exposed to API consumers
- Backend systems with no browser UI where the API is the product surface
- Cross-service flows that are initiated through the public API and need a real
  started local endpoint

Do not write API E2E tests for:

- Tests that import controllers, route handlers, or service classes directly
- In-process helper-driven coverage that never targets a consumer-visible HTTP
  endpoint
- UI workflows that require a browser; use Playwright UI E2E instead

### Integration Tests (Vitest)

Write integration tests for:

- Service layer methods that read from or write to a real database
- API handler logic where you need real database state but do not need a fully
  started consumer-visible endpoint
- Cross-component data flows where multiple services interact
- Business logic that requires real relationship data to be meaningful
- In-process HTTP coverage where a helper talks to app internals rather than a
  started local API server

Do not write integration tests for:
- Public API behavior whose main risk is the HTTP boundary itself
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

- Unit and integration tests often live in `__tests__/` folders next to the
  code they test and may share a Vitest project
- Test files are named according to the repository's existing pattern
- API E2E tests usually live in `tests/api/` or `tests/e2e-api/` and often run
  in a dedicated Vitest project or config
- UI E2E tests live in `tests/spec/` organized by feature area
- Page objects live in `tests/page-objects/`
- One concept per file — when a test file grows large, split by sub-feature
