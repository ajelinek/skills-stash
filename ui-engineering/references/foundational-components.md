# Foundational Components

Design and implementation rules for shared foundation UI primitives.
These rules apply regardless of framework. Framework-specific examples live in
the `react` and `solid.js` skills.

---

## Purpose

Foundation components are the lowest-level building blocks of the UI. They are:

- Shared across all features and pages — never feature-specific
- Accessible by default — ARIA and keyboard behavior built in
- Strongly typed
- Styled with CSS Modules and CSS custom properties only
- The canonical source of reusable UI shapes

Every component lives in `components/foundation/` under its own directory.
When a UI pattern appears in two or more feature components, it moves to
foundation immediately.

**There are no generic shared CSS classes.** Reuse happens through these
components and through CSS custom properties (tokens). If you need a "card",
create a `Card` component. If you need a shared color, use a semantic token.

---

## Directory Layout

```
components/foundation/
├── icons/                  # Standalone SVG files — one per icon
│   ├── close.svg
│   ├── chevron-down.svg
│   ├── check.svg
│   ├── warning.svg
│   ├── search.svg
│   └── …
├── Icon/
│   ├── index.tsx           # Renders SVG from icons/ with size + a11y props
│   └── styles.module.css
├── IconButton/
│   ├── index.tsx           # Button that wraps Icon; always requires aria-label
│   └── styles.module.css
├── Button/
│   ├── index.tsx
│   └── styles.module.css
├── Input/
│   ├── index.tsx
│   └── styles.module.css
├── Alert/
│   ├── index.tsx
│   └── styles.module.css
├── Dialog/
│   ├── index.tsx
│   └── styles.module.css
├── Dropdown/
│   ├── index.tsx
│   └── styles.module.css
├── Loading/
│   ├── index.tsx
│   └── styles.module.css
├── List/
│   ├── index.tsx
│   └── styles.module.css
└── Table/
    ├── index.tsx
    └── styles.module.css
```

---

## Icon SVG Files

All icons live as individual `.svg` files in `components/foundation/icons/`.

**SVG file rules:**

- One icon per file.
- File name is the icon's semantic name in kebab-case: `close.svg`,
  `chevron-down.svg`, `warning-triangle.svg`.
- Remove all hard-coded presentation attributes from the SVG root: no `fill`,
  no `stroke`, no `width`, no `height`, no `color` on the `<svg>` element.
- Always include a `viewBox` attribute so the icon scales correctly.
- Use `currentColor` for `fill` or `stroke` on path elements so that the CSS
  `color` property controls icon color from outside.
- Do not add `<title>` or `<desc>` inside the SVG — accessibility labeling is
  the responsibility of the `Icon` or `IconButton` wrapper component.

```svg
<!-- components/foundation/icons/close.svg -->
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none">
  <path
    d="M18 6L6 18M6 6l12 12"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
    stroke-linejoin="round"
  />
</svg>
```

**Never inline SVG markup directly in a component template.** Import icons
through the `Icon` or `IconButton` foundation component only.

---

## BaseProps Convention

All foundation components extend a shared `BaseProps` interface:

```typescript
type BaseProps = {
  className?: string
  id?: string
  'aria-label'?: string
  'aria-labelledby'?: string
  'aria-describedby'?: string
}
```

Do not repeat these fields in every component's own `Props` type. Extend or
intersect `BaseProps` instead.

---

## Required API Conventions

Use consistent prop names across all foundation components:

| Prop | Type | Purpose |
| --- | --- | --- |
| `variant` | `'primary' \| 'secondary' \| 'danger' \| 'ghost'` | Visual style variant |
| `size` | `'sm' \| 'md' \| 'lg'` | Size modifier |
| `label` | `string` | Accessible or visible label text |
| `errorMessage` | `string` | Validation error for input-type components |
| `isDisabled` | `boolean` | Controlled disabled state |
| `isLoading` | `boolean` | Busy or loading state |
| `className` | `string` | Additional CSS class from the consumer |
| `children` | framework child type | Slot for nested content |

