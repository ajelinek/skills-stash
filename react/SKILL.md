---
name: react
description: >
  Use this skill when writing or refactoring React TypeScript code that should
  follow this repo's React conventions: CSS Modules, foundational components,
  service-driven state and validation, shared form hooks, SWR service modules,
  Zustand service hooks, route and auth composition, and accessible semantic
  HTML.
  Trigger on requests to build a React component, hook, foundational UI
  primitive, theme toggle, SWR service, or Zustand store or service that should
  match this coding style rather than generic React advice.
---

# React

Use this skill to match this repository's React style, not generic React advice.
Prefer the established shared UI and app patterns over ecosystem-default
patterns.

## When To Use This Skill

- Building or refactoring React components in TypeScript
- Creating foundational UI components under a shared component system
- Deciding where React state belongs in this architecture
- Building shared form hooks or service-backed forms
- Structuring auth, route layout, and async page composition
- Using SWR through service modules
- Using Zustand through a store plus service-hook architecture
- Wiring forms where validation lives in the store or service layer

Default preference:

- Current preferred style: TypeScript-first React, shared foundation package,
  CSS Modules, typed custom hooks, provider-based auth, explicit route layouts,
  and service-backed forms.
- Historical lineage is still useful for legacy code: simpler shared form
  helpers, route-builder abstractions, section-scoped error boundaries, and
  older modal wrappers.

## Core Rules

### 1. Component Shape

- Use typed props.
- Destructure props in the function signature.
- Keep components small, focused, and composable.
- Keep JSX logic simple; move complex logic into variables or helpers.
- Use standard JavaScript control flow in JSX: `&&`, simple ternaries, and
  `.map()` for lists.
- Define components at module scope, not inside other components.
- Prefer composition over prop drilling, HOCs, render props, or `cloneElement`.
- Use error boundaries where a subtree should fail independently.
- Prefer thin page shells that compose shared forms, services, and foundation
  primitives over monolithic screen components.

Read `./references/component-structure.md` for component shape, file layout, and
page-shell composition.

### 2. Foundational Components First

Before writing any button, input, form, modal, toggle, or other common UI
element, check `components/foundation/` first. The decision rule is:

1. **Primitive exists** — use it. Do not re-implement it inline.
2. **Primitive is close but missing a prop** — extend the existing primitive.
   Do not fork it or work around it in the page component.
3. **Primitive does not exist** — create it in `components/foundation/` before
   using it. Never inline a one-off button, input, modal, or toggle in a page
   or feature component.

The same rule applies to the shared form hook: reach for `useFormManagement`
before managing form state ad hoc. If the hook is missing a capability, extend
it — do not duplicate form state logic in the page component.

Additional rules:

- Foundational components must be consistent, reusable, accessible, and
  strongly typed.
- Wrap interactive native elements with `forwardRef` so consumers can attach
  refs.
- Keep APIs consistent: use `className`, `children`, `variant`, `size`,
  `label`, and `errorMessage` where they fit.
- Put busy, disabled, label, help, and error rendering into the primitive.
  Page components must not re-implement these behaviors.
- When a base UI pattern appears in two or more places, move it into
  `components/foundation/` immediately.

Read `./references/foundational-components.md` for Button, Input, Dialog,
Loading, Alert, Toggle, Typography, and EmptyState primitives.
Read `./examples/use-form-management.ts` for the canonical form hook shape.

### 3. Styling Rules

- Use CSS Modules for all component styling.
- Each component lives in its own directory with `index.tsx` and
  `styles.module.css`.
- Use semantic HTML and semantic class names.
- Use exactly one class per element unless a single modifier class is truly
  necessary.
- Use CSS custom properties for tokens and theming.
- Use semantic or global tokens directly in component CSS. Only create
  component tokens when the value is reused across multiple component CSS files.
- No inline styles.
- No utility-class stacking.
- No complex selectors or deep nesting.

Read `./references/styling-and-theme.md` for CSS Modules, theme tokens,
`data-theme`, and component CSS structure.

### 4. State Placement

- Use `useState` for component-local ephemeral state.
- Use `useMemo` only for expensive derived values when the performance need is
  real.
- Flatten state instead of deeply nesting objects.
- Return cleanup functions from `useEffect`.
- Put shareable navigation state, filters, and view state in the URL.
- Use `sessionStorage` for temporary state that should survive refresh.
- Use `localStorage` for persistent user preferences such as theme.
- Do not store sensitive data in browser storage.
- Do not duplicate server data in client storage.

### 5. Service-Driven Data Flow

- Components should be presentation logic only.
- No direct external system calls from components.
- Components access state and async behavior through services or hooks.
- Repository functions handle raw external interactions only.
- Service hooks manage async state, loading, errors, subscriptions, and state
  updates.
- Keep validation in the store or service layer, not in presentation
  components.
- Centralize auth and app-session concerns in providers plus custom hooks, then
  keep route gating in app shells or route layouts.

Read `./references/state-and-data.md` for service boundaries, SWR, Zustand,
storage, and provider-backed app state.

### 6. SWR Pattern

- Manage global REST-style state through service modules that use SWR
  internally.
