# Form UX Reference

Standards for form structure, label association, validation, error messaging,
and submission state management.

---

## Labels and Input Association

Every form control must have a visible, programmatically associated label.

**Required pattern:**

```html
<label for="email-input">Email address</label>
<input
  id="email-input"
  type="email"
  name="email"
  autocomplete="email"
  required
/>
```

Rules:
- Generate a unique `id` for every input at render time. Do not use static IDs
  when a form may appear more than once on a page (e.g., login widget and inline
  login form on the same route).
- The `for` attribute on `<label>` must exactly match the `id` on the `<input>`.
- Never use `placeholder` as a substitute for a label. Placeholder text
  disappears on input and is not reliably read by screen readers.
- Use foundation input components — never raw `<input>` directly in feature or
  page components.

---

## Appropriate Input Types

Use the most specific HTML5 `type` for every input:

| Data type | Use |
| --- | --- |
| Email address | `type="email"` |
| Password | `type="password"` |
| Phone number | `type="tel"` |
| URL | `type="url"` |
| Number (quantity) | `type="number"` |
| Date | `type="date"` |
| Search | `type="search"` |
| Free text (default) | `type="text"` |

Add `autocomplete` attributes where they improve UX:

```html
<input type="email"    autocomplete="email" />
<input type="password" autocomplete="current-password" />
<input type="text"     autocomplete="name" />
```

---

## Validation Contract

Form validation is the responsibility of the store or service layer, not
presentation components.

**What components do:**
- Accept an `errorMessage?: string` prop per field.
- Render the error message in a visually distinct way (red border, error icon,
  error text below the field).
- Associate the error message with the input via `aria-describedby`.
- Set `aria-invalid="true"` on the input when an error is present.

**What services do:**
- Run validation on form submit (and optionally on blur for long forms).
- Return structured field-level errors to the component.
- Own all business rule logic (password length, email uniqueness, required
  fields).

**Error message anatomy:**

```html
<label for="username-input">Username</label>
<input
  id="username-input"
  type="text"
  aria-invalid="true"
  aria-describedby="username-error"
/>
<span id="username-error" role="alert">
  Username must be at least 3 characters.
</span>
```

Error message rules:
- Be specific — state what is wrong and what the user should do.
  Bad: "Invalid input." Good: "Username must be at least 3 characters."
- Use `role="alert"` on the error container so screen readers announce it.
- Clear error messages when the field value changes or when re-validation passes.
- Place error messages immediately after the associated input — not in a summary
  at the top of the form (a summary in addition is acceptable for long forms).

---

## Fieldsets and Groups

Group related fields with `<fieldset>` and `<legend>`:

```html
<fieldset>
  <legend>Notification preferences</legend>

  <label>
    <input type="checkbox" name="email-notify" />
    Email notifications
  </label>

  <label>
    <input type="checkbox" name="sms-notify" />
    SMS notifications
  </label>
</fieldset>
```

Use `<fieldset>` + `<legend>` for:
- Groups of radio buttons
- Groups of related checkboxes
- Multi-part inputs (date fields split into day/month/year)

---

## Submission State Machine

A form's submission goes through these states:

```
idle → submitting → success
                  → error
```

| State | UI behavior |
| --- | --- |
| `idle` | Submit button enabled, no loading indicator |
| `submitting` | Submit button disabled, loading indicator visible, form fields may be disabled |
| `success` | Confirmation message shown, form reset or user redirected |
| `error` | Error message shown (network error or server-level validation), form remains editable |

Implementation rules:
- Disable the submit button while `submitting` to prevent duplicate submissions.
- Show a loading indicator that is accessible (`role="status"`, `aria-label`).
- On network error, display a clear, user-visible error message. Do not silently
  swallow fetch errors.
- After success, either reset the form and display a confirmation, or redirect
  the user to the next step.
- Do not lock the form permanently after a server-side validation error — let
  the user correct and resubmit.

---

## Keyboard Navigation in Forms

- Tab moves focus forward through fields in logical order.
- Shift+Tab moves focus backward.
- Enter submits the form when focus is on the submit button.
- All field types (text, checkbox, radio, select, date) are keyboard-accessible
  by default when using semantic HTML — do not override or disable this.
- After a validation error, move focus to the first failing field or to the
  error summary if one exists at the top.

---

## Multi-Step Forms

When a form spans multiple steps:

- Show a progress indicator (step count or step bar) with `aria-label` describing
  the current step.
- Preserve completed field values when the user navigates back.
- Validate the current step's fields before advancing.
- Keep submit in the final step only.
- Move focus to the top of the new step's content after advancing.
