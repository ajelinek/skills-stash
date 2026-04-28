# Accessibility Patterns

Build accessibility into primitives and shared structures first. Do not add
ARIA as an afterthought.

## Core Rules

- Use semantic HTML before adding ARIA.
- Add ARIA attributes only where they provide genuine additional meaning.
- Every interactive element must have an accessible name.
- Maintain visible focus states; do not remove `:focus-visible` outlines.
- Minimum 44px touch targets for all interactive elements.
- Respect `prefers-reduced-motion` in transitions and animations.
- Meet WCAG AA contrast ratios.

## Labels And Inputs

- Every input must have a real `<label>` tied via `for` / `id`.
- Do not rely on `placeholder` as a label — placeholders disappear on input.
- Generate a fallback `id` with `createUniqueId()` from `solid-js` when none
  is provided. This is SSR-safe and stable per component instance. Do not call
  `nanoid()` or `Math.random()` at component scope.
- Set `aria-invalid="true"` on inputs that have validation errors.
- Render error text using `role="alert"` so screen readers announce it.

```tsx
import { createUniqueId } from 'solid-js'

// Inside the Input foundational component
const inputId = props.id || createUniqueId()

return (
  <div class={styles.formGroup}>
    {props.label && <label for={inputId}>{props.label}</label>}
    <input
      {...inputProps}
      id={inputId}
      aria-invalid={props.errorMessage ? 'true' : undefined}
      aria-describedby={props.errorMessage ? `${inputId}-error` : undefined}
    />
    <Show when={props.errorMessage}>
      <span id={`${inputId}-error`} role="alert" class={styles.error}>
        {props.errorMessage}
      </span>
    </Show>
  </div>
)
```

## Error Messaging

- The `Alert` foundational component renders `role="alert"` so errors are
  announced immediately to screen readers.
- Use `Alert` for form-level and operation-level errors.
- Use `errorMessage` prop on individual inputs for field-level errors.
- Do not suppress errors silently — surface them in the UI.

## Async Announcements

- Loading regions that update after user action should use `role="status"`.
- Errors should use `role="alert"`.
- Success toasts or inline messages can use `role="status"` with `aria-live`.

```tsx
<div role="status" aria-live="polite">
  <Show when={op.status.isProcessing}>Saving…</Show>
</div>
```

## Dialog And Modal Semantics

- Use `role="dialog"` and `aria-modal="true"` on modal wrappers.
- Tie the dialog title to the dialog using `aria-labelledby`.
- Close the dialog on `Escape` key via `onKeyDown`.
- Manage focus: move focus into the modal when it opens; restore it when it
  closes.
- Use `Portal` from `solid-js/web` to avoid stacking context problems.

```tsx
<Show when={props.isOpen}>
  <Portal>
    <div
      class={styles.backdrop}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      onKeyDown={(e) => e.key === 'Escape' && props.onClose()}
    >
      <div class={styles.modal}>
        <h2 id="modal-title">{props.title}</h2>
        {props.children}
        <button type="button" onClick={props.onClose} aria-label="Close modal">×</button>
      </div>
    </div>
  </Portal>
</Show>
```

## Toggle States

- Toggle primitives should wrap a real `<input type="checkbox">` or a
  `<button role="switch">`.
- Associate a visible label via `for` / `id`.
- Use `aria-checked` for switch buttons when not using a checkbox.

## Touch Targets

- Set `min-width: 44px` and `min-height: 44px` on all interactive elements via
  CSS.
- Do not rely on padding alone for small icon buttons — verify computed size.

## Keyboard Support

- All interactive elements must be reachable and operable by keyboard.
- Tab order should follow visual reading order.
- Custom interactive components must handle `Enter` and `Space` where
  applicable.
- Modal close buttons must be focusable and operable with `Enter`.

## Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

## Anti-Patterns

- Placeholder text used as a label.
- `aria-label` on non-interactive elements.
- Missing `for` / `id` associations on labels and inputs.
- Removing `:focus-visible` outlines without a custom focus indicator.
- Interactive elements smaller than 44px.
- Errors that only appear in the console.
- Custom components that are not keyboard operable.
