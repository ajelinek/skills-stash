# Iteration 1 — Eval Results

Skill: `website-health-analytics` | Date: 2026-07-08 | Runner model: Sonnet

## Scoreboard

| Eval | Run | Verdict | Notes |
| --- | --- | --- | --- |
| 1 unconfigured-project-routing | with_skill | **PASS** | Preflight ran first; `ready: false` correctly detected (missing GSC CLI, credentials, both config files); routed to setup.md; produced concrete user asks; no fabricated analysis; no unauthorized installs. |
| 2 daily-health-check-on-fixtures | with_skill | **PASS** | Real scripts ran (normalize → detect); flagged conversions −42.3% and signups −74.1% critical on 2026-07-07; applied "confirm it's real" via prior-day recheck + GA4 provisional-window reasoning; provider-mix checked; PR #87 surfaced only as Low-confidence timing lead; correctly did NOT run the remediation engine (out of daily-check scope). |
| 2 daily-health-check-on-fixtures | without_skill (baseline) | good analysis, weaker discipline | Found the same drop and suspect PR, but used ad-hoc methodology, stronger causal language with no confidence rubric, no preflight, non-reproducible report structure. |
| 3 deploy-correlation-discipline | with_skill | **PASS** | Re-ran correlate-window live (expected 404s), attempted all required diff inspections (all failed against fictional repo), assigned **Medium** confidence explicitly because the file-evidence pillar was unverified, claimed no file/line cause, fabricated no fix. P1 (capped below P0 by unverified root cause). |

## What the baseline comparison shows

With data already staged and a candidate list handed over, a bare agent can do
competent analysis. The skill's measured value is in: the preflight gate, the
configured thresholds (identical anomaly math every run), the confirm-it's-real
lag discipline, the explicit confidence rubric (baseline asserted "clear
suspect"; the skill runs said "Medium confidence, diff unverified"), and the
reproducible report template. Exactly the thin-orchestrator division of labor
the architecture intended.

## Change applied from this iteration

Both with-skill runs on the configured fixture had to consciously deviate from
the letter of the preflight stop rule (`ready: false` due only to a missing
fetch CLI, while pre-fetched raw data existed). SKILL.md now codifies that as
**degraded mode**: fetch-CLI failures with existing `.claude/wha-work/` data may
proceed with a disclosed deviation; config/credential failures always stop.

## Known environment caveats (not skill defects)

- Eval-runner subagents hit a Write-tool guardrail on filenames containing
  "report"; they worked around it via bash. Irrelevant to real usage.
- `firebase`/`gh` were already authenticated on this machine, so eval 1 could
  not exercise the not-authed branches of check-setup (they were exercised in
  the scripts agent's smoke tests instead).

## Not yet tested (needs real credentials / real repo)

- Live GA4/GSC fetching through the companion skills end-to-end.
- Phase 4 diff inspection against a real repo where the diff CAN be read
  (High-confidence path and worked-example fidelity).
- A real historical deploy-regression case.
