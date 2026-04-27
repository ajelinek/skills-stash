# TestContext System

## Overview

TestContext is the centralized system for managing test data in integration and
E2E tests. It coordinates data generation, ID management, database insertion,
and authentication setup through a unified API.

**If the project does not already have a TestContext, stop and ask before
creating one.** Building the system from scratch is a significant effort.
See `./examples/test-context-implementation.md` for the full build guide.

## Core Rules

### Never instantiate TestContext directly in test files

Always use the `ctx` fixture or a `setUp()` helper. Direct calls to
`TestContext.create()` in test files are not allowed.

### All initial data goes through `ctx.setupEnv()`

```typescript
// Good: all initial data in one setupEnv call
const { selector, authUser } = await ctx.setupEnv(baseData, testData, page, 'U1', loginFn)

// Bad: data created outside of setupEnv for initial setup
await ctx.db.users.insertOne({ ... })
```

Additional data created as part of a test scenario (not initial setup) may
use `ctx.scenario` builder methods.

### Additive data only

Test data is only ever added, never deleted between tests. Global setup handles
table truncation and schema recreation. Individual test setups only insert data.
Tests do not clean up data they created.

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

**Critical:** Shorthand IDs must be unique within a single `setupEnv()` call.
Never use the same shorthand ID in both `baseData` and `testData` — this
creates duplicate key violations.

## setupEnv() Signature

```typescript
ctx.setupEnv(
  baseData: DataGenObject,    // Module-level base data
  testData: DataGenObject,    // Test-specific additions/overrides
  page?: Page,               // Playwright page (omit for non-browser tests)
  authShortId?: string,      // Shorthand ID of user to authenticate as
  loginFn?: Function,        // Login function (e.g., apiBasedLogin)
)
```

Returns `{ selector, authUser }` where:
- `selector` — object for accessing seeded data by shorthand ID
- `authUser` — the authenticated user entity (if auth was requested)

## Accessing Data with Selector

Use the `selector` to retrieve seeded data by shorthand ID:

```typescript
const { selector } = await ctx.setupEnv(baseData, testData)

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

## Avoiding Duplicate Key Violations

This is the most common TestContext error. Never reuse a shorthand ID between
`baseData` and `testData`:

```typescript
// BAD: U1 appears in both baseData and testData
const MODULE_BASE_DATA = {
  orgs: [{ _id: 'O1' }],
  users: [{ _id: 'U1', orgId: 'O1' }],
  userDetails: [{ _id: 'U1' }],
}

await ctx.setupEnv(MODULE_BASE_DATA, {
  users: [{ _id: 'U1', email: 'custom@example.com' }],  // ← duplicate!
})

// GOOD: use a new shorthand ID for test-specific data
await ctx.setupEnv(MODULE_BASE_DATA, {
  users: [{ _id: 'U2', orgId: 'O1', email: 'custom@example.com' }],  // ← U2
  userDetails: [{ _id: 'U2' }],
})
```

## 8-Module Architecture

The TestContext system is built from eight cooperating modules:

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

The `DatabaseAdapter` interface ensures the system works with any database
(Firestore, PostgreSQL, MongoDB) by requiring only that adapters implement
standard read/write operations.

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
