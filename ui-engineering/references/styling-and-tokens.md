# Styling and Tokens Reference

CSS architecture, token strategy, theming, responsive design, and animation
rules for UI components.

---

## The Reuse Model

**Shared styles flow through CSS custom properties and foundation components.
There is no generic utility class layer.**

| Reuse need | Solution |
| --- | --- |
| A raw value used in many places (color hex, spacing unit) | Global token in `styles/tokens/` |
| A contextual value (text color, interactive color) | Semantic token in `styles/themes/` |
| A value shared across 2+ component CSS files | Component token (optional third layer) |
| A repeating visual shape (card, button, badge, input) | Foundation component in `components/foundation/` |
| Styling unique to one component | Classes in that component's `styles.module.css` |

If you are about to create a class in a shared stylesheet and apply it to
elements in multiple components, stop. The right answer is either a CSS custom
property (if it is a value) or a foundation component (if it is a shape).

---

## CSS Modules Rules

Every component has its own `styles.module.css` colocated in its directory.

```
Button/
├── index.tsx
└── styles.module.css
```

Import pattern:

```typescript
import styles from './styles.module.css'

// Usage
<button className={styles.button}>…</button>

// With a variant modifier (the only case where two classes are combined)
<button className={`${styles.button} ${styles.secondary}`}>…</button>
```

**Class structure rules:**

- **One class per element** as the default.
- **One modifier class** is permitted alongside the base class when the element
  has a meaningful variant (e.g., `button` + `secondary`, `button` + `sm`).
  This is the only case where two classes appear on one element.
- Never stack three or more classes on a single element.
- Never create classes intended to be applied from outside the component.

**Class naming — role, not appearance:**

```css
/* Good — names describe what the element is in this component */
.container {}
.header {}
.body {}
.footer {}
.actions {}
.label {}
.errorMessage {}
.icon {}

/* Bad — names describe appearance or layout primitives */
.flexRow {}
.redText {}
.mb16 {}
.textSm {}
.dFlex {}
```

**What never appears in a `styles.module.css`:**

- Generic utility classes meant to be reused by other components
- Classes that duplicate what a semantic HTML element already provides
- Classes with hard-coded color values or spacing values — use tokens
- `!important`
- ID selectors
- Complex descendant selectors (`.container .header .title span`)
- Deep nesting (keep selectors to two levels maximum)

---

## Token Architecture

### Layer 1 — Global Tokens

Raw base values defined in `:root`. These are meaningless on their own —
just named values.

```css
/* styles/tokens/_colors.css */
:root {
  --color-brand-teal: #008080;
  --color-brand-teal-light: #33a3a3;
  --color-neutral-grey900: #1a1a1a;
  --color-neutral-grey700: #404040;
  --color-neutral-grey300: #c0c0c0;
  --color-neutral-grey100: #f5f5f5;
  --color-white: #ffffff;
  --color-error-red: #d93025;
  --color-success-green: #188038;
}

/* styles/tokens/_spacing.css */
:root {
  --spacing-2xs: 0.125rem;
  --spacing-xs:  0.25rem;
  --spacing-sm:  0.5rem;
  --spacing-md:  1rem;
  --spacing-lg:  1.5rem;
  --spacing-xl:  2rem;
  --spacing-2xl: 3rem;
}

/* styles/tokens/_typography.css */
:root {
  --font-size-xs:  0.75rem;
  --font-size-sm:  0.875rem;
  --font-size-md:  1rem;
  --font-size-lg:  1.25rem;
  --font-size-xl:  1.5rem;
  --font-weight-regular: 400;
  --font-weight-medium:  500;
  --font-weight-bold:    700;
  --line-height-tight:  1.25;
  --line-height-normal: 1.5;
  --line-height-loose:  1.75;
}

/* styles/tokens/_radii.css */
:root {
  --radius-sm: 0.25rem;
  --radius-md: 0.375rem;
  --radius-lg: 0.5rem;
  --radius-full: 9999px;
}
```

### Layer 2 — Semantic Tokens

Contextual aliases that reference global tokens. These carry meaning and are
what component CSS files should consume. Defined in theme files.

```css
/* styles/themes/light.css */
:root {
  /* Text */
  --color-text-primary:   var(--color-neutral-grey900);
  --color-text-secondary: var(--color-neutral-grey700);
  --color-text-inverse:   var(--color-white);
  --color-text-disabled:  var(--color-neutral-grey300);

  /* Backgrounds */
  --color-background-page:    var(--color-neutral-grey100);
  --color-background-surface: var(--color-white);
  --color-background-subtle:  var(--color-neutral-grey100);

  /* Interactive */
  --color-interactive-primary:       var(--color-brand-teal);
  --color-interactive-primary-hover: var(--color-brand-teal-light);
  --color-interactive-primary-subtle: color-mix(in srgb, var(--color-brand-teal) 10%, transparent);

  /* Borders */
  --color-border-default: var(--color-neutral-grey300);
  --color-border-focus:   var(--color-brand-teal);

  /* Focus ring */
  --color-focus-ring: var(--color-brand-teal);

  /* Status */
  --color-status-error:         var(--color-error-red);
  --color-status-error-subtle:  color-mix(in srgb, var(--color-error-red) 10%, transparent);
  --color-status-success:       var(--color-success-green);
}

/* styles/themes/dark.css */
[data-theme='dark'] {
  --color-text-primary:          var(--color-white);
  --color-text-secondary:        var(--color-neutral-grey300);
  --color-background-page:       var(--color-neutral-grey900);
  --color-background-surface:    var(--color-neutral-grey700);
  --color-background-subtle:     var(--color-neutral-grey700);
  --color-interactive-primary:   var(--color-brand-teal-light);
  --color-border-default:        var(--color-neutral-grey700);
}
```

