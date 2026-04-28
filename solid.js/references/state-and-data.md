# State And Data

Follow a layered state architecture for SolidJS applications rather than
falling back to generic SolidJS patterns. Keep components presentation-focused
and move all shared async, validation, and external access behavior into hooks,
services, and repositories.

## Preferred Pattern

Keep components presentation-focused. Move all async, validation, and external
access behavior into hooks, services, and repositories.

## Storage Strategy

- **URL state**: user navigation state, filters, search queries, route state,
  and view preferences that should be shareable or bookmarkable.
- **sessionStorage**: temporary state that should survive refresh but not a new
  session (redirect messages, pending redirects).
- **localStorage**: persistent user preferences such as theme settings.
- **`createSignal`**: component-local ephemeral reactive values.
- **`createStore`**: component-local structured or nested reactive state.

### Do

- Use URL state for shareable user interactions.
- Use `localStorage` for persistent user preferences.
- Use `sessionStorage` for temporary state that survives refresh.
- Use `createSignal` for simple local state.
- Register cleanup with `onCleanup` inside `createEffect`.

### Do Not

- Store sensitive data in `localStorage` or `sessionStorage`.
- Store large objects in URL parameters.
- Use global state for component-specific data.
- Duplicate server data in browser storage.
- Manipulate the DOM directly when SolidJS reactive state can handle it.

## Layer Separation

The store layer follows a four-layer architecture:

```text
/store
├── repository/      — raw external calls only
├── service/         — business logic, validation, subscription wiring
├── hooks/           — SolidJS reactive wiring (useAsyncOperation / useAsyncSubscription)
└── utilities/       — createAsyncStore, useAsyncOperation, useAsyncSubscription, helpers
```

### Repository Layer

- External system interactions only (Firebase, REST APIs, etc.).
- Pure async functions or subscription setup functions.
- No business logic.
- No store or signal access.
- Error handling required at the boundary.

### Service Layer

- Pure TypeScript functions — no SolidJS reactivity inside services.
- Own business logic, input validation, and error handling.
- Mutation services: `async function doSomethingService(...)` — validates,
  calls repository, throws `ApiError[]` on failure.
- Subscription services: `function subscribeToSomethingService(param)` —
  returns `{ subscribe, enabled }` descriptor. No reactive state held here.

```ts
// Mutation service
export async function upsertDetailsService(userId: string, data: Partial<Details>): Promise<string> {
  if (!userId) throw [{ code: 'invalid-user', message: 'User ID required' }]
  const result = validateDetails(data)
  if (!result.isValid) throw result.errors
  return await upsertDetailsRepository(userId, data)
}

// Subscription service
export function subscribeToDetailsService(id: string) {
  return {
    subscribe: (onData: (d: Details) => void, onError: (e: Error) => void) => {
      if (!id || id === 'NEW') {
        onData(defaultDetails)
        return () => {}
      }
      return subscribeToDetailsRepository(id, onData, onError)
    },
    enabled: !!id,
  }
}
```

### Hook Layer

- Hook functions live in `store/hooks/`.
- Hook functions wire service functions to reactive state using the two
  foundational utilities: `useAsyncOperation` and `useAsyncSubscription`.
- Keep hooks thin — most logic belongs in the service layer.

```ts
// Mutation hook
export function useUpsertDetails() {
  return useAsyncOperation(async (userId: string, data: Partial<Details>) => {
    return await upsertDetailsService(userId, data)
  })
}

// Subscription hook
export function useDetails(id: string) {
  return useAsyncSubscription<Details | null, [string]>(subscribeToDetailsService, id)
}
```

### Component Layer

- Presentation logic only.
- No direct repository or service function calls.
- No direct store mutations.
- Reads state from hooks; calls `execute` on mutation hooks.

## The AsyncStore Pattern

All async state — both mutations and subscriptions — uses the same typed shape:

```ts
type AsyncStatus = {
  isProcessing: boolean
  isError: boolean
  isDone: boolean
  isReprocessing: boolean
  isInitial: boolean
  isSuccess: boolean
}

type ApiError = {
  code: string
  message: string
}

type AsyncStore<T> = {
  status: AsyncStatus
  errors: ApiError[] | null
  data: T | null
}
```

The `createAsyncStore<T>()` utility creates a reactive `AsyncStore` backed by
SolidJS `createStore` and exposes `setLoading`, `setSuccess`, `setError`,
`setErrors`, and `addError` helpers.

See `../examples/async-store.ts`.

## `useAsyncOperation` — Mutations

Use for one-time async operations: create, update, delete, send.

```ts
const op = useAsyncOperation(async (args) => {
  return await myService(args)
})

// In component:
await op.execute(args)
op.status.isProcessing  // reactive
op.errors               // reactive
op.data                 // reactive
```

Rules:

- Returns `{ execute, status, errors, data }`.
- `execute` sets loading, calls the operation, then sets success or error.
- Structured `ApiError[]` thrown by the service surface through `op.errors`.
- Generic `Error` thrown by the operation surfaces through a single error entry.

