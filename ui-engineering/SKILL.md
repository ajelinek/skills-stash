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

## When To Use This Skill

- Designing or auditing component boundaries and composition rules
- Building or evaluating a foundation component library
- Applying accessibility requirements (WCAG 2.1 AA) to new components or forms
- Choosing a CSS architecture, token strategy, or theming approach
- Setting up a project's directory structure for UI code
- Deciding how to manage form state, validation, and submission UX
- Establishing cross-team or cross-project UI conventions in TypeScript

## When Not To Use This Skill

When you need framework-specific implementation guidance, reach for the
framework skill first and treat this skill as the shared baseline underneath it:

- React components and hooks → `react` skill
- Solid components and stores → `solid.js` skill
- Astro pages and islands → `astro.js` skill

---

## Core Rules

### 1. Foundation Components First

Build and consume a shared foundation layer before writing any button, input,
dialog, alert, icon, or loading state in a feature component.

Decision order:

1. **Primitive exists** — use it. Never re-implement it inline.
2. **Primitive is close but missing a variant or prop** — extend it. Do not
   fork it or work around it at the call site.
3. **Primitive does not exist** — create it in `components/foundation/` before
   using it anywhere. Never inline a one-off UI primitive in a page or feature
   component.

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
`components/foundation/icons/`. Each file contains one optimized icon with no
hard-coded presentation attributes:

```
components/foundation/
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

### 2. Component Shape

- Type all props explicitly — no untyped components or props.
- Keep components small and single-purpose.
- Keep JSX logic simple; move complex logic into variables or helper functions
  before the return statement.
- Components handle presentation only. Business logic, validation, and external
  calls belong in stores, services, or repositories.
- No prop drilling past one level. Use composition, context, or state management
  instead.
- No inline `style` attributes.
- No direct DOM manipulation.
- Lazy-load large or infrequently used components.
- Implement proper cleanup for side effects.

File layout for each component:

```
ComponentName/
├── index.tsx            # Main component logic and view
└── styles.module.css    # CSS Modules for component-scoped styles
```

Use `default export` for the component name from `index.tsx`.

---

### 3. Semantic HTML

Use the most specific HTML element that describes the content or role. The
full element reference table is in the Accessibility section below — semantic
HTML and ARIA are inseparable, so they are documented together.

Key rule: `<div>` and `<span>` are last-resort containers. If a semantic
element exists for the purpose, use it. Never use a `<div>` with a `role`
when the native element already carries that role implicitly.

---

### 4. Accessibility (WCAG 2.1 AA)

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

### 5. CSS Architecture

**The reuse model has two and only two layers: CSS custom properties and
foundation components. There is no third layer of generic utility classes.**

Shared styles flow through the codebase in exactly this way:

1. **CSS custom properties (variables)** — define any value that needs to be
   shared across components (colors, spacing, radii, typography, shadows).
   Consumed directly in component CSS files via `var(--token-name)`.
2. **Foundation components** — any repeated UI pattern becomes a component in
   `components/foundation/`. Consumers reuse the component, not the CSS class.

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
| Is it a recurring UI shape (button, card, input, badge)? | Foundation component in `components/foundation/` |
| Is it component-specific styling (layout, spacing inside one component)? | In that component's `styles.module.css` using tokens |
| Is it a page-level or feature-level layout? | In that page/feature component's `styles.module.css` |

**Icons:**

- All icons live as individual `.svg` files in
  `components/foundation/icons/`.
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

### 6. Form UX

Forms enforce consistent UX patterns across all UI implementations.

**Labels and inputs:**
- Every input must have a visible `<label>`.
- Use a generated unique ID to tie each label and input together.
- Use the appropriate HTML5 `type` for every input.
- Use foundation input components — never raw `<input>` or `<button>` in
  feature or page components.
- Ensure screen reader compatibility and keyboard focus management.

**Validation:**
- Form validation runs in the store or service layer, not in presentation
  components.
- Components receive validation errors as props from service operations.
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

### 7. Project Directory Structure

Organize UI source code into stable zones that separate building blocks from
features and pages.

```
src/
├── components/
│   ├── foundation/         # Reusable UI primitives (Button, Input, Alert…)
│   ├── layout/             # Header, Footer, Sidebar, page shells
│   └── features/           # Feature-scoped components (Auth, Dashboard…)
├── pages/                  # Route-level page components
├── styles/                 # Global tokens, themes, animations
├── hooks/ or composables/  # Shared logic hooks
└── services/               # Business logic, data access, state management
```

Foundation components are never feature-specific. When a UI pattern appears in
two or more feature components, move it to `components/foundation/` immediately.

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
- [ ] Icons rendered through `Icon` or `IconButton` only — no inlined SVG markup
- [ ] Icon SVG files live in `components/foundation/icons/` as standalone files
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
- [ ] Form validation is in the service layer, not the component
- [ ] Submit button is disabled and loading shown during submission
- [ ] CSS Modules used — no inline styles, no utility-class stacking, no generic shared classes
- [ ] All shared values use CSS custom properties (tokens) — no hard-coded colors or sizes
- [ ] Component tokens created only when a value is shared across two or more component CSS files
- [ ] One class per element in CSS Modules (plus at most one modifier)
