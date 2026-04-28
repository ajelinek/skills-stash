# API E2E Testing with Vitest

## Purpose and Scope

API E2E tests verify the public HTTP contract of your application without a
browser. They run in Vitest, call the API over HTTP, and assert behavior a real
consumer would see: status codes, headers, JSON shape, auth behavior,
validation, persistence side effects, and cross-service flows behind the API
boundary.

Playwright also has first-class API testing support, but this skill's default
is: use Playwright for browser-driven UI E2E and use Vitest for API-only E2E.
Keep Playwright API calls inside UI specs for setup or postcondition checks when
that complements a browser test.

Write API E2E tests for:

- Public API behavior where the API itself is the product surface
- Auth, validation, routing, middleware, serialization, and error envelopes at
  the HTTP boundary
- Backend systems with no browser UI
- Flows that must hit a real started local API endpoint instead of app internals

Do not write API E2E tests for:

- Pure service logic with no HTTP boundary
- Tests that import controllers, route handlers, or services directly
- Browser workflows; use Playwright UI E2E instead

## Boundary Rule

Classify the test by the boundary it crosses.

These are API E2E:

- `fetch(`${apiBaseUrl}/...`)` against a started local server
- A helper that boots the real HTTP server and exposes a real local endpoint

These are usually integration tests:

- Direct controller or route-handler imports
- Service calls below the HTTP boundary
- In-process helpers that bypass the real started API endpoint

The important question is: does the test talk to the public HTTP surface that a
real consumer would hit?

## Recommended Default

Use this default unless the repository already has a stronger established
pattern:

1. Use Vitest as the runner.
2. Keep API E2E in a dedicated Vitest project or config.
3. Start the API once in `globalSetup`, or point tests at an already-running
   local API managed elsewhere.
4. Provide the `apiBaseUrl` to tests through Vitest `provide` and `inject`, or
   via a repo-standard env var.
5. Use Node's built-in `fetch`.

Unit and integration tests can share a Vitest project if the repository already
does that. API E2E should usually be separated because it needs different
startup, timeouts, and failure triage.

## Project Setup Pattern

### Vitest project

```typescript
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    projects: [
      {
        extends: true,
        test: {
          name: 'api-e2e',
          include: ['tests/api/**/*.e2e.test.ts'],
          globalSetup: ['./tests/api/globalSetup.ts'],
        },
      },
    ],
  },
})
```

If the repository does not use Vitest projects, a dedicated
`vitest.api-e2e.config.ts` is also fine.

### Global setup

```typescript
import type { TestProject } from 'vitest/node'

export default async function setup(project: TestProject) {
  const server = await startRealApiServer()
  project.provide('apiBaseUrl', server.baseUrl)

  return async () => {
    await server.close()
  }
}

declare module 'vitest' {
  export interface ProvidedContext {
    apiBaseUrl: string
  }
}
```

Start the same local HTTP server path the application normally uses. Do not
create a parallel, test-only boot path when the real one is available.

## Alternative: Already-Running Local API

If the repository already uses Docker Compose, emulators, or a shared local dev
stack, it is acceptable for API E2E tests to target an already-running local
endpoint instead of starting the server in Vitest.

Rules for this mode:

- Fail fast when `API_BASE_URL` is missing or unreachable
- Keep the target local, deterministic, and disposable
- Document the startup command next to the tests
- Do not silently fall back to in-process imports

## Writing Tests

Use the repository's standard data seeding pattern for initial state, then call
the API through its public base URL.

```typescript
import { expect, inject, test } from 'vitest'

test('should return user through the public API', async ({ ctx }) => {
  const { selector } = await ctx.setupEnv({
    baseData: {
      orgs: [{ _id: 'O1' }],
      users: [{ _id: 'U1', orgId: 'O1' }],
      userDetails: [{ _id: 'U1' }],
    },
  })

  const apiBaseUrl = inject('apiBaseUrl')
  const user = selector.getUser('U1')

  const response = await fetch(`${apiBaseUrl}/api/users/${user._id}`)

  expect(response.status).toBe(200)
  await expect(response.json()).resolves.toMatchObject({ id: user._id })
})
```

Assert what a consumer can actually observe:

- Status code
- Headers
- Response body shape and values
- Durable side effects visible through follow-up API calls or database reads

If auth is required, send the same headers, cookies, or tokens a real client
would send. Prefer real login flows or repo-standard auth helpers over internal
service shortcuts.

## File Organization

- Put API E2E tests in `tests/api/` or `tests/e2e-api/`
- Use a clear suffix such as `.e2e.test.ts` when the repository does not already
  have a different convention
- Keep browser UI E2E in `tests/spec/`
- Keep page objects out of API E2E; there is no browser layer here

## See Also

- `./philosophy.md` — test taxonomy and selection rules
- `./integration-testing.md` — in-process collaboration and DB-backed tests
- `./test-context-system.md` — data seeding and shorthand ID rules
- `./examples/api-e2e-test.ts` — complete copyable API E2E file
