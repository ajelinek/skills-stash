#!/usr/bin/env node
// normalize-timeseries.mjs — pure transform, no network/CLI calls. Reads raw
// JSON files an agent already saved (from the GA4/GSC companion-skill CLIs,
// `firebase auth:export`, and correlate-window.mjs/`gh`) out of a working
// directory, and merges them into one canonical dataset keyed by calendar
// date in the configured timezone. See ../references/data-normalization.md
// for the full contract this implements.
//
// Usage:
//   node normalize-timeseries.mjs --config <path> --in <dir> [--out <file>]
//   node normalize-timeseries.mjs --help
//
// File naming convention read from --in:
//   ga4-*.json             GA4 companion-skill output (or raw Data API runReport response)
//   gsc-*.json             GSC companion-skill output (or raw Search Analytics API response)
//   firebase-users-*.json  `firebase auth:export` output
//   github-events.json     correlate-window.mjs output (candidates[]), or raw `gh` JSON
//
// A source with no matching files is tolerated: its metrics stay null for
// every day and a warning is recorded (never network/CLI failure — this
// script only reads what's already on disk).

import { existsSync, readFileSync, readdirSync, writeFileSync, statSync } from 'node:fs'
import path from 'node:path'

function printHelp() {
  console.log(`normalize-timeseries.mjs — merge raw source JSON into the canonical daily dataset

Usage:
  node normalize-timeseries.mjs --config <path> --in <dir> [--out <file>]

Options:
  --config <path>  Path to website-health-analytics.json (needs "timezone")
  --in <dir>       Directory containing ga4-*.json / gsc-*.json / firebase-users-*.json / github-events.json
  --out <file>     Also write the canonical dataset to this file (stdout always gets it too)
  --help           Show this help and exit

Output: one JSON object on stdout — { "meta": {...}, "days": { "<date>": {...} } }.
See ../examples/daily-metrics.schema.json for the full shape.`)
}

function parseArgs(argv) {
  const args = { help: false, config: null, in: null, out: null }
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i]
    if (a === '--help' || a === '-h') args.help = true
    else if (a === '--config') args.config = argv[++i]
    else if (a === '--in') args.in = argv[++i]
    else if (a === '--out') args.out = argv[++i]
    else throw new Error(`Unrecognized argument: ${a}`)
  }
  return args
}

function fail(message) {
  process.stderr.write(JSON.stringify({ error: message }) + '\n')
  process.exit(1)
}

function readJson(filePath) {
  return JSON.parse(readFileSync(filePath, 'utf8'))
}

// --------------------------------------------------------------------------
// Timezone: GA4/GSC dates arrive already expressed in the property's own
// timezone (per spec, passed through untouched). Firebase/GitHub timestamps
// are UTC epoch-ms/ISO instants and need converting to the *configured*
// timezone before being bucketed into a calendar day. The `en-CA` locale
// trick formats a Date as YYYY-MM-DD directly (Canadian English's date
// format is the ISO order), which sidesteps writing manual zero-padding
// logic for every field.
// --------------------------------------------------------------------------
function utcInstantToLocalDateKey(dateOrEpochMs, timeZone) {
  const d = dateOrEpochMs instanceof Date ? dateOrEpochMs : new Date(dateOrEpochMs)
  const formatter = new Intl.DateTimeFormat('en-CA', { timeZone, year: 'numeric', month: '2-digit', day: '2-digit' })
  return formatter.format(d) // e.g. "2026-07-01"
}

function ga4DateToKey(value) {
  // GA4 Data API dimensionValues for a "date" dimension come back as
  // YYYYMMDD with no separators; already-simplified CLI output may already
  // use YYYY-MM-DD. Accept both since the companion CLI's exact output
  // shape isn't documented here (see SKILL.md — this skill intentionally
  // doesn't own GA4/GSC CLI docs).
  if (/^\d{8}$/.test(value)) return `${value.slice(0, 4)}-${value.slice(4, 6)}-${value.slice(6, 8)}`
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) return value
  return null
}

function gscDateToKey(value) {
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) return value
  if (/^\d{8}$/.test(value)) return `${value.slice(0, 4)}-${value.slice(4, 6)}-${value.slice(6, 8)}`
  return null
}

function findFiles(dir, predicate) {
  return readdirSync(dir)
    .filter((name) => statSync(path.join(dir, name)).isFile())
    .filter(predicate)
    .map((name) => path.join(dir, name))
    .sort()
}

function emptyDay() {
  return {
    sessions: null,
    activeUsers: null,
    conversions: null,
    newUsers: null,
    clicks: null,
    impressions: null,
    ctr: null,
    avgPosition: null,
    signups: null,
    signupsByProvider: null,
    deploys: [],
  }
}

function getDay(days, key) {
  if (!days[key]) days[key] = emptyDay()
  return days[key]
}

