# Metric Definitions

Per-metric definition, source of truth, and the rule for reconciling that
metric when two sources disagree. When a metric appears in
`anomalyThresholds`, its detection method lives in
[analysis-rules.md](analysis-rules.md) — this file is about what the number
*means* and which source to trust, not how anomalies are flagged.

| Metric | Definition | Source of truth | Reconciliation rule |
| --- | --- | --- | --- |
| `sessions` | GA4 sessions for the property | GA4 | Single-sourced; no reconciliation needed. |
| `activeUsers` | GA4 active users for the day | GA4 | Single-sourced. |
| `newUsers` | GA4 new users for the day | GA4 | Single-sourced. GA4's "new user" detection is device/cookie-based and undercounts across devices — treat as directional, not exact. |
| `conversions` | GA4 conversion events (as configured in the GA4 property) | GA4 | Single-sourced, but only as good as the underlying event configuration — see `code-remediation.md`'s CTA/event-binding worked example for how this breaks silently. |
| `signups` | New Firebase Auth accounts created | **Firebase Auth is authoritative** — it is server-side truth, one row per account created. | GA4 also has a `sign_up` event, but it's client-side and ad blockers / consent-mode suppress it. If GA4's `sign_up` count and Firebase's `signups` diverge by more than 20%, flag an **instrumentation gap** (the GA4 event isn't firing reliably) rather than treating the divergence itself as a signup anomaly. |
| `signupsByProvider` | Signups bucketed by first-linked `providerUserInfo[].providerId` | Firebase Auth | See [firebase-auth.md](firebase-auth.md) for the "first provider" rule — a later-linked provider must not be double-counted. |
| `clicks` | GSC clicks | GSC | Single-sourced. Subject to the 2–3 day GSC lag — see [analysis-rules.md](analysis-rules.md) layer 1. |
| `impressions` | GSC impressions | GSC | Single-sourced, same lag caveat as `clicks`. |
| `ctr` | GSC click-through rate (`clicks / impressions`) | GSC (as reported; do not recompute from rounded `clicks`/`impressions` if GSC provides `ctr` directly — its underlying counts have more precision than what's exposed) | Same lag caveat. |
| `avgPosition` | GSC average search position | GSC | Same lag caveat. Remember: a numeric **increase** is a ranking regression, not an improvement — see the `absoluteDelta` note in analysis-rules.md. |
| `deploys` | Deploys/PRs/commits landing on a given day | GitHub (`gh`, via `correlate-window.mjs`) | Not itself a health metric — this is correlation input, attached to a day for context in the canonical dataset. |

## "$20 tier usage" — explicitly undefined

There is currently no GA4 custom event that captures tier-specific (e.g.
"$20 plan") usage. If a user asks this skill to analyze or report on
tier-specific metrics, **do not guess at a proxy** (e.g. inferring tier from
page path or a loosely-related event) — the resulting number would be
unreliable and easy to mistake for ground truth.

Instead, respond with a **P3 recommendation** to define the event, along the
lines of:

> No GA4 event currently tracks $20-tier usage. Recommend adding a custom
> event (e.g. `tier_usage` with a `tier` parameter) fired at the point where
> tier-gated functionality is used, so this can be measured going forward.
> Until that event exists, tier-specific usage cannot be reported from GA4
> data.

This keeps the gap visible instead of silently inventing a number for it.
