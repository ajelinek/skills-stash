#!/usr/bin/env node
// detect-anomalies.mjs — deterministic math only, no interpretation. Reads
// the canonical dataset produced by normalize-timeseries.mjs and flags
// metrics on one target day against a trailing baseline, per the method
// configured for each metric in anomalyThresholds. See
// ../references/analysis-rules.md for what the agent does with the output.
//
// Usage:
//   node detect-anomalies.mjs --metrics <daily-metrics.json> --config <path> [--date <ISO date>]
//   node detect-anomalies.mjs --help

import { existsSync, readFileSync } from 'node:fs'

function printHelp() {
  console.log(`detect-anomalies.mjs — flag metric anomalies on one day against a trailing baseline

Usage:
  node detect-anomalies.mjs --metrics <daily-metrics.json> --config <path> [--date <ISO date>]

Options:
  --metrics <path>  Path to a canonical dataset from normalize-timeseries.mjs
  --config <path>   Path to website-health-analytics.json (needs "anomalyThresholds")
  --date <ISO date> Day to analyze, e.g. 2026-07-08 (default: most recent complete day in --metrics)
  --help            Show this help and exit

Output: one JSON object on stdout —
  { "date": "...", "anomalies": [...], "healthy": [...], "skipped": [...] }`)
}

function parseArgs(argv) {
  const args = { help: false, metrics: null, config: null, date: null }
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i]
    if (a === '--help' || a === '-h') args.help = true
    else if (a === '--metrics') args.metrics = argv[++i]
    else if (a === '--config') args.config = argv[++i]
    else if (a === '--date') args.date = argv[++i]
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

// Which raw source each metric's value ultimately comes from — used to
// annotate anomalies so the agent knows which companion CLI/source to
// re-query when investigating.
const METRIC_SOURCE = {
  sessions: 'ga4',
  activeUsers: 'ga4',
  conversions: 'ga4',
  newUsers: 'ga4',
  clicks: 'gsc',
  impressions: 'gsc',
  ctr: 'gsc',
  avgPosition: 'gsc',
  signups: 'firebase',
}

// Metrics where a lower value is worse (a drop is bad, a spike is good/
// neutral): everything except avgPosition, where a *higher* number means a
// worse search ranking — so for avgPosition the "drop"/"spike" direction
// labels below are inverted relative to the raw arithmetic sign, per the
// spec's explicit callout that "avgPosition increase = bad".
const HIGHER_IS_BETTER = {
  sessions: true,
  conversions: true,
  signups: true,
  clicks: true,
  impressions: true,
  avgPosition: false,
}

function direction(metric, actual, baseline) {
  const higherIsBetter = HIGHER_IS_BETTER[metric] !== false
  const worse = higherIsBetter ? actual < baseline : actual > baseline
  return worse ? 'drop' : 'spike'
}

function mean(values) {
  return values.reduce((a, b) => a + b, 0) / values.length
}

// Sample standard deviation (n-1 denominator): the baseline is a sample of
// a metric's history, not the full population of all days that will ever
// exist, so Bessel's correction is the more defensible estimator here.
function sampleStdDev(values, avg) {
  if (values.length < 2) return 0
  const variance = values.reduce((sum, v) => sum + (v - avg) ** 2, 0) / (values.length - 1)
  return Math.sqrt(variance)
}

const MIN_BASELINE_POINTS = 7

function collectBaseline(days, sortedDateKeys, targetDate, metric, baselineDays) {
  const targetIdx = sortedDateKeys.indexOf(targetDate)
  const priorKeys = targetIdx === -1 ? sortedDateKeys.filter((k) => k < targetDate) : sortedDateKeys.slice(0, targetIdx)
  const windowKeys = priorKeys.slice(Math.max(0, priorKeys.length - baselineDays))
  const values = []
  for (const key of windowKeys) {
    const v = days[key]?.[metric]
    if (v !== null && v !== undefined && Number.isFinite(v)) values.push(v)
  }
  return values
}

