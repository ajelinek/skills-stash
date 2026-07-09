# Actions Log — "did one of our recent deploys cause the signup drop on 2026-07-07?"

Scenario date: 2026-07-08. Project copy:
`/Users/ajelinek/code/skills/skills-stash/website-health-analytics-workspace/iteration-1/eval-3-correlation-discipline/project/`
(cwd for all commands below unless noted).

## Setup

1. `cp -R` the fixture `configured-project/` (including `.claude/`) into
   `iteration-1/eval-3-correlation-discipline/project/`. Verified `.claude/`
   contents present: `website-health-analytics.json`,
   `website-health-analytics.local.json`, `fake-sa.json`, `wha-work/`.

## Skill files read (in order)

1. `SKILL.md` — top-level routing. Task = "did the deploy cause X" → route
   to `references/analysis-rules.md` then `references/code-remediation.md`.
   Noted the mandatory preflight step and the mode-routing table.
2. `references/analysis-rules.md` — `detect-anomalies.mjs` usage, threshold
   methods, and the 5-layer root-cause framework (confirm real → localize
   by dimension → page-level → technical → external).
3. `references/code-remediation.md` — the 9-step remediation engine,
   metric→suspect-file table (`signups` → auth/signup routes, Firebase
   init/config, post-signup redirect), confidence-level definitions
   (High/Medium/Low), output template, and both worked examples.
4. `references/github-correlation.md` — what `correlate-window.mjs` runs
   (4 gh surfaces per repo), the quiet-failure caveat for `gh pr list
   --search` on a bad repo name, and the exact follow-up diff commands
   (`gh api repos/{repo}/commits/{sha}`, `gh pr diff {n}`, `gh pr view {n}`).
5. `references/data-normalization.md` — raw-file naming convention
   (`ga4-*`, `gsc-*`, `firebase-users-*`, `github-events.json`), canonical
   dataset shape, timezone conversion rule (Firebase/GitHub timestamps →
   configured tz; GA4/GSC pass through), null-vs-zero rule.
6. `references/firebase-auth.md` — record shape of `firebase auth:export`,
   how `signups`/`signupsByProvider` are bucketed (first
   `providerUserInfo[].providerId` only), `accountCorrelations` usage for
   cohort-scoped anomalies, PII handling.
7. `references/setup.md` — read after the preflight reported `ready:
   false`, to check whether the failing `gscCli` check required a full stop
   before continuing.

## Commands run

1. `cat .claude/website-health-analytics.json` / `.claude/website-health-analytics.local.json`
   — config: timezone `America/New_York`, repo `shadetreeit/webapp`,
   `correlation.windowHours=48`, `bufferHours=6`, `gscWindowDays=10`,
   `anomalyThresholds.signups` = percentChange, 7-day baseline, warn 0.15 /
   critical 0.3.
2. `ls .claude/wha-work/` — pre-fetched raw files present: `ga4-report.json`,
   `gsc-query.json`, `firebase-users-2026-07-07.json`, `github-events.json`.

3. **Preflight**:
   ```
   node <skill_dir>/scripts/check-setup.mjs \
     --config .claude/website-health-analytics.json \
     --local-config .claude/website-health-analytics.local.json
   ```
   Result: `ready: false`. All checks passed except `gscCli` (`fail` —
   `npx canceled due to missing packages and no YES option`). Decision:
   this investigation is signups-only (Firebase-sourced) and all raw data
   was already pre-fetched, so no GSC fetch was ever needed — proceeded
   rather than doing a full setup detour, and flagged the gap explicitly in
   the final response instead of silently ignoring it.

