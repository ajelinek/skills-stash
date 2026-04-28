# Styling And CSS Modules

All Astro component, layout, and page styling uses CSS Modules in a separate
`styles.module.css` file. Styles are never written inside the Astro `<style>` block.

---

## The Rule

```
ComponentName/
├── index.astro         ← markup and logic only
└── styles.module.css   ← ALL styles for this component
```

**Every** component directory must have a `styles.module.css`. If a component
needs no styles today, create the file anyway so the convention is maintained
and the addition of styles later is a one-step change.

Import the module in the frontmatter fence:

```astro
---
import styles from './styles.module.css'
---
```

Apply classes in markup:

```astro
<!-- single class -->
<div class={styles.container}>

<!-- conditional classes -->
<div class:list={[styles.card, isActive && styles.active]}>

<!-- multiple non-conditional classes (rare) -->
<div class={`${styles.base} ${styles.variant}`}>
```

---

## Why Not Astro `<style>` Blocks

Astro ships with a scoped `<style>` block that co-locates CSS with markup. This
project does not use it because:

- CSS Modules in a separate file keeps markup files smaller and easier to scan.
- Separate files make the CSS independently searchable, reviewable, and editable.
- The pattern is consistent with the SolidJS and React island components that live
  alongside `.astro` files — one convention across all components in the project.
- IDE tooling for CSS Modules (autocomplete, go-to-definition) works reliably on
  standalone `.css` files.

---

## Token Strategy

Use CSS custom properties for all design tokens. Do not hard-code color, spacing,
or typography values.

**Global tokens** — raw values defined in `styles/tokens/`:

```css
/* styles/tokens/_colors.css */
:root {
  --color-brand-teal: #008080;
  --color-neutral-grey900: #1a1a1a;
}
```

**Semantic tokens** — contextual aliases defined in `styles/global.css` or theme files:

```css
/* styles/global.css */
:root {
  --color-text-primary: var(--color-neutral-grey900);
  --color-interactive-primary: var(--color-brand-teal);
}
```

**Component CSS** — reference semantic tokens directly. Do not create
component-level token files unless a value is shared across two or more
component CSS files.

```css
/* Button/styles.module.css */
.button {
  padding: var(--spacing-sm) var(--spacing-md);
  background-color: var(--color-interactive-primary);
  color: var(--color-text-inverse);
  min-height: 44px;
}
```

Component-specific values (e.g., `min-height`, `border-radius`) belong directly
in the component's CSS file. Only extract to a token when the value is reused
across multiple component CSS files.

---

## Global Style Organization

```
src/styles/
├── tokens/
│   ├── _colors.css
│   ├── _spacing.css
│   ├── _typography.css
│   └── _breakpoints.css   (use sparingly — prefer container queries)
├── animations/
│   ├── _fade.css
│   ├── _slide.css
│   └── index.css
├── global.css              ← reset, base element styles, semantic token definitions
└── themes/
    ├── light.css
    └── dark.css
```

Import `global.css` once in your root layout. Token files are imported by
`global.css`, not individually from components.

---

## CSS Writing Rules

**Do:**

- Use CSS custom properties for every design token.
- One class per element in normal usage. One optional modifier class when needed.
- Use logical properties (`inline`, `block`, `inline-start`, etc.) for RTL and
  responsive support.
- Use CSS Grid for two-dimensional layout; Flexbox for one-dimensional.
- Define animations globally in `styles/animations/`; reference them in components.
- Keep selectors flat (maximum two levels of nesting).
- Use container queries for layout-responsive components.
- Fluid typography and spacing with `clamp()` and tokens.

**Do not:**

- Do not use `!important` (only accepted in base utility-reset edge cases).
- Do not use complex selectors (`div > span > a`).
- Do not use ID selectors for styling.
- Do not use inline `style` attributes.
- Do not stack multiple utility classes on an element.
- Do not use fixed `px` units for typography or spacing (use `rem`).
- Do not use viewport media queries for layout when container queries apply.
- Do not add component-level token files unless a token is shared across
  multiple component CSS files.

---

## Theming

Themes are implemented via `data-theme` attribute and separate theme CSS files.
Token definitions in `themes/light.css` and `themes/dark.css` override semantic
tokens by scoping them to the `[data-theme]` selector.

```css
/* themes/dark.css */
[data-theme='dark'] {
  --color-text-primary: var(--color-neutral-grey100);
  --color-background-page: var(--color-neutral-grey900);
}
```

Set the attribute at the document root:

```astro
<!-- BaseLayout/index.astro -->
<html data-theme="light">
```

Components reference semantic tokens only — they are automatically themed.

---

## Animation

1. Define animations in `styles/animations/` with semantic names (`fade-in`, `slide-up`).
2. Reference them by name in component CSS files.
3. Keep animations subtle and purposeful.
4. Always respect reduced motion:

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

This rule belongs in `styles/global.css`.

---

## Responsive And Mobile

- Mobile-first: write base styles for small viewports, enhance for larger.
- Use container queries (`@container`) for layout — prefer over viewport media queries.
- Fluid typography and spacing using `clamp()` with token values.
- Touch targets: minimum 44×44 logical pixels.
- Provide hover alternatives for touch; never rely on hover-only interactions.
- Use `srcset` and `sizes` for responsive images; prefer AVIF/WebP.
