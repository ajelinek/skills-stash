# Accessibility Reference

WCAG 2.1 AA implementation standards for UI components and forms. Apply these
requirements at build time — not as a post-ship audit.

---

## Semantic HTML — Element Reference

Use the most specific element that describes the purpose. A `<div>` or `<span>`
with a `role` is always second-best to the native element.

### Page Structure

| Purpose | Element | Notes |
| --- | --- | --- |
| Primary page content | `<main>` | One per page |
| Site-wide header | `<header>` | At page root, not inside `<main>` |
| Site-wide footer | `<footer>` | At page root, not inside `<main>` |
| Navigation region | `<nav aria-label="…">` | Add `aria-label` when multiple `<nav>` elements exist |
| Supporting content | `<aside aria-label="…">` | Sidebar, callout, related links |
| Grouped page section | `<section aria-label="…">` | Must have an accessible label |
| Self-contained article | `<article>` | Blog post, card, feed item |
| Page-level heading | `<h1>` | One per page; describes the page purpose |
| Sub-section headings | `<h2>` → `<h3>` → `<h4>` | Follow logical hierarchy; never skip levels |

### Interactive Elements

| Purpose | Element | Notes |
| --- | --- | --- |
| User action (submit, open, toggle) | `<button type="button">` | Never use `<div>` or `<span>` for click handlers |
| Form submit | `<button type="submit">` | Only inside a `<form>` |
| Navigate to a URL | `<a href="…">` | Use `<button>` when there is no URL destination |
| Checkbox | `<input type="checkbox">` + `<label>` | |
| Radio group | `<fieldset>` + `<legend>` + `<input type="radio">` + `<label>` | |
| Select menu | `<select>` + `<option>` | |
| Text area | `<textarea>` + `<label>` | |

### Content

| Purpose | Element | Notes |
| --- | --- | --- |
| Unordered list | `<ul>` + `<li>` | Never use `<div>` lists |
| Ordered / sequential list | `<ol>` + `<li>` | Steps, rankings |
| Tabular data | `<table>` + `<thead>` + `<th scope>` + `<td>` | Never for layout |
| Quoted content | `<blockquote>` | |
| Code | `<code>`, `<pre>` | |
| Emphasized text | `<em>` (semantic) vs `<i>` (stylistic) | |
| Important text | `<strong>` (semantic) vs `<b>` (stylistic) | |
| Time or date | `<time datetime="…">` | |
| Abbreviation | `<abbr title="…">` | |

---

## Accessible Names — Priority Order

Every interactive element must have an accessible name. The browser computes
this name in the following priority order. Use the highest applicable source:

1. **Visible text content** — the element's own text or its descendants
   (preferred — no extra attributes needed)
2. **`aria-labelledby`** — points to another visible element's `id`
3. **`aria-label`** — string directly on the element (use when no visible text
   exists and `aria-labelledby` is not practical)

Never use `aria-label` to override or shadow meaningful visible text. If the
visible label and `aria-label` disagree, screen reader users and sighted users
get different experiences.

### When aria-label Is Required

**Icon-only buttons and controls** — no visible text, so `aria-label` is
mandatory:

```html
<button type="button" aria-label="Close dialog">
  <svg aria-hidden="true">…</svg>
</button>
```

**Multiple navigation regions on the same page**:

```html
<nav aria-label="Main navigation">…</nav>
<nav aria-label="Breadcrumb">…</nav>
<nav aria-label="Pagination">…</nav>
```

**Section landmarks**:

```html
<section aria-label="Featured products">…</section>
<section aria-label="Customer reviews">…</section>
```

**Search inputs without a visible label**:

```html
<input type="search" aria-label="Search products" />
```

**Dialogs** — use `aria-labelledby` pointing to the visible title:

```html
<dialog aria-labelledby="dialog-title">
  <h2 id="dialog-title">Confirm deletion</h2>
</dialog>
```

**Tables** — caption or label:

```html
<table aria-label="Monthly sales figures">
  …
</table>
```

### Decorative vs Meaningful Icons

Icons inside a button or alongside text:

```html
<!-- Decorative: text provides the name -->
<button type="button">
  <svg aria-hidden="true">…</svg>
  Save changes
</button>

<!-- Meaningful standalone icon: no accompanying text -->
<button type="button" aria-label="Delete item">
  <svg aria-hidden="true">…</svg>
</button>
```

Never add `aria-label` to a `<svg>` or `<img>` that is decorative — use
`aria-hidden="true"` instead.

---

## Form Accessibility

### Label Association

Every form control must have a programmatic label. Use explicit association
as the default:

```html
<!-- Preferred: explicit for/id pair -->
<label for="username-a1b2">Username</label>
<input id="username-a1b2" type="text" autocomplete="username" />
```

Generate unique IDs per input instance — do not use static IDs when a
component may render more than once on a page.

Never use `placeholder` as a label substitute. Placeholder text disappears on
input, fails contrast requirements, and is inconsistently read by screen readers.

### Error Messaging

```html
<label for="email-x9y8">Email address</label>
<input
  id="email-x9y8"
  type="email"
  aria-invalid="true"
  aria-describedby="email-x9y8-error"
/>
<span id="email-x9y8-error" role="alert">
  Enter a valid email address.
</span>
```

Rules:
- `aria-invalid="true"` on the input signals an invalid state to screen readers.
- `aria-describedby` links the input to its error message.
- `role="alert"` causes the error to be announced immediately when it appears.
- Error messages must be specific and actionable. "Invalid input" is not
  acceptable. "Enter a valid email address" is.
- Clear errors when re-validation passes.
- Place error messages immediately after their associated input.

### Grouped Fields

Use `<fieldset>` + `<legend>` for groups of radio buttons, checkboxes, or
related fields:

