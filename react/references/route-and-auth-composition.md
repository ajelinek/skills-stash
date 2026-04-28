# Route And Auth Composition

Route structure should stay explicit, and auth concerns should live in providers
and app shells rather than leaking through individual pages.

## Current Preferred Pattern

- Keep the route tree explicit.
- Use nested route layouts for shared structure.
- Centralize redirect logic in the app shell, auth boundary, or route layout.
- Reuse page shells and form shells across auth flows.
- Keep pages thin and focused on composition.

## Auth Provider Pattern

- Create an auth provider that owns subscription, bootstrap, and status state.
- Expose narrow custom hooks for reading auth state.
- Throw from custom auth hooks when used outside the provider.
- Keep session logic out of presentational components.

## Page Shell Pattern

Pages should assemble:

- foundation primitives
- shared form components
- service hooks
- route parameters or navigation helpers

Pages should not duplicate provider logic or repository access.

## Historical Context

Older code may use route-builder abstractions or older router conventions. Keep
those patterns in mind when working inside legacy paths, but prefer explicit
nested route definitions for new work.

## Error Isolation

When a section can fail independently, wrap that section in an error boundary
instead of taking down the whole screen.

## See Also

- `./component-structure.md`
- `./state-and-data.md`
- `../examples/auth-form-shell.tsx`
- `../examples/service-backed-form-page.tsx`

## Anti-Patterns

- Route gates copied into many pages
- Repository calls inside route components
- Repeating auth-form structure across login, registration, and verification
- Giant app components that mix route config, auth bootstrap, and page markup
