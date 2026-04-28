# Async UI States

Async UI should be explicit, accessible, and mostly standardized through shared
primitives and SolidJS control flow.

## Preferred Pattern

Use explicit state branches via SolidJS `<Show>` and `<Switch>/<Match>` at page
level, and shared primitives for repeated busy, loading, and error behavior.

## Preferred Branching

At page level, prefer explicit branches for:

- loading
- empty
- error
- content

Use `<Switch>/<Match>` when the branches are mutually exclusive:

```tsx
<Switch fallback={<NotFound />}>
  <Match when={data.status.isProcessing}>
    <LoadingSpinner />
  </Match>
  <Match when={data.status.isError}>
    <Alert errors={data.errors} />
  </Match>
  <Match when={data.status.isSuccess && !data.data}>
    <EmptyState message="No items found." />
  </Match>
  <Match when={data.status.isSuccess}>
    <ContentView data={data.data!} />
  </Match>
</Switch>
```

## Primitive-Level Rules

- Put repeated busy and disabled behavior into shared buttons and inputs.
- Use `LoadingSpinner` for overlays and inline loading states.
- Use the `Alert` primitive for action errors — feed it `op.errors`.
- Disable buttons during processing using `op.status.isProcessing`.

## Page-Level Rules

- Keep branching near the top of the page component.
- Use `<Show when={...} fallback={...}>` for simple two-state toggles.
- Use `<Switch>/<Match>` for multi-state branches.
- Use explicit empty states instead of blank containers.
- Render content branches only when required data is ready.

## Reacting To Success

Use `createEffect` to respond to `status.isSuccess` after a mutation:

```tsx
createEffect(() => {
  if (op.status.isSuccess) {
    window.location.href = '/next-page'
  }
})
```

After successful async actions, prefer one of:

- Reset the form for repeated entry.
- Redirect to the next logical route.
- Show a clear success message when staying on the page.

Choose one intentionally. Do not stack multiple success behaviors.

## Error Handling

- Surface structured errors from service operations through the `Alert`
  foundational component.
- Do not log errors only to the console — surface them in the UI.
- Field-level errors can be passed as `errorMessage` to input primitives.

```tsx
<Alert errors={op.errors} />
<Input
  name="email"
  label="Email"
  value={form.state.email}
  onInput={form.onChange}
  errorMessage={fieldError('email', op.errors)}
/>
```

## Accessibility Rules

- Loading regions should use `role="status"` when announcing progress.
- Errors rendered by `Alert` should use `role="alert"` so they are announced
  automatically.
- Busy buttons should be `disabled` during processing.
- Empty states should still use meaningful headings and actions.

## See Also

- `./accessibility-patterns.md`
- `./foundational-components.md`
- `./form-management.md`
- `../examples/service-backed-form-page.tsx`

## Anti-Patterns

- Hiding errors in console logs only.
- Rendering loading UI with no accessible announcement.
- Leaving submit buttons active during mutations.
- Mixing stale content and loading state without clear intent.
- Using generic spinners where an empty or error state is more accurate.
- Using bare JS ternaries or `.map()` instead of `<Show>` / `<For>`.