Wrap interactive native elements with `forwardRef` (React) or expose `ref`
(Solid) so consumers can attach refs when needed.

---

## Component Catalog

### Icon

Responsibilities: renders a named SVG icon from `icons/` with correct size,
color, and accessibility attributes.

Props:

| Prop | Required | Purpose |
| --- | --- | --- |
| `name` | yes | Maps to a file in `components/foundation/icons/` |
| `size` | no | Applies `width` and `height` via a token value |
| `aria-hidden` | no | Pass `true` when icon is decorative |
| `aria-label` | no | Pass when icon is meaningful and has no sibling text |

Rules:
- Decorative icons (used alongside visible text): always `aria-hidden="true"`.
- Meaningful standalone icons: requires `aria-label` on the `Icon` element
  itself, or `aria-label` on the parent interactive element.
- Never hard-code `width` or `height` as numbers — map `size` to a CSS
  custom property or token value.
- Apply `color: inherit` by default so the icon inherits the surrounding text
  color; let consumers override via CSS.

```tsx
// Decorative — text label present
<Icon name="check" aria-hidden="true" size="md" />
<span>Saved</span>

// Meaningful standalone icon — no sibling text
<Icon name="warning" aria-label="Warning" size="md" />
```

---

### IconButton

Responsibilities: icon-only interactive actions. A button that wraps `Icon`.

Rules:
- **Always requires `aria-label`**. There is no visible text, so the
  accessible name must come from `aria-label`.
- Use `<button type="button">` by default.
- Pass `aria-hidden="true"` to the inner `Icon` — the button's `aria-label`
  provides the accessible name for the whole control.
- Minimum 44×44px touch target.
- Show a visible `:focus-visible` indicator.
- Support `isDisabled` and `isLoading` states.

```tsx
<IconButton aria-label="Close dialog" onPress={onClose}>
  <Icon name="close" aria-hidden="true" size="md" />
</IconButton>
```

---

### Button

Responsibilities: text actions and form submission.

Rules:
- Use `<button type="button">` by default; `type="submit"` only inside a
  `<form>`.
- When `isLoading` is true: disable the button, show a loading indicator
  inside the button, and update the accessible label to indicate activity
  (e.g., `aria-label="Saving…"` or `aria-busy="true"`).
- When `isDisabled` is true: set both `disabled` and `aria-disabled="true"`.
- Minimum 44px height for all variants.
- Text content provides the accessible name — no `aria-label` needed when
  button text is meaningful.
- Icon + text buttons: icon is `aria-hidden="true"`, text provides the name.

---

### Input

Responsibilities: text, email, password, number, and search fields.

Rules:
- Always render a visible `<label>` with a `for` attribute matching the
  input's `id`.
- Generate a unique `id` for every input instance — do not use static IDs.
- Accept `errorMessage` prop; when present:
  - Set `aria-invalid="true"` on the `<input>`
  - Associate the error via `aria-describedby` pointing to the error element
  - Render the error message with `role="alert"` so it is announced
- Use the appropriate HTML5 `type` attribute for every usage.
- Add `autocomplete` attributes where they improve UX.
- Never use `placeholder` as a substitute for a `<label>`.

```html
<label for="email-abc123">Email address</label>
<input
  id="email-abc123"
  type="email"
  autocomplete="email"
  aria-invalid="true"
  aria-describedby="email-abc123-error"
/>
<span id="email-abc123-error" role="alert">
  Enter a valid email address.
</span>
```

---

### Alert

Responsibilities: feedback messages, inline errors, success confirmations,
warnings.

Rules:
- Use `role="alert"` for urgent messages that must be announced immediately
  by screen readers (errors, destructive confirmations).
