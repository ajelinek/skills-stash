# Analysis Rules

Two layers: the deterministic thresholds `detect-anomalies.mjs` applies, and
the agentic 5-layer root-cause framework you walk afterward to decide
whether an anomaly is real and where it's localized.

## Contents

1. [Running detect-anomalies.mjs](#running-detect-anomaliesmjs)
2. [Threshold methods](#threshold-methods)
3. [The 5-layer root-cause framework](#the-5-layer-root-cause-framework)

## Running detect-anomalies.mjs

```bash
node <skill_dir>/scripts/detect-anomalies.mjs \
  --metrics .claude/wha-work/daily-metrics.json \
  --config .claude/website-health-analytics.json \
  [--date 2026-07-08]
```

`--date` defaults to the most recent complete day in the dataset. Output:

```json
{
  "date": "2026-07-08",
  "anomalies": [
    {
      "metric": "signups",
      "date": "2026-07-08",
      "baseline": 40.1,
      "actual": 22,
      "delta": -0.45,
      "direction": "drop",
      "method": "percentChange",
      "severityDraft": "critical",
      "source": "firebase"
    }
  ],
  "healthy": ["sessions", "clicks"],
  "skipped": [{ "metric": "...", "reason": "insufficient baseline" }]
}
```

This script does deterministic math only — no interpretation. `severityDraft`
(`warn`/`critical`, from `anomalyThresholds`) is a starting point, not the
final P0–P3 call; that comes out of the root-cause framework below and
[code-remediation.md](code-remediation.md) step 7's confidence rules.

## Threshold methods

Configured per metric in `anomalyThresholds` (see the config template in
[examples/website-health-analytics.json](../examples/website-health-analytics.json)):

| Method | How it works | Used for | Notes |
| --- | --- | --- | --- |
| `zscore` | Rolling mean/stddev over the trailing `baselineDays`, excluding the evaluated day. Flags if `\|z\| >= warn` (or `critical`). | `sessions`, `clicks`, `impressions` | Skipped if fewer than 7 baseline points or stddev is 0 — see `skipped` in the output. |
| `percentChange` | Percent difference vs. the mean of the trailing `baselineDays`. Flags if `\|delta\| >= threshold`. | `conversions`, `signups` | Straightforward relative-change detection for metrics with noisier day-to-day counts. |
| `absoluteDelta` | Raw difference vs. the trailing mean (not a ratio). | `avgPosition` | For `avgPosition`, an **increase** is bad (worse ranking) — direction matters here more than for the other metrics. |

## The 5-layer root-cause framework

Walk these layers in order for any "did X cause Y" or drop investigation.
Each layer names what to check and where its result routes you next — most
anomalies resolve by layer 2 or 3; only genuinely code-caused regressions
need to go all the way to [code-remediation.md](code-remediation.md).

### Layer 1 — Confirm it's real

Check the anomaly's date against data-lag windows before trusting it:

- GA4 data is provisional for ~24–48 hours.
- GSC data lags 2–3 days; use `correlation.gscWindowDays`.

**Check:** re-run the relevant companion-skill report for the same date a
day or two later and compare. **Route:** if the anomaly shrinks or
disappears once data settles, stop — say "unconfirmed, re-check after the
data-lag window closes." If it persists, go to layer 2.

### Layer 2 — Localize by dimension

**Check:** pivot the confirmed metric by device, channel, page, country,
and query, using the companion skills' documented pivot/dimension queries
(GA4 dimensions, GSC query/page breakdowns).
**Route:** a drop concentrated in one dimension (e.g. only `organic search`,
only `mobile`, only one country) points toward a narrower cause — continue
to layer 3 for page-level detail. A drop spread evenly across all
dimensions points away from a code change and toward layer 5 (external
causes).

### Layer 3 — Page-level

**Check:** for the localized dimension, break down by landing page / query
in GSC or page path in GA4 to find which specific pages or URLs account for
the movement.
**Route:** a small number of pages responsible for most of the drop →
strong candidate for a code-caused regression; proceed to layer 4 to rule
out a technical cause before jumping to correlation. Broad, page-agnostic
movement → proceed to layer 5.

### Layer 4 — Technical

**Check:** indexing status and sitemap presence for the affected pages
(GSC), whether the site's tracking tag/snippet is still present and firing
(page source or GA4 DebugView-equivalent), and whether a redirect or route
deletion is in play.
**Route:** a technical fault (deindexed page, missing tracking snippet,
broken redirect) found here → skip straight to
[code-remediation.md](code-remediation.md) step 4 (the mechanism is known,
the causing commit still needs finding). No technical fault found →
proceed to layer 5, or straight to code-remediation.md if timing already
strongly suggests a deploy (layers 2–3 pointed at a narrow, recently-changed
area).

### Layer 5 — External

**Check:** known search-algorithm updates around the anomaly date,
seasonality (compare to the same period in prior weeks/years), and whether
a major referral source (a partner site, a social post) simply stopped
sending traffic.
**Route:** an external cause found here → state it as the root cause with
appropriate confidence (see code-remediation.md step 7); no code fix to
propose. Nothing found at any layer → move to
[code-remediation.md](code-remediation.md) anyway, starting from its
correlation step, but state Low confidence — proximity in time to a deploy
is suggestive, not proof, without a layer 2–4 signal backing it.
