---
name: astro.js
description: >
  Use this skill when writing or refactoring Astro TypeScript code: Astro for
  static pages and layouts, SolidJS or React islands for all interactivity, CSS
  Modules in separate files, hydration directives, content collections, server
  islands, on-demand rendering, Astro Actions, and accessible semantic HTML.
  Use alongside `ui-engineering` whenever the task also involves shared UI
  structure, styling, semantics, accessibility, or foundation-component
  decisions.
  Trigger on requests to build an Astro page, layout, island, action, or
  server-rendered feature.
---

# Astro

Astro owns static structure: pages, layouts, and purely presentational regions.
SolidJS or React owns all interactivity: every component that handles user input,
manages state, or responds to events is a framework island — not an `.astro` file.

CSS Modules are used for all component styling — always in a separate
`styles.module.css` file, never inline or inside the Astro `<style>` block.

## When To Use This Skill

- Structuring a new Astro project or adding pages and layout areas
- Building `.astro` pages, layouts, or static presentational regions
- Deciding whether something belongs in Astro or in a SolidJS/React island
- Choosing which hydration directive to use for an island
- Applying CSS Modules styling within `.astro` files or framework islands
- Working with content collections (`src/content/`, `src/content.config.ts`)
- Wiring service-layer data into server-rendered Astro pages
- Using server islands (`server:defer`) for personalized deferred regions
- Setting up on-demand rendering (SSR) with adapters and middleware
- Defining and calling Astro Actions for type-safe server mutations

## Astro vs Islands — The Core Architecture Decision

**This is the most important decision in any Astro project.**

| What it does | Use |
| --- | --- |
| Renders static HTML from data — no user interaction | `.astro` |
| Page shell, layout wrapper, navigation structure | `.astro` |
| Content sections, blog posts, marketing regions | `.astro` |
| Any component with `onClick`, `onChange`, form state, or reactive data | SolidJS or React island |
| Foundational UI components (Button, Input, Modal, Alert, etc.) | SolidJS or React island |
| Any component that reads or writes to a store or service hook | SolidJS or React island |

**The rule in plain terms:**

- Astro renders structure and content. It does not handle user interaction.
- SolidJS or React handles all interactivity, all form state, and all foundational
  interactive UI primitives — even a simple button that fires an event.
- Do not build interactive UI in `.astro` files. Astro does not have reactivity.
  Attempting to add interactivity to an `.astro` file produces fragile, un-testable code.

**Which framework — SolidJS or React?**

The project uses one consistently. Check `astro.config.mjs` for the configured
integration (`@astrojs/solid-js` or `@astrojs/react`) and use that framework for
all islands in the project. Do not mix both frameworks in the same project.

Read `./references/islands-and-hydration.md` for the full decision guide and
hydration directive reference.

## Styling Rules — CSS Modules In Separate Files

**This is the most critical rule in this skill.**

Every Astro component, page, and layout uses CSS Modules for scoped styling.
The CSS lives in a separate file — never inside the Astro `<style>` tag.

```
ComponentName/
├── index.astro         ← component logic and markup
└── styles.module.css   ← ALL styles for this component, always a separate file
```

- **Always** create `styles.module.css` alongside `index.astro`.
- **Never** put styles inside Astro's `<style>` block.
- **Never** use inline `style` attributes.
- Import the module at the top of the frontmatter fence: `import styles from './styles.module.css'`
- Apply classes using the `class:list` directive or direct class binding:
  - `<div class={styles.container}>`
  - `<div class:list={[styles.container, isActive && styles.active]}>`
- Use semantic class names. No utility-class stacking.
- Use CSS custom properties for all design tokens (colors, spacing, typography).
- No `!important`. No deep selectors. No ID selectors for styling.

Read `./references/styling-and-css-modules.md` for token strategy, theme
variables, responsive rules, and animation guidance.
Read `./examples/button-component/` for a complete Button example with separate
CSS Module file.

