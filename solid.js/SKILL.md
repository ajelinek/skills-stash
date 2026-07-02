---
name: solid.js
description: >
  Use this skill when writing or refactoring SolidJS TypeScript code following
  structured conventions: CSS Modules, foundational component system, service-driven
  state and validation, shared form hooks, native SolidJS store state management,
  and accessible semantic HTML. Use alongside `ui-engineering` whenever the
  task also involves shared UI structure, styling, semantics, accessibility, or
  foundation-component decisions.
  Trigger on requests to build a SolidJS component, hook, foundational UI primitive,
  async operation, store service, or subscription hook where architectural consistency
  matters more than generic SolidJS patterns.
---

# SolidJS

Use this skill to apply structured SolidJS conventions rather than reaching for
generic patterns. Prefer shared UI and architectural patterns over ad hoc
per-component decisions.

## When To Use This Skill

- Building or refactoring SolidJS components in TypeScript
- Creating foundational UI components under a shared component system
- Deciding where reactive state belongs and how to layer it
- Building shared form hooks or service-backed forms
- Wiring async operations (mutations) or subscriptions to reactive state
- Using the native SolidJS store for global async state management
- Structuring auth, route layout, and async page composition
- Understanding the `useAsyncOperation` / `useAsyncSubscription` store patterns

## Core Rules

### 1. Component Shape

- Use typed props with `Component<Props>` or a plain typed function.
- Access props directly — do not destructure props in the function signature;
  SolidJS props are reactive getters and destructuring breaks reactivity.
- Keep components small, focused, and composable.
- Keep JSX logic simple; move complex logic into variables or helpers.
- Use SolidJS control flow components for conditionals and lists:
  `<Show>`, `<For>`, `<Switch>/<Match>`, `<Index>`.
- Define components at module scope, not inside other components.
- Prefer composition over prop drilling.
- Prefer thin page shells that compose shared forms, services, and foundation
  primitives over monolithic screen components.

Read `./references/component-structure.md` for component shape, file layout,
and page-shell composition.

### 2. Foundational Components First

Before writing any button, input, form, modal, or other common UI element,
check `components/foundation/` first. The decision rule is:

1. **Primitive exists** — use it. Do not re-implement it inline.
2. **Primitive is close but missing a prop** — extend the existing primitive.
   Do not fork it or work around it in the page component.
3. **Primitive does not exist** — create it in `components/foundation/` before
   using it. Never inline a one-off button, input, modal, or toggle in a page
   or feature component.

The same rule applies to the shared form hook: reach for `useFormManagement`
before managing form state ad hoc.

Additional rules:

- Foundational components must be consistent, reusable, accessible, and
  strongly typed.
- Keep APIs consistent: use `class`, `children`, `variant`, `size`, `label`,
  and `errorMessage` where they fit.
- Put busy, disabled, label, help, and error rendering into the primitive.
  Page components must not re-implement these behaviors.
- When a base UI pattern appears in two or more places, move it into
  `components/foundation/` immediately.

Read `./references/foundational-components.md` for Button, Input, Alert,
Loading, Modal, and EmptyState primitives.
Read `./examples/use-form-management.ts` for the canonical form hook shape.

### 3. Styling Rules

- Use CSS Modules for all component styling.
- Each component lives in its own directory with `index.tsx` and
  `styles.module.css`.
- Use semantic HTML and semantic class names.
- Use CSS custom properties for tokens and theming.
- Use `class` (not `className`) for SolidJS JSX.
- No inline styles.
- No utility-class stacking.
- No complex selectors or deep nesting.

Read `./references/styling-and-theme.md` for CSS Modules, theme tokens,
`data-theme`, and component CSS structure.

### 4. Reactivity Rules

- Use `createSignal` for simple component-local reactive values.
- Use `createStore` from `solid-js/store` for structured or nested reactive
  state.
- Use `createMemo` for derived reactive values — only when the derivation is
  non-trivial. Do not wrap every derived value in a memo.
- Use `createEffect` for side effects; always register cleanup with `onCleanup`
  when the effect attaches a listener or subscription.