### Layer 3 — Component Tokens (Optional)

Create component tokens only when a value is shared across two or more separate
component CSS files. Never create them for a value used in only one component.

```css
/* styles/tokens/_card.css — created only because Card and Modal both need it */
:root {
  --card-padding: var(--spacing-md);
  --card-border-radius: var(--radius-lg);
}
```

For single-component values, use semantic or global tokens directly:

```css
/* Button/styles.module.css — component-specific values go directly here */
.button {
  min-height: 44px;                   /* specific to Button, no token needed */
  padding: var(--spacing-sm) var(--spacing-md);
  background-color: var(--color-interactive-primary);
  color: var(--color-text-inverse);
}
```

---

## Icon SVG Files

Icons live as individual `.svg` files in `components/foundation/icons/`.

**SVG authoring rules:**

- One icon per file. File name matches the icon's semantic name (`close.svg`,
  `chevron-down.svg`, `warning.svg`).
- Remove all hard-coded presentation attributes from the SVG element itself:
  no `fill`, no `stroke`, no `width`, no `height`, no `color`.
- Set `viewBox` so the icon scales correctly when `width` and `height` are
  applied by the wrapper component.
- Use `currentColor` for fill or stroke paths so the CSS `color` property
  controls icon color.

```svg
<!-- components/foundation/icons/close.svg -->
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none">
  <path
    d="M18 6L6 18M6 6l12 12"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
  />
</svg>
```

The `Icon` component applies `width`, `height`, and accessibility attributes
at render time. Never set these in the SVG file.

---

## Theming With data-theme

- Apply `data-theme` on the root `<html>` element.
- Light theme tokens live under `:root` in `light.css`.
- Dark theme overrides live under `[data-theme='dark']` in `dark.css`.
- Initialize and persist theme preference before first paint:

```typescript
function initTheme(): void {
  const saved = localStorage.getItem('theme') ?? 'light'
  document.documentElement.setAttribute('data-theme', saved)
}

function toggleTheme(): void {
  const current = document.documentElement.getAttribute('data-theme')
  const next = current === 'dark' ? 'light' : 'dark'
  document.documentElement.setAttribute('data-theme', next)
  localStorage.setItem('theme', next)
}
```

- Never reference a global token directly in a component that needs to
  theme-switch. Always use semantic tokens.
- Verify contrast ratios independently for both themes.

---

## Responsive and Mobile

- Write mobile-first styles. Add larger-viewport overrides via container queries.
- Prefer `@container` over `@media` for component-level layout changes.
  Components should not need to know the viewport width.
- Use `clamp()` for fluid typography and spacing:
  ```css
  font-size: clamp(var(--font-size-sm), 2.5vw, var(--font-size-lg));
  ```
- Use logical properties (`margin-inline`, `padding-block`) for RTL support.
- Use `rem` for font sizes and most spacing. Use `px` only for borders and
  fixed decorative elements.
- Avoid hover-only interactions — touch devices do not support hover.
- Responsive images: `srcset` + `sizes`, AVIF/WebP via `<picture>`.

---

## Layout Defaults

| Need | Use |
| --- | --- |
| Two-dimensional layout | CSS Grid |
| One-dimensional layout | Flexbox |
| Spacing between children | `gap` with a spacing token |
| Vertical stack | `display: flex; flex-direction: column; gap: var(--spacing-md)` |

Use `gap` between children of a layout container. Do not use `margin` on
children to create spacing inside a grid or flex context.

---

## Animation

Define keyframes globally in `styles/animations/`. Reference them in component
CSS files.

```css
/* styles/animations/index.css */
@keyframes fade-in {
  from { opacity: 0; }
  to   { opacity: 1; }
}

@keyframes slide-up {
  from { transform: translateY(8px); opacity: 0; }
  to   { transform: translateY(0);   opacity: 1; }
}
```

Rules:
- Keep animations subtle and purposeful.
- Use role-based names (`fade-in`, `slide-up`) not visual names (`flash-red`).
- Every animated component must include a `prefers-reduced-motion` block:

```css
@media (prefers-reduced-motion: reduce) {
  .myComponent {
    animation: none;
    transition: none;
  }
}
```

---

## Global CSS Import Order

`global.css` imports in this order:

```css
/* 1. Global token values */
@import './tokens/_colors.css';
@import './tokens/_spacing.css';
@import './tokens/_typography.css';
@import './tokens/_radii.css';

/* 2. Semantic token aliases (default theme) */
@import './themes/light.css';

/* 3. Dark theme overrides (loaded always; activated by data-theme) */
@import './themes/dark.css';

/* 4. Base element resets and typography */
/* … reset rules … */

/* 5. Animation keyframes */
@import './animations/index.css';
```

---

## Anti-Patterns

| Anti-pattern | Why | Fix |
| --- | --- | --- |
| Generic class in a shared stylesheet (`.card`, `.flex-row`, `.text-sm`) | Creates invisible coupling; bypasses component boundaries | Create a foundation component or use a CSS variable |
| Hard-coded color or size in component CSS | Breaks theming and consistency | Use a semantic token via `var(--…)` |
| Inlining SVG markup in component templates | Duplicates icons, bypasses the icon system | Import through `Icon` or `IconButton` |
| Three or more classes on one element | Utility-class creep | One base class plus at most one modifier |
| ID selectors for styling | High specificity, impossible to override cleanly | Use a class in the component's CSS Module |
| `!important` | Breaks cascade; masks the real problem | Fix specificity at the source |
| Deep selector nesting | Fragile, unreadable | Keep selectors flat (max two levels) |
| Media queries for component layout | Components should not know about viewport width | Use container queries |
