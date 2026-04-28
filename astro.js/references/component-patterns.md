# Component Patterns

Frontmatter shape, typed props, slot usage, Astro API reference, and anti-patterns
for Astro components.

---

## Frontmatter Fence

The `---` frontmatter fence is the server-side execution environment. Use it for:

- Imports (CSS Modules, other components, utilities, service functions)
- Type definitions and prop destructuring
- Data fetching and transformation
- Variables used in the template

```astro
---
import styles from './styles.module.css'
import Button from '../foundation/Button/index.tsx'
import { getCollection } from 'astro:content'

interface Props {
  title: string
  subtitle?: string
  cta?: string
}

const { title, subtitle, cta = 'Learn more' } = Astro.props
const posts = await getCollection('blog')
---
```

---

## Typed Props

Define `interface Props` in the frontmatter fence. Destructure from `Astro.props`.
Use TypeScript types — never `any`.

```astro
---
import styles from './styles.module.css'

interface Props {
  variant: 'primary' | 'secondary' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  disabled?: boolean
  href?: string
}

const { variant, size = 'md', disabled = false, href } = Astro.props
---
```

---

## Slots

Use `<slot />` for content injection. Named slots for multiple injection points.

```astro
---
import styles from './styles.module.css'
---

<section class={styles.card}>
  <header class={styles.header}>
    <slot name="header" />
  </header>
  <div class={styles.body}>
    <slot />
  </div>
  <footer class={styles.footer}>
    <slot name="footer" />
  </footer>
</section>
```

Usage:

```astro
<Card>
  <h2 slot="header">Title</h2>
  <p>Body content goes in the default slot.</p>
  <Button slot="footer">Action</Button>
</Card>
```

---

## Class Binding

Always use CSS Module class references. Never write raw string class names.

```astro
<!-- single class -->
<div class={styles.container}>

<!-- conditional class -->
<div class:list={[styles.button, isActive && styles.active]}>

<!-- variant-based class -->
<div class:list={[styles.button, styles[variant]]}>

<!-- multiple conditional classes -->
<div class:list={[
  styles.alert,
  styles[type],
  isDismissible && styles.dismissible
]}>
```

---

## Astro API Reference

| API | Purpose |
| --- | --- |
| `Astro.props` | Typed component props |
| `Astro.params` | Dynamic route parameters from `[param]` segments |
| `Astro.request` | Server-side `Request` object (headers, cookies, method) |
| `Astro.url` | Current page `URL` object |
| `Astro.site` | Configured site URL from `astro.config.mjs` |
| `Astro.cookies` | Cookie read/write API |
| `Astro.redirect()` | Server-side redirect |
| `getStaticPaths()` | Enumerate paths for SSG dynamic routes |
| `getCollection(name)` | Query an entire content collection |
| `getEntry(collection, id)` | Query a single content entry |

---

## Dynamic Routes With `getStaticPaths`

```astro
---
import styles from './styles.module.css'
import { getCollection } from 'astro:content'
import type { GetStaticPaths } from 'astro'

export const getStaticPaths: GetStaticPaths = async () => {
  const posts = await getCollection('blog')
  return posts.map((post) => ({
    params: { slug: post.slug },
    props: { post },
  }))
}

interface Props {
  post: Awaited<ReturnType<typeof getCollection<'blog'>>>[number]
}

const { post } = Astro.props
const { Content } = await post.render()
---

<article class={styles.article}>
  <h1 class={styles.title}>{post.data.title}</h1>
  <Content />
</article>
```

---

## Service-Layer Data In Pages

Fetch data in page frontmatter. Pass it down to components as typed props.
Components do not call service or repository functions.

```astro
---
import styles from './styles.module.css'
import PostList from '../../components/features/PostList/index.astro'
import { getPublishedPosts } from '../../store/service/posts'

const posts = await getPublishedPosts()
---

<main class={styles.page}>
  <PostList posts={posts} />
</main>
```

---

## Anti-Patterns To Avoid

- **Styles inside `<style>` blocks** — always use a separate `styles.module.css`.
- **Inline `style` attributes** — use CSS Module classes.
- **Bare string class names** — always reference `styles.className`.
- **Business logic in components** — keep it in the service layer.
- **Direct repository or API calls in components** — fetch in page frontmatter.
- **Prop drilling beyond one level** — compose or restructure the data flow.
- **Untyped props** — always define `interface Props`.
- **Complex expressions in template markup** — compute values in frontmatter variables.
