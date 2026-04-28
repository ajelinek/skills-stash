# Component Structure

## Preferred Pattern

Use this default component shape and keep pages thin.

## File Structure

Use this default component shape:

```text
PascalCase/
├── index.tsx
└── styles.module.css
```

For foundational components, place them under `components/foundation/`.

## Component Definition

- The main component file is `index.tsx`.
- Use typed props.
- Destructure props in the function signature.
- Keep the implementation directly readable.
- Prefer named exports for normal components.
- Use `forwardRef` for shared interactive primitives that need ref access.

Basic pattern:

```tsx
import s from './styles.module.css'
import type { ExampleProps } from './types'

export function Example({ title }: ExampleProps) {
  return <div className={s.container}>{title}</div>
}
```

## Rules

- Keep components small and single purpose.
- Leverage foundational components as building blocks.
- Use semantic HTML instead of generic wrappers when possible.
- Ensure interactive elements have accessible names.
- Keep component trees as flat as practical.
- Use variables or helpers for complex JSX logic.

## Hooks And Control Flow

- Use `useState` for component-local state.
- Use `useMemo` for expensive derived values when justified.
- Use `useEffect` for side effects with proper dependencies and cleanup.
- Use `&&`, simple ternaries, and `.map()` for render control flow.
- Prefer thin page shells that compose shared forms, services, and foundational
  primitives.

See also:

- `./route-and-auth-composition.md`
- `../examples/service-backed-form-page.tsx`
- `../examples/auth-form-shell.tsx`

## Anti-Patterns

- Prop drilling through multiple layers
- Declaring components inside components
- Overusing `useMemo` or `useCallback`
- Overusing Context for complex global state
- Putting too much logic in one component
- Inline styles
- Untyped props or event handlers
- Complex JSX logic inline

## See Also

- `./foundational-components.md`
- `./route-and-auth-composition.md`
- `../examples/service-backed-form-page.tsx`
- `../examples/auth-form-shell.tsx`
