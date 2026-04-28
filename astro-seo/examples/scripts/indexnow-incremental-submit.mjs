#!/usr/bin/env node
/**
 * indexnow-incremental-submit.mjs
 *
 * Submits only a specified list of URLs to IndexNow. Designed for use in CI
 * pipelines after detecting which pages actually changed in the current deploy.
 *
 * Usage — pass URLs as arguments or via stdin (newline-separated):
 *   node scripts/indexnow-incremental-submit.mjs https://yourdomain.com/blog/post-1/ https://yourdomain.com/about/
 *   git diff --name-only HEAD~1 | node scripts/indexnow-incremental-submit.mjs
 *
 * In a GitHub Actions workflow (after build):
 *   CHANGED=$(git diff --name-only ${{ github.event.before }} ${{ github.sha }} \
 *     | grep '^dist/.*\.html$' \
 *     | sed 's|^dist/||; s|index\.html$|/|; s|\.html$|/|; s|^|https://yourdomain.com/|')
 *   echo "$CHANGED" | node scripts/indexnow-incremental-submit.mjs
 *
 * Required environment variables:
 *   INDEXNOW_KEY   — your IndexNow API key
 *   SITE_URL       — public site origin, e.g. https://yourdomain.com
 *
 * Optional environment variables:
 *   INDEXNOW_HOST  — submission endpoint host (default: api.indexnow.org)
 */

import { createInterface } from 'readline'

const INDEXNOW_KEY = process.env.INDEXNOW_KEY
const SITE_URL = process.env.SITE_URL?.replace(/\/$/, '')
const INDEXNOW_HOST = process.env.INDEXNOW_HOST ?? 'api.indexnow.org'
const BATCH_SIZE = 10_000
const ENDPOINT = `https://${INDEXNOW_HOST}/indexnow`

if (!INDEXNOW_KEY) {
  console.error('ERROR: INDEXNOW_KEY environment variable is not set.')
  process.exit(1)
}
if (!SITE_URL) {
  console.error('ERROR: SITE_URL environment variable is not set.')
  process.exit(1)
}

const host = new URL(SITE_URL).hostname

/**
 * Collect URLs from CLI args or stdin (newline-separated).
 * Filters to only include URLs that belong to SITE_URL.
 * Also accepts dist-relative HTML paths and converts them to URLs.
 */
async function collectUrls() {
  const args = process.argv.slice(2)

  if (args.length > 0) {
    return normalizeUrls(args)
  }

  // Read from stdin
  if (process.stdin.isTTY) {
    console.error('ERROR: No URLs provided. Pass as arguments or pipe newline-separated URLs via stdin.')
    process.exit(1)
  }

  const lines = []
  const rl = createInterface({ input: process.stdin, crlfDelay: Infinity })
  for await (const line of rl) {
    const trimmed = line.trim()
    if (trimmed) lines.push(trimmed)
  }

  return normalizeUrls(lines)
}

/**
 * Normalize a list of strings into full URLs.
 * Accepts:
 *   - Full https:// URLs (must match SITE_URL host)
 *   - dist-relative HTML paths: dist/blog/post/index.html → https://yourdomain.com/blog/post/
 */
function normalizeUrls(inputs) {
  const urls = []
  for (const input of inputs) {
    if (input.startsWith('http://') || input.startsWith('https://')) {
      const parsed = new URL(input)
      if (parsed.hostname === host) {
        urls.push(input)
      } else {
        console.warn(`  Skipping URL from different host: ${input}`)
      }
    } else if (input.endsWith('.html')) {
      // Convert dist-relative path to URL
      const rel = input.replace(/^dist\//, '')
      if (rel === 'index.html') {
        urls.push(`${SITE_URL}/`)
      } else {
        const path = rel.replace(/\/index\.html$/, '/').replace(/\.html$/, '/')
        urls.push(`${SITE_URL}/${path}`)
      }
    } else {
      console.warn(`  Skipping unrecognized input: ${input}`)
    }
  }
  return [...new Set(urls)] // deduplicate
}

/**
 * Submit a batch of URLs to IndexNow. Never throws — logs errors and returns.
 */
async function submitBatch(urlList, batchNumber) {
  const body = JSON.stringify({ host, key: INDEXNOW_KEY, urlList })
  console.log(`Submitting batch ${batchNumber}: ${urlList.length} URL(s)...`)
  try {
    const res = await fetch(ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json; charset=utf-8' },
      body,
    })
    if (res.ok || res.status === 202) {
      console.log(`  Batch ${batchNumber}: HTTP ${res.status} — accepted.`)
    } else {
      const text = await res.text().catch(() => '')
      console.error(`  Batch ${batchNumber}: HTTP ${res.status} — ${text}`)
    }
  } catch (err) {
    console.error(`  Batch ${batchNumber}: Network error — ${err.message}`)
  }
}

async function main() {
  const urls = await collectUrls()

  if (urls.length === 0) {
    console.log('No URLs to submit.')
    return
  }

  console.log(`Submitting ${urls.length} changed URL(s) to IndexNow...`)

  for (let i = 0; i < urls.length; i += BATCH_SIZE) {
    const batch = urls.slice(i, i + BATCH_SIZE)
    const batchNumber = Math.floor(i / BATCH_SIZE) + 1
    await submitBatch(batch, batchNumber)
  }

  console.log('IndexNow incremental submission complete.')
}

main()