## Project Structure

```
src/
├── components/
│   ├── foundation/         # Interactive UI primitives — SolidJS or React, NOT .astro
│   │   ├── Button/
│   │   │   ├── index.tsx           ← SolidJS (.tsx) or React (.tsx)
│   │   │   └── styles.module.css
│   │   └── Input/
│   │       ├── index.tsx
│   │       └── styles.module.css
│   ├── layout/             # Static layout structure — .astro
│   │   ├── Header/
│   │   │   ├── index.astro
│   │   │   └── styles.module.css
│   │   └── Footer/
│   │       ├── index.astro
│   │       └── styles.module.css
│   └── features/           # Interactive feature areas — SolidJS or React
│       └── SomeFeature/
│           ├── index.tsx           ← island component
│           └── styles.module.css
├── layouts/
│   └── BaseLayout/
│       ├── index.astro             ← layout shell is always .astro
│       └── styles.module.css
├── pages/
│   ├── index/
│   │   ├── index.astro             ← page is always .astro
│   │   └── styles.module.css
│   └── [dynamic]/
│       ├── index.astro
│       └── styles.module.css
├── content/
│   ├── blog/
│   └── [collection-name]/
├── content.config.ts   ← Astro 5 collection schemas and loaders
├── store/
│   ├── repository/
│   ├── service/
│   └── config.ts
├── styles/
│   ├── tokens/
│   │   ├── _colors.css
│   │   ├── _spacing.css
│   │   └── _typography.css
│   ├── global.css
│   └── themes/
│       ├── light.css
│       └── dark.css
└── utils/
```

**Naming conventions:**
- `.astro` pages and layouts: `PascalCase/` folder with `index.astro`
- Framework island components: `PascalCase/` folder with `index.tsx`
- Pages: `kebab-case/` folder with `index.astro` or `[dynamic]/` with `index.astro`
- CSS Module files: always `styles.module.css` — one per component directory
- Utilities: `kebab-case.ts`

Read `./references/project-structure.md` for a full breakdown of directory
responsibilities and naming conventions.

## Astro Component Shape

`.astro` files are for static structure only. They render HTML from props and
data — they do not handle events or manage state.

- Use typed props via `interface Props` in the frontmatter fence.
- Access props with `Astro.props`.
- Keep components small and single-purpose.
- Prefer composition over prop drilling.
- Keep expressions simple; move complex logic into frontmatter variables.
- Use semantic HTML elements — `<section>`, `<article>`, `<nav>`, `<main>`, `<header>` —
  instead of generic `<div>` wrappers when the element has semantic meaning.

```astro
---
import styles from './styles.module.css'

interface Props {
  title: string
  subtitle?: string
}

const { title, subtitle } = Astro.props
---

<section class={styles.hero} aria-label={title}>
  <h1 class={styles.title}>{title}</h1>
  {subtitle && <p class={styles.subtitle}>{subtitle}</p>}
  <slot />
</section>
```

Read `./references/component-patterns.md` for frontmatter conventions, slot usage,
and Astro API reference.

## Foundational Components — SolidJS or React, Not Astro

Foundational UI primitives (Button, Input, Alert, Modal, Select, Toggle, etc.)
are **always** built as SolidJS or React components. They are **never** `.astro` files.

**Why:** Foundational components handle user events, manage focus, expose `onClick`
and `onChange` callbacks, and sometimes hold internal state. None of this is
possible in an `.astro` file. Building a "button" as `.astro` produces static HTML
that can't respond to clicks in a typed, reusable way.

The decision rule:

1. **Primitive exists** — use it.
2. **Primitive is close but missing a prop** — extend the existing primitive.
3. **Primitive does not exist** — create it as a SolidJS or React component in
   `components/foundation/` before using it. Never inline one-off interactive
   elements in page or feature components.

All foundational components must be consistent, accessible, and strongly typed.
Refer to the `solid.js` or `react` skill for the implementation conventions that
apply inside island components.

