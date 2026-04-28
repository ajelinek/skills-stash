# Form Management

Prefer shared form helpers over rebuilding controlled-form logic in each page.

## Current Preferred Pattern

The current house style is a typed `useFormManagement` style hook that owns:

- form state
- `onChange`
- `onSubmit`
- `isDirty`
- reset helpers
- optional direct state updates
- dotted-path updates for nested form data

Use this when forms are reused, nested, or backed by a service layer.

## Historical Lineage

Older code also uses a simpler flat-state shared form hook. That pattern is
still acceptable in smaller or legacy surfaces, but prefer the typed nested-path
version for new TypeScript work.

## Rules

- Keep forms controlled.
- Use foundational input primitives rather than raw inputs.
- Input `name` should match the form state path.
- Support dotted field names for nested state when the form shape warrants it.
- Keep validation in services or store-backed operations, not in presentation
  components.
- Track dirty state and use it to gate submit buttons when appropriate.
- Disable submit while the request is in flight.
- Surface field-level and form-level errors clearly.
- Reset or refocus after success only when it improves the workflow.

## Typical Hook Shape

```ts
type UseFormManagementOptions<TData> = {
  initialState: TData
  onSubmit: (data: TData) => Promise<void> | void
}

type UseFormManagementResult<TData> = {
  state: TData
  isDirty: boolean
  updateState: (path: string, value: unknown) => void
  resetState: () => void
  onChange: (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => void
  onSubmit: (event: FormEvent<HTMLFormElement>) => void
}
```

## Page Composition Pattern

- Page shells should stay thin.
- The page composes a shared form hook, service hook, and foundational
  components.
- The page should not own validation rules or external calls directly.

## See Also

- `./state-and-data.md`
- `./async-ui-states.md`
- `../examples/use-form-management.ts`
- `../examples/service-backed-form-page.tsx`

## Anti-Patterns

- One-off state handlers per field in every form
- Validation logic inside presentational inputs
- Direct API calls inside the component submit handler
- Repeating submit-disabled and busy-state logic across pages
- Unlabeled inputs
