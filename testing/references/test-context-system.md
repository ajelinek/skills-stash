# TestContext System

## Overview

TestContext is the centralized system for managing test data in integration,
API E2E, and UI E2E tests. It coordinates data generation, ID management,
database insertion, and authentication setup through a unified API.

**If the project does not already have a TestContext, gather the data model
before creating one.** The system is built around your specific entities and
their relationships. Ask the user for a schema file, type definitions,
`schema.prisma`, SQL DDL, or a prose description. If none exists, analyze
the codebase to infer it. See `./examples/test-context-implementation.md`
**Step 0** for the full data model discovery workflow.

## Core Rules

### Prefer the repository's standard TestContext entry point

Use the repository's standard fixture or helper pattern.

- In UI E2E tests, that usually means a `ctx` fixture.
- In backend, integration, or API E2E tests, that may mean a local
  `setupTest()` helper that creates `TestContext` directly.

Do not invent a new access pattern when the repository already has one.

### All initial data goes through `ctx.setupEnv()`

```typescript
// Good: all initial data in one setupEnv call
const { selector } = await ctx.setupEnv({
  baseData,
  testData,
  page,
  authShortId: 'U1',
  loginFn,
})

// Bad: data created outside of setupEnv for initial setup
await ctx.db.users.insertOne({ ... })
```

Additional data created as part of a test scenario (not initial setup) may
use `ctx.scenario` builder methods.

### Additive setup, environment-owned cleanup

Test data is only ever added, never deleted between tests. Global setup handles
environment reset, truncation, schema recreation, or emulator cleanup.
Individual test setups only insert data. Tests do not perform per-test teardown
for seeded data.

## Shorthand ID System

All entities in test data use shorthand IDs. The `IdProvider` maps these to
real database IDs (UUIDs or numeric) consistently within a test run.

### Standard Shorthand Conventions

| Shorthand | Entity |
| --- | --- |
| `O1, O2, O3...` | Organizations |
| `U1, U2, U3...` | Users |
| `G1, G2, G3...` | User Groups |
| `A1, A2, A3...` | Activities |
| `T1, T2, T3...` | Targets |
| `S1, S2, S3...` | Services |
| `R1, R2, R3...` | Target Rules |
| `TT1, TT2, TT3...` | Target Types |
| `SP1, SP2, SP3...` | Sponsors |
| `REQ1, REQ2...` | Requests |

Shorthand IDs are reusable across different test files. The same `U1` in two
different test files refers to two different database users — the IdProvider
creates a fresh UUID for each test context.

**Critical:** Shorthand IDs are test-local aliases.

- Reusing `U1` across different tests is expected and safe because each test
  gets a fresh context and fresh real IDs.
- Within one seeded dataset, IDs must be unambiguous.
- If the repository supports key-based merge, reusing the same shorthand ID in
  `baseData` and `testData` is how you override module defaults.
- Key-based override is usually replace-by-entity, not deep merge. Repeat
  required relationship fields when overriding.

## setupEnv() Signature

```typescript
ctx.setupEnv({
  baseData: DataGenObject,    // Module-level base data
  testData?: DataGenObject,   // Test-specific additions/overrides
  page?: Page,                // Playwright page (omit for API E2E and other non-browser tests)
  authShortId?: string,       // Shorthand ID of user to authenticate as
  loginFn?: Function,         // Login function (repo-specific)
})
```

Returns `{ selector, authUser }` where:
- `selector` — object for accessing seeded data by shorthand ID
- `authUser` — the authenticated user entity (if auth was requested)

## Accessing Data with Selector

Use the `selector` to retrieve seeded data by shorthand ID:

```typescript
const { selector } = await ctx.setupEnv({ baseData, testData })

const user = selector.getUser('U1')       // returns the full user entity
const org = selector.getOrg('O1')         // returns the full org entity
const group = selector.getUserGroup('G1') // returns the full group entity
```

All selector methods resolve shorthand IDs to real database IDs. Never
resolve IDs manually or access the IdProvider directly in test files.

## Entity Relationship Map

When creating test data, satisfy all required relationships:

```
Organization
  └── User (requires orgId)
        └── UserDetail (requires userId as _id)
        └── OrgAdministrator (requires userId + orgId)
        └── UserGroupMember (requires userId + userGroupId)
  └── UserGroup (requires orgId)
        └── Service (requires userGroupId + activityId + userId)
        └── Target (requires userGroupId + targetTypeId + ruleId)
  └── Activity (requires orgId)
  └── TargetType (requires orgId)
  └── TargetRule (requires orgId)
  └── Sponsor (requires orgId)
```

Always check that foreign key relationships are included in test data.
Creating a `Service` without providing its required `UserGroup`, `Activity`,
and `User` will fail at insertion time.

## Key-Based Overrides

When the repository implements merge-by-key, reuse the same shorthand ID to
override module defaults:

```typescript
// Good: testData overrides the base entity with the same shorthand key
const MODULE_BASE_DATA = {
  orgs: [{ _id: 'O1' }],
  users: [{ _id: 'U1', orgId: 'O1' }],
  userDetails: [{ _id: 'U1' }],
}

await ctx.setupEnv({
  baseData: MODULE_BASE_DATA,
  testData: {
    users: [{ _id: 'U1', orgId: 'O1', email: 'custom@example.com' }],
  },
})
```

Use a new shorthand ID when you want an additional entity rather than a
replacement.

If the repository does not implement key-based merge, do not assume override
behavior. Follow the repository's existing `mergeData()` semantics.

## 8-Module Architecture

Some repositories use a multi-module TestContext architecture:

| Module | Purpose |
| --- | --- |
| `IdProvider` | Maps shorthand IDs to real database IDs |
| `Generators` | Create realistic entity data using faker |
| `Scenario` | Assembles data with correct dependency ordering |
| `Selector` | Pre-computed indexes for O(1) data access |
| `TestContext` | Main facade — coordinates all other modules |
| `DataMerger` | Pure function that merges baseData and testData |
| `AuthManager` | Firebase Auth user creation and token generation |
| `DatabaseReader` | Database read operations with ID resolution |

That architecture is a reference design, not a required shape. Simpler projects
may keep merge, scenario building, selectors, and DB writes in fewer files.

For the full implementation guide for building a TestContext from scratch,
see `./examples/test-context-implementation.md`.

## Minimal Data Specification

Only specify values that the test depends on. Let generators handle names,
emails, timestamps, and other non-critical fields:

```typescript
// Good: only IDs and relationships
const baseData = {
  orgs: [{ _id: 'O1' }],
  users: [{ _id: 'U1', orgId: 'O1' }],
  userDetails: [{ _id: 'U1' }],
}

// Bad: over-specifying data generators can handle
const baseData = {
  orgs: [{ _id: 'O1', name: 'My Test Org', description: 'A test org' }],
  users: [{ _id: 'U1', orgId: 'O1', email: 'test@example.com', firstName: 'Test' }],
  userDetails: [{ _id: 'U1', bio: 'Test user' }],
}
```
