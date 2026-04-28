# Foundational Components

Foundational components are the building blocks of the application. They should
be consistent, reusable, accessible, and stored in `components/foundation/`.

## Preferred Pattern

Build shared primitives first, then compose them into pages and feature flows.

## Rules

- Small and single purpose.
- Full accessibility compliance.
- Mobile-first design.
- Type-safe interfaces.
- Consistent API patterns.
- CSS Modules for styling; use `class` not `className`.
- No prop destructuring — access via `props.foo`.

## Shared File Shape

```text
ComponentName/
├── index.tsx
└── styles.module.css
```

## Base Props Convention

Foundational components should accept at minimum:

```ts
type BaseProps = {
  class?: string
  children?: JSX.Element
}
```

Keep `class` and `children` consistent across the system so consumers can
compose and extend without fighting the API.

## Core Foundational Components

These are the primary reusable building blocks:

- Button
- Input
- Alert (for error lists)
- LoadingSpinner
- Modal (using `Portal` from `solid-js/web`)
- Tag / TagInput
- Icon / IconButton
- EmptyState

## Button Rules

- Accept `variant`: `primary`, `secondary`, `outline`.
- Accept `size`: `small`, `medium`, `large`.
- Accept `disabled` and treat a processing state as disabled at the call site.
- Accept `type`: `button`, `submit`, `reset`; default to `button`.
- Accept `onClick` and `class`.
- Use native `<button>` semantics.

```tsx
type ButtonProps = {
  variant?: 'primary' | 'secondary' | 'outline'
  size?: 'small' | 'medium' | 'large'
  disabled?: boolean
  onClick?: () => void
  class?: string
  type?: 'button' | 'submit' | 'reset'
  children: JSX.Element
}
```

See `../examples/foundational-button.tsx`.

## Input Rules

- Accept native input attributes via JSX spread plus additional options.
- Accept `label` and render a real `<label>` tied to the input with `for`.
- Accept `errorMessage` and render it accessibly with `role="alert"`.
- Generate a fallback `id` with `createUniqueId()` from `solid-js` when none is provided. This is SSR-safe and produces a stable, per-instance id. Do not use `nanoid()` or `Math.random()` at component scope.
- Accept `class` for the input and `formGroupClass` for the wrapper.
- Set `aria-invalid` when there is an error.

```ts
type InputOptions = {
  name: string
  label?: string
  class?: string
  formGroupClass?: string
  errorMessage?: string | null
}

type InputProps = JSX.InputHTMLAttributes<HTMLInputElement> & InputOptions
```

See `../examples/foundational-input.tsx`.

## Alert Rules

- Accept `errors: ApiError[] | null`.
- Render nothing when errors is null or empty.
- Use `role="alert"` so screen readers announce errors automatically.
- Render each error message in the list.

```tsx
type AlertProps = {
  errors: ApiError[] | null
  class?: string
}
```

## Modal Rules

- Accept `isOpen`, `onClose`, `title`, `children`.
- Use `Portal` from `solid-js/web` so the modal renders outside the component
  tree and avoids stacking context problems.
- Use `<Show when={props.isOpen}>` to conditionally render.
- Apply `role="dialog"`, `aria-modal="true"`, `aria-labelledby` tied to the
  title element.
- Handle `Escape` key via `onKeyDown` on the backdrop.
- Close on backdrop click by checking `e.target === e.currentTarget`.
- Lock body scroll with `createEffect` when open; restore on `onCleanup`.

See `../examples/foundational-modal.tsx`.

## Form Integration

Foundational inputs integrate with the shared form hook and service layer:

- Validation lives in the service layer.
- Inputs receive `errorMessage` from service-managed validation state.
- Input `name` should match the form state path.
- Input `value` and `onInput` / `onChange` come from `useFormManagement`.
- Submit buttons disable when `status.isProcessing` is true.

See also:

- `./form-management.md`
- `../examples/use-form-management.ts`
- `../examples/service-backed-form-page.tsx`

## Styling Rules

- Use CSS Modules.
- Use CSS custom properties for theming.
- Keep transitions subtle and purposeful.
- Use visible focus states.
- Ensure minimum 44px touch targets for interactive components.

## Accessibility Rules

- Semantic HTML.
- ARIA only where needed.
- Keyboard support.
- Focus management for modals and dialogs.
- Screen reader compatibility.
- WCAG AA contrast.
- Clear handling for error, disabled, and loading states.

## Anti-Patterns

- Raw HTML controls repeated across many pages.
- Feature-specific styling baked into a shared primitive.
- Inconsistent prop names for the same kind of primitive.
- Re-implementing busy, error, or label handling in feature code.
- Destructuring props inside a foundational component.

## See Also

- `./form-management.md`
- `./async-ui-states.md`
- `./accessibility-patterns.md`
- `../examples/foundational-button.tsx`
- `../examples/foundational-input.tsx`
- `../examples/foundational-modal.tsx`
