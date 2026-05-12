---
name: ui-engineering
description: >
  Use this skill when writing UI components, designing component systems, or
  applying shared front-end standards that apply across frameworks. Trigger on
  requests about component structure, foundation components, accessibility, form
  UX, CSS token architecture, semantic HTML, theming, or project directory
  layout for any TypeScript UI codebase — whether React, Solid, or Astro.
---

# UI Engineering

Shared front-end standards for component design, accessibility, styling, and
form UX that apply across frameworks. Use this skill to set the baseline before
reaching for a framework-specific skill.

This is the canonical home for shared frontend code-organization rules. Apply
these boundary and import conventions first, then layer framework-specific React,
SolidJS, or Astro guidance on top.

## When To Use This Skill

- Designing or auditing component boundaries and composition rules
- Building or evaluating a foundation component library
- Applying accessibility requirements (WCAG 2.1 AA) to new components or forms
- Choosing a CSS architecture, token strategy, or theming approach
- Setting up a project's directory structure for UI code
- Deciding how to manage form state, validation, and submission UX
- Establishing cross-team or cross-project UI conventions in TypeScript

## Core Rules

### 1. Project Organization And Boundaries

Organize UI code by business boundary, not by technical layer. Default to
`app/`, `shared/`, and `features/`. The same internal shape repeats globally and
within each feature boundary.

```text
src/
├── app/                          # App-wide runtime wiring and routing
│   ├── components/
│   ├── hooks/
│   ├── store/
│   ├── types/
│   └── index.ts
├── shared/                       # Reusable cross-domain code
│   ├── components/
│   │   └── foundation/
│   ├── hooks/
│   ├── store/
│   ├── types/
│   └── index.ts
├── features/
    ├── search/
    │   ├── components/
    │   ├── hooks/
    │   ├── pages/
    │   ├── store/
    │   ├── types/
    │   └── index.ts              # Public API barrel
    └── customer/
        ├── components/
        ├── hooks/
        ├── pages/
        ├── store/
        ├── types/
        └── index.ts
└── types/                        # Truly global cross-boundary types only
```

`app/` owns application bootstrap and routing concerns:

- router configuration and route composition
- app shell and top-level layouts
- providers and dependency wiring
- auth/session bootstrap
- theme/bootstrap state
- app-level store, hooks, components, and types

Each feature owns its business UI and behavior:

- `components/` for feature-scoped UI
- `hooks/` for the UI bridge into feature behavior and state
- `pages/` for page containers or screens owned by that feature
- `store/` for feature state, services, and providers
- `types/` for feature-specific types

Each top-level shared area mirrors the same internal shape:

- `app/components|hooks|store|types`
- `shared/components|hooks|store|types`
- `features/<feature>/components|hooks|pages|store|types`

Routing rule:

- Default: routing lives in `app/`, and routes render pages exported from
  `features/<feature>/pages/`.
- File-based routing exception: when a framework requires route files such as
  `src/pages/`, keep them thin and have them delegate directly to feature-owned
  pages. They are routing entrypoints, not the main home of page logic.

Example thin file-based route entry:

```ts
import { SearchPage } from '@search'

export default SearchPage
```

Store interaction rule:

- Components and pages talk to hooks.
- Hooks are the UI-facing bridge and should call services.
- Services are the primary business interface and should read/write store state.
- Providers are the external-system interface and should handle API calls,
  Firebase, local storage, browser persistence, and similar integrations.
- Components should not call providers directly.
- Components should avoid calling services directly unless there is a very clear,
  local exception.

- Every feature exposes a public API from its `index.ts` barrel.
- Cross-boundary imports go through path aliases such as `@search`, `@customer`,
  or `@shared`.
- Do not import through relative deep paths such as
  `../features/search/components/SearchBar`.
- Keep app-wide singletons and cross-cutting configuration in `app/`.
- Keep truly reusable components, hooks, store helpers, and shared types in
  `shared/`.
- Keep only genuinely global types in the root `types/` folder.
- If the project uses Sheriff or similar boundary tooling, enforce one-way
  imports and prevent circular dependencies.

### 2. Foundation Components First

Build and consume a shared foundation layer before writing any button, input,
dialog, alert, icon, or loading state in a feature component.

Decision order:

1. **Primitive exists** — use it. Never re-implement it inline.
2. **Primitive is close but missing a variant or prop** — extend it. Do not
   fork it or work around it at the call site.