## Islands And Hydration

Every interactive component is an island. Mount islands from `.astro` pages and
layouts using a `client:*` directive. Choose the minimum directive that satisfies
the interaction requirement.

| Directive | When to use |
| --- | --- |
| `client:load` | Must be interactive immediately on page load |
| `client:idle` | Can wait until the browser is idle |
| `client:visible` | Only needs to hydrate when it enters the viewport |
| `client:media="(query)"` | Only interactive at a specific viewport size |
| `client:only="solid-js"` or `client:only="react"` | Requires browser APIs at render; skip SSR |

Default to `client:visible` or `client:idle`. Use `client:load` only for UI the
user will interact with immediately — primary forms, navigation dropdowns, auth pages.

Island components always have their own `styles.module.css`:

```
components/features/ContactForm/
├── index.tsx          ← SolidJS or React island
└── styles.module.css  ← separate CSS Module, same rule as everywhere else
```

Mounting an island from an Astro page:

```astro
---
import styles from './styles.module.css'
import ContactForm from '../../components/features/ContactForm/index.tsx'

const { prefillEmail } = Astro.props
---

<section class={styles.section}>
  <h2 class={styles.heading}>Contact Us</h2>
  <ContactForm client:visible prefillEmail={prefillEmail} />
</section>
```

Read `./references/islands-and-hydration.md` for the full decision guide,
framework-specific notes, and data-passing rules.

## Content Collections

Content collections are the canonical way to manage Markdown, MDX, and
structured data files with full TypeScript type safety.

**Astro 5 key changes:**

- Config lives at `src/content.config.ts` (not `src/content/config.ts`)
- Collections use a `loader` — `glob()` or `file()` from `astro/loaders`
- `render(entry)` is a function imported from `astro:content` (not `entry.render()`)
- Import `z` from `astro:content`, not directly from `zod`

```ts
// src/content.config.ts
import { defineCollection, z, reference } from 'astro:content'
import { glob } from 'astro/loaders'

const blog = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/blog' }),
  schema: z.object({
    title: z.string(),
    pubDate: z.coerce.date(),
    draft: z.boolean().default(false),
  }),
})

export const collections = { blog }
```

Render in a page:

```astro
---
import { getEntry, render } from 'astro:content'
const post = await getEntry('blog', Astro.params.slug)
const { Content } = await render(post)
---
<Content />
```

Read `./references/content-collections.md` for the full API: loaders, cross-collection
references, custom loaders, runtime collections, and dynamic route patterns.

## Server Islands, SSR, and Actions

### Server Islands (`server:defer`)

Defer a personalized or dynamic `.astro` component while serving the page shell
immediately. Requires an adapter.

```astro
<UserCart server:defer>
  <span slot="fallback">···</span>
</UserCart>
```

The deferred component runs server-side and streams in. Use it for user-specific
UI (cart counts, notifications, personalized greetings) that would otherwise block
static page delivery.

### On-Demand Rendering (SSR)

Opt pages into server rendering with `export const prerender = false` (hybrid mode)
or set `output: 'server'` globally.

SSR pages have access to `Astro.cookies`, `Astro.request`, `Astro.redirect()`,
and `Astro.locals` (populated by middleware).

### Middleware

Define request-intercepting logic in `src/middleware.ts`:

```ts
import { defineMiddleware } from 'astro:middleware'

export const onRequest = defineMiddleware(async (context, next) => {
  context.locals.user = await getUser(context.cookies.get('session')?.value)
  return next()
})
```

### Astro Actions

Type-safe server functions defined in `src/actions/index.ts`, callable from
islands or HTML forms:

```ts
// src/actions/index.ts
import { defineAction, ActionError } from 'astro:actions'
import { z } from 'astro:content'

export const server = {
  newsletter: {
    subscribe: defineAction({
      input: z.object({ email: z.string().email() }),
      handler: async ({ email }) => {
        await addSubscriber(email)
        return { success: true }
      },
    }),
  },
}
```

