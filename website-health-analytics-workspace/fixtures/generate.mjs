#!/usr/bin/env node
// fixtures/generate.mjs — deterministically (re)generates
// fixtures/configured-project/ for the website-health-analytics evals.
//
// This is a plain data generator (no dependency on the skill's own scripts)
// so it can be re-run any time the eval scenarios need fresh/adjusted raw
// data. It never uses Math.random() — everything is derived from the day
// index so reruns are byte-for-byte stable.
//
// Story encoded in the fixtures:
//   - 34 "normal" days (2026-06-02 .. 2026-07-05): healthy baseline across
//     GA4 sessions/activeUsers/conversions/newUsers, GSC clicks/impressions/
//     ctr/avgPosition, and ~38 Firebase signups/day (60% google.com / 40%
//     password).
//   - 2026-07-06 and 2026-07-07: a signup-form regression drops signups to
//     ~15 and ~9/day, with a matching conversions dip (~40 -> ~25 -> ~22).
//     GSC stays healthy throughout (the regression is signup/conversion
//     scoped, not an SEO issue).
//   - github-events.json: a hand-authored correlate-window.mjs-shaped
//     output for the fictional repo shadetreeit/webapp, with a plausible
//     PR candidate (touches the signup form) plus two lower-signal
//     candidates (a dependency bump, a docs-only commit).
//
// Usage: node fixtures/generate.mjs