- Use `role="status"` for non-urgent updates (saved successfully, item added).
- Use `aria-live="polite"` for notifications that should not interrupt.
- Support `variant` of `error`, `warning`, `success`, `info`.
- Never use `aria-live="assertive"` for progress or loading states.
- Pair color with an icon and text — never rely on color alone.

---

### Dialog

Responsibilities: modal overlays and popups requiring user interaction.

Rules:
- Use native `<dialog>` element.
- Set `aria-labelledby` pointing to the dialog's visible title element.
- Trap focus inside the dialog while open.
- Return focus to the trigger element on close.
- Close on Escape key.
- Close on backdrop click only for non-destructive dialogs (confirmation
  dialogs should require an explicit button press).
- The dialog title should be an `<h2>` inside the dialog.

```html
<dialog aria-labelledby="confirm-dialog-title">
  <h2 id="confirm-dialog-title">Confirm deletion</h2>
  <p>This action cannot be undone.</p>
  <div>
    <button type="button">Cancel</button>
    <button type="button">Delete</button>
  </div>
</dialog>
```

---

### Dropdown

Responsibilities: selection menus and contextual action menus.

Rules:
- Manage open/closed state internally.
- Close on outside click and on Escape.
- Support keyboard navigation within the list: arrow keys move between items,
  Enter selects, Escape closes.
- Use `role="listbox"` + `role="option"` for selection menus.
- Use `role="menu"` + `role="menuitem"` for action menus.
- The trigger button must have `aria-haspopup` and `aria-expanded`.

```html
<button
  type="button"
  aria-haspopup="listbox"
  aria-expanded="true"
  aria-controls="sort-listbox"
>
  Sort by: Newest
</button>
<ul id="sort-listbox" role="listbox" aria-label="Sort options">
  <li role="option" aria-selected="true">Newest</li>
  <li role="option" aria-selected="false">Oldest</li>
</ul>
```

---

### Loading

Responsibilities: spinners and skeleton states for async content.

Rules:
- Use `role="status"` and `aria-label="Loading"` on the spinner container.
- Skeleton states must match the layout dimensions of the content they replace.
- Respect `prefers-reduced-motion` — reduce or disable spinner animation.
- Remove the loading element from the DOM (or hide it) when content is ready,
  and announce completion via a live region if the user needs to know.

---

### List

Responsibilities: ordered and unordered data display.

Rules:
- Use `<ul>` + `<li>` for unordered data.
- Use `<ol>` + `<li>` for ordered or sequential data.
- Never render lists as `<div>` grids.
- Support an empty state via a prop or slot — render a meaningful empty message,
  not nothing.
- Add `aria-label` to the list element when its purpose is not clear from
  surrounding context.

---

### Table

Responsibilities: tabular data grids.

Rules:
- Use `<table>`, `<thead>`, `<tbody>`, `<tr>`, `<th>`, `<td>`.
- All `<th>` elements must have `scope="col"` or `scope="row"`.
- Provide a caption via `<caption>` or `aria-label` on the `<table>` element.
- Sortable columns: add `aria-sort="ascending"`, `aria-sort="descending"`, or
  `aria-sort="none"` to the column `<th>`.
- Do not use a table for layout — only for genuinely tabular data.

---

## Anti-Patterns

| Anti-pattern | Fix |
| --- | --- |
| Re-implementing a foundation primitive inline in a page or feature | Check `components/foundation/` first; extend what exists |
| Forking a component to add a variant | Add the variant prop to the existing component |
| Inlining SVG markup directly in a template | Import through `Icon` or `IconButton` only |
| `IconButton` without `aria-label` | Always required — there is no visible text |
| Using `Button` for icon-only actions | Use `IconButton` instead |
| Leaking business logic into a foundation component | Validation, data fetching, and mutations belong in services |
| Re-implementing error message rendering in page components | Put `errorMessage` rendering inside the foundation primitive |
| Applying generic shared CSS classes to foundation elements | Use CSS custom properties for shared values; use components for shared shapes |