3. **Primitive does not exist** — create it in `shared/components/foundation/`
   before using it anywhere. Never inline a one-off UI primitive in a page or
   feature component.

Foundation component requirements:

- Single purpose. One module per component.
- Fully accessible and keyboard-navigable.
- Strongly typed props with a consistent API (`variant`, `size`, `label`,
  `errorMessage`, `className`, `children`).
- Mobile-first. Minimum 44px touch target for all interactive elements.
- CSS Modules for all styling — tokens via CSS custom properties, no utility
  classes, no inline styles.

Core foundation component set:

| Component | Responsibility |
| --- | --- |
| `Button` | Text actions and form submission |
| `IconButton` | Icon-only actions — always requires `aria-label` |
| `Input` | Text, email, password, number fields |
| `Alert` | Notifications, inline errors, feedback |
| `Dialog` | Modals and popups |
| `Dropdown` | Selection menus |
| `Icon` | Wrapper that renders SVG icons from `icons/` |
| `Loading` | Spinners and skeleton states |
| `List` | Ordered and unordered data display |
| `Table` | Tabular data grids |

**Icon file structure:**

All icons are standalone `.svg` files stored in
`shared/components/foundation/icons/`. Each file contains one optimized icon with no
hard-coded presentation attributes:

```
shared/components/foundation/
├── icons/
│   ├── close.svg
│   ├── chevron-down.svg
│   ├── check.svg
│   ├── warning.svg
│   └── search.svg
├── Icon/
│   └── index.tsx        # Renders an SVG from icons/ with size + a11y props
├── IconButton/
│   └── index.tsx        # Button that wraps Icon; requires aria-label
├── Button/
│   └── index.tsx
…
```

Never inline SVG markup directly in component templates. Import and render
icons through the `Icon` or `IconButton` foundation component only.

Read `./references/foundational-components.md` for component shape rules,
`BaseProps` conventions, icon SVG authoring standards, and per-component
ARIA requirements.

---

### 3. Component Shape

- Type all props explicitly — no untyped components or props.
- Keep components small and single-purpose.
- Keep JSX logic simple; move complex logic into variables or helper functions
  before the return statement.
- Components handle presentation only. Business logic belongs in store services,
  external access belongs in store providers, and components should reach both
  through hooks.
- No prop drilling past one level. Use composition, context, or state management
  instead.
- No inline `style` attributes.
- No direct DOM manipulation.
- Lazy-load large or infrequently used components.
- Implement proper cleanup for side effects.

UI interaction boundary:

- Prefer `Component -> hook -> service -> provider`.
- Hooks are the only normal bridge between UI and the store layer.
- Use a hook when a component needs state, derived view data, or actions.
- Use local component state only for ephemeral, non-shared UI state.
- Do not let components/pages import providers directly.

File layout for each component:

```
ComponentName/
├── index.tsx            # Main component logic and view
└── styles.module.css    # CSS Modules for component-scoped styles
```

Use `default export` for the component name from `index.tsx`.

---

### 4. Semantic HTML

Use the most specific HTML element that describes the content or role. The
full element reference table is in the Accessibility section below — semantic
HTML and ARIA are inseparable, so they are documented together.

Key rule: `<div>` and `<span>` are last-resort containers. If a semantic
element exists for the purpose, use it. Never use a `<div>` with a `role`
when the native element already carries that role implicitly.

---

### 5. Accessibility (WCAG 2.1 AA)

Apply these requirements to every component. Accessibility is not a post-build
audit step; it is a build-time requirement.

**Semantic HTML first — use the right element:**

| Purpose | Element |
| --- | --- |
| Page primary content | `<main>` |
| Site header | `<header>` |
| Site footer | `<footer>` |
| Navigation region | `<nav aria-label="…">` |
| Secondary content | `<aside aria-label="…">` |
| Grouped content with a label | `<section aria-label="…">` |
| Self-contained article | `<article>` |
| User-triggered action | `<button type="button">` |
| Navigation to a new URL | `<a href="…">` |
| Grouped list items | `<ul>` / `<ol>` + `<li>` |
| Tabular data | `<table>` + `<th scope="col|row">` + `<td>` |
| Form field | `<input>` / `<select>` / `<textarea>` with `<label>` |
| Group of related fields | `<fieldset>` + `<legend>` |
| Heading hierarchy | `<h1>` → `<h2>` → `<h3>` in logical order |

