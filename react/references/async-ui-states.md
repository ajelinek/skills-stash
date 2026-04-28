# Async UI States

Async UI should be explicit, accessible, and mostly standardized through shared
primitives.

## Preferred Pattern

Use explicit state branches in pages and shared primitives for repeated busy,
loading, and error behavior.

## Preferred Branching

At page level, prefer explicit branches for:

- loading
- empty
- error
- content

This keeps async flows easy to scan and prevents partial inconsistent renders.

## Primitive-Level Rules

- Put repeated busy and disabled behavior into shared buttons and inputs.
- Use loading primitives for overlays, inline spinners, and status regions.
- Use shared alert or notification primitives for action errors and success
  messaging.

## Page-Level Rules

- Keep branching near the top of the page component.
- Return early for hard loading and fatal error states.
- Use explicit empty states instead of blank containers.
- Use content branches only when the data required to render is ready.

## Success Handling

After successful async actions, prefer one of these flows:

- reset the form for repeated entry
- refocus the next useful field
- redirect to the next logical route
- show a clear success message when staying on the page

Choose one intentionally. Do not stack multiple success behaviors without a user
flow reason.

## Accessibility Rules

- Busy buttons should expose `aria-busy` when relevant.
- Loading regions should use `role="status"` when they are announcing progress.
- Errors should use `role="alert"` or an appropriate live region.
- Empty states should still use meaningful headings and actions.

## See Also

- `./accessibility-patterns.md`
- `./foundational-components.md`
- `../examples/service-backed-form-page.tsx`

## Anti-Patterns

- Hiding errors in console logs only
- Rendering loading UI with no accessible announcement
- Leaving submit buttons active during mutations
- Mixing stale content and loading state without clear intent
- Using generic spinners where an empty or error state is more accurate
