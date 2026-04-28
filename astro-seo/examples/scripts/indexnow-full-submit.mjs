#!/usr/bin/env node
/**
 * indexnow-full-submit.mjs
 *
 * Scans the Astro build output (dist/) for all HTML files, maps them to
 * public URLs, and submits the full list to IndexNow in batches of 10,000.
 *
 * Run after a successful deploy:
 *   node scripts/indexnow-full-submit.mjs
 *
 * Required environment variables:
 *   INDEXNOW_KEY   — your IndexNow API key
 *   SITE_URL       — public site origin, e.g. https://yourdomain.com
 *
 * Optional environment variables:
 *   DIST_DIR       — path to build output (default: dist)
 *   INDEXNOW_HOST  — submission endpoint host (default: api.indexnow.org)
 */

import { readdir } from 'fs/promises'
import { join, relative } from 'path'

const INDEXNOW_KEY = process.env.INDEXNOW_KEY
const SITE_URL = process.env.SITE_URL?.replace(/\/$/, '')
const DIST_DIR = process.env.DIST_DIR ?? 'dist'
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
 * Recursively collect all .html files under a directory.
 */
async function collectHtmlFiles(dir) {
  const entries = await readdir(dir, { withFileTypes: true })
  const files = []
  for (const entry of entries) {
    const fullPath = join(dir, entry.name)
    if (entry.isDirectory()) {
      files.push(...(await collectHtmlFiles(fullPath)))
    } else if (entry.isFile() && entry.name.endsWith('.html')) {
      files.push(fullPath)
    }
  }
  return files
}

/**
 * Map a dist HTML file path to its public URL.
 * dist/index.html          → https://yourdomain.com/
 * dist/blog/post/index.html → https://yourdomain.com/blog/post/
 * dist/about.html          → https://yourdomain.com/about/
 */
function htmlPathToUrl(filePath) {
  const rel = relative(DIST_DIR, filePath).replace(/\\/g, '/')
  if (rel === 'index.html') return `${SITE_URL}/`
  const withoutIndex = rel.replace(/\/index\.html$/, '/')
  const withoutHtml = withoutIndex.endsWith('.html')
    ? withoutIndex.replace(/\.html$/, '/')
    : withoutIndex
  return `${SITE_URL}/${withoutHtml}`
}

/**
 * Submit a batch of URLs to IndexNow. Never throws — logs errors and returns.
 */
async function submitBatch(urlList, batchNumber) {
  const body = JSON.stringify({ host, key: INDEXNOW_KEY, urlList })
  console.log(`Submitting batch ${batchNumber}: ${urlList.length} URLs...`)
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
  let htmlFiles
  try {
    htmlFiles = await collectHtmlFiles(DIST_DIR)
  } catch (err) {
    console.error(`ERROR: Could not read dist directory "${DIST_DIR}": ${err.message}`)
    console.error('Run the Astro build before submitting to IndexNow.')
    process.exit(1)
  }

  const urls = htmlFiles.map(htmlPathToUrl)
  console.log(`Found ${urls.length} URLs to submit from ${DIST_DIR}/`)

  if (urls.length === 0) {
    console.log('No URLs to submit.')
    return
  }

  // Submit in batches
  for (let i = 0; i < urls.length; i += BATCH_SIZE) {
    const batch = urls.slice(i, i + BATCH_SIZE)
    const batchNumber = Math.floor(i / BATCH_SIZE) + 1
    await submitBatch(batch, batchNumber)
  }

  console.log('IndexNow submission complete.')
}

main()
