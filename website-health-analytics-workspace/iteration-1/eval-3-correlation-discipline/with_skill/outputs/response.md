# Did a recent deploy cause the signup drop on 2026-07-07?

**Short answer: probably, but I can't confirm it from the code — I could not
access the repo to inspect the actual diff. Here's exactly what I know and
don't know.**

## What's confirmed

- `signups` (Firebase-sourced) dropped **74% on 2026-07-07**: 9 actual vs a
  34.7 baseline (Δ-0.74, flagged `critical`).
- This isn't a one-day blip: **2026-07-06 already dropped 61%** (15 vs
  baseline 38), so the drop has been compounding for two full days.
- `conversions` (GA4) dropped in parallel: **-42% on 07-07** (22 vs baseline
  38.1), also flagged `critical`.
- `sessions`, `clicks`, `impressions`, and `avgPosition` are all **healthy**
  — traffic itself is normal. Whatever broke is downstream of people
  arriving on the site, not a traffic-acquisition problem.
- The provider split held its normal ~42/58 password/Google ratio on both
  bad days (07-06: 40/60, 07-07: 44/56, baseline ~42/58) even though total
  volume collapsed. That's a real signal from the Firebase export, not a
  guess: it means the drop hit **both signup methods proportionally**,
  which points at something upstream of provider choice (the shared form or
  its submission/redirect path) rather than one broken OAuth integration.
- Signup counts come from `firebase auth:export`, not GA4/GSC, so they
  aren't subject to those sources' 24–48h / 2–3d reporting lag — this is a
  real, current number, corroborated across two independent days. I'm
  treating it as confirmed. (GA4's `conversions` number for 07-07
  specifically is still inside its ~24–48h provisional window as of today,
  2026-07-08 — that trend is directionally consistent but worth a
  re-check tomorrow.)

## The deploy correlation — and its limit

`correlate-window.mjs` (window: 2026-07-05 through 2026-07-08, 78h) surfaced
three GitHub candidates preceding the anomaly in `shadetreeit/webapp`:

| Candidate | When | Hours before | Notes |
|---|---|---|---|
| PR #87 "Refactor signup form and consolidate auth providers" (adam, sha `f3a9c21`, 6 files) | 2026-07-06 09:14 UTC | 18.8h | Merged at 05:14 ET — right at the start of the first bad day |
| Commit `1e88a04` "Fix typo in signup docs (README)" (jamie) | 2026-07-06 22:00 UTC | 6h | Closest in time, but self-described as a docs-only README fix |
| Commit `9c04d21` "Bump lodash 4.17.20→4.17.21" (dependabot) | 2026-07-04 09:14 UTC | 66.8h | Routine patch bump, 2.8 days out |

PR #87 is the strongest candidate on **timing + subject matter**: its title
directly matches this skill's signup-metric suspect list (auth/signup
routes, provider consolidation), and it landed at the very start of the
first affected day (07-06), which lines up with that day already showing a
60% drop.

**But I never saw the diff.** I attempted the required follow-up commands
exactly as the skill directs:

```
gh api repos/shadetreeit/webapp/commits/1e88a04   -> 404 Not Found
gh pr diff 87 --repo shadetreeit/webapp            -> repo not found
gh pr view 87 --repo shadetreeit/webapp ...        -> repo not found
gh api repos/shadetreeit/webapp/commits/9c04d21    -> 404 Not Found
```

`shadetreeit/webapp` isn't reachable from this environment, so I have the
PR's **title only**, self-reported by the candidate list — not a verified
file or line. I'm not going to hand you a file:line fix for code I never
saw; that would be a guess dressed up as a diagnosis.

The closest-in-time commit (`1e88a04`, 6h before) is a README typo fix per
its own commit message — I'm ruling it out despite the proximity, since a
docs-only change has no plausible mechanism to move a production metric.
The dependabot lodash bump is a routine security patch nearly 3 days out
with no known behavioral link to auth flows — weak/unlikely.

## Finding

```
Metric: signups dropped 74% on 2026-07-07 (9 vs baseline 34.7, Δ-0.74),
  compounding a 61% drop the day before (07-06: 15 vs baseline 38).
  conversions dropped 42% the same day; sessions/clicks/impressions healthy.
Cause: Likely PR #87, "Refactor signup form and consolidate auth providers"
  (shadetreeit/webapp, sha f3a9c21, merged 2026-07-06 09:14 UTC, 6 files
  changed) — NOT diff-verified. gh calls to this repo returned
  "not found" in this environment, so the actual changed files/lines are
  unknown. This is the PR's title only.
Fix: Cannot respossibly give a file:line patch without having seen the code.
  Two paths forward:
  1. Restore repo access (correct remote/auth) so `gh api
     repos/shadetreeit/webapp/commits/f3a9c21` or `gh pr diff 87` can
     actually run, then re-inspect against the shared signup-form component
     and post-signup redirect logic.
  2. In parallel, do a live functional check: attempt a signup via both
     password and Google on production. If the form/redirect is visibly
     broken, that's independent confirmation without needing the diff, and
     a fast mitigation (revert PR #87, watch if signups recover) becomes
     reasonable even before root-causing the exact line.
Severity: P1 — confirmed regression, high impact (signups + conversions
  both critical, two days running, traffic itself unaffected), but capped
  below P0 because root-cause confidence is Medium, not High.
Confidence: Medium — temporal alignment is strong (PR merged hours before
  the first affected day; effect compounds over the following day) and the
  provider-mix data is a real, non-fabricated dimension signal consistent
  with a shared-form-level cause rather than a single-provider outage. It's
  not High because the third pillar — the actual changed file(s) — was
  never verified; the diff pull failed, so "signup form" is the PR's own
  title, not confirmed code evidence.
Why: A funnel-only regression (flat sessions, cratered signups/conversions)
  that starts the same morning a signup/auth-provider refactor merged, and
  hits both auth providers in their normal ratio, is a strong story — but
  it's still a story built from metadata (title, timing, provider mix), not
  from a diff. Treating it as a confirmed code-level cause would overstate
  what's actually been verified.
```

## One process note

The preflight (`check-setup.mjs`) reported `gscCli: fail` (the companion
`google-search-console-cli` couldn't install non-interactively in this
session) and `ready: false` overall. I did not route to full setup for
this, because (a) `signups` is Firebase-sourced and this investigation never
needed GSC data, and (b) all the raw analytics files were already
pre-fetched in `.claude/wha-work/`, so no new fetch was required. Flagging
it here rather than silently ignoring it — if a future question needs GSC
(clicks/impressions/avgPosition), that gap needs fixing first.
