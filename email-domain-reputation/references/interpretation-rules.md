# Interpretation rubric

This is the judgment layer. `scripts/check_reputation.py` only fetches and
normalizes — it never computes a verdict. Read this file when you have a
merged JSON object in hand (from stdout) and need to turn `signals` into a
**Trust / Caution / Block** verdict plus the reasons behind it.

Evaluate in this order. The first tier that matches wins — don't average or
soften a Block into a Caution because a Trust signal is also present.

## 1. Insufficient data

If both `sources.emailrep.ok` and `sources.abstractapi.ok` are `false`, there's
no signal to judge — say so plainly (name which service failed and why, from
`sources.*.error`/`detail`) and stop. Don't guess a verdict from nothing.

If exactly one source failed (`partial: true` but not both), proceed through
the tiers below using whatever signals the surviving source provided, and say
in the verdict that it's based on partial data — name the source that was
unavailable and why (`sources.<name>.error`).

## 2. Block-level signals (any one true → Block)

| Signal | Condition |
|---|---|
| `signals.blacklisted` | `true` |
| `signals.malicious_activity_recent` | `true` |
| `signals.is_disposable` **and** `signals.new_domain` | both `true` |
| `signals.suspicious_tld` | `true` |

`is_disposable` alone (a throwaway-mailbox provider that's existed for years)
isn't block-level by itself — it's the combination with a freshly-registered
domain that reads as "spun up to send once and disappear." Name every
triggering condition, not just the first one found.

## 3. Caution-level signals (any one true → Caution, if not already Block)

| Signal | Condition |
|---|---|
| `signals.credentials_leaked` | `true` |
| `signals.data_breach` | `true` |
| `signals.is_free_email` **and** `signals.is_role` | both `true` (e.g. `support@gmail.com` — a generic role account with no corporate domain behind it) |
| `signals.domain_age_days` | not null and `< 90` |
| `signals.is_catchall` **and** (`signals.profiles` is null or empty) | true — accepts-all-mail with no corroborating public presence |

## 4. Trust-supporting signals (used to affirmatively state Trust when no Block/Caution signal fired)

| Signal | Condition |
|---|---|
| `signals.reputation` | `"high"` |
| `signals.profiles` | 2 or more entries |
| `signals.deliverable` | `true` |
| `signals.spf_strict` **and** `signals.dmarc_enforced` | both `true` |
| `signals.quality_score` | not null and `> 0.7` |

If none of tiers 2–3 fired but few or no tier-4 signals are present either
(mostly nulls — a domain/address with almost no footprint either way), don't
default to Trust. Say the check came back clean but thin, and name which
fields were null, so the requester knows it's a weak "no red flags" rather
than a strong "verified good."

## 5. Own-domain audit (additional output, only when the target is the requester's own domain)

This only applies when the user is auditing their own domain's outbound
config (FR4) — not when triaging someone else's inbound address. If it's
ambiguous which case applies, ask.

- If `signals.spf_strict` is `false`: flag as an action item. The fix is
  tightening the domain's SPF TXT record to hard-fail (`-all`) instead of a
  soft-fail (`~all`) or missing record, e.g.:
  `v=spf1 include:<your mail provider's SPF include> -all`
- If `signals.dmarc_enforced` is `false`: flag as an action item. The fix is
  publishing (or tightening) a `_dmarc.<domain>` TXT record to an enforcing
  policy, e.g.:
  `v=DMARC1; p=reject; rua=mailto:dmarc-reports@<domain>`
  (`p=quarantine` is a reasonable intermediate step before `p=reject` if the
  domain hasn't been monitoring DMARC reports yet.)

These are action items regardless of the Trust/Caution/Block verdict — a
domain can be otherwise reputable and still have a DNS gap worth closing.

## Tuning note

These thresholds (particularly `domain_age_days < 90` and
`quality_score > 0.7`) are reasonable starting defaults, not validated
against real fraud data. Treat them as a first cut — if real usage shows
false positives/negatives, adjust the numbers in this file; nothing in
`check_reputation.py` needs to change.
