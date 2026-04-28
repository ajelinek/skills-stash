# Accessibility Patterns

WCAG 2.1 AA requirements, ARIA usage, form labels, heading hierarchy, and
keyboard navigation for Astro components.

---

## Core Requirements

- **Text contrast**: minimum 4.5:1 for normal text, 3:1 for large text.
- **UI element contrast**: minimum 3:1 for interactive elements and boundaries.
- **Never use color alone** to convey information.
- **Touch targets**: minimum 44×44 logical pixels for all interactive elements.
- **Keyboard**: all interactions accessible via keyboard.
- **Visible focus indicators** on every interactive element.
- **Reduced motion**: respect `prefers-reduced-motion`.

---

## Semantic HTML First

Use the most semantically correct HTML element before reaching for ARIA.
ARIA supplements semantic HTML — it does not replace it.

```astro
<!-- Do this -->
<nav aria-label="Main navigation">
  <ul>
    <li><a href="/">Home</a></li>
    <li><a href="/about">About</a></li>
  </ul>
</nav>

<main>
  <article>
    <h1>Post Title</h1>
    <p>Content...</p>
  </article>
</main>

<footer>
  <p>© 2024 Example</p>
</footer>

<!-- Not this -->
<div class={styles.nav}>
  <div class={styles.list}>
    <div class={styles.item}><a href="/">Home</a></div>
  </div>
</div>
```

---

## Heading Hierarchy

Use heading levels in logical document order. Never skip a level.

```astro
<main>
  <h1>{pageTitle}</h1>          <!-- one h1 per page -->
  <section aria-label="Features">
    <h2>Features</h2>
    <div>
      <h3>Speed</h3>
      <p>...</p>
    </div>
    <div>
      <h3>Reliability</h3>
      <p>...</p>
    </div>
  </section>
</main>
```

Do not choose heading levels based on visual size. Use CSS to control appearance.

---

## ARIA Labels

Add `aria-label` or `aria-labelledby` to landmark regions and elements where
the accessible name is not clear from the content alone.

```astro
<!-- landmark with label -->
<section aria-label="Recent articles">
  ...
</section>

<!-- icon button -->
<button aria-label="Close dialog" class={styles.closeButton}>
  <CloseIcon aria-hidden="true" />
</button>

<!-- search form -->
<form role="search" aria-label="Site search">
  <input type="search" aria-label="Search query" />
  <button type="submit">Search</button>
</form>
```

---

## Form Accessibility

Every input must have a visible label associated via `for`/`id` or wrapping.

```astro
---
import styles from './styles.module.css'
---

<div class={styles.field}>
  <label for="email" class={styles.label}>
    Email address
    <span class={styles.required} aria-label="required">*</span>
  </label>
  <input
    id="email"
    type="email"
    name="email"
    class={styles.input}
    autocomplete="email"
    required
    aria-describedby="email-hint email-error"
  />
  <span id="email-hint" class={styles.hint}>
    We'll never share your email.
  </span>
  {errorMessage && (
    <span id="email-error" class={styles.error} role="alert">
      {errorMessage}
    </span>
  )}
</div>
```

- Always associate `<label>` with its input via matching `for`/`id`.
- Use `aria-describedby` to link hint text and error messages to the input.
- Use `role="alert"` on error messages so screen readers announce them.
- Mark required fields visually and with `required` (or `aria-required="true"`).

---

## Keyboard Navigation

- Ensure logical tab order that matches visual reading order.
- Provide visible focus indicators — never suppress `outline` without an alternative.
- Use `tabindex="0"` to make non-interactive elements focusable only when necessary.
- Never use `tabindex` values greater than 0.
- Skip links: provide a "Skip to main content" link as the first focusable element on the page.

```astro
<!-- Skip link at the top of BaseLayout -->
<a href="#main-content" class={styles.skipLink}>
  Skip to main content
</a>
...
<main id="main-content" tabindex="-1">
  <slot />
</main>
```

```css
/* styles.module.css */
.skipLink {
  position: absolute;
  top: -100%;
  left: var(--spacing-sm);
  background: var(--color-background-page);
  padding: var(--spacing-xs) var(--spacing-sm);
  z-index: 9999;
}

.skipLink:focus {
  top: var(--spacing-sm);
}
```

---

## Live Regions

Announce dynamic content changes to screen readers using `aria-live`.

```astro
<!-- Status messages -->
<div aria-live="polite" aria-atomic="true" class={styles.statusRegion}>
  {statusMessage}
</div>

<!-- Urgent alerts -->
<div role="alert" aria-live="assertive">
  {criticalError}
</div>
```

Use `polite` for status updates that should not interrupt. Use `assertive`
(or `role="alert"`) only for time-sensitive or error messages.

---

## Images And Icons

```astro
<!-- Informative image -->
<img src={hero.src} alt="A team working together at a whiteboard" />

<!-- Decorative image -->
<img src={decoration.src} alt="" aria-hidden="true" />

<!-- Icon with adjacent text (icon is decorative) -->
<button class={styles.button}>
  <SearchIcon aria-hidden="true" />
  Search
</button>

<!-- Icon-only button -->
<button class={styles.button} aria-label="Search">
  <SearchIcon aria-hidden="true" />
</button>
```

---

## Dialog And Modal

Use the native `<dialog>` element for modals. Manage focus on open and restore
on close.

```astro
---
import styles from './styles.module.css'
---

<dialog
  id={dialogId}
  class={styles.dialog}
  aria-labelledby={`${dialogId}-title`}
  aria-describedby={`${dialogId}-desc`}
>
  <h2 id={`${dialogId}-title`} class={styles.title}>
    {title}
  </h2>
  <p id={`${dialogId}-desc`} class={styles.desc}>
    {description}
  </p>
  <slot />
  <button
    class={styles.closeButton}
    aria-label="Close dialog"
    autofocus
  >
    Close
  </button>
</dialog>
```

- Set `autofocus` on the first actionable element inside the dialog.
- Return focus to the trigger element when the dialog closes.
- The native `<dialog>` element manages `aria-modal` automatically in modern browsers.

---

## Testing Accessibility

- Test all interactions using keyboard only.
- Test with VoiceOver (macOS/iOS) or NVDA (Windows).
- Check color contrast ratios with browser DevTools or an accessibility checker.
- Verify at 200% zoom without horizontal scrolling.
- Test with a color blindness simulator.
