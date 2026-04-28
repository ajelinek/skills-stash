# Performance SEO Reference

Core Web Vitals and loading performance directly affect search rankings. These
are the Astro-specific patterns to meet Google's thresholds.

---

## Core Web Vitals Targets

| Metric | Target | What It Measures |
| --- | --- | --- |
| LCP (Largest Contentful Paint) | < 2.5s | How fast the main content loads |
| INP (Interaction to Next Paint) | < 200ms | Responsiveness to user input |
| CLS (Cumulative Layout Shift) | < 0.1 | Visual stability — no unexpected shifts |

Measure with [PageSpeed Insights](https://pagespeed.web.dev/) and Google Search
Console's Core Web Vitals report (field data, not just lab data).

---

## Images

### Use `astro:assets` for All Build-Time Images

```astro
---
import { Image } from 'astro:assets'
import heroImg from '../assets/hero.jpg'
---

<!-- Responsive, optimized, explicit dimensions -->
<Image
  src={heroImg}
  alt="Descriptive alt text describing the image content"
  widths={[400, 800, 1200]}
  sizes="(max-width: 640px) 400px, (max-width: 1024px) 800px, 1200px"
/>
```

- `astro:assets` generates WebP/AVIF automatically with fallbacks.
- Always provide `widths` and `sizes` for above-the-fold images.
- The Image component sets explicit `width` and `height` to prevent CLS.
- Never use the legacy `@astrojs/image` integration on Astro 5.

### Lazy Loading

```astro
<!-- Above the fold — do not lazy load -->
<Image src={heroImg} alt="..." loading="eager" fetchpriority="high" />

<!-- Below the fold — lazy load -->
<Image src={cardImg} alt="..." loading="lazy" />
```

### OG/Social Images

OG images are served from `public/` and referenced as absolute URLs:

```astro
---
const ogImageUrl = new URL('/og/my-page.png', Astro.site).href
---
<meta property="og:image" content={ogImageUrl} />
```

- Dimensions: 1200×630 for both OG and Twitter Card.
- Serve as static PNG or JPG from `public/og/`.
- For dynamic OG images, use a build-time script or a serverless endpoint.

---

## Fonts

### Self-Host WOFF2

Download fonts from Google Fonts or the vendor and serve them yourself. This
avoids a third-party DNS lookup on every page load.

```
public/fonts/
  inter-400.woff2
  inter-700.woff2
```

### CSS Font Declaration

```css
@font-face {
  font-family: 'Inter';
  src: url('/fonts/inter-400.woff2') format('woff2');
  font-weight: 400;
  font-style: normal;
  font-display: swap;
}

@font-face {
  font-family: 'Inter';
  src: url('/fonts/inter-700.woff2') format('woff2');
  font-weight: 700;
  font-style: normal;
  font-display: swap;
}
```

`font-display: swap` prevents invisible text during font load (FOIT) and reduces
CLS impact from font metrics.

### Preload Critical Fonts

```astro
---
// In your SEO layout <head>
---
<link
  rel="preload"
  href="/fonts/inter-400.woff2"
  as="font"
  type="font/woff2"
  crossorigin
/>
```

Only preload the font weights actually used above the fold. Preloading unused
fonts wastes bandwidth.

---

## Resource Hints

### Preconnect to Third Parties

```astro
<!-- Preconnect to analytics or other critical third parties -->
<link rel="preconnect" href="https://www.googletagmanager.com" />
<link rel="dns-prefetch" href="https://www.googletagmanager.com" />
```

Use `preconnect` only for origins your page actually connects to on load.
Too many preconnects create competition for the browser's connection pool.

### Preload Hero Image

If the LCP element is a background image or an `<img>` tag whose `src` is
dynamically determined, preload it explicitly:

```astro
<link
  rel="preload"
  href="/images/hero.webp"
  as="image"
  type="image/webp"
/>
```

For `astro:assets` `<Image>` components, the browser can discover the image
from the `src` attribute directly — preloading is optional but can help LCP.

---

## JavaScript and Hydration

### Defer Non-Critical Islands

```astro
<!-- Loads only when visible in viewport -->
<MyWidget client:visible />

<!-- Loads during browser idle time -->
<MyWidget client:idle />

<!-- Loads immediately on page load — use sparingly -->
<MyWidget client:load />
```

`client:load` delays the page's Time to Interactive. Prefer `client:visible` for
below-the-fold components and `client:idle` for non-critical UI.

### Avoid Unnecessary Islands

Not every interactive element needs an island. Static navigation, accordions
driven by CSS `:target` or `<details>`, and disclosure patterns often require
no JavaScript at all.

---

## Layout Stability (CLS)

### Explicit Image Dimensions

The `astro:assets` `<Image>` component handles this automatically by reading
source image dimensions at build time. For `<img>` tags:

```html
<!-- Always provide width and height -->
<img src="/icons/logo.svg" alt="Logo" width="120" height="40" />
```

### Font Metrics

`font-display: swap` causes a brief layout shift when the web font swaps in.
Minimize this by using `size-adjust`, `ascent-override`, or similar font metric
descriptors to match the fallback font metrics:

```css
@font-face {
  font-family: 'Inter-fallback';
  src: local('Arial');
  ascent-override: 90%;
  size-adjust: 107%;
}
```

Then set the fallback in the font stack:

```css
body {
  font-family: 'Inter', 'Inter-fallback', sans-serif;
}
```

### Ads and Embeds

Reserve space for any dynamically loaded content (ads, embeds, banners) using
`min-height` or an aspect-ratio wrapper to prevent CLS when content loads.

---

## Staging Isolation

Prevent staging content from being indexed. Do not rely on robots.txt alone —
crawlers may ignore it.

```astro
---
// In your SEO layout
const isStaging = import.meta.env.PUBLIC_STAGING === 'true'
---
{isStaging && <meta name="robots" content="noindex, nofollow" />}
```

Set `PUBLIC_STAGING=true` in the staging environment config. Remove or set to
`false` in production.

---

## 404 Page

A missing or broken 404 page causes crawl errors and soft-404 signals.

```
src/pages/404.astro
```

The 404 page must:
- Return HTTP status 404 (Astro does this automatically for `404.astro`)
- Use the global SEO layout with `noindex` set to `true`
- Provide clear navigation back to the site
- Not redirect to the homepage (that creates soft-404s)

---

## Performance Checklist

- [ ] All build-time images use `astro:assets` `<Image>`
- [ ] Explicit `width` and `height` on all `<img>` elements
- [ ] Non-critical images have `loading="lazy"`
- [ ] Above-fold hero image has `loading="eager"` and `fetchpriority="high"`
- [ ] OG images are 1200×630, served from `public/`
- [ ] Fonts are self-hosted WOFF2 with `font-display: swap`
- [ ] Critical fonts are preloaded with correct `as="font"` and `crossorigin`
- [ ] `preconnect` added for critical third parties only
- [ ] Islands use `client:visible` or `client:idle` instead of `client:load`
- [ ] `src/pages/404.astro` exists and returns real 404 status
- [ ] Staging environment sets `noindex` via env var
- [ ] PageSpeed Insights score ≥ 90 on mobile for key pages