Never use `<div>` or `<span>` for an element that has a semantic equivalent.

**ARIA labels — when and how:**

Every interactive element must have an accessible name. The source of that name
follows this priority order:

1. Visible text content of the element (preferred — no ARIA needed)
2. `aria-labelledby` pointing to a visible text element elsewhere
3. `aria-label` on the element itself (use when no visible label is possible)

Common required cases:

```html
<!-- Icon-only button: no visible text, must have aria-label -->
<button type="button" aria-label="Close dialog">
  <Icon name="close" aria-hidden="true" />
</button>

<!-- Navigation regions when multiple navs exist on the page -->
<nav aria-label="Main navigation">…</nav>
<nav aria-label="Breadcrumb">…</nav>

<!-- Section landmarks -->
<section aria-label="Product filters">…</section>

<!-- Dialog: title element provides the label -->
<dialog aria-labelledby="dialog-title">
  <h2 id="dialog-title">Confirm deletion</h2>
</dialog>

<!-- Input with error -->
<label for="email">Email address</label>
<input id="email" type="email" aria-invalid="true" aria-describedby="email-error" />
<span id="email-error" role="alert">Enter a valid email address.</span>
```

**Decorative vs meaningful icons:**

- Decorative icons (accompanied by visible text): `aria-hidden="true"`
- Meaningful icons (standalone, convey information alone): `aria-label` on the
  wrapper or parent interactive element

**Color and contrast:**
- Normal text: minimum 4.5:1 contrast ratio
- Large text (≥ 18px or ≥ 14px bold): minimum 3:1
- Interactive elements and their borders: minimum 3:1
- Never use color alone to convey meaning — always pair with text, icon, or
  pattern

**Keyboard navigation:**
- All interactive functionality must be reachable and operable by keyboard alone
- Tab order must follow logical visual sequence — never use `tabindex > 0`
- All interactive elements must have a visible `:focus-visible` indicator
- Provide a skip navigation link at the top of pages with persistent nav regions
- Escape closes dialogs, menus, and dropdowns
- Arrow keys navigate composite widgets (menus, listboxes, tab lists)

**Screen reader announcements:**
- Announce dynamic content changes with ARIA live regions
- Use `role="alert"` or `aria-live="assertive"` for errors and urgent changes
- Use `role="status"` or `aria-live="polite"` for non-urgent updates
- Never use `aria-live="assertive"` for loading indicators

**Visual design:**
- Support text scaling to 200% without horizontal scrolling
- Respect `prefers-reduced-motion` — disable or reduce all animation when set
- Maintain visible focus state during dynamic content changes

**Touch:**
- Minimum 44×44px touch target for all interactive elements
- Minimum 8px gap between adjacent touch targets
- No hover-only interactions

Read `./references/accessibility.md` for full implementation patterns, ARIA
role reference, focus management rules, and the per-component testing checklist.

---

### 6. CSS Architecture

**The reuse model has two and only two layers: CSS custom properties and
foundation components. There is no third layer of generic utility classes.**

Shared styles flow through the codebase in exactly this way:

1. **CSS custom properties (variables)** — define any value that needs to be
   shared across components (colors, spacing, radii, typography, shadows).
   Consumed directly in component CSS files via `var(--token-name)`.
2. **Foundation components** — any repeated UI pattern becomes a component in
   `shared/components/foundation/`. Consumers reuse the component, not the CSS
   class.

What this means in practice:

- Do not create generic CSS class names (`.flex-row`, `.card`, `.text-sm`,
  `.mb-4`) that get applied to arbitrary elements across the codebase.
- Do not build a utility class system or a shared stylesheet full of reusable
  classes. That work lives in foundation components and CSS variables instead.
- If two pages both need a card-shaped container, create a `Card` foundation
  component — do not create a `.card` class in a shared stylesheet.

**CSS Modules for every component:**

- Every component has its own `styles.module.css` file colocated in its
  directory.
- Import as: `import styles from './styles.module.css'`
- One class per element. Add a single modifier class only when strictly
  necessary (e.g., `.button` base + `.secondary` variant applied together).
- Class names describe the element's role in the component, not its appearance.
  Use `.container`, `.header`, `.actions`, `.errorMessage` — not `.flexRow`,
  `.redText`, `.mb16`.
