# Type Modeling

Use this reference when the work is primarily about how a TypeScript domain is
represented.

## Defaults

- Start from `strict` thinking even if you are editing an older codebase.
- Prefer `unknown` over `any` at boundaries.
- Export shared types and keep local-only types local.
- Use `import type` and `export type` where appropriate.
- Use the simplest construct that expresses the invariant clearly.
- Prefer `type` by default for aliases, object shapes, unions, mapped types,
  conditional types, and composed domain models.
- Use `interface` only when you need behavior that is specific to interfaces,
  such as declaration merging or an existing class-oriented pattern that already
  depends on it.

## Good Fits For Stronger Modeling

- Discriminated unions for result states, async state, or variant payloads
- `as const` when you need runtime values and a derived literal union
- Type guards when boundary data starts as `unknown`
- Assertion functions when a precondition must be established once and then
  relied on afterward
- Narrow utility types when they remove duplication without obscuring meaning

## Avoid

- `any` as a shortcut around a modeling problem
- Broad assertions like `as SomeType` when validation is missing
- Non-null assertions when the guarantee is not obvious from local control flow
- Inlining complex anonymous object types repeatedly across a file or module
- Reaching for `interface` out of habit when `type` would express the model more
  directly

## Modeling Heuristics

- Model the concept the code relies on, not every possible future variation.
- When several branches share a core shape plus one varying field, a union is
  usually clearer than many optional properties.
- When a value crosses a boundary, prefer a narrow transport type and an
  explicit validation or mapping step before broad use.
- When a type alias becomes difficult to scan, split it into named pieces.
- If an object shape starts simple, keep it as a `type` unless you have a real
  reason to switch.

## Narrowing Toolbox

Prefer language-supported narrowing before assertions:

- `typeof` for primitives
- `instanceof` for class-backed values
- `in` for property-based refinement
- equality checks for literal discrimination
- control-flow returns and guards to make later code narrower
- discriminated unions plus exhaustive `never` checks for variant handling

Truthiness checks can be useful, but be careful with empty strings, `0`, and
other falsy values that may still be valid inputs.

## Examples To Prefer

Prefer a result type over boolean-plus-side-channel error state:

```ts
type SaveUserResult =
  | { kind: 'success'; userId: string }
  | { kind: 'conflict'; message: string }
```

Prefer a runtime constant plus derived union when the values are used at
runtime:

```ts
const STATUS = {
  active: 'active',
  disabled: 'disabled',
} as const

type Status = (typeof STATUS)[keyof typeof STATUS]
```

Prefer narrowing from `unknown`:

```ts
function isAccountRecord(value: unknown): value is AccountRecord {
  return !!value && typeof value === 'object' && 'accountId' in value
}
```

Prefer exhaustive handling for closed unions:

```ts
function renderState(state: LoadState) {
  switch (state.kind) {
    case 'idle':
      return 'idle'
    case 'loading':
      return 'loading'
    case 'loaded':
      return state.value
    default: {
      const exhaustiveCheck: never = state
      return exhaustiveCheck
    }
  }
}
```

## Official Guidance

- Narrowing handbook: `https://www.typescriptlang.org/docs/handbook/2/narrowing.html`
- Strict mode and strict-family flags: `https://www.typescriptlang.org/tsconfig/#strict`
- Catch variables as `unknown`: `https://www.typescriptlang.org/tsconfig/#useUnknownInCatchVariables`