import { mkdirSync, writeFileSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const OUT_ROOT = path.join(__dirname, 'configured-project')
const CLAUDE_DIR = path.join(OUT_ROOT, '.claude')
const WORK_DIR = path.join(CLAUDE_DIR, 'wha-work')

const START_DATE = '2026-06-02'
const END_DATE = '2026-07-07' // inclusive; 36 days total
const DROP_DAYS = new Set(['2026-07-06', '2026-07-07'])

// --------------------------------------------------------------------------
// Date helpers. The fixture range sits entirely inside US Eastern Daylight
// Time (DST runs mid-March to early November 2026), so America/New_York is a
// fixed UTC-4 offset for every date used here — no need to pull in Intl
// timezone math for a static fixture generator.
// --------------------------------------------------------------------------
function addDaysIso(isoDate, n) {
  const [y, m, d] = isoDate.split('-').map(Number)
  const dt = new Date(Date.UTC(y, m - 1, d))
  dt.setUTCDate(dt.getUTCDate() + n)
  return dt.toISOString().slice(0, 10)
}

function dateRange(startIso, endIso) {
  const dates = []
  let cur = startIso
  while (cur <= endIso) {
    dates.push(cur)
    cur = addDaysIso(cur, 1)
  }
  return dates
}

// Eastern-time local hour -> UTC epoch ms on the given ISO date (EDT, UTC-4).
function etHourToEpochMs(isoDate, hour, minute = 0) {
  const [y, m, d] = isoDate.split('-').map(Number)
  return Date.UTC(y, m - 1, d, hour + 4, minute, 0)
}

const DATES = dateRange(START_DATE, END_DATE)

// --------------------------------------------------------------------------
// Deterministic "noise" — small bounded oscillation from the day index, no
// Math.random() anywhere so reruns are stable.
// --------------------------------------------------------------------------
function wobble(i, amplitude, freq1 = 0.45, freq2 = 1.7, w2 = 0.4) {
  return amplitude * Math.sin(i * freq1) + amplitude * w2 * Math.cos(i * freq2)
}

// --------------------------------------------------------------------------
// GA4 fixture (flattened-array shape: normalize-timeseries.mjs's
// normalizeGa4() accepts `Array.isArray(raw) ? raw : ...` and reads
// row.sessions / row.activeUsers / row.conversions / row.newUsers directly).
// --------------------------------------------------------------------------
function buildGa4() {
  return DATES.map((date, i) => {
    const sessions = Math.round(1200 + wobble(i, 45))
    const activeUsers = Math.round(sessions * 0.875 + wobble(i, 8, 0.6, 2.1))
    const newUsers = Math.round(300 + wobble(i, 10, 0.5, 1.3))
    let conversions = Math.round(40 + wobble(i, 2, 0.7, 2.3))
    if (date === '2026-07-06') conversions = 25
    if (date === '2026-07-07') conversions = 22
    return { date, sessions, activeUsers, conversions, newUsers }
  })
}

// --------------------------------------------------------------------------
// GSC fixture (flattened-array shape). Healthy throughout — no injected
// drop, per the eval story (the regression is signup/conversion scoped).
// --------------------------------------------------------------------------
function buildGsc() {
  return DATES.map((date, i) => {
    const clicks = Math.round(220 + wobble(i, 12, 0.5, 1.9))
    const impressions = Math.round(9000 + wobble(i, 250, 0.4, 1.5))
    const ctr = Number((clicks / impressions).toFixed(4))
    const avgPosition = Number((12 + wobble(i, 0.4, 0.6, 2.2)).toFixed(2))
    return { date, clicks, impressions, ctr, avgPosition }
  })
}

// --------------------------------------------------------------------------
// Firebase auth:export fixture. ~38 signups/day on baseline days, dropping
// to ~15 (07-06) and ~9 (07-07). 60% google.com / 40% password, alternated
// deterministically (2 of every 5 users are password).
// --------------------------------------------------------------------------
function signupCountFor(date) {
  if (date === '2026-07-06') return 15
  if (date === '2026-07-07') return 9
  return 38
}

function buildFirebaseUsers() {
  const users = []
  let uidCounter = 1
  for (const date of DATES) {
    const count = signupCountFor(date)
    for (let j = 0; j < count; j++) {
      // Spread signups across the local day: ET hour 0..19 (so +4h UTC
      // offset never rolls into the next UTC day's *different* ET date).
      const hour = count > 1 ? Math.floor((j / (count - 1)) * 19) : 10
      const minute = (j * 7) % 60
      const createdAt = etHourToEpochMs(date, hour, minute)
      const isPassword = j % 5 < 2 // 2 of 5 => 40% password, 60% google.com
      const uid = `uid_${String(uidCounter).padStart(6, '0')}`
      users.push({
        localId: uid,
        email: `user${uidCounter}@shadetreeit.biz`,
        createdAt: String(createdAt),
        providerUserInfo: [{ providerId: isPassword ? 'password' : 'google.com' }],
      })
      uidCounter++
    }
  }
  return { users }
}

// --------------------------------------------------------------------------
// github-events.json — hand-authored in correlate-window.mjs's own output
// shape ({ window, candidates, warnings }), for the fictional repo
// shadetreeit/webapp. Ranked ascending by hoursBeforeAnomaly per the
// script's own sort order (closest-preceding-the-anomaly first).
//
// anomalyDayStartUtc for 2026-07-07 local midnight America/New_York (EDT,
// UTC-4) is 2026-07-07T04:00:00Z — hoursBeforeAnomaly values below are
// computed from that instant so the fixture stays internally consistent
// with what correlate-window.mjs would have produced.
// --------------------------------------------------------------------------
function hoursBefore(atIso, anomalyDayStartIso = '2026-07-07T04:00:00Z') {
  const diffMs = new Date(anomalyDayStartIso).getTime() - new Date(atIso).getTime()
  return Math.round((diffMs / 3_600_000) * 10) / 10
}

function buildGithubEvents() {
  const candidates = [
    {
      // (c) docs-only commit, ~6h before the anomaly window starts.
      type: 'commit',
      repo: 'shadetreeit/webapp',
      sha: '1e88a04',
      prNumber: null,
      title: null,
      message: 'Fix typo in signup docs (README)',
      author: 'jamie',
      at: '2026-07-06T22:00:00Z',
      hoursBeforeAnomaly: hoursBefore('2026-07-06T22:00:00Z'),
      filesChangedCount: null,
    },
    {
      // (a) the primary candidate: signup-form refactor PR.
      type: 'pr',
      repo: 'shadetreeit/webapp',
      sha: 'f3a9c21',
      prNumber: 87,
      title: 'Refactor signup form and consolidate auth providers',
      message: null,
      author: 'adam',
      at: '2026-07-06T09:14:00Z',
      hoursBeforeAnomaly: hoursBefore('2026-07-06T09:14:00Z'),
      filesChangedCount: 6,
    },
    {
      // (b) innocuous dependency-bump commit, ~2 days earlier.
      type: 'commit',
      repo: 'shadetreeit/webapp',
      sha: '9c04d21',
      prNumber: null,
      title: null,
      message: 'Bump lodash from 4.17.20 to 4.17.21',
      author: 'dependabot[bot]',
      at: '2026-07-04T09:14:00Z',
      hoursBeforeAnomaly: hoursBefore('2026-07-04T09:14:00Z'),
      filesChangedCount: null,
    },
  ]
  candidates.sort((x, y) => x.hoursBeforeAnomaly - y.hoursBeforeAnomaly)

  return {
    window: { from: '2026-07-05T04:00:00Z', to: '2026-07-08T09:59:59Z', hours: 78 },
    candidates,
    warnings: [],
  }
}

// --------------------------------------------------------------------------
// Config files (mirrors examples/website-health-analytics*.json in the
// skill, customized for the fictional shadetreeit.biz project).
// --------------------------------------------------------------------------
function buildCommittedConfig() {
  return {
    timezone: 'America/New_York',
    sites: [
      { name: 'prod', gscSiteUrl: 'https://shadetreeit.biz/', ga4PropertyId: 'properties/424242424' },
    ],
    githubRepos: ['shadetreeit/webapp'],
    correlation: {
      windowHours: 48,
      bufferHours: 6,
      gscWindowDays: 10,
    },
    anomalyThresholds: {
      sessions: { method: 'zscore', baselineDays: 28, warn: 2.0, critical: 3.0 },
      conversions: { method: 'percentChange', baselineDays: 7, warn: 0.15, critical: 0.30 },
      signups: { method: 'percentChange', baselineDays: 7, warn: 0.15, critical: 0.30 },
      clicks: { method: 'zscore', baselineDays: 28, warn: 2.0, critical: 3.0 },
      impressions: { method: 'zscore', baselineDays: 28, warn: 2.0, critical: 3.0 },
      avgPosition: { method: 'absoluteDelta', baselineDays: 28, warn: 3, critical: 6 },
    },
  }
}

function buildLocalConfig() {
  return {
    googleApplicationCredentials: '.claude/fake-sa.json',
    accountCorrelations: [
      { githubUsername: 'adam', firebaseUid: 'uid_000001', googleEmail: 'adam@shadetreeit.biz', displayName: 'Adam' },
    ],
  }
}

function buildFakeServiceAccount() {
  return {
    type: 'service_account',
    project_id: 'shadetreeit-biz-fixture',
    client_email: 'wha-fixture@shadetreeit-biz-fixture.iam.gserviceaccount.com',
    client_id: '000000000000000000000',
    private_key_id: 'fixture-fake-key-id',
  }
}

function writeJson(filePath, data) {
  writeFileSync(filePath, JSON.stringify(data, null, 2) + '\n')
  console.log(`wrote ${filePath}`)
}

function main() {
  mkdirSync(WORK_DIR, { recursive: true })

  writeJson(path.join(CLAUDE_DIR, 'website-health-analytics.json'), buildCommittedConfig())
  writeJson(path.join(CLAUDE_DIR, 'website-health-analytics.local.json'), buildLocalConfig())
  writeJson(path.join(CLAUDE_DIR, 'fake-sa.json'), buildFakeServiceAccount())

  writeJson(path.join(WORK_DIR, 'ga4-report.json'), buildGa4())
  writeJson(path.join(WORK_DIR, 'gsc-query.json'), buildGsc())
  writeJson(path.join(WORK_DIR, 'firebase-users-2026-07-07.json'), buildFirebaseUsers())
  writeJson(path.join(WORK_DIR, 'github-events.json'), buildGithubEvents())

  console.log('done.')
}

main()
