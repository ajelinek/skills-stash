# Actions Log — Daily Website Health Check

Working directory for all commands below:
/Users/ajelinek/code/skills/skills-stash/website-health-analytics-workspace/iteration-1/eval-2-daily-health-check/project

Skill directory:
/Users/ajelinek/code/skills/skills-stash/website-health-analytics

## 0. Setup (eval harness, not part of the skill)

- `cp -R fixtures/configured-project/ iteration-1/eval-2-daily-health-check/project/`
  -- copied the fixture project (including .claude/) into the working
  project dir, then used it as cwd for everything below.

## 1. Skill files read

1. `SKILL.md` -- top-level routing. Confirmed hard dependency on
   `google-analytics-cli` and `google-search-console-cli` companion skills
   for any fetch; identified the daily-check route
   (references/daily-health-check.md); noted the mandatory preflight step.
2. `references/daily-health-check.md` -- the dashboard-mode workflow: fetch
   yesterday + 28-day trailing baseline, normalize, detect, report using the
   given template; explicitly states the daily check does NOT run the full
   remediation engine, only surfaces anomalies that need it.
3. `references/data-normalization.md` -- canonical dataset contract, raw
   file naming convention (ga4-*.json, gsc-*.json, firebase-users-*.json,
   github-events.json), timezone conversion rules, null-vs-zero rules.
4. `references/analysis-rules.md` -- threshold methods reference (zscore /
   percentChange / absoluteDelta per metric) and the 5-layer root-cause
   framework; used Layer 1 ("Confirm it's real" -- check against GA4's
   24-48h provisional window and GSC's 2-3 day lag) to decide whether the
   detected anomalies could be trusted in this report.

## 2. Commands run

### 2.1 Preflight

```
node <skill_dir>/scripts/check-setup.mjs \
  --config .claude/website-health-analytics.json \
  --local-config .claude/website-health-analytics.local.json
```

Result: `ready: false`. All checks passed (ga4Cli, googleCredentials, ghCli,
ghAuthed, firebaseCli, firebaseAuthed, config, localConfig) except
`gscCli: fail` -- `npx google-search-console-cli --version` could not
install/run in this sandboxed environment (no network access for on-demand
npx package fetch). Per SKILL.md this should normally stop the session and
route to references/setup.md. Per this eval's explicit instructions, the
companion CLIs are known to be unavailable here and raw data was
pre-provided in .claude/wha-work/, so I proceeded using those files instead
of attempting a live fetch, and flagged the deviation in the report.

### 2.2 Inspected pre-staged raw data

```
ls -la .claude/wha-work/
```
-> firebase-users-2026-07-07.json (282k), ga4-report.json (4.5k),
   github-events.json (1.1k), gsc-query.json (4.4k)

Spot-checked each file's shape against data-normalization.md's naming
convention and schema expectations (ga4-report.json: per-day
sessions/activeUsers/conversions/newUsers from 2026-06-02; gsc-query.json:
per-day clicks/impressions/ctr/avgPosition; github-events.json: a
`candidates` array of commit/PR events with timestamps and
hoursBeforeAnomaly; firebase-users-*.json: a `{"users": [...]}` export).

### 2.3 Normalize

```
node <skill_dir>/scripts/normalize-timeseries.mjs \
  --config .claude/website-health-analytics.json \
  --in .claude/wha-work \
  --out .claude/wha-work/daily-metrics.json
```

Result summary (meta block):
```
"sources": ["ga4", "gsc", "firebase", "github"],
"warnings": []
```
36 days normalized, 2026-06-02 through 2026-07-07, no warnings (no missing
sources, no unparseable files).

### 2.4 Detect anomalies (latest complete day, default --date)

```
node <skill_dir>/scripts/detect-anomalies.mjs \
  --metrics .claude/wha-work/daily-metrics.json \
  --config .claude/website-health-analytics.json
```

Defaulted to `date: 2026-07-07` (most recent complete day in the dataset).
Result:
```
anomalies:
  - conversions: baseline 38.14, actual 22, delta -42.3%, critical, source ga4
  - signups:     baseline 34.71, actual 9,  delta -74.1%, critical, source firebase
healthy: [sessions, clicks, impressions, avgPosition]
skipped: []
```

### 2.5 Detect anomalies for the prior day (Layer-1 persistence check)

```
node <skill_dir>/scripts/detect-anomalies.mjs \
  --metrics .claude/wha-work/daily-metrics.json \
  --config .claude/website-health-analytics.json \
  --date 2026-07-06
```

Run to test analysis-rules.md Layer 1 ("confirm it's real" against GA4's
24-48h provisional window) -- 2026-07-07 alone is only one day old as of
"today" (2026-07-08) and technically still inside that window. Checking
2026-07-06, which is now outside the window, showed the same two metrics
already critical:
```
anomalies:
  - conversions: baseline 40.43, actual 25, delta -38.2%, critical, source ga4
  - signups:     baseline 38,    actual 15, delta -60.5%, critical, source firebase
healthy: [sessions, clicks, impressions, avgPosition]
```
This persistence across two days (one of which is safely outside the GA4
provisional window) was treated as satisfying Layer 1 -- the anomaly is
real, not a data-lag artifact.

### 2.6 Metric summary table computation (python, ad hoc)

Computed actual vs. trailing-baseline (matching each metric's configured
`baselineDays` -- 28 for sessions/clicks/impressions/avgPosition, 7 for
conversions/signups) for all six tracked metrics on 2026-07-07, to fill in
the report template's full Metric Summary table (detect-anomalies.mjs only
emits the metrics it flags or marks healthy by name, not their baseline
numbers for the healthy ones).

