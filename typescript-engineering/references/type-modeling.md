# Type Modeling

## Defaults

- Use `unknown` over `any` at boundaries; narrow explicitly before use.
- All types belong in a top-level `types/` folder. Do not co-locate types inside domain modules or feature folders.
- Prefer `type` over `interface`. Use `interface` only when declaration merging or class implementation patterns already established in the codebase require it.
- Use the simplest type construct that expresses the invariant.

## Patterns worth reaching for

**Discriminated unions** for variant states and result types:

```ts
type LoadState<T> =
  | { kind: 'idle' }
  | { kind: 'loading' }
  | { kind: 'loaded'; value: T }
  | { kind: 'failed'; message: string }
```

Always handle the `default` branch with `never` to get exhaustiveness checking:

```ts
const exhaustiveCheck: never = state
return exhaustiveCheck
```

**`as const` + derived union** for enum-like values:

```ts
const Theme = {
  LIGHT: 'light',
  DARK: 'dark',
} as const

type Theme = (typeof Theme)[keyof typeof Theme]
```

**Type guards** for narrowing from `unknown`:

```ts
function isUser(value: unknown): value is User {
  return (
    !!value &&
    typeof value === 'object' &&
    'userId' in value &&
    'email' in value
  )
}
```

**Intersection types** for type composition:

```ts
type UserWithPreferences = User & {
  preferences: UserPreferences
}
```

**Indexed access types** to derive fields from an existing type rather than duplicating them:

```ts
type UserSummary = {
  userId: User['userId']
  displayName: User['displayName']
}
```

## Narrowing toolbox

- `typeof` — primitive checks
- `instanceof` — class checks
- `in` — property-based refinement
- equality checks — discriminant narrowing
- control-flow returns / guard clauses — eliminate invalid states early
- discriminated unions + exhaustive `never` — catch unhandled variants at compile time

## Avoid

- `any` — use `unknown` with a type guard instead
- Broad `as SomeType` assertions without prior validation
- Non-null assertions (`!`) — treat as a last resort
- Inlining complex anonymous object types — give them a name in `types/`
- Reaching for `interface` out of habit