- No `!important`, no ID selectors, no complex descendant selectors.
- Keep selectors flat — no more than two levels of nesting.
- No inline `style` attributes anywhere.
- No utility-class stacking.

**CSS variable (token) system — two layers:**

1. **Global tokens** — raw base values, defined in `:root`, no semantic meaning.
   ```css
   --color-brand-teal: #008080;
   --spacing-md: 1rem;
   --radius-md: 0.375rem;
   ```

2. **Semantic tokens** — contextual aliases that reference global tokens and
   carry meaning. Consumed in all component CSS.
   ```css
   --color-text-primary: var(--color-neutral-grey900);
   --color-interactive-primary: var(--color-brand-teal);
   --color-background-page: var(--color-neutral-grey100);
   ```

   Component tokens are allowed only when a value is shared across two or more
   component CSS files. Never create them for single-component use.

**Deciding where a style lives:**

| Question | Answer |
| --- | --- |
| Is it a raw value (color hex, px size, font family)? | Global token in `styles/tokens/` |
| Is it a contextual alias (text color, interactive color, spacing scale)? | Semantic token in `styles/themes/` |
| Is it a recurring UI shape (button, card, input, badge)? | Foundation component in `shared/components/foundation/` |
| Is it component-specific styling (layout, spacing inside one component)? | In that component's `styles.module.css` using tokens |
| Is it a page-level or feature-level layout? | In that page/feature component's `styles.module.css` |

**Icons:**

- All icons live as individual `.svg` files in
  `shared/components/foundation/icons/`.
- Each SVG file contains one icon, optimized and stripped of presentation
  attributes (`fill`, `stroke`, `width`, `height` — set these via the wrapper
  component or CSS).
- Do not inline SVG markup directly in component templates. Import through the
  `Icon` foundation component.
- The `Icon` component wraps the SVG and applies `size`, `color` via CSS
  variables, and accessibility attributes.

**Theming:**
- Use `data-theme` on `<html>` for theme switching.
- Define semantic tokens under `[data-theme='dark']` in `dark.css`.
- Persist theme preference in `localStorage`.
- Never hard-code color values in component CSS — always use semantic tokens.

**Style file layout:**

```
styles/
├── tokens/
│   ├── _colors.css       # Global color values
│   ├── _spacing.css      # Spacing scale
│   ├── _typography.css   # Type scale and weights
│   └── _radii.css        # Border radius scale
├── animations/
│   └── index.css         # Keyframe definitions only
├── themes/
│   ├── light.css         # Semantic token aliases (default)
│   └── dark.css          # Semantic token overrides for dark theme
└── global.css            # Resets, base element styles, import order
```

Read `./references/styling-and-tokens.md` for token naming conventions, the
full decision guide, theming patterns, responsive rules, and animation
guidelines.

---

### 7. Form UX

Forms enforce consistent UX patterns across all UI implementations.

**Labels and inputs:**
- Every input must have a visible `<label>`.
- Use a generated unique ID to tie each label and input together.
- Use the appropriate HTML5 `type` for every input.
- Use foundation input components — never raw `<input>` or `<button>` in
  feature or page components.
- Ensure screen reader compatibility and keyboard focus management.

**Validation:**
- Form validation runs in the service layer, not in presentation components.
- Hooks surface validation state and actions to the UI.
- Components receive validation errors from hook-backed service operations.
- Errors must be clear, specific, and directly associated with the failing field.
- Provide recovery guidance alongside error messages.

**Submission UX:**
- Disable the submit button during submission.
- Show a loading indicator during the network call.
- Handle network errors clearly with user-visible feedback.
- Prevent duplicate submissions.
- Show success confirmation.
- Reset the form or redirect after a successful submission.

Read `./references/form-ux.md` for label and ID patterns, validation contract,
error message anatomy, and submission state machine.

---

### 8. Project Directory Structure

Use the boundary model above as the default structure. Framework-specific skills
may add routing or rendering directories, but the business-boundary rule stays
the same.