Output:
```
sessions     actual=1180  baseline=1200.86 (n=28) delta=-1.7%
conversions  actual=22    baseline=38.14   (n=7)  delta=-42.3%
signups      actual=9     baseline=34.71   (n=7)  delta=-74.1%
clicks       actual=204   baseline=219.14  (n=28) delta=-6.9%
impressions  actual=9186  baseline=8976.82 (n=28) delta=+2.3%
avgPosition  actual=12.33 baseline=11.99   (n=28) delta=+2.9% (+0.34, worse)
```

### 2.7 Signup provider-mix check (python, ad hoc, from already-normalized data)

Read `signupsByProvider` for the last 10 days directly out of
daily-metrics.json to see whether the signup drop was concentrated in one
provider (password vs. google.com) or spread across both. Found it
proportional across both providers (roughly the same 40/60 password/google
split held before and during the drop) -- a Layer-2-adjacent observation
included in the report because it came free from already-fetched data, not
from running a new pivot query.

### 2.8 Inspected github-events.json candidates

Read the pre-staged `.claude/wha-work/github-events.json` directly (no
script run -- `correlate-window.mjs` was intentionally NOT run, since full
root-causing/correlation is out of scope for the daily check per
daily-health-check.md: "the daily check itself does not run the full
remediation engine, it surfaces what needs it"). Found one candidate inside
the correlation window that precedes the anomaly onset:
- PR #87, "Refactor signup form and consolidate auth providers", author
  adam, merged 2026-07-06T09:14:00Z, 6 files changed, 18.8 hours before the
  anomaly window's reference point.
Two other candidates (a README typo commit, a dependabot lodash bump) were
present but not timing- or content-relevant.

This was reported only as a timing lead in the report's Anomalies section,
explicitly marked Low confidence -- Layers 2-4 (dimension pivot, page-level
breakdown, technical checks) were not walked, and no diff was pulled for PR
#87, so no root-cause claim was made.

## 3. Scripts intentionally NOT run (and why)

- `correlate-window.mjs` -- out of scope for the daily-check route; belongs
  to the "did X cause Y" / troubleshooting route
  (references/analysis-rules.md -> references/code-remediation.md). The
  daily check's job is to surface the anomaly and hand it off, not to fully
  root-cause it.
- `gh api repos/.../commits/{sha}`, `gh pr diff 87` -- part of the
  code-remediation.md "Inspect" step, same reasoning as above.
- No live GA4/GSC/firebase fetch commands were run -- the companion CLIs
  are not available in this environment (see 2.1) and the eval instructions
  specified using the pre-provided raw files instead.
