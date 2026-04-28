# Server Rendering

Astro supports three rendering modes. This reference covers server islands
(`server:defer`), on-demand rendering (SSR), and Astro Actions — the Astro 5
features for server-side interactivity.

---

## Rendering Modes

| Mode | Config | Behavior |
| --- | --- | --- |
| Static (default) | `output: 'static'` | All pages pre-rendered at build time |
| Hybrid | `output: 'hybrid'` | Pre-render by default; opt individual pages into SSR |
| Server | `output: 'server'` | All pages rendered on demand; opt individual pages into SSR |

All server rendering modes require an adapter (`@astrojs/node`, `@astrojs/vercel`, etc.).

```js
// astro.config.mjs
import { defineConfig } from 'astro/config'
import node from '@astrojs/node'

export default defineConfig({
  output: 'hybrid',   // or 'server'
  adapter: node({ mode: 'standalone' }),
})
```

---

## On-Demand Rendering (SSR Pages)

### Opt a page out of pre-rendering (hybrid mode)

```astro
---
// src/pages/dashboard/index.astro
export const prerender = false   // this page renders on every request

import { getUser } from '../../store/service/auth'

const user = await getUser(Astro.cookies.get('session')?.value)
if (!user) return Astro.redirect('/login')
---

<h1>Hello, {user.name}</h1>
```

### Opt a page into pre-rendering (server mode)

```astro
---
export const prerender = true   // render at build time even in 'server' mode
---
```

### Server-side APIs available on-demand

| API | Description |
| --- | --- |
| `Astro.cookies` | Read and write cookies (`get`, `set`, `delete`, `has`) |
| `Astro.request` | Full `Request` object with headers, body, method |
| `Astro.response` | Mutable `Response` object for setting headers and status |
| `Astro.redirect(url)` | Return a redirect response |
| `Astro.locals` | Per-request data set by middleware |

```astro
---
export const prerender = false

// Set a response header
Astro.response.headers.set('Cache-Control', 'no-store')

// Read a cookie
const theme = Astro.cookies.get('theme')?.value ?? 'light'

// Redirect if not authenticated
const token = Astro.cookies.get('auth-token')?.value
if (!token) return Astro.redirect('/login')
---
```

---

## Middleware

Define middleware in `src/middleware.ts`. Use `defineMiddleware` from `astro:middleware`.

```ts
// src/middleware.ts
import { defineMiddleware } from 'astro:middleware'

export const onRequest = defineMiddleware(async (context, next) => {
  // context.locals is per-request data passed to pages
  const token = context.cookies.get('auth-token')?.value
  if (token) {
    context.locals.user = await verifyToken(token)
  }

  return next()
})
```

Access `Astro.locals` in any page or endpoint:

```astro
---
export const prerender = false
const { user } = Astro.locals
if (!user) return Astro.redirect('/login')
---
<p>Welcome, {user.name}</p>
```

Define the `locals` shape in `env.d.ts`:

```ts
// src/env.d.ts
/// <reference types="astro/client" />

declare namespace App {
  interface Locals {
    user?: { id: string; name: string; email: string }
  }
}
```

---

## Server Islands (`server:defer`)

Server islands let you defer a dynamic, personalized region while keeping the
rest of the page static. The static shell renders immediately; the deferred
region renders server-side and streams in afterward.

### When to use

- Personalized content (user-specific UI, cart counts, notifications)
- Components that require fresh data but should not block page delivery
- Regions that are expensive to compute but don't need to be in the initial HTML

### Requirements

- An adapter must be configured.
- The deferred component must be an `.astro` component (not a framework island).

### Basic usage

```astro
---
// src/pages/index/index.astro
import UserGreeting from '../../components/features/UserGreeting/index.astro'
---

<main>
  <h1>Welcome</h1>
  <!-- static content renders immediately -->
  <p>Our site content here...</p>

  <!-- this region defers and streams in server-side -->
  <UserGreeting server:defer>
    <p slot="fallback">Loading your personalized greeting...</p>
  </UserGreeting>
</main>
```

```astro
---
// src/components/features/UserGreeting/index.astro
// This component is rendered server-side after the page shell is sent
import { getUser } from '../../../store/service/auth'
import styles from './styles.module.css'

const user = await getUser(Astro.cookies.get('session')?.value)
---

{user
  ? <p class={styles.greeting}>Hello, {user.name}!</p>
  : <a href="/login" class={styles.loginLink}>Sign in</a>
}
```

### Fallback content

Provide a `slot="fallback"` for content shown while the deferred island loads:

```astro
<UserCart server:defer>
  <span slot="fallback">···</span>
</UserCart>
```

### Passing props to deferred components

Props work the same as any `.astro` component:

```astro
<RecentOrders server:defer userId={userId}>
  <p slot="fallback">Loading orders...</p>
</RecentOrders>
```

---

## Astro Actions

Actions are type-safe server functions defined once, callable from anywhere
(islands, HTML forms, API routes). They live in `src/actions/index.ts`.

### When to use

- Form submissions that need server-side validation
- Mutations that should run on the server (database writes, email sends)
- Any server operation called from a client-side island

### Defining actions