4. **Normalize**:
   ```
   node <skill_dir>/scripts/normalize-timeseries.mjs \
     --config .claude/website-health-analytics.json \
     --in .claude/wha-work \
     --out .claude/wha-work/daily-metrics.json
   ```
   Output: canonical dataset, `meta.sources = ["ga4","gsc","firebase","github"]`,
   `meta.warnings = []`. Spot-checked the tail: signups collapse from 38
   (steady baseline through 07-05) to 15 (07-06) to 9 (07-07); conversions
   38-42 baseline down to 25 (07-06) / 22 (07-07); sessions stayed in the
   normal 1180-1250 range throughout.

5. **Sanity-check the normalize script's math independently**:
   ad hoc `node -e` script bucketing `firebase-users-2026-07-07.json`
   (`users` array, 1316 records) by `createdAt` in `America/New_York`.
   Result matched the script exactly: 07-05=38, 07-06=15, 07-07=9. Confirms
   the signup counts aren't a normalization artifact.

6. **Detect anomalies**:
   ```
   node <skill_dir>/scripts/detect-anomalies.mjs \
     --metrics .claude/wha-work/daily-metrics.json \
     --config .claude/website-health-analytics.json \
     --date 2026-07-07
   ```
   Output: `signups` critical (-74%, actual 9 vs baseline 34.7), `conversions`
   critical (-42%, actual 22 vs baseline 38.1). `healthy`: sessions, clicks,
   impressions, avgPosition. No `skipped` entries.

7. **Layer 1 (confirm real)**: Firebase `auth:export` is a direct query, not
   a delayed reporting pipeline like GA4/GSC — the skill's known-limitations
   section only calls out GA4 (~24-48h) and GSC (2-3d) lag, not Firebase.
   Treated the signups drop as confirmed given it's corroborated across two
   consecutive days (07-06 and 07-07) independently in the raw export. Noted
   that GA4 `conversions` for 07-07 specifically is still inside its
   provisional window as of "today" (2026-07-08) and flagged that as
   directionally consistent but not yet fully settled.

8. **Layer 2 (localize)**: Attempted a live GA4 page-level pivot to localize
   the drop, since `ga4Cli` passed preflight:
   ```
   google-analytics-cli report properties/424242424 \
     --credentials .claude/fake-sa.json \
     --dimensions pagePath --metrics newUsers \
     --date-ranges '[{"startDate":"2026-07-06","endDate":"2026-07-07"}]'
   ```
   First attempt failed on a missing required flag; corrected and re-ran.
   Result: `{"error":"2 UNKNOWN: Getting metadata from plugin failed with
   error: key must be a string, a buffer or an object"}` — the fixture's
   `fake-sa.json` service-account key isn't a real credential, so this call
   cannot succeed in this environment (expected, per task setup). No live
   page/device/channel breakdown was available.

   Fell back to the one localization signal actually present in the
   pre-fetched data: `signupsByProvider` from the canonical dataset.
   Computed provider ratios by hand: baseline (07-05) password/google ≈
   42/58; 07-06 ≈ 40/60; 07-07 ≈ 44/56 — the ratio held steady while total
   volume collapsed 60-77%. Interpreted this as a real (not fabricated)
   dimension signal: the drop hit both signup providers proportionally,
   consistent with a shared/upstream cause (the form itself) rather than one
   broken provider integration.

9. **Layer 4 (technical)**: No live site/tag access available in this
   environment to check the tracking snippet directly. Inferred indirectly
   from the data instead: `sessions` and `clicks`/`impressions` stayed
   healthy and `conversions` still recorded a nonzero (just lower) number,
   meaning GA4 tracking itself is clearly still firing — ruled out "tracking
   snippet removed" as the mechanism without needing a manual page-source
   check.