// --------------------------------------------------------------------------
// GA4: accepts either a raw Data API runReport response
// ({ dimensionHeaders, metricHeaders, rows: [{dimensionValues, metricValues}] })
// or an already-flattened array/({rows: [...]})  of
// { date, sessions, activeUsers, conversions, newUsers }. Trying both makes
// this resilient to whichever shape the companion CLI happens to print,
// since that CLI's exact JSON shape isn't part of this skill's contract.
// --------------------------------------------------------------------------
function normalizeGa4(days, raw, warnings, fileLabel) {
  const metricNameMap = {
    sessions: 'sessions',
    activeusers: 'activeUsers',
    active_users: 'activeUsers',
    conversions: 'conversions',
    newusers: 'newUsers',
    new_users: 'newUsers',
  }

  if (raw && Array.isArray(raw.dimensionHeaders) && Array.isArray(raw.metricHeaders) && Array.isArray(raw.rows)) {
    const dimNames = raw.dimensionHeaders.map((h) => h.name)
    const dateIdx = dimNames.findIndex((n) => n.toLowerCase() === 'date')
    if (dateIdx === -1) {
      warnings.push(`${fileLabel}: GA4 report has no "date" dimension; skipping.`)
      return
    }
    const metricNames = raw.metricHeaders.map((h) => h.name)
    for (const row of raw.rows) {
      const rawDate = row.dimensionValues?.[dateIdx]?.value
      const key = rawDate ? ga4DateToKey(rawDate) : null
      if (!key) continue
      const day = getDay(days, key)
      metricNames.forEach((name, i) => {
        const mapped = metricNameMap[name.toLowerCase()]
        if (!mapped) return
        const value = row.metricValues?.[i]?.value
        if (value === undefined) return
        day[mapped] = Number(value)
      })
    }
    return
  }

  const rows = Array.isArray(raw) ? raw : Array.isArray(raw?.rows) ? raw.rows : null
  if (!rows) {
    warnings.push(`${fileLabel}: unrecognized GA4 JSON shape; skipping.`)
    return
  }
  for (const row of rows) {
    const key = row.date ? ga4DateToKey(String(row.date)) : null
    if (!key) continue
    const day = getDay(days, key)
    for (const [rawName, mapped] of Object.entries(metricNameMap)) {
      const candidate = row[mapped] !== undefined ? row[mapped] : row[rawName]
      if (candidate !== undefined) day[mapped] = Number(candidate)
    }
  }
}

// --------------------------------------------------------------------------
// GSC: accepts a raw Search Analytics API response
// ({ rows: [{ keys: [date], clicks, impressions, ctr, position }] }) or a
// flattened array of { date, clicks, impressions, ctr, avgPosition|position }.
// --------------------------------------------------------------------------
function normalizeGsc(days, raw, warnings, fileLabel) {
  const rows = Array.isArray(raw) ? raw : Array.isArray(raw?.rows) ? raw.rows : null
  if (!rows) {
    warnings.push(`${fileLabel}: unrecognized GSC JSON shape; skipping.`)
    return
  }
  for (const row of rows) {
    const rawDate = Array.isArray(row.keys) ? row.keys[0] : row.date
    const key = rawDate ? gscDateToKey(String(rawDate)) : null
    if (!key) continue
    const day = getDay(days, key)
    if (row.clicks !== undefined) day.clicks = Number(row.clicks)
    if (row.impressions !== undefined) day.impressions = Number(row.impressions)
    if (row.ctr !== undefined) day.ctr = Number(row.ctr)
    const position = row.avgPosition !== undefined ? row.avgPosition : row.position
    if (position !== undefined) day.avgPosition = Number(position)
  }
}

// --------------------------------------------------------------------------
// Firebase: `firebase auth:export` output. Top-level is either a bare array
// of user records or { users: [...] }. createdAt is epoch-ms (string or
// number, per the real CLI's output). providerUserInfo[].providerId feeds
// the provider-mix breakdown.
// --------------------------------------------------------------------------
function normalizeFirebase(days, raw, timezone, warnings, fileLabel) {
  const users = Array.isArray(raw) ? raw : Array.isArray(raw?.users) ? raw.users : null
  if (!users) {
    warnings.push(`${fileLabel}: unrecognized firebase auth:export JSON shape; skipping.`)
    return
  }
  for (const user of users) {
    if (user.createdAt === undefined || user.createdAt === null) continue
    const epochMs = Number(user.createdAt)
    if (!Number.isFinite(epochMs)) continue
    const key = utcInstantToLocalDateKey(epochMs, timezone)
    const day = getDay(days, key)
    day.signups = (day.signups ?? 0) + 1
    const providers = Array.isArray(user.providerUserInfo) ? user.providerUserInfo : []
    if (!day.signupsByProvider) day.signupsByProvider = {}
    if (providers.length === 0) {
      day.signupsByProvider.unknown = (day.signupsByProvider.unknown || 0) + 1
    } else {
      for (const p of providers) {
        const id = p.providerId || 'unknown'
        day.signupsByProvider[id] = (day.signupsByProvider[id] || 0) + 1
      }
    }
  }
}

