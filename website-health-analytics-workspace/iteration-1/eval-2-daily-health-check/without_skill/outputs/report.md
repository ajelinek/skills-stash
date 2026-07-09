# Daily Website Health Check — shadetreeit.biz (prod)
**Run date:** 2026-07-08 | **Timezone:** America/New_York | **Data through:** 2026-07-07

## TL;DR

Critical: signup conversions have collapsed starting 2026-07-06, while site traffic is normal. This looks like a broken signup flow, not a traffic/demand problem. The most likely cause is PR #87 "Refactor signup form and consolidate auth providers" (merged 2026-07-06 09:14 UTC), which lands the same day the drop shows up in both GA4 conversions and actual Firebase account creations.

Everything else (organic search performance, overall traffic/sessions) is within normal range.

---

## 1. Traffic & Conversions (GA4)

| Metric | 2026-07-06 | 2026-07-07 | 7-day baseline avg | Change (latest vs baseline) |
|---|---|---|---|---|
| Sessions | 1,224 | 1,180 | ~1,201 | normal (z ~= +0.7 / -0.6) |
| Active Users | 1,077 | 1,038 | ~1,068-1,075 | normal (-3% to +1%) |
| New Users | 294 | 290 | ~303 | normal (-3% to -4%) |
| Conversions | 25 | 22 | ~38-40 | CRITICAL: -38% / -42% |

- Sessions, active users, and new-user counts are all inside normal day-to-day variation (z-scores well under the configured warn threshold of 2).
- Conversions dropped ~38% on 7/6 and ~42% on 7/7 versus the trailing 7-day average. This crosses the configured critical threshold (30% change) on both days.
- Because raw traffic and new-user counts are flat, this is not a traffic problem -- people are reaching the site at the normal rate but not completing whatever GA4 is tracking as a "conversion" (signup completion).

## 2. Account Creation (Firebase Auth Export)

I cross-checked GA4 conversions against actual account creation timestamps in the `firebase-users-2026-07-07.json` auth export (1,316 total users), bucketed by day:

| Date | New accounts | vs. ~38/day baseline (prior 12 days flat) |
|---|---|---|
| 2026-06-24 -> 2026-07-05 | 38/day (steady) | baseline |
| 2026-07-06 | 15 | -60% |
| 2026-07-07 (export cutoff, partial day) | 9 | -74% (partial day, so directionally worse, not necessarily worse per-hour) |

Breaking this down by auth provider:

| Date | password | google.com |
|---|---|---|
| 2026-07-05 | 16 | 22 |
| 2026-07-06 | 6 | 9 |
| 2026-07-07 | 4 | 5 |

Both the password and Google auth providers dropped by roughly the same proportion (~55-60%) on the same day. A provider-specific outage (e.g., Google OAuth misconfiguration only) would typically hit one provider much harder than the other -- this proportional, across-the-board drop instead points to something upstream and shared, like the signup form itself or a shared submission/redirect step.

This independently confirms the GA4 conversion drop is real (not an instrumentation/tagging artifact) -- actual account creation in Firebase fell off a cliff on the same day.

## 3. Likely Cause -- Deploy Correlation

Recent commits/PRs to `shadetreeit/webapp` in the window around the anomaly:

| When (UTC) | Type | Author | Description | Timing vs anomaly |
|---|---|---|---|---|
| 2026-07-06 09:14 | PR #87 | adam | "Refactor signup form and consolidate auth providers" (6 files changed) | ~18.8h before the anomaly window ends; conversions visibly drop the same day |
| 2026-07-06 22:00 | commit 1e88a04 | jamie | "Fix typo in signup docs (README)" | 6h before |
| 2026-07-04 09:14 | commit 9c04d21 | dependabot | "Bump lodash from 4.17.20 to 4.17.21" | 66.8h before |

PR #87 is the standout candidate:
- It's the only change that directly touches the signup form and auth providers -- exactly the surface where the drop is occurring.
- It was merged the morning of 2026-07-06 (UTC), the same calendar day account creation started collapsing.
- The proportional drop across both password and Google auth (rather than just one) is consistent with a shared-form-layer regression introduced by "consolidating" the providers, e.g., a broken submit handler, validation bug, or routing/redirect issue that affects all providers equally.
- The jamie commit is a README typo fix -- not a plausible cause. The dependabot lodash patch bump landed two days earlier and lodash patch bumps rarely cause functional regressions of this nature; also, the timing is off (it doesn't line up with the 7/6 drop as well as PR #87 does).

Recommendation: Treat PR #87 as the primary suspect. Suggest a rollback or hotfix of the signup form changes, and manually test the signup flow (both password and Google) end-to-end today. Every day this persists is costing roughly 25-30 lost signups vs. baseline.

## 4. Search Performance (Google Search Console)

| Metric | 2026-07-06 | 2026-07-07 | 28-day baseline | Status |
|---|---|---|---|---|
| Clicks | 208 | 204 | ~219-220 | Normal (z ~= -1.3 / -1.7, below warn threshold of 2) |
| Impressions | 9,289 | 9,186 | ~8,970-8,980 | Normal (z ~= +1.8 / +1.1, below warn threshold of 2, worth a passing glance) |
| Avg. Position | 12.53 | 12.33 | ~11.97-11.99 | Normal (delta ~= +0.34 to +0.56, below warn threshold of 3) |
| CTR | 2.24% | 2.22% | ~2.4-2.6% (recent weeks) | Trending slightly down but not flagged by any configured threshold |

No search-visibility anomalies today. Clicks and average position are both drifting slightly unfavorably over the last ~2 weeks but remain inside normal variation bands per the configured thresholds -- nothing actionable here today, just worth keeping an eye on if the trend continues.

## 5. What's Healthy

- Overall site traffic (sessions, active users, new users) -- normal.
- Organic search clicks, impressions, ranking position -- normal, no threshold breaches.
- No other GitHub deploys in the lookback window besides the three listed above.

## 6. Action Items

1. Today: Manually test the signup flow (password + Google) on production. Look for broken validation, silent JS errors, or a submit/redirect step that fails silently.
2. Today: Review PR #87's diff for the auth-provider consolidation logic -- this is the prime suspect.
3. If confirmed, hotfix or roll back PR #87 and re-verify signups recover to the ~38/day baseline.
4. Re-run this check tomorrow (2026-07-09) once a fix ships, to confirm signups and conversions have recovered before declaring this resolved -- the 07-07 figure is based on a partial day (export was taken 2026-07-07), so treat it as directionally consistent rather than a final number.

---
Notes on method: This check was run without live API access (no network fetching available in this environment); it uses the pre-pulled data files already staged in `.claude/wha-work/` (GA4, GSC, Firebase Auth export, GitHub events). Anomaly thresholds and baseline windows follow the project's configured `anomalyThresholds` in `.claude/website-health-analytics.json` (sessions/clicks/impressions: z-score, 28-day baseline, warn 2 / critical 3; conversions/signups: % change, 7-day baseline, warn 15% / critical 30%; avg position: absolute delta, 28-day baseline, warn 3 / critical 6).
