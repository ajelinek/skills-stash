#!/usr/bin/env node
// check-setup.mjs — preflight for all four website-health-analytics data sources
// (GA4 CLI, GSC CLI, gh, firebase) plus the two config files. Never mutates
// anything: every external call made here is a read-only version/status/auth
// check. Prints exactly one JSON object to stdout; usage errors go to stderr
// as JSON with exit code 1 (see printErrorAndExit below). A successful run
// (even one that reports failed checks) exits 0 — "some checks failed" is a
// normal, well-formed result, not a script error.
//
// Usage:
//   node check-setup.mjs --config <path> [--local-config <path>]
//   node check-setup.mjs --help

import { existsSync, readFileSync } from 'node:fs'
import { execFileSync } from 'node:child_process'

// A hung/interactive CLI (e.g. a credential helper prompting on a TTY that
// isn't there) must not hang the preflight forever. 5s is generous for a
// local `--version`/`auth status` call but short enough that a single dead
// check doesn't stall an entire session start.
const TIMEOUT_MS = 5000

function printHelp() {
  console.log(`check-setup.mjs — preflight for website-health-analytics data sources

Usage:
  node check-setup.mjs --config <path> [--local-config <path>]

Options:
  --config <path>        Path to the committed website-health-analytics.json (required)
  --local-config <path>  Path to the gitignored website-health-analytics.local.json (optional)
  --help                 Show this help and exit

Output: one JSON object on stdout:
  { "checks": { "<name>": { "status": "pass"|"fail"|"warn", "detail": "..." }, ... },
    "warnings": [...], "ready": true|false }
"ready" is true only if every non-"warn" check has status "pass".`)
}

function parseArgs(argv) {
  const args = { help: false, config: null, localConfig: null }
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i]
    if (a === '--help' || a === '-h') args.help = true
    else if (a === '--config') args.config = argv[++i]
    else if (a === '--local-config') args.localConfig = argv[++i]
    else throw new Error(`Unrecognized argument: ${a}`)
  }
  return args
}

function printErrorAndExit(message) {
  process.stderr.write(JSON.stringify({ error: message }) + '\n')
  process.exit(1)
}

/**
 * Runs a command with no shell involvement (argv array, not a string), a
 * bounded timeout, and captures stdout/stderr instead of letting them hit
 * the terminal. Distinguishes "binary not found" (ENOENT) from "timed out"
 * from "ran but exited non-zero" so callers can report the right state.
 */
function runCommand(cmd, args) {
  try {
    const stdout = execFileSync(cmd, args, {
      timeout: TIMEOUT_MS,
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'pipe'],
    })
    return { ok: true, notFound: false, timedOut: false, stdout: stdout.trim(), stderr: '' }
  } catch (err) {
    if (err && err.code === 'ENOENT') {
      return { ok: false, notFound: true, timedOut: false, stdout: '', stderr: '' }
    }
    if (err && (err.signal === 'SIGTERM' || err.killed)) {
      return { ok: false, notFound: false, timedOut: true, stdout: '', stderr: `timed out after ${TIMEOUT_MS}ms` }
    }
    return {
      ok: false,
      notFound: false,
      timedOut: false,
      stdout: (err && err.stdout ? err.stdout.toString() : '').trim(),
      stderr: (err && err.stderr ? err.stderr.toString() : (err && err.message) || '').trim(),
    }
  }
}

function check(status, detail) {
  return { status, detail }
}

