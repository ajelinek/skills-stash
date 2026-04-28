# Accessibility Patterns

Accessibility is built into the shared primitives, not bolted onto pages later.

## Preferred Pattern

Solve accessibility in the primitive or shared shell first so feature code stays
simple and consistent.

## Form Fields

- Every input needs a real label.
- Tie label and control with an ID.
- Use `useId()` for generated fallback IDs.
- Use `aria-invalid` when the field has a validation error.
- Point `aria-describedby` at help text or error text when present.
- Render validation errors accessibly, usually with `role="alert"`.

## Buttons And Toggles

- Every interactive element needs an accessible name.
- Busy buttons should expose their busy state and remain semantically buttons.
- Toggle-style controls should use the correct semantic state such as
  `aria-pressed` or native checkbox semantics.
- Preserve keyboard interaction and visible focus states.

## Dialogs

- Prefer real dialog semantics.
- Ensure the dialog has an accessible label, typically via `aria-labelledby`.
- Return focus sensibly when the dialog closes.
- Keep dialog actions keyboard reachable.

## Async Messaging

- Use `role="status"` for progress or non-urgent async updates.
- Use `role="alert"` for urgent errors.
- Do not announce the same message multiple times through competing live
  regions.

## Layout And Touch Targets

- Use semantic headings, sections, forms, lists, and buttons.
- Keep touch targets at least 44px when interactive.
- Avoid hover-only disclosure patterns.
- Respect reduced motion and contrast requirements.

## Anti-Patterns

- Placeholder-only labeling
- Clickable `div` or `span` instead of button or link
- Removing focus outlines without replacement
- Error text that is not programmatically associated with the field
- Dialogs with no clear title or close path

## See Also

- `./foundational-components.md`
- `./async-ui-states.md`
- `./styling-and-theme.md`
