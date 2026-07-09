# Daily Health Check

The dashboard-mode workflow: pull yesterday plus a 28-day trailing baseline
across all four sources, normalize, detect, and produce the report below.
This is the route for "daily analytics dashboard" / "run a website health
check" requests with no specific anomaly already in hand.

## Workflow

1. **Fetch** yesterday's data plus the trailing 28 days (enough baseline for
   `zscore` methods) via:
   - The GA4 companion skill's documented commands
   - The GSC companion skill's documented commands
   - `firebase auth:export` (see [firebase-auth.md](firebase-auth.md))
   Save all raw output into `.claude/wha-work/` using the naming convention
   in [data-normalization.md](data-normalization.md).
2. **Normalize:**
   ```bash
   node <skill_dir>/scripts/normalize-timeseries.mjs \
     --config .claude/website-health-analytics.json \
     --in .claude/wha-work \
     --out .claude/wha-work/daily-metrics.json
   ```
3. **Detect:**
   ```bash
   node <skill_dir>/scripts/detect-anomalies.mjs \
     --metrics .claude/wha-work/daily-metrics.json \
     --config .claude/website-health-analytics.json
   ```
4. **Report** using the template below. Anomalies that look real and
   code-caused get handed to [analysis-rules.md](analysis-rules.md) and
   [code-remediation.md](code-remediation.md) for root-causing — the daily
   check itself does not run the full remediation engine, it surfaces what
   needs it.

## Report template

```
# Website Health Check — <date range>

Sources: GA4 | GSC | Firebase Auth | GitHub (<repo list>)
Overall: 🟢 Healthy | 🟡 Needs attention | 🔴 Regression detected

## Metric Summary

| Metric | Actual | Baseline | Δ |
| --- | --- | --- | --- |
| sessions | ... | ... | ... |
| conversions | ... | ... | ... |
| signups | ... | ... | ... |
| clicks | ... | ... | ... |
| impressions | ... | ... | ... |
| avgPosition | ... | ... | ... |

## Anomalies

### P0
- <metric>: <one-line observation> — next action: <route to analysis-rules.md / code-remediation.md, or "re-check after data-lag window">

### P1
- ...

### P2
- ...

### P3
- ...

(omit any severity section with nothing in it)
```

## Quiet-day variant

When `detect-anomalies.mjs` returns an empty `anomalies` array, skip the
Anomalies section entirely and use a short form:

```
# Website Health Check — <date range>

Sources: GA4 | GSC | Firebase Auth | GitHub (<repo list>)
Overall: 🟢 Healthy — no action needed

All tracked metrics (sessions, conversions, signups, clicks, impressions,
avgPosition) are within their baseline thresholds. No anomalies detected.
```

Do not pad a quiet day with speculative growth suggestions unless the user
asked for growth ideas specifically — that's a distinct request routed to
[code-remediation.md](code-remediation.md) § Growth Mode, not part of the
daily check's default output.
