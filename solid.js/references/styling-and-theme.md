# Styling And Theme

## Core Rules

- Use CSS Modules for all component styling.
- Use `class` (not `className`) in SolidJS JSX.
- Use CSS custom properties for theme tokens.
- Use semantic HTML and semantic class names.
- No inline styles.
- No utility-class stacking.
- No complex selectors or deep nesting.

## File Layout

Each component lives in its own directory:

```text
ComponentName/
├── index.tsx
└── styles.module.css
```

Import the module and apply classes:

```tsx
import styles from './styles.module.css'

// Single class
<div class={styles.container}>...</div>

// Conditional class
<button class={`${styles.button} ${props.variant ? styles[props.variant] : ''}`}>
```

## CSS Modules Pattern

```css
/* styles.module.css */
.container {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.button {
  min-height: 44px;
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-sm);
  font-size: var(--text-base);
}

.primary {
  background-color: var(--color-primary);
  color: var(--color-primary-foreground);
}

.secondary {
  background-color: var(--color-secondary);
  color: var(--color-secondary-foreground);
}
```

## Token Strategy

- Use semantic or global tokens directly in component CSS.
- Only create component-level CSS custom properties when a value is reused
  across multiple component CSS files.
- Tokens should be defined at the root or layout level; components consume them.

Common token categories:

- Colors: `--color-primary`, `--color-secondary`, `--color-background`,
  `--color-foreground`, `--color-error`, `--color-success`
- Spacing: `--spacing-xs`, `--spacing-sm`, `--spacing-md`, `--spacing-lg`,
  `--spacing-xl`
- Typography: `--text-sm`, `--text-base`, `--text-lg`, `--text-xl`,
  `--font-weight-normal`, `--font-weight-bold`
- Radius: `--radius-sm`, `--radius-md`, `--radius-lg`
- Shadows: `--shadow-sm`, `--shadow-md`

## Theming With `data-theme`

Use the `data-theme` attribute on `<html>` or a layout wrapper to switch
between light and dark themes:

```css
:root {
  --color-background: #ffffff;
  --color-foreground: #1a1a1a;
}

[data-theme='dark'] {
  --color-background: #1a1a1a;
  --color-foreground: #ffffff;
}
```

Read and write the theme using `localStorage`:

```ts
// Read on mount
const stored = localStorage.getItem('theme') as 'light' | 'dark' | null
document.documentElement.setAttribute('data-theme', stored ?? 'light')

// Toggle
function toggleTheme() {
  const next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark'
  document.documentElement.setAttribute('data-theme', next)
  localStorage.setItem('theme', next)
}
```

## Responsive Styling

- Use mobile-first breakpoints.
- Use CSS custom properties and grid/flex for layout.
- Avoid JavaScript-driven layout; prefer CSS media queries.

```css
.grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--spacing-md);
}

@media (min-width: 768px) {
  .grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
```

## Anti-Patterns

- Inline styles (`style="color: red"`).
- `className` instead of `class` in SolidJS JSX.
- Deep selectors (`.card .header .title span`).
- Hard-coded color or spacing values instead of tokens.
- Utility-class stacking (Tailwind-style without a tailwind setup).
- Global styles in component files.
