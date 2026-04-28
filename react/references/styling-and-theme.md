# Styling And Theme

## Preferred Pattern

Use CSS Modules with semantic tokens and keep component CSS flat and local.

## CSS Modules

Use CSS Modules for all component styling.

Component files should follow this structure:

```text
ComponentName/
├── index.tsx
└── styles.module.css
```

Import styles as:

```ts
import s from './styles.module.css'
```

## Global vs Component Styles

### Global styles

- design tokens and theme variables
- base element styles
- animation definitions
- resets and normalization

### Component styles

- component-specific styles only
- exactly one class name per element
- optional single modifier class only when necessary
- semantic or global tokens used directly in component CSS

## Token System

Use the original two-layer token architecture, with optional component tokens.

### Global tokens

- base colors
- spacing
- typography
- radii

### Semantic tokens

- usage-specific tokens such as text, surface, border, and interactive colors

### Component tokens

Only create component tokens when a value is reused across multiple component
CSS files.

If a value is used in one component only, keep it directly in that component's
CSS.

## Styling Rules

### Do

- Use CSS custom properties for all design tokens
- Use semantic HTML
- Keep selectors flat
- Use Flexbox for one-dimensional layout
- Use Grid for two-dimensional layout
- Use logical properties where appropriate
- Define animations globally and reference them from components
- Implement visible focus states

### Do Not

- Use inline styles
- Use utility-class stacking
- Use complex selectors
- Use deep nesting
- Use ID selectors for styling
- Use component tokens for single-component values

## Theme Rules

- Use `data-theme` on the `<html>` element for theme switching.
- Define theme-specific CSS custom properties in theme files.
- Store theme preference in `localStorage`.
- Use semantic color tokens, not direct color values, in component CSS.
- Initialize the theme on page load.
- Provide a theme toggle in the UI.

Basic flow:

1. Read saved theme from `localStorage`
2. Apply it to `document.documentElement`
3. Persist explicit user changes back to `localStorage`

See `../examples/theme-toggle.tsx`.

## Responsive Rules

- Mobile-first styles
- 44x44 minimum touch targets
- Avoid hover-only interactions
- Respect reduced motion
- Keep contrast and zoom usability intact in every theme

See also:

- `./foundational-components.md`
- `./accessibility-patterns.md`
- `./example-gallery.md`

## Anti-Patterns

- Utility-class stacking in component markup
- Inline styles for normal component layout or theming
- Deep selectors that depend on markup internals
- Direct color literals in component CSS when semantic tokens exist
