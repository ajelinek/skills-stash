# Unit Testing

## Purpose and Scope

Unit tests verify individual functions, classes, or modules in isolation from
the database and external services. They are the right choice for:

- Complex business logic with many branching paths
- Pure functions: parsers, formatters, validators, calculators
- Edge cases that would be slow or expensive to set up in integration tests

Do not write unit tests for code that simply delegates to other services —
the delegation is not the behavior you need to verify.

## Setup Pattern

Unit tests do not use TestContext. Use factory functions and generator utilities
from your project's `@data/generators` package to build test inputs.

```typescript
import { generateUser } from '@data/generators'
import { UserValidator } from '../UserValidator'

async function setUp(overrides: Partial<UserOptions> = {}) {
  const user = generateUser(overrides)
  const validator = new UserValidator()
  return { user, validator }
}
```

The `setUp` function:
- Accepts optional overrides for fields the test cares about
- Delegates all other field values to the generator
- Returns only the objects the test actually uses
- Is called inside each test, not in `beforeEach`

## Writing Tests

```typescript
test('should reject user with missing email', async () => {
  const { user, validator } = await setUp({ email: null })

  const result = validator.validate(user)

  expect(result.isValid).toBe(false)
  expect(result.errors).toContain('email is required')
})

test('should accept user with valid email and name', async () => {
  const { user, validator } = await setUp()

  const result = validator.validate(user)

  expect(result.isValid).toBe(true)
})
```

Each test:
- Calls `setUp()` at the top (Given)
- Performs one action (When)
- Makes assertions on the result (Then)
- Has a name in `should / when / then` form that describes the behavior

## Data Management

### Let generators do the work

Only specify values the test depends on. Generators produce realistic random
data for everything else.

```typescript
// Good: only override what matters for this test
const { user } = await setUp({ email: null })

// Bad: specifying data that is irrelevant to the test
const { user } = await setUp({
  email: null,
  firstName: 'John',
  lastName: 'Doe',
  createdAt: new Date('2024-01-01'),
})
```

### Factory functions for complex objects

When a test needs a complex nested object that a generator does not produce
directly, write a small factory function rather than building the object inline
in every test.

```typescript
function makeOrderWithItems(itemCount = 1) {
  return {
    id: generateId(),
    items: Array.from({ length: itemCount }, () => generateOrderItem()),
    status: 'pending',
  }
}
```

## File Organization

- Place unit tests in `__tests__/` next to the file being tested
- Name the file `[module].test.ts` matching the source file
- One test file per source module
- Group related tests into the same file; split when a file grows too large
  to navigate easily

```
src/
├── validators/
│   ├── UserValidator.ts
│   └── __tests__/
│       └── UserValidator.test.ts
├── utils/
│   ├── formatDate.ts
│   └── __tests__/
│       └── formatDate.test.ts
```

## Performance

- Keep individual unit tests under 100ms
- No database connections in unit tests
- No network calls in unit tests
- If a test requires a real database to be meaningful, it is an integration test

## See Also

- `./examples/unit-test.ts` — complete copyable unit test file
