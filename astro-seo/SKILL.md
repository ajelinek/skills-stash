---
name: astro-seo
description: >
  Use this skill when implementing production SEO for an Astro 5 site: metadata
  components, canonical URLs, Open Graph, structured data (JSON-LD), sitemaps,
  robots.txt, IndexNow CI/CD submission, Core Web Vitals, image optimization via
  astro:assets, font performance, and content hygiene. Trigger on requests to
  add SEO to an Astro project, wire up IndexNow, generate a global SEO layout,
  implement JSON-LD schema, or automate URL submission after deploy.
---

# Astro SEO

End-to-end SEO implementation for Astro 5 sites. This skill owns **code
generation and deployment automation** — metadata components, JSON-LD, IndexNow
scripts, and CI/CD wiring. For auditing an existing site use the `seo-audit`
skill. For AI/LLM citation optimization use the `ai-seo` skill.

## Companion Skills — Check First

This skill works best alongside two public skills. If either is not installed,
prompt the user before continuing:

```
The following companion skills improve SEO coverage:
  - seo-audit    → auditing crawlability, on-page factors, and E-E-A-T signals
  - ai-seo       → optimizing content for AI Overviews and LLM citation

Install with:
  npx skills add https://github.com/coreyhaines31/marketingskills --skill seo-audit
  npx skills add https://github.com/coreyhaines31/marketingskills --skill ai-seo

Proceed without them? (yes / install first)
```

If the user chooses to proceed, continue. If they want to install first, pause
and let them do so.

## When To Use This Skill

- Adding a global SEO layout to an Astro project
- Generating JSON-LD structured data components (Article, FAQ, Breadcrumb, etc.)
- Configuring `@astrojs/sitemap` and `robots.txt`
- Setting up IndexNow key verification and CI/CD submission scripts
- Optimizing images with `astro:assets` for Core Web Vitals
- Implementing font performance (self-hosted WOFF2, `font-display: swap`)
- Enforcing staging `noindex` at the environment level
- Wiring full or incremental IndexNow submission into a deploy pipeline

## When Not To Use This Skill

- Auditing an existing site for SEO problems → use `seo-audit`
- Optimizing content for AI Overview citation → use `ai-seo`
- General Astro component and page architecture → use `astro.js`

---

## Constraints

- Astro 5.x only. Use `astro:assets` for all images — no legacy image integration.
- Use `Astro.site` for all absolute URLs. Never hardcode the origin.
- Runtime JS must be minimal — Astro islands only where interactivity is required.
- Use built-in Node `fetch` (Node 18+). No external HTTP libraries for IndexNow scripts.
- OG and Twitter images must be absolute URLs at 1200×630.

---

## Implementation Checklist

Work through these areas in order. Each section links to a reference or example
file for the full implementation detail.

### 1. Base Config

In `astro.config.mjs`:

```js
import { defineConfig } from 'astro/config'
import sitemap from '@astrojs/sitemap'

export default defineConfig({
  site: 'https://yourdomain.com',
  integrations: [sitemap()],
})
```

In `public/robots.txt`:

```
User-agent: *
Allow: /
Sitemap: https://yourdomain.com/sitemap.xml
```

For staging environments, inject `noindex` via a meta tag driven by an env var —
do not rely on `robots.txt` alone for staging isolation.

### 2. Global SEO Layout

Create one layout used by every page. Props: `title`, `description`, `ogImage`,
`type`, `noindex`.

Required tags inside `<head>`:

| Tag | Purpose |
| --- | --- |
| `<title>` | Unique per page, ≤60 chars |
| `<meta name="description">` | Unique, 150–160 chars |
| `<link rel="canonical">` | `href={Astro.url.href}` |
| Open Graph (`og:title`, `og:description`, `og:image`, `og:url`, `og:type`) | Social previews |
| Twitter Card (`twitter:card`, `twitter:title`, etc.) | Twitter/X previews |
| `<meta name="robots">` | Respects `noindex` prop |
| `<html lang>` | Set on `<html>` root |

See `./examples/SeoLayout.astro` for a complete, copy-ready implementation.

### 3. Structured Data (JSON-LD)

Create reusable Astro components that emit `<script type="application/ld+json">`.
Build only what each page type needs — do not include unrelated schema.

| Component | Use on |
| --- | --- |
| `WebSite` + `WebPage` | Every public page |
| `Article` | Blog posts and learn pages |
| `BreadcrumbList` | Any page with a hierarchy |
| `FAQPage` | Pages with FAQ sections |