```
src/
├── app/
│   ├── components/
│   ├── hooks/
│   ├── store/
│   │   ├── providers/
│   │   ├── services/
│   │   └── types/
│   ├── types/
│   └── index.ts
├── shared/
│   ├── components/
│   │   └── foundation/
│   ├── hooks/
│   ├── store/
│   │   ├── providers/
│   │   ├── services/
│   │   └── types/
│   ├── types/
│   └── index.ts
├── features/
    └── some-boundary/
        ├── components/
        ├── hooks/
        ├── pages/
        ├── store/
        │   ├── providers/
        │   ├── services/
        │   └── types/
        ├── types/
        └── index.ts
└── types/
```

The `store/` folder has a defined internal contract:

- `services/` is the primary business interface for the boundary.
- `providers/` handles all external system interaction.
- state files in `store/` should stay small and mostly pure.
- hooks bind framework UI to services and store state.

Preferred flow:

```text
Component/Page
  -> Hook
    -> Service
      -> Provider

Service
  -> store state
```

Use a hook when the UI needs:

- state subscription
- derived view data
- user-triggered actions
- lifecycle binding to service operations

Use a service when the code needs:

- business rules
- orchestration
- validation
- state updates
- coordination across providers and store state

Use a provider when the code needs:

- API calls
- Firebase or realtime backends
- local storage or browser persistence
- any other external system access

Foundation components are never feature-specific. When a UI pattern appears in
two or more feature components, move it to `shared/components/foundation/`
immediately.

App routing stays in `app/`. If a framework uses file-based route files, keep
those route-entry files thin and compose their feature page through the public
barrel export.

---

## Supporting Files

- `./references/foundational-components.md`
  Component shape, `BaseProps` conventions, foundation component list, and
  composition expectations.

- `./references/accessibility.md`
  WCAG 2.1 AA standards, keyboard navigation, ARIA patterns, form error
  messaging, live regions, and touch targets.

- `./references/styling-and-tokens.md`
  Token layers, CSS Modules rules, theming with `data-theme`, responsive and
  mobile styling, and animation guidelines.

- `./references/form-ux.md`
  Label and ID patterns, validation contract, error message anatomy, submission
  state, and multi-step form guidance.

- `./examples/foundational-button.css`
  CSS Modules example for a Button component using the two-layer token system.

- `./examples/form-with-validation.html`
  Annotated semantic HTML form example demonstrating label association, ARIA
  error messaging, and accessible field structure.

---

## Quality Bar

Before shipping any UI component or form, confirm:

- [ ] Foundation components used where they exist — nothing re-invented inline
- [ ] The app is organized by `app`, `shared`, and `features/`, not by top-level technical folders
- [ ] `app/`, `shared/`, and each feature use the repeated internal shape: `components/`, `hooks/`, `store/`, and `types/`, with `pages/` inside features
- [ ] Each `store/` clearly separates `services/` and `providers/`
- [ ] Every feature exposes a public API through `index.ts`
- [ ] Routing lives in `app/` by default; file-based `pages/` files, when required, are thin delegators to feature pages
- [ ] Cross-boundary imports go through aliases such as `@search` or `@shared`, not deep relative paths
- [ ] Components talk to hooks, hooks talk to services, and providers are not imported directly into UI code
- [ ] Icons rendered through `Icon` or `IconButton` only — no inlined SVG markup
- [ ] Icon SVG files live in `shared/components/foundation/icons/` as standalone files
- [ ] `IconButton` always has an `aria-label`
- [ ] All props and events are typed
- [ ] Semantic HTML used — no `<div>` where a meaningful element exists
- [ ] Every landmark region has a label when multiple of the same type exist on the page
- [ ] Every interactive element has an accessible name (visible text, `aria-labelledby`, or `aria-label`)
- [ ] Every interactive element has a visible `:focus-visible` indicator
- [ ] Keyboard navigation works without a mouse
- [ ] Color contrast meets WCAG 2.1 AA minimums in both light and dark themes
- [ ] Color is not the only differentiator for any state, error, or category
- [ ] `prefers-reduced-motion` respected for all animations and transitions
- [ ] Every form field has a `<label>` with a matching `id`
- [ ] Form validation is in the service layer and is surfaced to the UI through hooks
- [ ] Submit button is disabled and loading shown during submission
- [ ] CSS Modules used — no inline styles, no utility-class stacking, no generic shared classes
- [ ] All shared values use CSS custom properties (tokens) — no hard-coded colors or sizes
- [ ] Component tokens created only when a value is shared across two or more component CSS files
- [ ] One class per element in CSS Modules (plus at most one modifier)
