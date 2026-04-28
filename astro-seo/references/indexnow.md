# IndexNow Protocol Reference

IndexNow is an open protocol that lets you push URL change notifications directly
to participating search engines. One submission to `api.indexnow.org` is
automatically shared with all participating engines.

**Participating engines:** Bing, Yandex, Seznam, Naver, Amazon, Yep.  
**Not participating:** Google. Cover Google with sitemaps and Google Search Console.

---

## How It Works

1. You generate a unique API key and host a verification file at your domain root.
2. When content is added, updated, or deleted, you POST the changed URLs to the
   IndexNow endpoint.
3. The endpoint verifies your key file to confirm domain ownership, then accepts
   the URLs.
4. Participating engines share the URLs with each other — one submission covers all.

---

## Key File Setup

**Option 1 (preferred):** Host the key file at the domain root.

```
https://yourdomain.com/<your-key>.txt
```

File contents: the key string only, UTF-8 encoded, no extra whitespace.

For Astro, place the file in `public/`:

```
public/<your-key>.txt
```

Content of the file:

```
<your-key>
```

If the key is a secret, generate the file at build time from an env var rather
than committing it:

```js
// scripts/generate-indexnow-key-file.mjs
import { writeFileSync } from 'fs'
const key = process.env.INDEXNOW_KEY
if (!key) throw new Error('INDEXNOW_KEY env var not set')
writeFileSync(`public/${key}.txt`, key, 'utf-8')
```

**Option 2:** Host the key file at any public path and pass `keyLocation` with
each submission. Only URLs under that path can be submitted with that key. Use
Option 1 to avoid this restriction.

---

## Key Requirements

- 8 to 128 characters
- Allowed: `a-z`, `A-Z`, `0-9`, `-`
- A UUID (with hyphens) is a valid key

---

## Submission Endpoints

Submit to any one endpoint — submissions are shared with all participating engines.

| Engine | Endpoint |
| --- | --- |
| Global (recommended) | `https://api.indexnow.org/indexnow` |
| Bing | `https://www.bing.com/indexnow` |
| Yandex | `https://yandex.com/indexnow` |
| Seznam | `https://search.seznam.cz/indexnow` |

Use the global endpoint unless you have a reason to target a specific engine.

---

## Single URL Submission (GET)

```
GET https://api.indexnow.org/indexnow?url=<url-encoded-page-url>&key=<your-key>
```

Use this for real-time submission from a serverless webhook when a single page
is updated.

---

## Bulk Submission (POST)

Up to 10,000 URLs per request.

```
POST https://api.indexnow.org/indexnow
Content-Type: application/json; charset=utf-8

{
  "host": "www.example.com",
  "key": "<your-key>",
  "urlList": [
    "https://www.example.com/page1",
    "https://www.example.com/blog/post-slug"
  ]
}
```

The `host` field must match the domain of all URLs in `urlList`. URLs from
different domains cannot be batched together.

---

## Response Codes

| Code | Meaning | Action |
| --- | --- | --- |
| `200` | Accepted and processed | Done |
| `202` | Received, key verification pending | Normal on first submission; retry once verified |
| `400` | Bad request — malformed URL or key | Check URL encoding and key format |
| `403` | Key invalid — file not found or content mismatch | Verify key file is accessible and matches |
| `422` | URLs don't match host, or key schema violation | Confirm host/URL alignment; check key characters |
| `429` | Rate limited | Check `Retry-After` header; reduce batch frequency |

A `202` on the first submission is normal — the engine queues key verification.
Subsequent successful submissions return `200`.

---

## Best Practices

**Submit on meaningful changes only:**
- New pages, published blog posts, updated product pages
- Meta/title changes that affect how the page appears in results
- Deleted pages (submit the URL so engines can remove it from their index)
- Do not submit unchanged URLs or cosmetic layout-only changes

**Frequency:**
- Once per deploy is the standard pattern for static sites
- For dynamic content (e.g., user-generated): batch changes every 5–15 minutes
- Wait at least 5 minutes before resubmitting the same URL

**Use IndexNow alongside sitemaps:**
- IndexNow for fast freshness notification
- Sitemaps for complete site inventory and long-tail discovery

**Rate limit handling:**
- Respect `Retry-After` headers on `429` responses
- Never block a deploy on IndexNow failure — log and continue

**Logging:**
- Log timestamp, URLs submitted, HTTP status, and response body for every batch
- Errors should be warnings, not deploy failures

---

## Troubleshooting

**403 Forbidden**
- Key file not accessible at the expected URL
- Key file content does not exactly match the key string
- Test: `curl https://yourdomain.com/<your-key>.txt` — should return the key only

**422 Unprocessable Entity**
- URLs in `urlList` don't match the `host` field
- Key format contains invalid characters
- Same URL submitted repeatedly without content change

**Key file not verifying**
- Check for extra whitespace or BOM in the file
- Confirm the file is reachable without authentication
- Confirm the file name matches the key exactly (case-sensitive)

---

## Incremental Submission Pattern

For CI pipelines that can identify which pages changed in a deploy:

```bash
# Get HTML files changed in the last commit
git diff --name-only HEAD~1 HEAD -- 'dist/**/*.html'
```

Pass that list to `indexnow-incremental-submit.mjs`. See
`../examples/scripts/indexnow-incremental-submit.mjs` for the full implementation.

---

## Serverless Webhook Pattern

To notify IndexNow when a CMS publishes a single page:

```js
// Serverless function (e.g., Netlify/Vercel edge function)
export async function POST(request) {
  const { url } = await request.json()
  const key = process.env.INDEXNOW_KEY
  const endpoint = `https://api.indexnow.org/indexnow?url=${encodeURIComponent(url)}&key=${key}`
  const res = await fetch(endpoint)
  if (!res.ok) console.error('IndexNow error', res.status, await res.text())
  return new Response('ok')
}
```

Trigger this from your CMS publish webhook.