All JSON-LD URLs must be absolute: `new URL(path, Astro.site).href`.

See `./examples/JsonLd.astro` for all four component variants and the correct
`Astro.site`-based URL construction.

See `./references/structured-data.md` for schema field reference and validation
tools.

### 4. Sitemaps and Canonicalization

- Rely on `@astrojs/sitemap` — it generates `sitemap.xml` automatically from
  all static routes.
- Every content page must have exactly one canonical that matches its public URL.
- For multilingual sites: add `hreflang` alternates and localized entries in the
  sitemap. See `./references/structured-data.md`.

### 5. Images and Media

Use `astro:assets` for all build-time images:

```astro
---
import { Image } from 'astro:assets'
import heroImage from '../assets/hero.jpg'
---
<Image src={heroImage} alt="Descriptive alt text" widths={[400, 800, 1200]} />
```

- Always set descriptive `alt` text.
- Lazy-load non-critical images (`loading="lazy"`).
- OG images: absolute URL, 1200×630, served from `public/`.

### 6. Performance / Core Web Vitals

See `./references/performance-seo.md` for the full checklist. Key rules:

- Self-host fonts as WOFF2 with `font-display: swap`.
- Preload only critical fonts and above-the-fold hero images.
- Preconnect to third-party origins (analytics, etc.).
- Hydrate islands sparingly: prefer `client:visible` or `client:idle` over `client:load`.
- Explicit `width` and `height` on all images to prevent layout shift.
- Include a custom `src/pages/404.astro`.

### 7. Content Hygiene

- One `<h1>` per page.
- Title tags: ≤60 chars, primary keyword near the front.
- Meta descriptions: 150–160 chars, unique per page.
- Clean kebab-case slugs — avoid dates unless the content is date-specific.
- Internal links: related content, previous/next navigation, breadcrumbs.
- Avoid thin or duplicate content across pages.

### 8. IndexNow Setup and CI/CD

IndexNow notifies Bing, Yandex, and other participating engines immediately when
URLs are added, updated, or deleted. Google does not participate — use Google
Search Console and sitemaps for Google coverage.

**Setup:**
1. Generate a key: 8–128 alphanumeric chars (`[a-zA-Z0-9-]`). A UUID works.
2. Store the key as a CI secret (e.g., `INDEXNOW_KEY`).
3. Add `public/<your-key>.txt` containing only the key string.
4. Add the key file path to `.gitignore` if the key is sensitive, or generate it
   at build time from the env var.

**CI/CD wiring (after deploy):**

```yaml
# Example GitHub Actions step
- name: Submit to IndexNow
  run: node scripts/indexnow-full-submit.mjs
  env:
    INDEXNOW_KEY: ${{ secrets.INDEXNOW_KEY }}
    SITE_URL: https://yourdomain.com
```

See `./examples/scripts/indexnow-full-submit.mjs` — scans `dist/` for HTML
files, maps them to URLs, and POSTs in 10k-URL batches.

See `./examples/scripts/indexnow-incremental-submit.mjs` — takes a list of
changed URLs (from git diff or a deploy hook) and submits only those.

See `./references/indexnow.md` for protocol details, response codes, rate limits,
and troubleshooting.

**Failures must not block deploy.** Log errors with status and response body,
then exit 0.

---

## Validation

Before marking SEO implementation complete:

- [ ] Run Google's [Rich Results Test](https://search.google.com/test/rich-results) on key pages
- [ ] Validate schema at [Schema.org Validator](https://validator.schema.org/)
- [ ] Check `sitemap.xml` and `robots.txt` load correctly in production
- [ ] Verify `og:image` with [Facebook Debugger](https://developers.facebook.com/tools/debug/) or Twitter Card validator
- [ ] Run [PageSpeed Insights](https://pagespeed.web.dev/) on the homepage and a content page
- [ ] Confirm IndexNow submission returns HTTP 200 or 202 on first run

---

## Supporting Files

| File | Purpose |
| --- | --- |
| `./examples/SeoLayout.astro` | Global SEO layout — copy and adapt |
| `./examples/JsonLd.astro` | JSON-LD components for all page types |
| `./examples/scripts/indexnow-full-submit.mjs` | Full-site IndexNow submission script |
| `./examples/scripts/indexnow-incremental-submit.mjs` | Incremental IndexNow submission script |
| `./references/indexnow.md` | Protocol reference, response codes, troubleshooting |
| `./references/structured-data.md` | JSON-LD field reference, multilingual, validation |
| `./references/performance-seo.md` | Core Web Vitals checklist and font/image patterns |