- Use `onMount` only for DOM-dependent setup after the component is mounted.
- Never destructure props — access them as `props.foo` to preserve reactivity.
- Never read signals outside a reactive context when reactivity is required.

### 5. Service-Driven Data Flow

- Components should be presentation logic only.
- No direct external system calls from components.
- Components access state and async behavior through service hooks only.
- Repository functions handle raw external interactions only (Firebase, REST, etc.).
- Service functions own business logic, validation, and error handling.
- Hook functions wire service functions to SolidJS reactive state through
  `useAsyncOperation` or `useAsyncSubscription`.
- Keep validation in the service layer, not in presentation components.

Read `./references/state-and-data.md` for the full layer architecture, async
store patterns, storage, and store-management approach.

### 6. Global Store Pattern — Native SolidJS Store

Use native SolidJS `createStore` for global async state management. Prefer
this over external state libraries (Zustand, Redux, MobX) unless a project
has an existing investment in one.

The store layer has three layers:

- **Repository** — raw external system calls; no business logic; no store access.
- **Service** — business logic, validation, and subscription wiring. Returns
  a descriptor object; does not hold reactive state itself.
- **Hook** — wires a service function to a `createAsyncStore` instance via
  `useAsyncOperation` (mutations) or `useAsyncSubscription` (subscriptions).

Components call hooks and read reactive state from them. Components do not call
service or repository functions directly.

The two foundational hook utilities are:

- `useAsyncOperation(operation)` — wraps a one-time async call (create, update,
  delete). Returns `{ execute, status, errors, data }`.
- `useAsyncSubscription(subscriptionService, ...args)` — wraps a real-time data
  subscription. Returns `{ status, errors, data }`. Automatically re-subscribes
  when args change and cleans up on unmount via `createEffect` + `onCleanup`.

The `AsyncStore<T>` state shape used by both is:

```ts
type AsyncStore<T> = {
  status: AsyncStatus
  errors: ApiError[] | null
  data: T | null
}

type AsyncStatus = {
  isProcessing: boolean
  isError: boolean
  isDone: boolean
  isReprocessing: boolean
  isInitial: boolean
  isSuccess: boolean
}
```

Read `./references/state-and-data.md` for the full store architecture.
Read `./examples/async-store.ts` for the `createAsyncStore` and pattern utilities.

### 7. Forms

- Always use foundational input components — never raw `<input>`, `<button>`,
  or `<select>` directly in page or feature components.
- Every input must have a label.
- Always use the shared `useFormManagement` hook for form state.
- `useFormManagement` uses `createStore` internally and exposes:
  `state`, `isDirty`, `onChange`, `onSubmit`, `updateState`,
  `resetFormToInitialState`, `resetFormToNew`, `setField`.
- `onChange` reads `e.currentTarget.name` to path-set into store state.
- Support dotted field paths for nested form shapes.
- Keep form validation in the service layer.
- Disable submit during submission using `status.isProcessing`.
- Show a loading state during submission.
- Handle network errors through the `Alert` foundational component fed from
  operation `errors`.

Read `./references/form-management.md` for controlled forms, shared form hooks,
dirty state, nested field paths, and service-backed submit flows.

### 8. Async UI States

- Use `<Show>` to branch across loading, empty, error, and content states.
- Wrap async or risky subtrees in `<ErrorBoundary>` to catch render errors and
  display a fallback UI without crashing the whole page.
- For simple REST or promise-based fetches, `createResource` from `solid-js`
  is a lighter-weight alternative to `useAsyncOperation`. Use `createResource`
  for read-only fetches; use `useAsyncOperation` for mutations and operations
  that need status tracking across the service layer.
- Put loading and disabled behavior into shared primitives.
- Render notifications and action errors using the shared `Alert` primitive fed
  from service operation `errors`.
- Reset, refocus, or redirect after successful async actions using
  `createEffect` watching `status.isSuccess`.

Read `./references/async-ui-states.md` for loading, empty, error, success, and
busy-state patterns.

### 9. Accessibility

- Use semantic HTML instead of generic wrappers when the element has meaning.
- Add ARIA attributes where they add real semantic meaning.
- Ensure every interactive element has an accessible name.
- Maintain visible focus states and keyboard support.
- Keep minimum 44px touch targets for interactive elements.
- Respect reduced motion and contrast requirements.
- Use `Portal` from `solid-js/web` when rendering modals or overlays to avoid
  stacking context issues.

