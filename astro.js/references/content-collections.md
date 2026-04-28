# Content Collections

Astro 5 content collections are the canonical way to manage typed Markdown, MDX,
and structured data files. This reference covers the Astro 5 API — the config
file location, loader pattern, querying, and rendering.

---

## Config File Location

Astro 5 uses `src/content.config.ts` (not `src/content/config.ts`).

```
src/
├── content.config.ts   ← collection schemas and loaders (Astro 5)
├── content/
│   ├── blog/
│   │   ├── first-post.md
│   │   └── second-post.md
│   └── authors/
│       └── jane.json
```

> **Astro 4 note:** The older `src/content/config.ts` location still works for
> backwards compatibility, but new projects should use `src/content.config.ts`.

---

## Defining Collections

Import `defineCollection` and `z` from `astro:content`. Import loaders from
`astro/loaders`. Export a `collections` object.

```ts
// src/content.config.ts
import { defineCollection, z, reference } from 'astro:content'
import { glob, file } from 'astro/loaders'

const blog = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/blog' }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    pubDate: z.coerce.date(),
    draft: z.boolean().default(false),
    author: reference('authors'),   // cross-collection reference
    tags: z.array(z.string()).default([]),
  }),
})

const authors = defineCollection({
  loader: file('./src/content/authors.json'),
  schema: z.object({
    name: z.string(),
    bio: z.string().optional(),
    avatar: z.string().optional(),
  }),
})

export const collections = { blog, authors }
```

### Loader Types

| Loader | Use case |
| --- | --- |
| `glob({ pattern, base })` | Multiple Markdown/MDX/JSON files matching a glob |
| `file(path)` | Single JSON or YAML file containing an array of entries |
| Custom loader | Fetch from a CMS, database, or API at build time |

---

## Querying Collections

Use `getCollection` and `getEntry` from `astro:content` in page frontmatter.

```astro
---
import { getCollection, getEntry } from 'astro:content'

// All entries (filter out drafts in production)
const posts = await getCollection('blog', ({ data }) =>
  import.meta.env.PROD ? !data.draft : true
)

// Single entry by id
const post = await getEntry('blog', 'my-post-slug')

// Resolve a reference
const author = await getEntry(post.data.author)
---
```

Sort and filter before passing to components:

```astro
---
import { getCollection } from 'astro:content'

const posts = (await getCollection('blog'))
  .filter((p) => !p.data.draft)
  .sort((a, b) => b.data.pubDate.valueOf() - a.data.pubDate.valueOf())
---
```

---

## Rendering Entries

In Astro 5, import `render` from `astro:content` and call it with the entry.
The old `entry.render()` method is deprecated.

```astro
---
import { getEntry, render } from 'astro:content'

const post = await getEntry('blog', Astro.params.slug)
if (!post) return Astro.redirect('/404')

const { Content, headings } = await render(post)
---

<article>
  <h1>{post.data.title}</h1>
  <Content />
</article>
```

The `render()` function returns:

| Property | Type | Description |
| --- | --- | --- |
| `Content` | Astro component | The rendered Markdown/MDX body |
| `headings` | `MarkdownHeading[]` | Array of headings with `depth`, `slug`, `text` |
| `remarkPluginFrontmatter` | `Record<string, any>` | Data injected by remark plugins |

---

## Dynamic Routes With Collections

Use `getStaticPaths` with `getCollection` to generate one page per entry.

```astro
---
import { getCollection, render } from 'astro:content'
import type { GetStaticPaths } from 'astro'
import styles from './styles.module.css'
import BaseLayout from '../../../layouts/BaseLayout/index.astro'

export const getStaticPaths: GetStaticPaths = async () => {
  const posts = await getCollection('blog', ({ data }) => !data.draft)
  return posts.map((post) => ({
    params: { slug: post.id },
    props: { post },
  }))
}

const { post } = Astro.props
const { Content, headings } = await render(post)
---

<BaseLayout title={post.data.title} description={post.data.description}>
  <article class={styles.article}>
    <h1 class={styles.title}>{post.data.title}</h1>
    <Content />
  </article>
</BaseLayout>
```

---

## Collection References

Use `reference()` in a schema to create typed cross-collection links.

```ts
import { defineCollection, z, reference } from 'astro:content'

const blog = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/blog' }),
  schema: z.object({
    title: z.string(),
    author: reference('authors'),       // resolves to an authors entry id
    relatedPosts: z.array(reference('blog')).optional(),
  }),
})
```

Resolve references at query time with `getEntry`:

```astro
---
import { getEntry } from 'astro:content'

const author = await getEntry(post.data.author)
---
<p>By {author.data.name}</p>
```

---

## Custom Loaders (Build-Time CMS Fetching)

A custom loader fetches from any external source at build time.

```ts
// src/content.config.ts
import { defineCollection, z } from 'astro:content'

const products = defineCollection({
  loader: async () => {
    const res = await fetch('https://api.example.com/products')
    const data = await res.json()
    // Must return an array of objects with an `id` field
    return data.map((item: any) => ({ id: String(item.slug), ...item }))
  },
  schema: z.object({
    id: z.string(),
    name: z.string(),
    price: z.number(),
    inStock: z.boolean(),
  }),
})

export const collections = { products }
```

---

## Runtime Collections (`getLiveCollection`)

For on-demand rendered pages (SSR) that need fresh data at request time,
use `getLiveCollection` instead of `getCollection`. This bypasses the build-time
cache and re-fetches from the loader on every request.

```astro
---
// Only valid in on-demand rendered pages (output: 'server' or prerender: false)
import { getLiveCollection } from 'astro:content'

const posts = await getLiveCollection('blog')
---
```

Use `getLiveCollection` sparingly — prefer `getCollection` for static pages where
build-time data is acceptable.

---

## Anti-Patterns

- **Defining collections in `src/content/config.ts`** — use `src/content.config.ts` in Astro 5.
- **Calling `entry.render()`** — use `render(entry)` imported from `astro:content`.
- **Importing `z` from `zod` directly** — import from `astro:content` (`import { z } from 'astro:content'`) so Astro can process the schema.
- **Fetching collection data in components** — always query in page frontmatter, pass as props.
- **Skipping the schema** — always define a `schema` with `z.object(...)` for type safety.
