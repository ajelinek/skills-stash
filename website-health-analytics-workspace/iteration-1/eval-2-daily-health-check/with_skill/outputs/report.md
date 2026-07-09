# Website Health Check — 2026-06-02 to 2026-07-07 (baseline window; latest complete day: 2026-07-07)

Sources: GA4 | GSC | Firebase Auth | GitHub (shadetreeit/webapp)
Overall: Regression detected

Setup note: The preflight (check-setup.mjs) reported ready: false because the
google-search-console-cli companion CLI could not be reached via npx in this
environment (no network access for on-demand package installation). GA4/GSC/
Firebase raw data for this run was already staged in .claude/wha-work/
(pre-fetched), so normalization and detection proceeded against those files
rather than issuing live fetches. In a live session the skill's instructions
say to stop and route to setup.md first -- this run instead used pre-staged
data per the eval setup instructions.

## Metric Summary (2026-07-07 vs. baseline)

| Metric | Actual | Baseline | Delta |
| --- | --- | --- | --- |
| sessions | 1,180 | 1,200.9 (28d avg) | -1.7% |
| conversions | 22 | 38.1 (7d avg) | -42.3% |
| signups | 9 | 34.7 (7d avg) | -74.1% |
| clicks | 204 | 219.1 (28d avg) | -6.9% |
| impressions | 9,186 | 8,976.8 (28d avg) | +2.3% |
| avgPosition | 12.33 | 11.99 (28d avg) | +0.34 (slightly worse) |

Traffic and SEO metrics (sessions, clicks, impressions, avgPosition) are all
within normal variance. The regression is isolated to the two
conversion/signup metrics -- visitors are arriving normally, but far fewer of
them are converting or signing up.

## Anomalies

### P1

- conversions (GA4): dropped 42.3% on 2026-07-07 (22 vs. a 7-day baseline of
  38.1), flagged critical by detect-anomalies.mjs. Confirmed real, not a
  data-lag artifact: the same drop already appeared on 2026-07-06 (25 vs.
  baseline 40.4, -38.2%, also critical), which is now outside GA4's ~24-48h
  provisional window, and the regression persisted into 07-07. Onset
  coincides with PR #87 ("Refactor signup form and consolidate auth
  providers", merged 2026-07-06 09:14 UTC by adam, 6 files changed) -- timing
  only, not yet confirmed as cause. Confidence: Low (Layers 2-4 of the
  root-cause framework -- dimension/page/technical checks -- have not been
  walked in this run; this is a lead, not a diagnosis). Next action: route
  to analysis-rules.md starting at Layer 2 (localize by dimension), then
  code-remediation.md if a code cause is confirmed.

- signups (Firebase): dropped 74.1% on 2026-07-07 (9 vs. a 7-day baseline of
  34.7), flagged critical. Same two-day pattern as conversions: already
  critical on 2026-07-06 (15 vs. baseline 38, -60.5%) and worsened into
  07-07. The drop is proportional across both signup providers (password and
  google.com both fell to roughly the same share of baseline volume -- not
  concentrated in one provider), which points away from a single-provider
  auth integration bug and toward something upstream of both providers, e.g.
  the signup form itself. This is consistent with, but does not confirm, PR
  #87 touching the signup form. Confidence: Low for the same reason as
  above -- no Layer 2-4 investigation performed in this run. Next action:
  same as conversions -- the two metrics almost certainly share one root
  cause and should be investigated together, starting from analysis-rules.md
  Layer 2.

## Notes for the next investigation pass

- Both anomalies are business-critical (conversions and signups, not just
  traffic) and have now persisted two full days -- this should be
  prioritized over a routine re-check.
- The provider-mix breakdown (proportional drop in both password and
  google.com signups) is a useful Layer-2-adjacent data point already
  visible in the normalized dataset; it is included here because it came
  free from data already fetched, not from running the full root-cause
  workflow.
- github-events.json (already staged in .claude/wha-work/) lists PR #87 as
  the only candidate change inside the correlation window preceding the
  anomaly -- correlate-window.mjs was not run in this pass since full
  root-causing is out of scope for the daily check; a follow-up session
  should run it and pull the PR #87 diff (gh pr diff 87) against the
  signup-form suspect-file table in code-remediation.md.
