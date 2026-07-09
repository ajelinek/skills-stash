#!/usr/bin/env node
// correlate-window.mjs — shells out to `gh` across four surfaces (deployments,
// workflow runs, merged PRs, commits) to find candidate causes that PRECEDE
// an analytics anomaly. There is no native `gh deployment` list command, so
// this glues the four surfaces gh does offer into one ranked candidate list.
// Does NOT fetch diffs — that's the agent's job afterward
// (`gh api repos/{repo}/commits/{sha}`, `gh pr diff {n}`; see
// ../references/github-correlation.md).
//
// Usage:
//   node correlate-window.mjs --config <path> --date <anomaly ISO date>
//     [--window-hours N] [--buffer-hours N] [--repo org/name]
//   node correlate-window.mjs --help

import { existsSync, readFileSync } from 'node:fs'
import { execFileSync } from 'node:child_process'

// gh calls cross the network (GitHub API round trips), so they get a more
// generous timeout than the local version/auth checks in check-setup.mjs.
// Still bounded: a stuck `gh` call must not hang the whole correlation run —
// one failed surface just becomes a warning (see runGh below).
const GH_TIMEOUT_MS = 20000

function printHelp() {
  console.log(`correlate-window.mjs — rank GitHub deploy-shaped candidates preceding an anomaly

Usage:
  node correlate-window.mjs --config <path> --date <anomaly ISO date> \\
    [--window-hours N] [--buffer-hours N] [--repo org/name]

Options:
  --config <path>       Path to website-health-analytics.json
  --date <ISO date>     Anomaly date, e.g. 2026-07-08 (local calendar day, per config timezone)
  --window-hours <N>    Lookback hours before the anomaly day starts (default: config.correlation.windowHours)
  --buffer-hours <N>    Extra hours after the anomaly day ends, absorbing timestamp skew (default: config.correlation.bufferHours)
  --repo <org/name>     Limit to one repo instead of all of config.githubRepos (repeatable)
  --help                Show this help and exit

Output: one JSON object on stdout —
  { "window": {"from","to","hours"}, "candidates": [...], "warnings": [...] }
Candidates are ranked closest-preceding-the-anomaly first.`)
}