## `useAsyncSubscription` — Subscriptions

Use for real-time data that updates continuously (Firestore onSnapshot, WebSocket, etc.).

```ts
const details = useAsyncSubscription<Details | null, [string]>(
  subscribeToDetailsService,
  id,
)

// In component:
details.status.isSuccess  // reactive
details.data              // reactive
details.errors            // reactive
```

Rules:

- Returns `{ status, errors, data }`.
- Uses `createEffect` to re-subscribe when args change.
- Registers `onCleanup` to unsubscribe when the effect re-runs or the component
  unmounts — no memory leaks.
- Status stays `isInitial` when `enabled` is `false`.
- Business logic for edge cases (e.g., handling a `'NEW'` id) belongs in the
  service layer, not the hook.

See `../examples/async-store.ts` for the full implementations.

## Form State Integration

Validation belongs in the service layer, not the presentation component.

- Inputs get `errorMessage` from service-managed validation state.
- `onSubmit` calls the mutation hook's `execute`.
- Submit buttons disable during submission using `status.isProcessing`.
- Loading and error states flow from hooks into the UI.
- Use the `Alert` foundational component fed from `op.errors`.

See also:

- `./form-management.md`
- `./async-ui-states.md`
- `../examples/use-form-management.ts`
- `../examples/service-backed-form-page.tsx`

## Anti-Patterns

- Repository functions imported directly into components.
- Service functions called directly from components.
- Signals or stores mutated directly in page components for shared data.
- Validation logic living inside form JSX or presentation inputs.
- Subscriptions set up manually in components without `onCleanup`.
- Using SWR, Zustand, or other external state libraries when the native store
  pattern covers the need — prefer native `createStore` first.
- Using `produce` when a single targeted path-set is clearer.
- Mutating store state directly via the proxy outside `setStore` — always use
  the setter or `produce`.

## Store Utilities

### `produce` — multi-property mutations

Use `produce` from `solid-js/store` when you need to update several properties
of a store entry in one operation. It avoids multiple setter calls and keeps
the intent clear.

```ts
import { produce } from 'solid-js/store'

// Without produce — two setter calls
setStore('users', 0, 'username', 'newUsername')
setStore('users', 0, 'location', 'newLocation')

// With produce — single atomic update
setStore('users', 0, produce((user) => {
  user.username = 'newUsername'
  user.location = 'newLocation'
}))
```

`produce` is only compatible with arrays and objects. Use regular setter path
syntax for primitive values.

### `reconcile` — diffing incoming data

Use `reconcile` from `solid-js/store` when you receive fresh data from the
server or a snapshot and want to diff it against the current store state rather
than replacing everything. This preserves fine-grained reactivity for unchanged
entries.

```ts
import { createStore, reconcile } from 'solid-js/store'

const [items, setItems] = createStore<Item[]>([])

// Replace the list but only trigger updates for items that actually changed
function onFreshData(newItems: Item[]) {
  setItems(reconcile(newItems))
}
```

## `createResource` — One-Shot REST / Promise Fetching

Use `createResource` from `solid-js` as an alternative to `useAsyncOperation`
when the data flow is a single async fetch (REST endpoint, GraphQL query) and
the result is read-only in the component. `createResource` integrates directly
with `<Suspense>` and `<ErrorBoundary>`.

```ts
import { createResource, createSignal } from 'solid-js'

const fetchUser = async (id: string) => {
  const res = await fetch(`/api/users/${id}`)
  if (!res.ok) throw new Error('Failed to fetch user')
  return res.json() as Promise<User>
}

// source signal drives re-fetching automatically when it changes
const [userId, setUserId] = createSignal('123')
const [user] = createResource(userId, fetchUser)

// In JSX:
// user.loading — boolean
// user.error   — error value if thrown
// user()       — resolved data
// user.state   — 'unresolved' | 'pending' | 'ready' | 'refreshing' | 'errored'
```

With `<Suspense>` and `<ErrorBoundary>`:

```tsx
<ErrorBoundary fallback={(err) => <Alert errors={[{ code: 'fetch/error', message: err.message }]} />}>
  <Suspense fallback={<LoadingSpinner />}>
    <UserProfile />
  </Suspense>
</ErrorBoundary>
```

**When to use `createResource` vs `useAsyncOperation`:**

| Scenario | Use |
| --- | --- |
| One-shot read from a REST/GraphQL endpoint | `createResource` |
| Source signal drives automatic re-fetch | `createResource` |
| Suspense/ErrorBoundary integration desired | `createResource` |
| Mutation (create, update, delete) | `useAsyncOperation` |
| Real-time subscription | `useAsyncSubscription` |
| Complex error handling with `ApiError[]` shape | `useAsyncOperation` |

## See Also

- `./form-management.md`
- `../examples/async-store.ts`
- `../examples/service-backed-form-page.tsx`
- `./context-and-sharing.md` — sharing reactive state across the component tree
