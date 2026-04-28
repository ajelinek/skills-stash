# Integration Testing

## Purpose and Scope

Integration tests verify that components work correctly together — services
calling real databases, cross-module data flows, and API-layer behavior inside
the application boundary. They run in Vitest with a real database connection.

Integration is about real collaboration, not necessarily full end-to-end system
execution. If the test imports app internals or bypasses the consumer-visible
HTTP startup path, it is usually integration even when it exercises routing or
middleware.

Write integration tests for:
- Service methods that read from or write to a database
- Workflows involving multiple services or modules working together
- API handler logic where database state matters but a fully started local
  endpoint is not the point of the test

Do not classify these as API E2E:
- Direct controller or route-handler imports
- Service calls beneath the HTTP boundary
- Helper-driven HTTP coverage that talks to an in-process app rather than the
  started local API endpoint the consumer sees

Do not add an in-process HTTP simulation layer when a normal integration test or
real HTTP API E2E test would be clearer. Keep integration tests focused on real
module, service, database, and handler collaboration inside the app boundary.

## TestContext Requirement

All integration tests that need a database use TestContext. If the project does
not have a TestContext implementation, stop and ask the user before proceeding.

TestContext provides:
- Consistent data seeding through `ctx.setupEnv()`
- Shorthand ID resolution (`U1`, `O1`, `G1` → real database IDs)
- Data isolation through fresh contexts, generated real IDs, and additive setup
- A `selector` object for accessing seeded data in assertions

## Setup Pattern

```typescript
import { TestContext } from '@data/test-context'
import { DataGenObject } from '@data/test-context/types'
import { UserService } from '../UserService'

// Base data shared across all tests in this module
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
  const service = createServiceUnderTest()
  return { selector, service }
}
```

Key rules for `setUp`:
- Always define `MODULE_BASE_DATA` as a module-level constant
- Pass `MODULE_BASE_DATA` as `baseData`
- Pass test-specific data as `testData`
- Return the `selector` and any service instances the tests need
- If the repository supports key-based merge, reuse the same shorthand key in
  `testData` to override module defaults
- Override semantics are typically replace-by-key, not deep merge

## Writing Tests

```typescript
test('should return user by id', async ({ ctx }) => {
  const { selector, service } = await setUp(ctx)

  const user = selector.getUser('U1')
  const result = await service.findById(user._id)

  expect(result).toBeDefined()
  expect(result._id).toBe(user._id)
})

test('should create service for org', async ({ ctx }) => {
  const { selector, service } = await setUp(ctx, {
    activities: [{ _id: 'A1', orgId: 'O1' }],
    userGroups: [{ _id: 'G1', orgId: 'O1' }],
  })

  const org = selector.getOrg('O1')
  const result = await service.createService({ orgId: org._id, activityId: selector.getActivity('A1')._id })

  expect(result.orgId).toBe(org._id)
})
```

Notice the test-specific data (`activities`, `userGroups`) is passed as the
`testData` argument to `setUp`, which passes it to `ctx.setupEnv()`. Do not
call `ctx.setupEnv()` again inside a test.

## Accessing Seeded Data

Use the `selector` returned by `setUp` to access data by shorthand ID. Never
hardcode real database IDs.

```typescript
// Good: use selector with shorthand IDs
const user = selector.getUser('U1')
const org = selector.getOrg('O1')
const group = selector.getUserGroup('G1')

// Bad: hardcoding database IDs
const user = await service.findById('550e8400-e29b-41d4-a716-446655440000')
```

## Additional Data During Test Execution

Initial data always goes through `ctx.setupEnv()`. For data created as part of
a test scenario, use the repository's context-supported builder or helper
methods:

```typescript
test('should list services created after setup', async ({ ctx }) => {
  const { selector, service } = await setUp(ctx)

  // Additional data created as part of the test scenario — not initial setup
  await ctx.scenario.user({ userId: 'U2', orgId: 'O1' }).build().insert()

  const result = await service.listByOrg(selector.getOrg('O1')._id)
  expect(result).toHaveLength(1)
})
```

## Entity Relationships

When creating test data, always satisfy required relationships. Common patterns:

```typescript
// User requires org and userDetail
{
  orgs: [{ _id: 'O1' }],
  users: [{ _id: 'U1', orgId: 'O1' }],
  userDetails: [{ _id: 'U1' }],
}

// UserGroup and member requires org and user
{
  orgs: [{ _id: 'O1' }],
  users: [{ _id: 'U1', orgId: 'O1' }],
  userDetails: [{ _id: 'U1' }],
  userGroups: [{ _id: 'G1', orgId: 'O1' }],
  userGroupMembers: [{ userId: 'U1', userGroupId: 'G1' }],
}
```

Always check the entity relationship map in `./test-context-system.md` before
adding new entity types to test data.

## File Organization

- Place integration tests in `__tests__/` next to the service or module when
  that matches the repository's conventions
- Name files according to the repository's existing pattern
- Use the repository's existing fixture or `setupTest()` helper pattern

## See Also

- `./e2e-api.md` — API E2E boundary rules and running-server patterns
- `./test-context-system.md` — full TestContext system rules and shorthand IDs
- `./examples/integration-test.ts` — complete copyable integration test file
