# Form Management

Prefer shared form helpers over rebuilding controlled-form logic in each page.

## Preferred Pattern

Use the typed `useFormManagement` hook that owns:

- form state via `createStore` from `solid-js/store`
- `onChange` — path-sets into store state by reading `e.currentTarget.name`
- `onSubmit` — prevents default and calls the submit callback with unwrapped state
- `isDirty` — `createMemo` comparing current state against initial using deep equality
- `updateState` — merges a partial state object
- `resetFormToInitialState` — resets to original initial state
- `resetFormToNew` — replaces both initial and current state atomically
- `setField` — sets a single key directly

Use this whenever forms are backed by a service layer, are reused, or have
nested data shapes.

## Rules

- Keep forms controlled.
- Use foundational input primitives — never raw `<input>` or `<button>` in page
  components.
- Input `name` must match the form state path. For nested paths, use dot notation
  (`e.g. "address.city"`).
- Keep validation in the service layer, not in presentation components.
- Track dirty state and use it to gate submit buttons when appropriate.
- Disable submit while the operation is processing (`status.isProcessing`).
- Surface field-level and form-level errors clearly via the `Alert` primitive.
- Reset or refocus after success only when it improves the workflow.

## Hook Shape

```ts
function useFormManagement<Data>(
  initialState: Data,
  formSubmitCb: (data: Data) => void | Promise<void>,
): {
  state: Data                                    // reactive store state
  isDirty: Accessor<boolean>                     // createMemo
  onChange: (e: SolidOnChange) => void           // path-sets by name attribute
  onSubmit: (e: SolidFormSubmit) => void         // prevents default, calls cb
  updateState: (updated: Partial<Data>) => Data  // partial merge
  resetFormToInitialState: () => void
  resetFormToNew: (state: Data) => void          // atomic batch reset
  setField: <K extends keyof Data>(key: K, value: Data[K]) => void
}
```

The form state is a reactive SolidJS store. Reading `form.state.fieldName`
inside JSX is reactive automatically.

## Typical Usage

```tsx
const form = useFormManagement<FormData>(
  { title: '', description: '' },
  async (data) => {
    await myOperation.execute(data)
  },
)

return (
  <form onSubmit={form.onSubmit}>
    <Input name="title" label="Title" value={form.state.title} onInput={form.onChange} />
    <Button type="submit" disabled={myOperation.status.isProcessing}>
      {myOperation.status.isProcessing ? 'Saving...' : 'Save'}
    </Button>
  </form>
)
```

## Dot-Path Nested Fields

`onChange` splits `e.currentTarget.name` on `.` and path-sets into the store:

```tsx
// For a form with state: { address: { city: '' } }
<Input name="address.city" value={form.state.address.city} onInput={form.onChange} />
```

For fields that cannot use the name attribute (rich text, custom selects, etc.),
use `form.setField`:

```tsx
<RichTextEditor
  value={form.state.description}
  onChange={(val) => form.setField('description', val)}
/>
```

## Page Composition Pattern

- Page shells should stay thin.
- The page composes the form hook, a service mutation hook, and foundational
  components.
- The page must not own validation rules or make direct external calls.

```tsx
export default function MyPage() {
  const op = useMyOperation()
  const form = useFormManagement<MyData>(initialData, async (data) => {
    await op.execute(data)
  })

  return (
    <form onSubmit={form.onSubmit}>
      <Alert errors={op.errors} />
      <Input name="title" label="Title" value={form.state.title} onInput={form.onChange} />
      <Button type="submit" disabled={op.status.isProcessing}>Save</Button>
    </form>
  )
}
```

## See Also

- `./state-and-data.md`
- `./async-ui-states.md`
- `../examples/use-form-management.ts`
- `../examples/service-backed-form-page.tsx`

## Anti-Patterns

- One-off `createSignal` per field in every form.
- Validation logic inside presentational inputs.
- Direct service or repository calls inside the component submit handler.
- Repeating submit-disabled and busy-state logic across pages.
- Unlabeled inputs.
- Destructuring form state: `const { title } = form.state` — breaks reactivity.