- Components should call service functions or hooks, not SWR directly.
- Service functions should encapsulate SWR keys, fetchers, mutation hooks, cache
  updates, and error handling.
- Repositories should be accessed through service functions, not directly from
  components.
- Put shared SWR defaults in `<SWRConfig>` at the app root only.

### 7. Zustand Pattern

- Use a single store instance in `store/config.ts`.
- Keep the store definition to state shape only; no action methods in the store.
- Define `initialState` separately and use it for reset.
- Service hooks are the only layer that should call `useStore.setState()`.
- Components should read with narrow selectors, ideally via service selector
  hooks.
- Use `useStore.getState()` only for non-reactive reads in service hooks or
  utilities.
- Repository functions should not know about the store.

### 8. Forms

- Always use foundational input components — never raw `<input>`, `<button>`,
  or `<select>` directly in page or feature components.
- Every input must have a label.
- Use a generated ID to tie label and input together.
- Always use the shared `useFormManagement` hook for form state. Do not manage
  form fields with ad hoc `useState` per field.
- Support dotted field paths when the form shape is nested.
- Keep form validation in the store or service layer.
- Inputs receive validation errors from service operations.
- Disable submit during submission.
- Show a loading state during submission.
- Handle network errors clearly.
- Prevent multiple submissions.

Read `./references/form-management.md` for controlled forms, shared form hooks,
dirty state, nested field paths, and service-backed submit flows.

### 9. Async UI States

- Put loading and disabled behavior into shared primitives when it is a repeated
  interaction pattern.
- Use explicit loading, empty, error, and content branches in page-level UI.
- Render notifications and action errors accessibly.
- Reset, refocus, or redirect after successful async actions only when the
  interaction flow clearly benefits from it.

Read `./references/async-ui-states.md` for loading, empty, error, success, and
busy-state patterns.

### 10. Accessibility

- Use semantic HTML instead of generic wrappers when the element has meaning.
- Add ARIA attributes where they add real semantic meaning.
- Ensure every interactive element has an accessible name.
- Maintain visible focus states and keyboard support.
- Keep minimum 44px touch targets for interactive elements.
- Respect reduced motion and contrast requirements.

Read `./references/accessibility-patterns.md` for labels, error messaging,
async announcements, dialog semantics, toggle states, and touch targets.

### 11. Route And Auth Composition

- Prefer route layouts and thin page shells over large route-switch components.
- Keep route trees explicit.
- Centralize redirect and gate logic in the app shell, route layout, or auth
  boundary.
- Reuse form shells across login, registration, verification, and similar flows
  instead of duplicating structure.
- Treat route-builder patterns as historical context; prefer explicit nested
  routes in current code.

Read `./references/route-and-auth-composition.md` for route trees, auth
providers, app shells, redirects, and shared page shells.

## Supporting Files

- `./references/component-structure.md`
  React file layout, component shape, control flow, exports, and anti-patterns.
- `./references/foundational-components.md`
  Foundational component rules, base props, shared component list, and form
  integration expectations.
- `./references/state-and-data.md`
  Storage strategy, service and repository layering, SWR pattern, and Zustand
  pattern.
- `./references/form-management.md`
  Shared form hook patterns, dirty state, nested path updates, and submit flow
  guidance.
- `./references/async-ui-states.md`
  Loading, empty, error, success, and notification handling patterns.
- `./references/accessibility-patterns.md`
  House accessibility rules for forms, async states, toggles, dialogs, and
  touch targets.
- `./references/route-and-auth-composition.md`
  Route layouts, auth providers, app shell gating, and historical route-builder
  context.
- `./references/example-gallery.md`
  How to document shared primitives through a reference or widget page without
  turning it into feature code.
- `./references/styling-and-theme.md`
  CSS Modules rules, token strategy, theming, and responsive styling defaults.
- `./examples/foundational-button.tsx`
  House-style foundational button example.
- `./examples/foundational-input.tsx`
  House-style foundational input example.
- `./examples/foundational-toggle-slider.tsx`
  House-style toggle or switch primitive example.
- `./examples/foundational-modal.tsx`
  House-style dialog example using native dialog semantics.
- `./examples/use-form-management.ts`
  Shared form hook example with nested path updates.
- `./examples/service-backed-form-page.tsx`
  Thin page-shell example composed from foundation primitives and service hooks.
- `./examples/auth-form-shell.tsx`
  Reusable auth-shell example for login, registration, and verification flows.
- `./examples/theme-toggle.tsx`
  House-style theme toggle example.

## Quality Bar

- Components are typed, focused, and composable.
- Foundational components are used or extended — never re-invented inline. If a
  primitive is missing, it is created in `components/foundation/` before use.
- `useFormManagement` is used for all form state — no ad hoc per-field
  `useState`.
- CSS Modules and semantic tokens are used consistently.
- Components stay presentation-focused; services and repositories own business
  logic and external access.
- SWR is encapsulated in service modules.
- Zustand updates happen through service hooks, not directly in components or
  repositories.
- Forms keep validation in the service or store layer.
- Pages branch clearly across loading, empty, error, and content states.
- Accessibility semantics are built into primitives and async messaging.
- When current and historical examples differ, prefer the current TypeScript and
  shared-foundation style unless the task is clearly inside an older code path.