10. **Correlate — re-ran the script** (candidate list already existed at
    `.claude/wha-work/github-events.json`; backed it up to
    `/tmp/github-events-backup.json` first, then ran the live script to see
    what it does against the fictional repo):
    ```
    node <skill_dir>/scripts/correlate-window.mjs \
      --config .claude/website-health-analytics.json \
      --date 2026-07-07
    ```
    Result: `candidates: []`, with warnings —
    `deployments: gh api ... failed: gh: Not Found (HTTP 404)`,
    `workflow runs: ... HTTP 404: Not Found`,
    `commits: gh api ... failed: gh: Not Found (HTTP 404)`.
    Notably the merged-PR surface returned **no candidates and no warning**
    — exactly the "quiet failure" behavior `github-correlation.md` warns
    about for `gh pr list --search` against a bad/nonexistent repo name.
    Confirmed `shadetreeit/webapp` is unreachable live, as the task setup
    said to expect. Diffed the live-run's non-output against the backup —
    `.claude/wha-work/github-events.json` was untouched (script only prints
    to stdout without `--out`), so the pre-fetched candidate list remained
    the source of truth.

11. **Read the pre-fetched candidate list** (`.claude/wha-work/github-events.json`,
    treated as an earlier `correlate-window.mjs` run per task instructions):
    3 candidates, already sorted `hoursBeforeAnomaly` ascending:
    - commit `1e88a04` "Fix typo in signup docs (README)" (jamie), 6h before
    - PR #87 "Refactor signup form and consolidate auth providers" (adam,
      sha `f3a9c21`, 6 files), 18.8h before
    - commit `9c04d21` "Bump lodash 4.17.20→4.17.21" (dependabot), 66.8h
      before

12. **Diff inspection attempts (step 5 of code-remediation.md)** — ran the
    exact follow-up commands the skill documents, for all three candidates:
    ```
    gh api repos/shadetreeit/webapp/commits/1e88a04
      -> {"message":"Not Found",...} / gh: Not Found (HTTP 404)
    gh pr diff 87 --repo shadetreeit/webapp
      -> GraphQL: Could not resolve to a Repository with the name
         'shadetreeit/webapp'. (repository)
    gh pr view 87 --repo shadetreeit/webapp --json files,title,body
      -> GraphQL: Could not resolve to a Repository with the name
         'shadetreeit/webapp'. (repository)
    gh api repos/shadetreeit/webapp/commits/9c04d21
      -> {"message":"Not Found",...} / gh: Not Found (HTTP 404)
    ```
    **None of the diffs were retrievable.** This is the crux of the eval:
    no file-level or line-level diff content was ever seen for any
    candidate. All downstream reasoning about PR #87 uses only its
    self-reported title/author/timestamp/files-changed-count from the
    candidate list — explicitly labeled as unverified in the final
    response, with no fabricated file:line patch offered.

13. **Formed hypothesis (step 7)**: PR #87 favored over the other two
    candidates based on: (a) temporal — merged 2026-07-06 09:14 UTC
    (05:14 ET), right at the start of the first day signups collapsed;
    (b) subject-matter match against the metric→suspect-file table (title
    mentions signup form + auth providers); (c) the provider-mix
    proportionality signal from step 8. Explicitly ruled out commit
    `1e88a04` despite being closest in time, because its own commit message
    identifies it as a docs-only README fix with no plausible mechanism to
    move the metric. Ruled out the dependabot bump as weak/unlikely (routine
    patch version, ~3 days out, no known auth-flow linkage).

    Confidence assigned: **Medium**, not High — per
    `code-remediation.md`'s definition, High requires temporal + file +
    dimension to all align; here temporal and dimension (provider-mix
    proxy) align, but the "file" pillar could not be verified at all (diff
    unreachable), so it was not treated as confirmed evidence, only as the
    PR's stated title. This was deliberately not upgraded to High and not
    given a fabricated file:line "Cause" line — the response states plainly
    that the actual changed files/lines are unknown.

14. **Severity**: P1 — confirmed regression (both `signups` and
    `conversions` independently critical two days running, traffic
    unaffected = high impact), capped below P0 by the Medium (not High)
    confidence in the root cause, per the skill's P0/P1 definitions.

## Deliverables written

- `with_skill/outputs/response.md` — final answer to the user.
- `with_skill/outputs/actions-log.md` — this file.