Read `./references/accessibility-patterns.md` for labels, error messaging,
async announcements, dialog semantics, toggle states, and touch targets.

### 10. Context And Shared State

- Use `createContext` / `useContext` to share state across a subtree without
  prop drilling.
- Always provide a typed safe-accessor function that throws a clear error when
  a consumer is used outside its Provider — never return `undefined` silently.
- Prefer passing signal tuples `[signal, setter]` through context so consumers
  can read and update shared reactive state naturally.
- Use module-level signals instead of context when state is truly global and
  does not need to vary per subtree.
- Wrap the Provider at the closest common ancestor — usually a layout or route
  shell — not at the app root unless the state is truly app-wide.

Read `./references/context-and-sharing.md` for the full typed context pattern,
signal tuple sharing, and testing components that use context.

### 11. Route And Auth Composition

- Prefer route layouts and thin page shells over large route-switch components.
- Centralize redirect and gate logic in protected route components or auth
  boundaries.
- Reuse form shells across login, registration, and similar flows instead of
  duplicating structure.
- Auth state is managed via `useActiveUser()` from the auth service hook; do not
  read auth state from raw Firebase APIs in components.

## Supporting Files

- `./references/component-structure.md`
  SolidJS file layout, component shape, control flow, exports, and anti-patterns.
- `./references/foundational-components.md`
  Foundational component rules, base props, shared component list, and form
  integration expectations.
- `./references/state-and-data.md`
  Storage strategy, service and repository layering, native store pattern,
  `useAsyncOperation`, `useAsyncSubscription`, `createResource`, `produce`,
  and `reconcile`.
- `./references/context-and-sharing.md`
  Typed context pattern, safe-accessor, signal tuples, module-level signals,
  and testing components that depend on context.
- `./references/form-management.md`
  Shared form hook patterns, dirty state, nested path updates, and submit flow
  guidance.
- `./references/async-ui-states.md`
  Loading, empty, error, success, and notification handling patterns.
- `./references/accessibility-patterns.md`
  House accessibility rules for forms, async states, toggles, dialogs, and
  touch targets.
- `./references/styling-and-theme.md`
  CSS Modules rules, token strategy, theming, and responsive styling defaults.
- `./references/testing.md`
  SolidJS-specific component and hook test mechanics. For full testing philosophy
  and E2E patterns, install the `testing` standalone skill.
- `./examples/foundational-button.tsx`
  House-style foundational button example.
- `./examples/foundational-input.tsx`
  House-style foundational input example.
- `./examples/foundational-modal.tsx`
  House-style dialog example using native dialog semantics with `Portal`.
- `./examples/async-store.ts`
  `createAsyncStore`, `useAsyncOperation`, and `useAsyncSubscription` utilities.
- `./examples/use-form-management.ts`
  Shared form hook example using `createStore` with nested path updates.
- `./examples/service-backed-form-page.tsx`
  Thin page-shell example composed from foundation primitives and service hooks.

## Quality Bar

- Components are typed, focused, and composable.
- Props are never destructured — accessed as `props.foo` throughout.
- `<Show>`, `<For>`, `<Switch>`, `<Index>` are used for all conditional and list
  rendering — no bare ternaries mapping over arrays outside JSX control flow.
- Foundational components are used or extended — never re-invented inline.
- `useFormManagement` is used for all form state — no ad hoc per-field signals.
- CSS Modules and semantic tokens are used consistently; `class` not `className`.
- Components stay presentation-focused; services and repositories own business
  logic and external access.
- `useAsyncOperation` wraps all one-time mutations in service hooks.
- `useAsyncSubscription` wraps all real-time subscriptions with proper cleanup.
- `<ErrorBoundary>` wraps async and risky subtrees; pages do not crash without a fallback.
- Context is typed with a safe-accessor that throws on missing Provider; never returns `undefined`.
- Forms keep validation in the service layer; errors surface through `Alert`.
- Pages branch clearly across loading, empty, error, and content states.
- Accessibility semantics are built into primitives and async messaging.
