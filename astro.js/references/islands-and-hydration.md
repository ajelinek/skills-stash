# Islands And Hydration

The architecture split, hydration directive guide, framework selection, and
data-passing rules for Astro interactive components.

---

## The Hard Split: Astro vs Islands

Astro renders static HTML. It has no client-side reactivity.

**Use `.astro` for:**

- Pages and route entry points
- Layout shells (`BaseLayout`, `BlogLayout`, etc.)
- Static content regions — headers, footers, hero sections, article bodies,
  marketing copy, navigation structure
- Wrappers that compose islands but don't themselves need to react to events

**Use a SolidJS or React island for:**

- Any component with an `onClick`, `onChange`, `onSubmit`, or other event handler
- Any component that manages state (`createSignal`, `useState`, forms, toggles)
- Any component that subscribes to real-time data
- All foundational UI components — Button, Input, Alert, Modal, Select, Checkbox,
  Toggle, etc.
- Any component that calls a service hook or reads from a store

**If you're unsure:** ask whether the component needs to respond after the HTML
is delivered to the browser. If yes — even for a single button click — it is an island.

---

## Choosing The Framework

A project uses either SolidJS or React — not both. Check `astro.config.mjs`:

```js
// SolidJS project
import solidJs from '@astrojs/solid-js'
export default defineConfig({ integrations: [solidJs()] })

// React project
import react from '@astrojs/react'
export default defineConfig({ integrations: [react()] })
```

Use whichever framework is configured. Do not introduce the other. When building
foundational components or feature islands, follow the `solid.js` skill or the
`react` skill for the implementation conventions that apply inside those components.

---

## Hydration Directives

| Directive | When it hydrates | When to use |
| --- | --- | --- |
| `client:load` | Immediately on page load | Critical interactive UI that must be ready the moment the page appears |
| `client:idle` | When the browser is idle | Secondary interactive UI that can wait for higher-priority tasks |
| `client:visible` | When the element enters the viewport | Components below the fold or in content areas |
| `client:media="(query)"` | When a media query matches | UI that only appears at certain viewport sizes |
| `client:only="framework"` | Never SSR, only client | Components that require a browser API at render time |

**Default to `client:visible` or `client:idle`.** Use `client:load` only when the
interaction must be immediately available — e.g., a primary navigation dropdown or
an authentication form on a dedicated auth page.

---

## Island File Layout

Islands live in the same component directory structure as `.astro` files. The
framework extension changes; the CSS Module convention does not.

```
src/components/features/
└── Counter/
    ├── index.tsx          ← SolidJS (or React) island component
    └── styles.module.css  ← CSS Module for this island, always separate
```

**CSS Modules in islands follow exactly the same rule as in `.astro` files.**
Import and use `styles.module.css`. Do not use CSS-in-JS or inline styles.

---

## Using An Island From An Astro Page Or Component

```astro
---
import styles from './styles.module.css'
import Counter from '../../components/features/Counter/index.tsx'
---

<section class={styles.section}>
  <Counter client:visible initialCount={0} />
</section>
```

Only the `Counter` subtree is hydrated on the client. Everything else in the
`.astro` file remains static HTML.

---

## Passing Data From Server To Island

Pass data as props. Astro serializes props to JSON for client-side rehydration.
Prop values must be serializable (strings, numbers, plain objects, arrays).

```astro
---
import Watchlist from '../features/Watchlist/index.tsx'
import { getUserWatchlist } from '../../store/service/watchlist'

const items = await getUserWatchlist(userId)
---

<Watchlist client:idle items={items} userId={userId} />
```

Do not pass functions, class instances, or non-serializable values as props to
islands — they will not survive serialization.

---

## SolidJS Island Example

```tsx
// Counter/index.tsx
import { createSignal } from 'solid-js'
import styles from './styles.module.css'

interface Props {
  initialCount: number
}

export default function Counter(props: Props) {
  const [count, setCount] = createSignal(props.initialCount)

  return (
    <div class={styles.counter}>
      <button class={styles.button} onClick={() => setCount((c) => c - 1)}>
        -
      </button>
      <span class={styles.count}>{count()}</span>
      <button class={styles.button} onClick={() => setCount((c) => c + 1)}>
        +
      </button>
    </div>
  )
}
```

```css
/* Counter/styles.module.css */
.counter {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.button {
  min-width: 44px;
  min-height: 44px;
  padding: var(--spacing-xs) var(--spacing-sm);
  background-color: var(--color-interactive-primary);
  color: var(--color-text-inverse);
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
}

.count {
  font-variant-numeric: tabular-nums;
  min-width: 2ch;
  text-align: center;
}
```

---

## React Island Example

```tsx
// SearchBox/index.tsx
import { useState } from 'react'
import styles from './styles.module.css'

interface Props {
  placeholder?: string
  onSearch: (query: string) => void
}

export default function SearchBox({ placeholder = 'Search…', onSearch }: Props) {
  const [query, setQuery] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSearch(query)
  }

  return (
    <form className={styles.form} onSubmit={handleSubmit}>
      <input
        className={styles.input}
        type="search"
        value={query}
        placeholder={placeholder}
        onChange={(e) => setQuery(e.target.value)}
        aria-label="Search"
      />
      <button className={styles.submit} type="submit">
        Search
      </button>
    </form>
  )
}
```

Note: React uses `className` while SolidJS uses `class`. Both import from
the same `styles.module.css` pattern.

---

## `client:only` Caveats

`client:only` skips server-side rendering entirely. The component receives no
server-rendered HTML — the browser renders it from scratch on load. Use it
sparingly, only when the component requires a browser-only API (`window`,
`localStorage`, `navigator`, etc.) at render time.

```astro
<MapWidget client:only="react" apiKey={mapKey} />
```

Avoid `client:only` for most interactive components. Prefer `client:visible`
or `client:idle` to preserve SSR output and improve performance.