// --------------------------------------------------------------------------
// GitHub: github-events.json is either correlate-window.mjs's own output
// ({ candidates: [...] }) or a raw array of similarly-shaped objects. Only
// deploy-shaped candidate types become `deploys` entries — a bare "commit"
// candidate (one that never shipped via a deployment, workflow run, or
// merged PR) isn't a deploy event by itself, so it's excluded here.
// --------------------------------------------------------------------------
function normalizeGithub(days, raw, timezone, warnings, fileLabel) {
  const candidates = Array.isArray(raw) ? raw : Array.isArray(raw?.candidates) ? raw.candidates : null
  if (!candidates) {
    warnings.push(`${fileLabel}: unrecognized github-events JSON shape; skipping.`)
    return
  }
  const sourceMap = { deployment: 'deployment', workflow_run: 'run', pr: 'pr' }
  for (const candidate of candidates) {
    const source = sourceMap[candidate.type]
    if (!source) continue // commits alone aren't deploy events
    if (!candidate.at) continue
    const key = utcInstantToLocalDateKey(new Date(candidate.at), timezone)
    const day = getDay(days, key)
    day.deploys.push({ sha: candidate.sha || null, at: candidate.at, source })
  }
}

function main() {
  const args = parseArgs(process.argv.slice(2))
  if (args.help) {
    printHelp()
    process.exit(0)
  }
  if (!args.config) fail('--config <path> is required. See --help.')
  if (!args.in) fail('--in <dir> is required. See --help.')
  if (!existsSync(args.config)) fail(`Config not found at ${args.config}.`)
  if (!existsSync(args.in)) fail(`--in directory not found at ${args.in}.`)

  const config = readJson(args.config)
  const timezone = config.timezone
  if (!timezone) fail(`Config at ${args.config} has no "timezone".`)

  const warnings = []
  const sources = []
  const days = {}

  const ga4Files = findFiles(args.in, (n) => /^ga4-.*\.json$/.test(n))
  if (ga4Files.length === 0) {
    warnings.push(`No ga4-*.json files found in ${args.in}; GA4 metrics (sessions, activeUsers, conversions, newUsers) stay null for every day.`)
  } else {
    sources.push('ga4')
    for (const file of ga4Files) {
      try {
        normalizeGa4(days, readJson(file), warnings, path.basename(file))
      } catch (err) {
        warnings.push(`${path.basename(file)}: failed to parse/normalize (${err.message}).`)
      }
    }
  }

  const gscFiles = findFiles(args.in, (n) => /^gsc-.*\.json$/.test(n))
  if (gscFiles.length === 0) {
    warnings.push(`No gsc-*.json files found in ${args.in}; GSC metrics (clicks, impressions, ctr, avgPosition) stay null for every day.`)
  } else {
    sources.push('gsc')
    for (const file of gscFiles) {
      try {
        normalizeGsc(days, readJson(file), warnings, path.basename(file))
      } catch (err) {
        warnings.push(`${path.basename(file)}: failed to parse/normalize (${err.message}).`)
      }
    }
  }

  const firebaseFiles = findFiles(args.in, (n) => /^firebase-users-.*\.json$/.test(n))
  if (firebaseFiles.length === 0) {
    warnings.push(`No firebase-users-*.json files found in ${args.in}; signups/signupsByProvider stay null for every day.`)
  } else {
    sources.push('firebase')
    for (const file of firebaseFiles) {
      try {
        normalizeFirebase(days, readJson(file), timezone, warnings, path.basename(file))
      } catch (err) {
        warnings.push(`${path.basename(file)}: failed to parse/normalize (${err.message}).`)
      }
    }
    // `firebase auth:export` is a full historical export, not a date-scoped
    // report — unlike GA4/GSC, there's no such thing as "a day the export
    // didn't cover". So once at least one export was loaded, any day already
    // known to this dataset (from GA4/GSC) that still has no firebase-derived
    // value genuinely had zero signups that day, not "unreported" data —
    // zero-fill rather than leaving null, per the null-vs-zero policy.
    for (const day of Object.values(days)) {
      if (day.signups === null) {
        day.signups = 0
        day.signupsByProvider = {}
      }
    }
  }

  const githubFile = path.join(args.in, 'github-events.json')
  if (!existsSync(githubFile)) {
    warnings.push(`No github-events.json found in ${args.in}; deploys stay empty for every day.`)
  } else {
    sources.push('github')
    try {
      normalizeGithub(days, readJson(githubFile), timezone, warnings, 'github-events.json')
    } catch (err) {
      warnings.push(`github-events.json: failed to parse/normalize (${err.message}).`)
    }
  }

  const sortedDays = {}
  for (const key of Object.keys(days).sort()) sortedDays[key] = days[key]

  const output = {
    meta: {
      timezone,
      generatedAt: new Date().toISOString(),
      sources,
      warnings,
    },
    days: sortedDays,
  }

  const text = JSON.stringify(output, null, 2)
  console.log(text)
  if (args.out) writeFileSync(args.out, text + '\n')
  process.exit(0)
}

try {
  main()
} catch (err) {
  fail(err && err.message ? err.message : String(err))
}