function parseArgs(argv) {
  const args = { help: false, config: null, date: null, windowHours: null, bufferHours: null, repos: [] }
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i]
    if (a === '--help' || a === '-h') args.help = true
    else if (a === '--config') args.config = argv[++i]
    else if (a === '--date') args.date = argv[++i]
    else if (a === '--window-hours') args.windowHours = Number(argv[++i])
    else if (a === '--buffer-hours') args.bufferHours = Number(argv[++i])
    else if (a === '--repo') args.repos.push(argv[++i])
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
// Timezone: convert a local wall-clock instant (in the configured IANA
// timezone) to a UTC Date. Standard two-pass convergence — treat the wall
// clock as if it were already UTC for a first guess, see what that guess
// reads as in the target zone, and correct by the difference. Two passes
// (not one) so the result is still correct for wall-clock times that fall
// right at a DST transition.
// --------------------------------------------------------------------------
function getZonedParts(date, timeZone) {
  const formatter = new Intl.DateTimeFormat('en-US', {
    timeZone,
    hourCycle: 'h23',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
  const map = {}
  for (const part of formatter.formatToParts(date)) {
    if (part.type !== 'literal') map[part.type] = parseInt(part.value, 10)
  }
  return map
}

function zonedTimeToUtc({ year, month, day, hour, minute, second }, timeZone) {
  let guess = Date.UTC(year, month - 1, day, hour, minute, second, 0)
  for (let i = 0; i < 2; i++) {
    const parts = getZonedParts(new Date(guess), timeZone)
    const asIfUtc = Date.UTC(parts.year, parts.month - 1, parts.day, parts.hour, parts.minute, parts.second, 0)
    guess += guess - asIfUtc
  }
  return new Date(guess)
}

function parseIsoDateParts(isoDate) {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(isoDate)
  if (!m) throw new Error(`--date must be an ISO calendar date (YYYY-MM-DD), got ${JSON.stringify(isoDate)}.`)
  return { year: Number(m[1]), month: Number(m[2]), day: Number(m[3]) }
}

/**
 * Runs `gh` with no shell involvement and a bounded timeout. Throws on any
 * failure (not found, timeout, non-zero exit, unparseable JSON) — callers
 * are expected to catch per-endpoint and turn this into a warning, since
 * each of the four gh surfaces is allowed to fail independently (e.g. a repo
 * with no Deployments API usage is common and not an error).
 */
function runGhJson(args) {
  let stdout
  try {
    stdout = execFileSync('gh', args, { timeout: GH_TIMEOUT_MS, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] })
  } catch (err) {
    if (err && err.code === 'ENOENT') throw new Error("'gh' not found on PATH.")
    if (err && (err.signal === 'SIGTERM' || err.killed)) throw new Error(`gh ${args.join(' ')} timed out after ${GH_TIMEOUT_MS}ms.`)
    const stderr = (err && err.stderr ? err.stderr.toString() : (err && err.message) || '').trim()
    throw new Error(`gh ${args.join(' ')} failed: ${stderr || 'unknown error'}`)
  }
  try {
    return JSON.parse(stdout)
  } catch (err) {
    throw new Error(`gh ${args.join(' ')} returned unparseable JSON: ${err.message}`)
  }
}

function hoursBeforeAnomaly(atIso, anomalyDayStartUtc) {
  const diffMs = anomalyDayStartUtc.getTime() - new Date(atIso).getTime()
  return Math.round((diffMs / 3_600_000) * 10) / 10
}

function withinWindow(atIso, fromMs, toMs) {
  const t = new Date(atIso).getTime()
  return Number.isFinite(t) && t >= fromMs && t <= toMs
}

function candidateFromDeployment(repo, d, anomalyDayStartUtc) {
  const at = d.created_at
  return {
    type: 'deployment',
    repo,
    sha: d.sha || null,
    prNumber: null,
    title: d.description || d.task || null,
    message: null,
    author: d.creator?.login || null,
    at,
    hoursBeforeAnomaly: hoursBeforeAnomaly(at, anomalyDayStartUtc),
    filesChangedCount: null,
  }
}

function candidateFromRun(repo, r, anomalyDayStartUtc) {
  const at = r.createdAt
  return {
    type: 'workflow_run',
    repo,
    sha: r.headSha || null,
    prNumber: null,
    title: r.workflowName || null,
    message: null,
    author: null,
    at,
    hoursBeforeAnomaly: hoursBeforeAnomaly(at, anomalyDayStartUtc),
    filesChangedCount: null,
  }
}

function candidateFromPr(repo, pr, anomalyDayStartUtc) {
  const at = pr.mergedAt
  return {
    type: 'pr',
    repo,
    sha: pr.mergeCommit?.oid || pr.mergeCommit?.sha || null,
    prNumber: pr.number ?? null,
    title: pr.title || null,
    message: null,
    author: pr.author?.login || null,
    at,
    hoursBeforeAnomaly: hoursBeforeAnomaly(at, anomalyDayStartUtc),
    filesChangedCount: Array.isArray(pr.files) ? pr.files.length : null,
  }
}

function candidateFromCommit(repo, c, anomalyDayStartUtc) {
  const at = c.commit?.author?.date || c.commit?.committer?.date
  const message = c.commit?.message || null
  return {
    type: 'commit',
    repo,
    sha: c.sha || null,
    prNumber: null,
    title: null,
    message: message ? message.split('\n')[0] : null,
    author: c.author?.login || c.commit?.author?.name || null,
    at,
    hoursBeforeAnomaly: at ? hoursBeforeAnomaly(at, anomalyDayStartUtc) : null,
    filesChangedCount: null,
  }
}

function correlateRepo(repo, fromIso, toIso, fromMs, toMs, anomalyDayStartUtc, warnings) {
  const candidates = []

  // 1. Deployments — no date filter on this endpoint, so fetch and filter
  // client-side. Prefer environment=production entries when any exist;
  // otherwise fall back to all deployments (small repos often only deploy
  // to one unnamed environment).
  try {
    const all = runGhJson(['api', `repos/${repo}/deployments?per_page=100`])
    if (!Array.isArray(all)) throw new Error(all?.message || 'unexpected response shape (expected an array)')
    const production = all.filter((d) => d.environment === 'production')
    const pool = production.length > 0 ? production : all
    for (const d of pool) {
      if (withinWindow(d.created_at, fromMs, toMs)) candidates.push(candidateFromDeployment(repo, d, anomalyDayStartUtc))
    }
  } catch (err) {
    warnings.push(`${repo} deployments: ${err.message}`)
  }

  // 2. Successful workflow runs.
  try {
    const runs = runGhJson(['run', 'list', '--repo', repo, '--status', 'success', '--json', 'databaseId,workflowName,conclusion,createdAt,headSha,headBranch', '--limit', '50'])
    if (!Array.isArray(runs)) throw new Error('unexpected response shape (expected an array)')
    for (const r of runs) {
      if (withinWindow(r.createdAt, fromMs, toMs)) candidates.push(candidateFromRun(repo, r, anomalyDayStartUtc))
    }
  } catch (err) {
    warnings.push(`${repo} workflow runs: ${err.message}`)
  }

  // 3. Merged PRs — server-side filtered via the `merged:` search qualifier,
  // then re-checked client-side since search-index staleness/timezone
  // rounding can make the qualifier slightly imprecise at the edges.
  try {
    const prs = runGhJson(['pr', 'list', '--repo', repo, '--state', 'merged', '--search', `merged:${fromIso}..${toIso}`, '--json', 'number,title,mergedAt,mergeCommit,author,files', '--limit', '50'])
    if (!Array.isArray(prs)) throw new Error('unexpected response shape (expected an array)')
    for (const pr of prs) {
      if (pr.mergedAt && withinWindow(pr.mergedAt, fromMs, toMs)) candidates.push(candidateFromPr(repo, pr, anomalyDayStartUtc))
    }
  } catch (err) {
    warnings.push(`${repo} merged PRs: ${err.message}`)
  }

  // 4. Raw commits in range (catches direct pushes that never went through a
  // PR or a tracked workflow/deployment).
  try {
    const commits = runGhJson(['api', `repos/${repo}/commits?since=${fromIso}&until=${toIso}`])
    if (!Array.isArray(commits)) throw new Error(commits?.message || 'unexpected response shape (expected an array)')
    for (const c of commits) candidates.push(candidateFromCommit(repo, c, anomalyDayStartUtc))
  } catch (err) {
    warnings.push(`${repo} commits: ${err.message}`)
  }

  return candidates
}

function main() {
  const args = parseArgs(process.argv.slice(2))
  if (args.help) {
    printHelp()
    process.exit(0)
  }
  if (!args.config) fail('--config <path> is required. See --help.')
  if (!args.date) fail('--date <anomaly ISO date> is required. See --help.')
  if (!existsSync(args.config)) fail(`Config not found at ${args.config}.`)

  const config = readJson(args.config)
  const timezone = config.timezone
  if (!timezone) fail(`Config at ${args.config} has no "timezone".`)

  const windowHours = args.windowHours ?? config.correlation?.windowHours
  const bufferHours = args.bufferHours ?? config.correlation?.bufferHours
  if (!Number.isFinite(windowHours)) fail('No window-hours available: pass --window-hours or set correlation.windowHours in config.')
  if (!Number.isFinite(bufferHours)) fail('No buffer-hours available: pass --buffer-hours or set correlation.bufferHours in config.')

  const repos = args.repos.length > 0 ? args.repos : config.githubRepos
  if (!Array.isArray(repos) || repos.length === 0) fail('No repos to correlate: pass --repo or set githubRepos in config.')

  const { year, month, day } = parseIsoDateParts(args.date)
  const anomalyDayStartUtc = zonedTimeToUtc({ year, month, day, hour: 0, minute: 0, second: 0 }, timezone)
  const anomalyDayEndUtc = zonedTimeToUtc({ year, month, day, hour: 23, minute: 59, second: 59 }, timezone)

  const from = new Date(anomalyDayStartUtc.getTime() - windowHours * 3_600_000)
  const to = new Date(anomalyDayEndUtc.getTime() + bufferHours * 3_600_000)
  const fromIso = from.toISOString()
  const toIso = to.toISOString()
  const fromMs = from.getTime()
  const toMs = to.getTime()

  const warnings = []
  let candidates = []
  for (const repo of repos) {
    candidates = candidates.concat(correlateRepo(repo, fromIso, toIso, fromMs, toMs, anomalyDayStartUtc, warnings))
  }

  // Closest-preceding-the-anomaly first: ascending hoursBeforeAnomaly. Items
  // with a null hoursBeforeAnomaly (missing timestamp) sort last.
  candidates.sort((a, b) => {
    if (a.hoursBeforeAnomaly === null) return 1
    if (b.hoursBeforeAnomaly === null) return -1
    return a.hoursBeforeAnomaly - b.hoursBeforeAnomaly
  })

  const output = {
    window: { from: fromIso, to: toIso, hours: windowHours + bufferHours + 24 },
    candidates,
    warnings,
  }
  console.log(JSON.stringify(output, null, 2))
  process.exit(0)
}

try {
  main()
} catch (err) {
  fail(err && err.message ? err.message : String(err))
}
