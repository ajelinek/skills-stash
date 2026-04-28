# Structured Data Reference

JSON-LD structured data helps search engines and AI systems understand your
content type, relationships, and key attributes. Implement only the schemas
relevant to each page — do not include unrelated markup.

---

## General Rules

- All JSON-LD must be in `<script type="application/ld+json">` tags in `<head>`.
- All URLs must be absolute: use `new URL(path, Astro.site).href`.
- Validate with [Rich Results Test](https://search.google.com/test/rich-results)
  (renders JavaScript — more reliable than static HTML inspection) and
  [Schema.org Validator](https://validator.schema.org/).
- Include only the schemas the page actually represents. A blog post does not
  need `Product` schema.

---

## WebSite Schema

Add once, on the homepage. Enables sitelinks search box if eligible.

```json
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "Your Site Name",
  "url": "https://yourdomain.com",
  "description": "Short description of the site"
}
```

---

## WebPage Schema

Add on every public page. Provides basic page identity.

```json
{
  "@context": "https://schema.org",
  "@type": "WebPage",
  "name": "Page Title",
  "url": "https://yourdomain.com/page-slug",
  "description": "Page meta description",
  "isPartOf": {
    "@type": "WebSite",
    "url": "https://yourdomain.com"
  }
}
```

---

## Article Schema

Use on blog posts, tutorials, and editorial content. Required for Google's
Article rich result eligibility.

```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "How to Do the Thing",
  "description": "A concise description matching the meta description.",
  "image": "https://yourdomain.com/og/article-slug.png",
  "datePublished": "2025-03-01T00:00:00Z",
  "dateModified": "2025-04-10T00:00:00Z",
  "author": {
    "@type": "Person",
    "name": "Author Name",
    "url": "https://yourdomain.com/authors/author-slug"
  },
  "publisher": {
    "@type": "Organization",
    "name": "Your Site Name",
    "logo": {
      "@type": "ImageObject",
      "url": "https://yourdomain.com/logo.png"
    }
  }
}
```

- `datePublished` and `dateModified` must be ISO 8601 with timezone.
- `image` should be the OG image (1200×630).
- `author.url` should be a real author page if one exists.

---

## BreadcrumbList Schema

Add on any page that has a visible breadcrumb navigation.

```json
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "name": "Home",
      "item": "https://yourdomain.com"
    },
    {
      "@type": "ListItem",
      "position": 2,
      "name": "Blog",
      "item": "https://yourdomain.com/blog"
    },
    {
      "@type": "ListItem",
      "position": 3,
      "name": "Article Title",
      "item": "https://yourdomain.com/blog/article-slug"
    }
  ]
}
```

Position numbers are 1-indexed. The last item is the current page.

---

## FAQPage Schema

Add on pages that contain a visible FAQ section with question/answer pairs.

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "What is the return policy?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "We offer 30-day returns on all products."
      }
    },
    {
      "@type": "Question",
      "name": "Do you ship internationally?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes, we ship to over 50 countries."
      }
    }
  ]
}
```

The `text` in `acceptedAnswer` may contain basic HTML. Keep answers concise and
directly responsive to the question.

---

## Organization Schema

Add once, typically in the global layout or homepage. Helps establish entity
recognition for your brand.

```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "Your Company Name",
  "url": "https://yourdomain.com",
  "logo": "https://yourdomain.com/logo.png",
  "sameAs": [
    "https://twitter.com/yourhandle",
    "https://linkedin.com/company/yourcompany"
  ]
}
```

---

## Combining Multiple Schemas

Use a JSON-LD array or `@graph` when a page needs multiple schemas:

```json
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "WebPage",
      "url": "https://yourdomain.com/blog/post-slug",
      "name": "Post Title"
    },
    {
      "@type": "Article",
      "headline": "Post Title",
      "datePublished": "2025-01-01T00:00:00Z"
    },
    {
      "@type": "BreadcrumbList",
      "itemListElement": []
    }
  ]
}
```

---

## Multilingual Sites: hreflang

For multilingual Astro sites, add hreflang in every page's `<head>`:

```astro
---
// Locales your site supports
const locales = ['en', 'es', 'fr']
const baseUrl = Astro.site!.href.replace(/\/$/, '')
const currentPath = Astro.url.pathname
  .replace(/^\/(en|es|fr)/, '')  // strip locale prefix
---

{locales.map((lang) => (
  <link
    rel="alternate"
    hreflang={lang}
    href={`${baseUrl}/${lang}${currentPath}`}
  />
))}
<link rel="alternate" hreflang="x-default" href={`${baseUrl}/en${currentPath}`} />
```

**Rules:**
- Every page must include a self-referencing entry (its own locale in the set).
- Reciprocal: if `/en/page` points to `/es/page`, then `/es/page` must point
  back to `/en/page`.
- `x-default` should point to the default/fallback locale.
- All hreflang URLs must be canonical, indexable, and return HTTP 200.
- Invalid codes like `en-UK` (use `en-GB`) break the entire hreflang cluster.

For sites with many locales (10+), consider encoding hreflang in the sitemap
rather than in each page's HTML to reduce per-page weight.

---

## Validation Workflow

1. Run the [Rich Results Test](https://search.google.com/test/rich-results) on
   each page type — it renders JavaScript and catches dynamically injected schema
   that `curl` or static inspection misses.
2. Run the [Schema.org Validator](https://validator.schema.org/) for full field
   coverage and type checking.
3. After deploy, spot-check in Google Search Console → Enhancements to confirm
   Google detected the schema.

> Note: `web_fetch` and `curl` strip `<script>` tags and cannot see JSON-LD
> injected by JavaScript. Always use the Rich Results Test for accurate validation.