function mostRecentCompleteDay(sortedDateKeys, timezone) {
  if (sortedDateKeys.length === 0) return null
  const todayKey = new Intl.DateTimeFormat('en-CA', { timeZone: timezone, year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date())
  const last = sortedDateKeys[sortedDateKeys.length - 1]
  if (last !== todayKey) return last
  // Today is present but not "complete" yet — fall back to the prior day if
  // there is one, else fall back to today anyway (nothing else to analyze).
  return sortedDateKeys.length > 1 ? sortedDateKeys[sortedDateKeys.length - 2] : last
}

function evaluateMetric(metric, cfg, days, sortedDateKeys, targetDate) {
  const actual = days[targetDate]?.[metric]
  if (actual === null || actual === undefined || !Number.isFinite(actual)) {
    return { status: 'skipped', reason: 'no data for date' }
  }

  const baselineValues = collectBaseline(days, sortedDateKeys, targetDate, metric, cfg.baselineDays)
  if (baselineValues.length < MIN_BASELINE_POINTS) {
    return { status: 'skipped', reason: `insufficient baseline (${baselineValues.length} of ${MIN_BASELINE_POINTS} minimum points)` }
  }

  const baselineMean = mean(baselineValues)

  if (cfg.method === 'zscore') {
    const stdDev = sampleStdDev(baselineValues, baselineMean)
    if (stdDev === 0) return { status: 'skipped', reason: 'zero variance in baseline' }
    const z = (actual - baselineMean) / stdDev
    const magnitude = Math.abs(z)
    const severity = magnitude >= cfg.critical ? 'critical' : magnitude >= cfg.warn ? 'warn' : null
    return {
      status: severity ? 'anomaly' : 'healthy',
      severity,
      baseline: baselineMean,
      actual,
      delta: z,
    }
  }

  if (cfg.method === 'percentChange') {
    if (baselineMean === 0) return { status: 'skipped', reason: 'baseline mean is 0; percentChange undefined' }
    const pct = (actual - baselineMean) / baselineMean
    const magnitude = Math.abs(pct)
    const severity = magnitude >= cfg.critical ? 'critical' : magnitude >= cfg.warn ? 'warn' : null
    return {
      status: severity ? 'anomaly' : 'healthy',
      severity,
      baseline: baselineMean,
      actual,
      delta: pct,
    }
  }

  if (cfg.method === 'absoluteDelta') {
    const delta = actual - baselineMean
    const magnitude = Math.abs(delta)
    const severity = magnitude >= cfg.critical ? 'critical' : magnitude >= cfg.warn ? 'warn' : null
    return {
      status: severity ? 'anomaly' : 'healthy',
      severity,
      baseline: baselineMean,
      actual,
      delta,
    }
  }

  return { status: 'skipped', reason: `unknown method "${cfg.method}"` }
}

function main() {
  const args = parseArgs(process.argv.slice(2))
  if (args.help) {
    printHelp()
    process.exit(0)
  }
  if (!args.metrics) fail('--metrics <path> is required. See --help.')
  if (!args.config) fail('--config <path> is required. See --help.')
  if (!existsSync(args.metrics)) fail(`Metrics file not found at ${args.metrics}.`)
  if (!existsSync(args.config)) fail(`Config not found at ${args.config}.`)

  const metricsDataset = readJson(args.metrics)
  const config = readJson(args.config)
  const thresholds = config.anomalyThresholds
  if (!thresholds || typeof thresholds !== 'object') fail(`Config at ${args.config} has no "anomalyThresholds".`)

  const days = metricsDataset.days || {}
  const sortedDateKeys = Object.keys(days).sort()
  if (sortedDateKeys.length === 0) fail(`Metrics file at ${args.metrics} has no days to analyze.`)

  const timezone = metricsDataset.meta?.timezone || config.timezone || 'UTC'
  const targetDate = args.date || mostRecentCompleteDay(sortedDateKeys, timezone)
  if (!(targetDate in days)) fail(`Date ${targetDate} not present in ${args.metrics}.`)

  const anomalies = []
  const healthy = []
  const skipped = []

  for (const [metric, cfg] of Object.entries(thresholds)) {
    const result = evaluateMetric(metric, cfg, days, sortedDateKeys, targetDate)
    if (result.status === 'skipped') {
      skipped.push({ metric, reason: result.reason })
    } else if (result.status === 'healthy') {
      healthy.push(metric)
    } else {
      anomalies.push({
        metric,
        date: targetDate,
        baseline: result.baseline,
        actual: result.actual,
        delta: result.delta,
        direction: direction(metric, result.actual, result.baseline),
        method: cfg.method,
        severityDraft: result.severity,
        source: METRIC_SOURCE[metric] || 'unknown',
      })
    }
  }

  const output = { date: targetDate, anomalies, healthy, skipped }
  console.log(JSON.stringify(output, null, 2))
  process.exit(0)
}

try {
  main()
} catch (err) {
  fail(err && err.message ? err.message : String(err))
}
