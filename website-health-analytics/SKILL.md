---
name: website-health-analytics
description: >
  Use this skill to run cross-source website health checks and turn analytics
  anomalies into concrete code fixes. It correlates GA4, Google Search
  Console, Firebase Auth signups, and GitHub deploys/commits/PRs into one
  canonical timeline, detects statistically significant anomalies, and traces
  a confirmed anomaly back to the commit, file, and line that likely caused
  it. Trigger on requests like "run a website health check", "daily analytics
  dashboard", "why did traffic/conversions/signups drop", "did the deploy
  cause X", "correlate this commit/PR/deploy with an analytics change",
  "diagnose an SEO clicks/impressions drop", "analyze signup provider mix",
  "turn this anomaly into a code fix", or "growth suggestions from search
  data".
---

# Website Health Analytics

A thin orchestration skill. It correlates GA4, Google Search Console,
Firebase Auth, and GitHub activity into one canonical daily dataset, detects
anomalies with deterministic rules, and — its differentiator — traces a
confirmed anomaly back to the commit, file, and line that likely caused it,
producing a fix that can be handed straight to a coding agent.

This skill does not fetch GA4 or GSC data itself — that is fully delegated to
two companion CLIs (below). It also does not own everything analytics- or
SEO-adjacent:

- Implementing SEO code (metadata, JSON-LD, sitemaps, IndexNow) → use `astro-seo`
- Configuring Firebase Auth or Firestore in the app itself → use `firebase-auth-basics` or `firebase-firestore`
- A general on-page SEO audit with no cross-source correlation → use `seo-audit`

This skill owns cross-source correlation and code-level remediation only.

## Required Companion Skills

This skill cannot fetch any GA4 or GSC data itself. It is a **hard
dependency** on two companion skills by the same author — without them, GA4
and GSC work is impossible, not just degraded:

```
npx skills add Bin-Huang/google-analytics-cli
npx skills add Bin-Huang/google-search-console-cli
```

If either is missing, stop and install it before continuing. All GA4 and GSC
data collection goes through those skills' own documented commands — this
skill intentionally documents none of their syntax. `gh` and `firebase` are
native CLIs used directly (checked for authentication in the preflight,
never installed by this skill).

## When To Use This Skill

- Running a daily or periodic website health check across GA4, GSC, Firebase
  Auth, and GitHub
- Investigating a traffic, conversion, or signup drop
- Answering "did the deploy cause X"
- Correlating a commit, PR, or deploy with an analytics change
- Diagnosing an SEO clicks/impressions drop
- Analyzing signup provider mix
- Turning a confirmed anomaly into a concrete code fix
- Generating growth suggestions from search data when nothing is broken

## When Not To Use This Skill

- Fetching a single GA4 report or GSC query with no cross-source correlation
  → use `google-analytics-cli` / `google-search-console-cli` directly
- Implementing SEO code changes → use `astro-seo`
- Setting up Firebase Auth itself → use `firebase-auth-basics`
- A general on-page SEO audit with no analytics data behind it → use `seo-audit`

## First: Run the Preflight

At the start of any session that uses this skill, run:

```bash
node <skill_dir>/scripts/check-setup.mjs \
  --config .claude/website-health-analytics.json \
  --local-config .claude/website-health-analytics.local.json
```

Replace `<skill_dir>` with wherever this skill is installed (the directory
containing this SKILL.md). If `ready` is `false`, stop and route to
[references/setup.md](references/setup.md) before doing anything else — do
not attempt fetches against a broken setup.

One exception — degraded mode: if the only failing checks are fetch CLIs
(`ga4Cli`, `gscCli`, `firebaseCli`) and raw data files already exist in the
working dir (`.claude/wha-work/`), analysis of that existing data may
proceed. State the deviation plainly in the output (which sources are
pre-fetched rather than live, and how stale they are) instead of silently
ignoring the failed preflight. Config or credential failures always stop.

## Mode Routing

| Intent | Route |
| --- | --- |
| First run, or preflight reports not ready | [references/setup.md](references/setup.md) |
| Daily health check / dashboard | [references/daily-health-check.md](references/daily-health-check.md) |
| "Did X cause Y" troubleshooting | [references/analysis-rules.md](references/analysis-rules.md), then [references/code-remediation.md](references/code-remediation.md) |
| Direct "give me the fix" | [references/code-remediation.md](references/code-remediation.md) |
| Growth ideas, nothing broken | [references/code-remediation.md](references/code-remediation.md) § Growth Mode |

## Pipeline Overview