Call from an island:

```ts
import { actions } from 'astro:actions'
const { data, error } = await actions.newsletter.subscribe({ email })
```

Use `isInputError(error)` to distinguish Zod validation errors from handler errors.

Read `./references/server-rendering.md` for full coverage: rendering modes,
adapter config, middleware, server islands, on-demand APIs, actions with forms,
error codes, typed env vars (`astro:env`), and view transitions.

## Astro API Reference

- `Astro.props` — typed component props
- `Astro.params` — dynamic route parameters (`[slug]`, `[...path]`)
- `Astro.request` — server-side request object (headers, cookies, URL)
- `Astro.url` — current page URL
- `getStaticPaths()` — enumerate paths for static site generation
- `getEntry()` / `getCollection()` — content collection queries

## Service-Layer Data Flow

Astro pages and layouts are the correct place to call service or repository
functions in the frontmatter fence. Components should receive data as props.

- Fetch data in page frontmatter, not inside components.
- Pass data down as typed props.
- Components must not call repositories or external APIs directly.
- Keep validation and business logic in the service layer.

## Accessibility

- Use semantic HTML elements wherever the element has meaning.
- Add ARIA attributes where they add real semantic information.
- Ensure all interactive elements have accessible names.
- Maintain visible focus states.
- Keep a minimum 44px touch target size for interactive elements.
- Respect `prefers-reduced-motion`.
- Structure headings logically (`h1` → `h2` → `h3`) within page content.

Read `./references/accessibility-patterns.md` for ARIA patterns, form labels,
and heading hierarchy guidance.

## Supporting Files

- `./references/styling-and-css-modules.md`
  CSS Modules rules, token strategy, theming, animation, and global style organization.
- `./references/project-structure.md`
  Full directory breakdown, technology rules per layer, naming conventions, and config files.
- `./references/component-patterns.md`
  Frontmatter shape, typed props, slot usage, Astro API reference, and anti-patterns.
- `./references/islands-and-hydration.md`
  The Astro-vs-islands decision guide, framework selection, hydration directives, and data passing.
- `./references/content-collections.md`
  Astro 5 collection config, loaders, `render()`, cross-collection references, and dynamic routes.
- `./references/server-rendering.md`
  Server islands (`server:defer`), on-demand rendering (SSR), middleware, Astro Actions,
  typed env vars, and view transitions.
- `./references/accessibility-patterns.md`
  WCAG 2.1 AA requirements, ARIA usage, form labels, and keyboard navigation.
- `./examples/button-component/`
  Foundational Button as a SolidJS component with CSS Modules in a separate file.
  Demonstrates that foundational components are framework islands, not .astro files.
- `./examples/base-layout/`
  BaseLayout (.astro) with typed props, slot usage, skip link, and separate CSS Module.
- `./examples/island-counter/`
  Interactive SolidJS island with `client:visible` mounted from an Astro wrapper.

## Quality Bar

- Every `.astro` file has a sibling `styles.module.css`. No exceptions.
- Styles are never written inside Astro `<style>` blocks.
- Astro files contain no user event handlers — clicks, inputs, and form state
  live in SolidJS or React island components.
- Foundational UI components (Button, Input, Alert, Modal, etc.) are SolidJS or
  React — never `.astro`.
- Props are typed via `interface Props` in the frontmatter fence.
- Foundational components are used or extended — never re-invented inline.
- Hydration directives are the minimum needed (`client:visible` or `client:idle`
  over `client:load` unless the interaction must be immediately available).
- The project uses one framework consistently — SolidJS or React, not both.
- Semantic HTML is used; generic `<div>` is a last resort.
- Every interactive element has an accessible name.
- Service and repository calls live in page frontmatter, not in components.
- CSS custom properties are used for all design tokens.
- No inline styles. No `!important`. No utility-class stacking.
