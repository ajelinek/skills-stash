# State And Data

This repository has a specific state architecture. Follow it instead of falling
 back to generic React patterns.

## Preferred Pattern

Keep components presentation-focused and move shared async, validation, and
external access behavior into services, providers, and repositories.

## Storage Strategy

- **URL state**: user navigation state, filters, search queries, route state,
  and view preferences that should be shareable
- **sessionStorage**: temporary interactions that should survive refresh but not
  a new session
- **localStorage**: persistent user preferences, theme settings, and application
  configuration
- **useState**: component-local ephemeral state

### Do

- Use URL state for shareable user interactions
- Use `localStorage` for persistent user preferences
- Use `sessionStorage` for temporary state that survives refresh
- Use `useState` for local component state
- Implement cleanup in `useEffect`

### Do Not

- Store sensitive data in `localStorage` or `sessionStorage`
- Store large objects in URL parameters
- Use global state for component-specific data
- Duplicate server data in browser storage
- Manipulate the DOM directly

## Local State Rules

- Use `useState` for component-level state.
- Use `useMemo` only for expensive memoized calculations.
- Flatten state instead of deeply nesting it.
- Return cleanup functions for subscriptions, timers, and listeners.

## Layer Separation

Follow the shared UI store architecture:

```text
/store
├── repository/
├── service/
├── utilities/
└── config.ts
```

### Repository Layer

- External system interactions only
- Pure async functions
- No business logic
- Error handling required
- Minimal data selection
- No store access

### Service Layer

- Use React custom hooks for async state management
- Services expose a consistent named export object or hook interface
- Services own loading, errors, subscriptions, and state updates
- Components access data and async behavior via services or hooks only
- Centralize auth and session concerns in providers plus custom hooks, then keep
  route gating in app shells or layouts

### Components

- Presentation logic only
- No direct repository or external system calls
- No direct state mutation for shared store state

## SWR Pattern

Use the service-SWR pattern.

- Manage global state through service modules that use SWR internally.
- Components should call service functions or hooks only.
- Service functions should own SWR hooks and configuration.
- Repositories should be called by service functions, not components.
- Use stable SWR keys:
  - server data keys based on API endpoints
  - UI state keys based on descriptive `ui/...` identifiers
- Use `useSWRMutation` for mutations where that fits the repository pattern.
- Put shared SWR defaults in `<SWRConfig>` at the app root only.

### Do

- Use service functions for all global SWR-managed state
- Keep SWR usage inside services only
- Keep return patterns consistent across services
- Implement error handling in service functions

### Do Not

- Import SWR directly in components
- Access repositories directly from components
- Duplicate service-managed data in another client-state layer

## Zustand Pattern

Use the repo's stricter Zustand structure.

- Create one store instance with `create<Store>()()`.
- Put store creation in `store/config.ts`.
- Define `initialState` separately.
- Keep the store to state shape only; no action methods in the store.
- All mutations go through `useStore.setState()` inside service hooks.
- Service hooks may use `useState`, `useEffect`, and callbacks for async,
  mutation, or subscription behavior.
- Components read state via narrow selectors or service selector hooks.
- Use `useStore.getState()` for non-reactive reads in service hooks or
  utilities.

### Do

- Keep service hooks as the only layer calling `setState()`
- Use selector reads in components
- Use `initialState` for reset

### Do Not

- Define actions as store methods
- Call `setState()` inside repository functions
- Subscribe to the entire store in components
- Access the store directly from the repository layer

## Form State Integration

Validation belongs in the service layer, not the presentation component.

- Inputs get `errorMessage` from service-managed validation state.
- `onSubmit` should call service logic.
- Submit buttons should disable during submission.
- Loading and error states should flow from services into the UI.

See also:

- `./form-management.md`
- `./async-ui-states.md`
- `./route-and-auth-composition.md`
- `../examples/use-form-management.ts`
- `../examples/service-backed-form-page.tsx`
- `../examples/auth-form-shell.tsx`

## Anti-Patterns

- Repositories imported directly into components
- Shared async state split across services and component-local duplicates
- Store mutations happening in repositories
- Validation logic living only in form JSX

## See Also

- `./form-management.md`
- `./route-and-auth-composition.md`
- `../examples/use-form-management.ts`
- `../examples/service-backed-form-page.tsx`