1. **Fetch** — pull raw data via the companion skills' documented commands
   (GA4, GSC), `firebase auth:export` (see
   [references/firebase-auth.md](references/firebase-auth.md)), and `gh`
   (see [references/github-correlation.md](references/github-correlation.md)).
   Save each response as raw JSON in the working dir, following the naming
   convention in
   [references/data-normalization.md](references/data-normalization.md).
2. **Normalize** — `node <skill_dir>/scripts/normalize-timeseries.mjs` turns
   the raw files into one canonical dataset keyed by date.
3. **Detect** — `node <skill_dir>/scripts/detect-anomalies.mjs` flags
   statistically significant deviations against the configured thresholds.
4. **Root-cause (agentic)** — walk the 5-layer framework in
   [references/analysis-rules.md](references/analysis-rules.md) to localize
   the anomaly and confirm it's real, not a data-lag artifact.
5. **Correlate** — `node <skill_dir>/scripts/correlate-window.mjs` ranks
   candidate deploys, workflow runs, PRs, and commits that precede the
   anomaly.
6. **Inspect (agentic)** — pull diffs for the top candidates (`gh api
   repos/{repo}/commits/{sha}`, `gh pr diff {n}`) and match them against the
   metric→suspect-file table in
   [references/code-remediation.md](references/code-remediation.md).
7. **Remediate** — produce output using the templates in
   [references/code-remediation.md](references/code-remediation.md):
   observation → code-level cause → concrete fix → severity → confidence.

## Config Files

Two dedicated files live in the target project — not
`.claude/settings*.json`, to avoid Claude Code's settings validation
stripping unknown keys:

- `.claude/website-health-analytics.json` — **committed**, non-secret.
  Timezone, sites (GA4 property ID + GSC site URL — neither is a secret),
  GitHub repos, correlation windows, anomaly thresholds. Template:
  [examples/website-health-analytics.json](examples/website-health-analytics.json).
- `.claude/website-health-analytics.local.json` — **gitignored**. Service
  account credential path and `accountCorrelations` (GitHub↔Firebase↔email
  identity mapping). Template:
  [examples/website-health-analytics.local.json](examples/website-health-analytics.local.json).

Add the local file to `.gitignore` during setup — see
[references/setup.md](references/setup.md). `gh` and `firebase` use their
own cached OAuth sessions; neither config file carries auth fields for them.

## Output Conventions

Every finding — regression or growth suggestion — carries a severity:

- **P0** — confirmed regression, high-confidence root cause, high impact
- **P1** — confirmed regression, high impact, but only medium-confidence root cause
- **P2** — confirmed but lower-impact regression, or a high-confidence root
  cause on a moderate-impact metric
- **P3** — proactive growth suggestion; nothing is broken

Confidence (High / Medium / Low) is always stated explicitly alongside
severity — never fabricate a root cause. See
[references/code-remediation.md](references/code-remediation.md) step 7.

## Known Limitations

- GA4 data is provisional for roughly 24–48 hours; treat same-day anomalies
  as unconfirmed until they age out of that window.
- GSC data lags 2–3 days; use `correlation.gscWindowDays` (default 10) when
  windowing GSC-sourced anomalies.
- There is no GA4 custom event for "$20 tier usage" yet. If asked about
  tier-specific metrics, recommend defining the event (P3) rather than guess
  at a proxy metric — see
  [references/metric-definitions.md](references/metric-definitions.md).

## Supporting Files

| File | Purpose |
| --- | --- |
| `references/setup.md` | First-run setup: companion skills, `gh`/`firebase` auth, GCP service account, config files |
| `references/firebase-auth.md` | `firebase auth:export` glue — signup counts, provider mix, PII handling |
| `references/github-correlation.md` | What `correlate-window.mjs` runs, how to read candidates, agent follow-up diff commands |
| `references/data-normalization.md` | Canonical dataset contract, raw-file naming, timezone and null-vs-zero rules |
| `references/analysis-rules.md` | Anomaly-detection methods and the 5-layer root-cause framework |
| `references/code-remediation.md` | The 9-step remediation engine, metric→suspect-file table, worked examples |
| `references/metric-definitions.md` | Per-metric source of truth and reconciliation rules |
| `references/daily-health-check.md` | Dashboard-mode workflow and report template |
| `scripts/check-setup.mjs` | Preflight for all four sources |
| `scripts/normalize-timeseries.mjs` | Raw JSON → canonical dataset |
| `scripts/detect-anomalies.mjs` | Deterministic anomaly detection |
| `scripts/correlate-window.mjs` | Ranks candidate deploys/PRs/commits preceding an anomaly |
| `examples/website-health-analytics.json` | Committed config template |
| `examples/website-health-analytics.local.json` | Gitignored local config template |
| `examples/daily-metrics.schema.json` | JSON Schema for the canonical dataset |
