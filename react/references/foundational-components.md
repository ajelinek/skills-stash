# Foundational Components

Foundational components are the building blocks of the application. They should
be consistent, reusable, accessible, and stored in `components/foundation/`.

## Preferred Pattern

Build shared primitives first, then compose them into pages and feature flows.

## Rules

- Small and single purpose
- Full accessibility compliance
- Mobile-first design
- Type-safe interfaces
- Consistent API patterns
- CSS Modules for styling
- `forwardRef` when ref forwarding is needed

## Base Props

Foundational components should extend a shared base props interface:

```ts
export type BaseComponentProps = {
  className?: string
  children?: ReactNode
}
```

This keeps `className` and composition behavior consistent across the system.

## Shared File Shape

```text
ComponentName/
├── index.tsx
└── styles.module.css
```

## Core Foundational Components

These are the primary reusable building blocks expected by the original source
material:

- Button
- Input
- AlertMessage
- Loading or LoadingSpinner
- Modal or Dialog
- Typography
- ToggleSlider or Switch
- Icon or IconButton
- NotFound or EmptyState

## Input Rules

- Extend `BaseComponentProps` plus native input props.
- Use `forwardRef<HTMLInputElement, InputProps>`.
- Use `useId()` for a generated fallback ID.
- Accept optional `id`, `label`, and `errorMessage`.
- Render a real label tied to the input with `htmlFor`.
- Set `aria-invalid` when there is an error.
- Render error text accessibly with `role="alert"`.
- Wrap label, input, and error in a consistent wrapper.
- Compose classes using CSS Module classes plus optional `className`.

See `../examples/foundational-input.tsx`.

## Button Rules

- Extend `BaseComponentProps` plus native button props.
- Use `forwardRef<HTMLButtonElement, ButtonProps>`.
- Support variants: `primary`, `secondary`, `ghost`, `danger`.
- Support sizes: `sm`, `md`, `lg`.
- Support `isBusy` and treat it as disabled.
- Preserve native button semantics through `ButtonHTMLAttributes`.
- Keep class composition predictable through base, variant, size, and optional
  custom class.

See `../examples/foundational-button.tsx`.

## Toggle And Dialog Rules

- Toggle primitives should wrap a real checkbox or button semantic.
- Use generated IDs so labels and controls stay associated.
- Dialogs should use real dialog semantics and a clear accessible title.
- Keep busy, disabled, and error handling inside shared primitives when those
  states repeat across features.

See also:

- `../examples/foundational-toggle-slider.tsx`
- `../examples/foundational-modal.tsx`
- `./accessibility-patterns.md`

## Form Integration

The original pattern expects form handling to integrate with shared form logic.

- Validation lives in the store or service layer.
- Inputs receive validation errors from service-managed state.
- Input `name` should match the form state path.
- Input `value` and `onChange` should come from the shared form hook or service
  state.
- Submit buttons often disable when the form is not dirty or is submitting.

See also:

- `./form-management.md`
- `./async-ui-states.md`
- `../examples/use-form-management.ts`
- `../examples/service-backed-form-page.tsx`

## Styling Rules

- Use CSS Modules.
- Use CSS custom properties for theming.
- Keep transitions subtle and purposeful.
- Use visible focus states.
- Ensure minimum 44px touch targets for interactive components.

## Accessibility Rules

- Semantic HTML
- ARIA only where needed
- Keyboard support
- Focus management
- Screen reader compatibility
- WCAG AA contrast
- Clear handling for error, disabled, and loading states

See also:

- `./example-gallery.md`

## Anti-Patterns

- Raw HTML controls repeated across many pages
- Feature-specific styling baked into a shared primitive
- Inconsistent prop names for the same kind of primitive
- Re-implementing busy, error, or label handling in feature code

## See Also

- `./form-management.md`
- `./async-ui-states.md`
- `./accessibility-patterns.md`
- `./example-gallery.md`
