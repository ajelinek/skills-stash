# Example Gallery

When a shared foundation package grows, keep a small reference gallery page that
shows primitives, variants, states, and accessibility behavior in one place.

## Purpose

Use a gallery or widget page to:

- document the current primitive API
- compare variants and sizes quickly
- verify loading, error, disabled, and empty states visually
- exercise accessibility labels and semantic structure
- help contributors extend the design system consistently

This page is a reference surface, not feature UI.

## Rules

- Keep the gallery separate from product flows.
- Group examples by primitive type.
- Show realistic states, not only ideal defaults.
- Include busy, disabled, error, and empty states where relevant.
- Use semantic headings and sections so the page remains navigable.
- Reuse the real primitives directly; do not create fake one-off demo versions.

## Good Sections

- Buttons: variants, sizes, busy state, disabled state
- Inputs: label, help text, error state, prefilled value
- Toggles: on, off, disabled
- Dialogs: open state and action layout
- Loading and alerts: inline, page-level, and form-level patterns
- Empty states: no data and next action prompt

## Anti-Patterns

- Embedding production business logic into the gallery
- Styling demo-only variants that do not exist in the real API
- Showing components without labels or state context
- Letting the gallery become the only documentation of component expectations

## When To Add One

Add or extend a gallery page when:

- a foundation package gains several primitives
- a primitive has multiple variants or semantic states
- visual regression review is becoming difficult from isolated code alone
- the team needs a quick reference page for shared UI behavior

## See Also

- `./foundational-components.md`
- `./styling-and-theme.md`
- `./accessibility-patterns.md`
