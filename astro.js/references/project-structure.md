# Project Structure

Full directory breakdown, naming conventions, and configuration for Astro projects
following this skill's conventions.

---

## Top-Level Layout

```
├── src/
├── public/             ← static assets served at root (images, fonts, favicons)
├── dist/               ← build output (gitignored)
├── astro.config.mjs
├── tsconfig.json
├── package.json
└── .env
```

---

## Source Directory (`src/`)

```
src/
├── components/
├── layouts/
├── pages/
├── content/
├── store/
├── styles/
└── utils/
```

---

## Components (`src/components/`)

The `components/` directory contains three distinct groups with different rules
about which technology they use.

```
src/components/
├── foundation/         ← interactive UI primitives — SolidJS or React, NEVER .astro
│   ├── Button/
│   │   ├── index.tsx           ← SolidJS (.tsx) or React (.tsx)
│   │   └── styles.module.css
│   ├── Input/
│   │   ├── index.tsx
│   │   └── styles.module.css
│   ├── Alert/
│   │   ├── index.tsx
│   │   └── styles.module.css
│   └── Modal/
│       ├── index.tsx
│       └── styles.module.css
├── layout/             ← static structural components — .astro
│   ├── Header/
│   │   ├── index.astro
│   │   └── styles.module.css
│   ├── Footer/
│   │   ├── index.astro
│   │   └── styles.module.css
│   └── Nav/
│       ├── index.astro         ← static nav structure; interactive dropdowns are islands
│       └── styles.module.css
└── features/           ← interactive feature components — SolidJS or React islands
    ├── ContactForm/
    │   ├── index.tsx           ← island
    │   └── styles.module.css
    └── DataTable/
        ├── index.tsx           ← island
        └── styles.module.css
```

**`foundation/` rule:** Every component in `components/foundation/` is a SolidJS
or React file (`index.tsx`). These components handle events, manage focus, and
expose typed callbacks. They are never `.astro` files.

**`layout/` rule:** Static structural wrappers are `.astro`. If a layout region
needs interactivity (e.g., a mobile nav toggle), the interactive part is extracted
into a framework island and mounted inside the `.astro` wrapper.

**`features/` rule:** Feature-specific interactive components are framework islands
(`index.tsx`). Purely static feature regions (a read-only summary card, a static
testimonial block) may be `.astro` if they need no interactivity at all.

---

## Layouts (`src/layouts/`)

```
src/layouts/
├── BaseLayout/
│   ├── index.astro
│   └── styles.module.css
└── BlogLayout/
    ├── index.astro
    └── styles.module.css
```

Layouts wrap pages. `BaseLayout` typically sets `<html>`, `<head>`, global meta,
and slot injection points for page content.

---

## Pages (`src/pages/`)

Astro uses file-based routing. Each page is a directory with `index.astro`.

```
src/pages/
├── index/
│   ├── index.astro
│   └── styles.module.css
├── about/
│   ├── index.astro
│   └── styles.module.css
├── blog/
│   ├── index.astro              ← blog listing page
│   └── styles.module.css
└── blog/
    └── [slug]/
        ├── index.astro          ← dynamic blog post page
        └── styles.module.css
```

Pages use `getStaticPaths()` for dynamic routes with SSG.

---

## Content Collections (`src/content/`)

```
src/
├── content.config.ts   ← collection schemas and loaders (Astro 5)
└── content/
    ├── blog/
    │   ├── first-post.md
    │   └── second-post.md
    └── authors/
        └── authors.json
```

Content collections are the canonical way to manage Markdown and data files.
In Astro 5, the config lives at `src/content.config.ts` (not `src/content/config.ts`).
Define schemas using `defineCollection`, `z`, and loaders from `astro/loaders`.

Query collections from page frontmatter using `getCollection()` or `getEntry()`.
Render entries with `render(entry)` imported from `astro:content`.

Read `./content-collections.md` for the full Astro 5 collection API.

---

## Store (`src/store/`)

```
src/store/
├── repository/         ← raw external system calls (Firebase, REST, etc.)
├── service/            ← business logic, validation, data transformation
└── config.ts           ← client configuration and initialization
```

Pages and layouts call service functions from `src/store/service/` in their
frontmatter fence. Components receive data as typed props — they do not call
repository or service functions directly.

---

## Styles (`src/styles/`)

```
src/styles/
├── tokens/
│   ├── _colors.css
│   ├── _spacing.css
│   ├── _typography.css
│   └── _breakpoints.css
├── animations/
│   ├── _fade.css
│   ├── _slide.css
│   └── index.css
├── global.css
└── themes/
    ├── light.css
    └── dark.css
```

`global.css` is imported once in `BaseLayout`. Token files are imported inside
`global.css`. Do not import token files directly from components.

---

## Naming Conventions

| Item | Convention | Example |
| --- | --- | --- |
| Astro component directory | `PascalCase` | `Button/`, `HeroSection/` |
| Layout directory | `PascalCase` | `BaseLayout/`, `BlogLayout/` |
| Page directory | `kebab-case` | `about/`, `blog-post/` |
| Dynamic page segment | `[param]` folder | `[slug]/`, `[...path]/` |
| Component main file | always `index.astro` | `Button/index.astro` |
| Island main file | `index.tsx` or `index.jsx` | `Counter/index.tsx` |
| CSS Module file | always `styles.module.css` | `Button/styles.module.css` |
| Utility file | `kebab-case.ts` | `format-date.ts` |
| Config file | project-standard | `astro.config.mjs`, `tsconfig.json` |

---

## Configuration Files

- `astro.config.mjs` — Astro integrations, adapters, and build configuration
- `tsconfig.json` — TypeScript configuration; extend Astro's strict preset
- `package.json` — dependencies and scripts
- `.env` — environment variables (never committed); use `.env.example` for documentation