function checkNpxCli(pkgName, binName) {
  // Try the pinned/local install path first (npx --no-install never reaches
  // the network — it only resolves a binary that's already in
  // node_modules/.bin or npm's local cache), then fall back to a global
  // install on PATH.
  const viaNpx = runCommand('npx', ['--no-install', binName, '--version'])
  if (viaNpx.ok) return check('pass', `${pkgName} available via npx (--no-install): ${viaNpx.stdout || 'ok'}`)

  const viaGlobal = runCommand(binName, ['--version'])
  if (viaGlobal.ok) return check('pass', `${pkgName} available globally on PATH: ${viaGlobal.stdout || 'ok'}`)

  if (viaGlobal.notFound && viaNpx.notFound) {
    return check('fail', `${pkgName} not found via 'npx --no-install' or on PATH. Install the companion skill (see SKILL.md § Required Companion Skills).`)
  }
  if (viaNpx.timedOut || viaGlobal.timedOut) {
    return check('fail', `${pkgName} version check timed out after ${TIMEOUT_MS}ms.`)
  }
  return check('fail', `${pkgName} --version failed: ${viaGlobal.stderr || viaNpx.stderr || 'unknown error'}`)
}

function checkGoogleCredentials(localConfig) {
  const path = (localConfig && localConfig.googleApplicationCredentials) || process.env.GOOGLE_APPLICATION_CREDENTIALS
  if (!path) {
    return check('fail', 'No credentials path configured. Set "googleApplicationCredentials" in the local config, or export GOOGLE_APPLICATION_CREDENTIALS.')
  }
  if (!existsSync(path)) {
    return check('fail', `Credentials file not found at ${path}.`)
  }
  let parsed
  try {
    parsed = JSON.parse(readFileSync(path, 'utf8'))
  } catch (err) {
    return check('fail', `Credentials file at ${path} is not valid JSON: ${err.message}`)
  }
  if (!parsed || typeof parsed.client_email !== 'string' || !parsed.client_email) {
    return check('fail', `Credentials file at ${path} parses but has no "client_email" field — doesn't look like a service-account key.`)
  }
  return check('pass', `Service-account key at ${path} (${parsed.client_email}).`)
}

function checkGhCli() {
  const result = runCommand('gh', ['--version'])
  if (result.ok) return check('pass', result.stdout.split('\n')[0] || 'gh found')
  if (result.notFound) return check('fail', "'gh' not found on PATH. Install the GitHub CLI: https://cli.github.com")
  if (result.timedOut) return check('fail', `'gh --version' timed out after ${TIMEOUT_MS}ms.`)
  return check('fail', `'gh --version' failed: ${result.stderr || 'unknown error'}`)
}

function checkGhAuthed(ghCliStatus) {
  if (ghCliStatus !== 'pass') {
    return check('warn', "Skipped: 'gh' CLI not found, so auth state can't be checked.")
  }
  // `gh auth status` is non-interactive and exits non-zero when not logged
  // in — it never prompts, so it's safe to run under the same short timeout.
  const result = runCommand('gh', ['auth', 'status'])
  if (result.ok) return check('pass', 'gh is authenticated.')
  if (result.timedOut) return check('fail', `'gh auth status' timed out after ${TIMEOUT_MS}ms.`)
  return check('fail', `gh is not authenticated: ${result.stderr || result.stdout || "run 'gh auth login'"}`)
}

function checkFirebaseCli() {
  // Per spec: `npx -y firebase-tools@latest --version` is too slow for a
  // preflight (it can hit the npm registry). Only check PATH; if it's not
  // there, warn (not fail) rather than block readiness on it, since
  // firebase-tools is commonly invoked via npx by convention in this repo.
  const result = runCommand('firebase', ['--version'])
  if (result.ok) return check('pass', `firebase-tools ${result.stdout || ''} on PATH.`.trim())
  if (result.notFound) return check('warn', "'firebase' not found on PATH (checked PATH only — npx firebase-tools is too slow for a preflight). If you invoke it via npx, this warning is expected.")
  if (result.timedOut) return check('warn', `'firebase --version' timed out after ${TIMEOUT_MS}ms.`)
  return check('warn', `'firebase --version' failed: ${result.stderr || 'unknown error'}`)
}

