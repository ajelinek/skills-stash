# Code Shape and Naming

## Code shape rules

- One module, one purpose.
- Keep modules around 200 lines of implementation code. Split past ~300 lines unless the file is unusually cohesive, declarative, or generated.
- Keep functions around 20 lines. Decompose past ~30 lines unless the structure is still flat and obvious.
- Use guard clauses to exit early on preconditions and keep the main path obvious.
- Never pass more than 3 parameters to a function. If more than 3 values are needed, wrap them in an object parameter.
- Avoid nesting deeper than 2 levels. Use early returns, extracted functions, or guard clauses to flatten control flow.
- Export only what needs sharing. Keep internal helpers unexported.
- Place all exported/public functions at the top of a file. Place helper/utility functions at the bottom.
- Avoid comments. Write self-documenting code. Add a comment only when the reasoning is genuinely non-obvious and cannot be expressed in the code itself.

## Function style

Use the `function` keyword for all function declarations. Do not assign arrow functions to `const` for named functions.

```ts
// Correct
export function getUser(userId: string): User { ... }
function normalizeEmail(email: string): string { ... }

// Avoid
const getUser = (userId: string): User => { ... }
const normalizeEmail = (email: string): string => { ... }
```

Arrow functions are appropriate for inline callbacks and expressions — not for named, standalone functions.

## Variable declarations

Use `const` by default. Use `let` only when the value must be reassigned. Never use `var`.

```ts
const user = await getUser(userId)  // correct
let retries = 0                     // correct — reassigned in loop
```

## Ternary statements

Single-level ternaries are allowed. Never nest ternaries.

```ts
// Allowed
const label = isActive ? 'Active' : 'Inactive'

// Avoid — nested ternary
const label = isActive ? 'Active' : isArchived ? 'Archived' : 'Inactive'
```

Do not use ternaries for complex logic. Extract a variable or helper function instead.

## Naming conventions

| Construct | Convention | Example |
|---|---|---|
| Types / classes | `PascalCase` | `UserProfile`, `LoginResult` |
| Functions / hooks | `camelCase` | `getUser`, `useLogin` |
| Variables | `camelCase` | `isLoading`, `authUser` |
| Booleans | `is` / `has` / `can` prefix | `isActive`, `hasPermission`, `canEdit` |
| Timestamps | Descriptive `Timestamp` suffix | `insertTimestamp`, `updateTimestamp` |
| IDs | Entity-qualified | `userId`, `projectId` — never bare `id` |
| TypeScript / JSON fields | `camelCase` | `userId`, `orgId` |
| REST URLs | `kebab-case` | `/users`, `/user-groups` |
| SQL tables / columns | `snake_case` | `user_id`, `insert_timestamp` |

## Avoid

- Generic names like `data`, `info`, `item`, `result` — name what it actually is.
- Bare `id` — always qualify with the entity name.
- Abbreviations that hide intent.
- Naming drift between related types, functions, and exports.