```html
<fieldset>
  <legend>Preferred contact method</legend>
  <label><input type="radio" name="contact" value="email" /> Email</label>
  <label><input type="radio" name="contact" value="phone" /> Phone</label>
</fieldset>
```

---

## ARIA Live Regions

Live regions announce dynamic content changes to screen readers without
requiring focus to move.

| Urgency | Use |
| --- | --- |
| Errors, session expiry, critical alerts | `role="alert"` (implicitly `aria-live="assertive"`) |
| Status updates, save confirmations, counts | `role="status"` (implicitly `aria-live="polite"`) |
| Progress that should not interrupt | `aria-live="polite"` on a container |
| Content that should not be announced | Default (no `aria-live` needed) |

Rules:
- Do not use `aria-live="assertive"` for loading indicators — it interrupts
  whatever the user is doing.
- The live region element must be in the DOM before content changes into it.
  Adding a live region and populating it simultaneously is unreliable.
- Keep live region announcements brief and informative.

---

## Keyboard Navigation

Every interaction achievable by mouse must be achievable by keyboard alone.

### Focus Order

- Tab order follows logical visual sequence: top-to-bottom, left-to-right.
- Do not use `tabindex` values greater than `0` to reorder focus. Fix the DOM
  order instead.
- Use `tabindex="0"` only to make a non-interactive element focusable when
  absolutely necessary.
- Use `tabindex="-1"` to make an element programmatically focusable (for
  focus management in dialogs, tabs, etc.) without placing it in the tab order.

### Focus Indicators

Every interactive element must have a visible focus indicator when focused
via keyboard. Do not remove the browser default without replacing it:

```css
/* In the component's styles.module.css */
.button:focus-visible {
  outline: 3px solid var(--color-focus-ring);
  outline-offset: 2px;
}
```

Use `:focus-visible` — not `:focus` — so the indicator only shows during
keyboard navigation, not on mouse click.

### Key Behavior by Widget Type

| Widget | Key | Behavior |
| --- | --- | --- |
| All interactive | Tab / Shift+Tab | Move focus forward / backward |
| Button | Enter, Space | Activate |
| Link | Enter | Follow |
| Checkbox | Space | Toggle |
| Radio group | Arrow keys | Move between options |
| Select / Listbox | Arrow keys | Move between options; Enter selects |
| Menu | Arrow keys | Move between items; Enter activates; Escape closes |
| Dialog | Escape | Close |
| Dropdown / Combobox | Escape | Close; Arrow Down opens |

### Skip Navigation

Pages with persistent navigation must have a skip link as the first focusable
element:

```html
<a href="#main-content" class="skip-link">Skip to main content</a>
…
<main id="main-content">…</main>
```

The skip link may be visually hidden until focused:

```css
.skip-link {
  position: absolute;
  transform: translateY(-100%);
}
.skip-link:focus {
  transform: translateY(0);
}
```

---

## Focus Management

Move focus programmatically only for significant content changes. Do not
move focus for minor UI state changes.

| Situation | Focus moves to |
| --- | --- |
| Dialog opens | First focusable element inside the dialog |
| Dialog closes | The element that triggered the dialog |
| Page navigation (SPA) | The new page's `<h1>` or top of main content |
| Inline error appears | First field with an error (or error summary heading) |
| Step advances in a multi-step form | Top of the new step's content |

Trap focus inside a dialog while it is open — tabbing past the last
focusable element wraps back to the first, and Shift+Tab past the first
wraps to the last.

---

## Color and Contrast

| Context | Minimum ratio |
| --- | --- |
| Normal text (< 18px or < 14px bold) | 4.5:1 |
| Large text (≥ 18px regular, ≥ 14px bold) | 3:1 |
| Interactive element boundaries and icons | 3:1 |

Additional rules:
- Never use color as the only differentiator for state, error, category, or
  meaning. Always pair with text, icon, pattern, or shape.
- Test protanopia, deuteranopia, and tritanopia scenarios.
- Verify contrast ratios independently in both light and dark themes.

---

## Visual Design

### Text Scaling

- All layouts must remain usable at 200% browser zoom without horizontal
  scrolling.
- Use `rem` for font sizes. Use `em` or `rem` for spacing that should scale
  with text.
- Avoid fixed-height containers that clip content when text grows.

### Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

Place this in `styles/global.css`. For JavaScript-driven animations, check:

```typescript
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
```

---

## Touch and Mobile

- Minimum 44×44 logical pixels for all interactive elements.
- Minimum 8px gap between adjacent touch targets.
- No hover-only interactions. Touch devices do not have hover.
- Test on real devices or reliable emulators for tap target size.

---

## Component Testing Checklist

Before shipping any foundation component or form, verify:

- [ ] Keyboard-only navigation reaches and operates every interactive element
- [ ] Tab order is logical and matches visual sequence
- [ ] Visible `:focus-visible` indicator on all interactive elements
- [ ] Screen reader announces role, name, and state correctly
- [ ] `aria-label` present on all icon-only controls
- [ ] Multiple `<nav>` or `<section>` elements are distinguished by `aria-label`
- [ ] Color contrast passes 4.5:1 for text, 3:1 for UI elements (both themes)
- [ ] Color is not the only differentiator for any state or category
- [ ] All form fields have associated `<label>` elements
- [ ] Errors use `aria-invalid`, `aria-describedby`, and `role="alert"`
- [ ] Dynamic content changes are announced via live regions
- [ ] Zoom to 200% does not break layout or clip content
- [ ] `prefers-reduced-motion` suppresses all animations and transitions
- [ ] Dialog traps focus and returns it on close
- [ ] Skip link is present on pages with persistent navigation