function checkFirebaseAuthed(firebaseCliStatus) {
  if (firebaseCliStatus === 'fail') {
    return check('warn', "Skipped: 'firebase' CLI not usable, so auth state can't be checked.")
  }
  const result = runCommand('firebase', ['login:list'])
  if (result.notFound) return check('warn', "Skipped: 'firebase' not found on PATH.")
  if (result.timedOut) return check('fail', `'firebase login:list' timed out after ${TIMEOUT_MS}ms.`)
  const output = `${result.stdout}\n${result.stderr}`
  if (/no authorized accounts/i.test(output)) {
    return check('fail', "No authorized firebase accounts. Run 'firebase login' (or 'firebase login --no-localhost' headless).")
  }
  if (result.ok && result.stdout) {
    return check('pass', result.stdout.split('\n')[0] || 'firebase is authenticated.')
  }
  return check('fail', `Could not determine firebase auth state: ${result.stderr || result.stdout || 'unknown error'}`)
}

function loadConfigFile(path, requiredKeysDescription, validate) {
  if (!path) {
    return { status: check('warn', 'Not provided (no --local-config path given).'), data: null }
  }
  if (!existsSync(path)) {
    return { status: check('fail', `File not found at ${path}.`), data: null }
  }
  let data
  try {
    data = JSON.parse(readFileSync(path, 'utf8'))
  } catch (err) {
    return { status: check('fail', `Not valid JSON (${path}): ${err.message}`), data: null }
  }
  const missing = validate ? validate(data) : []
  if (missing.length > 0) {
    return { status: check('fail', `Missing required keys (${requiredKeysDescription}): ${missing.join(', ')}`), data }
  }
  return { status: check('pass', `Valid, all required keys present (${path}).`), data }
}

function validateCommittedConfig(data) {
  const missing = []
  if (typeof data.timezone !== 'string' || !data.timezone) missing.push('timezone')
  if (!Array.isArray(data.githubRepos)) missing.push('githubRepos')
  if (!Array.isArray(data.sites) || data.sites.length === 0) {
    missing.push('sites')
  } else {
    data.sites.forEach((site, i) => {
      if (!site || typeof site.ga4PropertyId !== 'string' || !site.ga4PropertyId) missing.push(`sites[${i}].ga4PropertyId`)
      if (!site || typeof site.gscSiteUrl !== 'string' || !site.gscSiteUrl) missing.push(`sites[${i}].gscSiteUrl`)
    })
  }
  return missing
}

function main() {
  const args = parseArgs(process.argv.slice(2))
  if (args.help) {
    printHelp()
    process.exit(0)
  }
  if (!args.config) {
    printErrorAndExit('--config <path> is required. See --help.')
  }

  const configResult = loadConfigFile(args.config, 'sites[].ga4PropertyId, sites[].gscSiteUrl, githubRepos, timezone', validateCommittedConfig)
  const localConfigResult = loadConfigFile(args.localConfig, 'none strictly required; googleApplicationCredentials recommended', () => [])

  const ga4Cli = checkNpxCli('google-analytics-cli', 'google-analytics-cli')
  const gscCli = checkNpxCli('google-search-console-cli', 'google-search-console-cli')
  const googleCredentials = checkGoogleCredentials(localConfigResult.data)
  const ghCli = checkGhCli()
  const ghAuthed = checkGhAuthed(ghCli.status)
  const firebaseCli = checkFirebaseCli()
  const firebaseAuthed = checkFirebaseAuthed(firebaseCli.status)

  const checks = {
    ga4Cli,
    gscCli,
    googleCredentials,
    ghCli,
    ghAuthed,
    firebaseCli,
    firebaseAuthed,
    config: configResult.status,
    localConfig: localConfigResult.status,
  }

  const warnings = Object.entries(checks)
    .filter(([, c]) => c.status === 'warn')
    .map(([name, c]) => `${name}: ${c.detail}`)

  const ready = Object.values(checks).every((c) => c.status !== 'fail')

  const output = { checks, warnings, ready }
  console.log(JSON.stringify(output, null, 2))
  process.exit(0)
}

try {
  main()
} catch (err) {
  printErrorAndExit(err && err.message ? err.message : String(err))
}