```ts
// src/actions/index.ts
import { defineAction, ActionError } from 'astro:actions'
import { z } from 'astro:content'   // or 'astro/zod'

export const server = {
  newsletter: {
    subscribe: defineAction({
      input: z.object({
        email: z.string().email(),
        name: z.string().min(1),
      }),
      handler: async ({ email, name }) => {
        // server-side logic
        const result = await addSubscriber({ email, name })
        if (!result.ok) {
          throw new ActionError({
            code: 'BAD_REQUEST',
            message: 'Email already subscribed.',
          })
        }
        return { success: true }
      },
    }),
  },

  contact: {
    send: defineAction({
      accept: 'form',   // accept FormData in addition to JSON
      input: z.object({
        subject: z.string().min(1),
        message: z.string().min(10),
      }),
      handler: async ({ subject, message }, context) => {
        await sendEmail({ subject, message, from: context.locals.user?.email })
        return { sent: true }
      },
    }),
  },
}
```

### Calling actions from a framework island

```tsx
// src/components/features/NewsletterForm/index.tsx (SolidJS)
import { createSignal } from 'solid-js'
import { actions } from 'astro:actions'

export default function NewsletterForm() {
  const [status, setStatus] = createSignal<'idle' | 'loading' | 'done' | 'error'>('idle')

  async function handleSubmit(e: SubmitEvent) {
    e.preventDefault()
    setStatus('loading')
    const form = e.currentTarget as HTMLFormElement
    const { error } = await actions.newsletter.subscribe({
      email: form.email.value,
      name: form.name.value,
    })
    setStatus(error ? 'error' : 'done')
  }

  return (
    <form onSubmit={handleSubmit}>
      <input name="email" type="email" required />
      <input name="name" type="text" required />
      <button type="submit" disabled={status() === 'loading'}>Subscribe</button>
      {status() === 'error' && <p>Something went wrong. Try again.</p>}
      {status() === 'done' && <p>Subscribed!</p>}
    </form>
  )
}
```

### Calling actions from an HTML form (no JavaScript)

Use `action={actions.contact.send}` on an HTML form. Requires `accept: 'form'`
in the action definition.

```astro
---
import { actions } from 'astro:actions'
import styles from './styles.module.css'
---

<form method="POST" action={actions.contact.send} class={styles.form}>
  <input name="subject" type="text" required />
  <textarea name="message" required></textarea>
  <button type="submit">Send</button>
</form>
```

### Reading action results in Astro pages

After a form POST, read the result with `Astro.getActionResult`:

```astro
---
import { actions } from 'astro:actions'

const result = Astro.getActionResult(actions.contact.send)
---

{result?.error && <p class="error">{result.error.message}</p>}
{result?.data?.sent && <p>Message sent!</p>}
```

### Error handling

```ts
import { actions, isInputError } from 'astro:actions'

const { data, error } = await actions.newsletter.subscribe({ email, name })

if (error) {
  if (isInputError(error)) {
    // Zod validation errors — keyed by field name
    console.log(error.fields.email)   // string[] of messages
  } else {
    // ActionError thrown in handler
    console.log(error.code, error.message)
  }
}
```

### ActionError codes

| Code | HTTP status | When to use |
| --- | --- | --- |
| `BAD_REQUEST` | 400 | Invalid input not caught by Zod |
| `UNAUTHORIZED` | 401 | User is not authenticated |
| `FORBIDDEN` | 403 | User lacks permission |
| `NOT_FOUND` | 404 | Resource doesn't exist |
| `INTERNAL_SERVER_ERROR` | 500 | Unexpected server failure |

---

## Typed Environment Variables (`astro:env`)

Define typed, validated environment variables using `astro:env`.

```js
// astro.config.mjs
import { defineConfig, envField } from 'astro/config'

export default defineConfig({
  env: {
    schema: {
      PUBLIC_API_URL: envField.string({ context: 'client', access: 'public' }),
      DATABASE_URL: envField.string({ context: 'server', access: 'secret' }),
      MAX_ITEMS: envField.number({ context: 'server', access: 'public', default: 10 }),
    },
  },
})
```

Use in server code:

```ts
import { DATABASE_URL, MAX_ITEMS } from 'astro:env/server'
import { PUBLIC_API_URL } from 'astro:env/client'
```

Missing required variables throw a clear error at build time rather than silently
being `undefined` at runtime.

---

## View Transitions

Enable client-side navigation with persistent layouts and animated transitions.

```astro
---
// src/layouts/BaseLayout/index.astro
import { ViewTransitions } from 'astro:transitions'
---

<html>
  <head>
    <ViewTransitions />
  </head>
  <body>
    <slot />
  </body>
</html>
```

### Transition directives

```astro
<!-- name a persistent element across pages -->
<img src={post.image} transition:name={`post-image-${post.id}`} />

<!-- control animation type -->
<h1 transition:animate="slide">{post.title}</h1>

<!-- persist an island across navigations (keeps its state) -->
<MusicPlayer client:load transition:persist />
```

### Programmatic navigation

```ts
import { navigate } from 'astro:transitions/client'

// Navigate without a full page reload
await navigate('/new-page')
```

### Lifecycle events

```ts
document.addEventListener('astro:page-load', () => {
  // runs after each page navigation (including first load)
})

document.addEventListener('astro:before-swap', (e) => {
  // e.newDocument is the incoming document
})
```
