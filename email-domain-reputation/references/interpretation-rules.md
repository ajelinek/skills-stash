# Interpretation rubric

This is the judgment layer. Neither `scripts/check_reputation.py` nor
`scripts/check_dns_auth.py` computes a verdict — they only fetch and
normalize. Read this file when you have one or both scripts' JSON output in
hand and need to turn it into a **Trust / Caution / Block** verdict plus the
reasons behind it.

Two field namespaces, one per script, used independently or together:

- `signals.*` — from `check_reputation.py`'s output (`signals` object).
- `dns.*` — from `check_dns_auth.py`'s output. `dns.spf.*` maps to that
  script's `spf` object, `dns.dmarc.*` to `dmarc`, `dns.mx.*` to `mx`,
  `dns.dkim.*` to `dkim`.

Evaluate in this order. The first tier that matches wins — don't average or
soften a Block into a Caution because a Trust signal is also present.

## 1. Insufficient data

If you ran `check_reputation.py` and its top-level `source.ok` is `false`,
there's no reputation signal to judge — say so plainly (name the error and
detail from `source.error`/`source.detail`).

If you ran `check_dns_auth.py`, check its `errors` object: a non-empty entry
for a given section (`errors.mx`, `errors.spf`, `errors.dmarc`,
`errors.dkim`) means that section's result is missing, not negative — don't
treat a failed lookup the same as "no record found." Proceed with whichever
sections did succeed and say plainly which didn't.

If neither script ran successfully, there's nothing to judge — say so and
stop. Don't guess a verdict from nothing.

## 2. Block-level signals (any one true → Block)

| Signal | Condition |
|---|---|
| `signals.address_risk` | `"high"` |
| `signals.is_risky_tld` | `true` |
| `signals.is_disposable` **and** `signals.domain_age_days` | both true / `< 90` |

`is_disposable` alone (a throwaway-mailbox provider that's existed for
years) isn't block-level by itself — it's the combination with a
freshly-registered domain that reads as "spun up to send once and
disappear." Name every triggering condition, not just the first one found.

## 3. Caution-level signals (any one true → Caution, if not already Block)

| Signal | Condition |
|---|---|
| `signals.address_risk` | `"medium"` |
| `signals.domain_risk` | `"medium"` or `"high"` |
| `signals.total_breaches` | not null and `> 0` |
| `signals.is_free_email` **and** `signals.is_role` | both `true` (e.g. `support@gmail.com` — a generic role account with no corporate domain behind it) |
| `signals.domain_age_days` | not null and `< 90` |
| `signals.deliverability_status` | `"undeliverable"` |
| `signals.is_catchall` | `true` |
| `dns.mx.found` | `false` (domain can't receive mail at all — a live sender claiming this domain is already suspect) |

Deliberately *not* here: `dns.spf.found`/`dns.dmarc.found` being `false`
alone. Most legitimate small-business domains still lack DMARC — flagging
every one as Caution would drown the signal. Missing SPF/DMARC only counts
toward Trust when present (tier 4), and is instead surfaced as an
own-domain action item (tier 5) when the target is the requester's own
domain.

## 4. Trust-supporting signals (used to affirmatively state Trust when no Block/Caution signal fired)

| Signal | Condition |
|---|---|
| `signals.address_risk` **and** `signals.domain_risk` | both `"low"` |
| `signals.deliverable` | `true` |
| `dns.spf.strict` **and** `dns.dmarc.enforced` | both `true` — prefer these over `signals.spf_strict`/`signals.dmarc_enforced` when `check_dns_auth.py` ran; AbstractAPI's own fields are frequently `null` |
| `signals.quality_score` | not null and `> 0.7` |
| `signals.total_breaches` | `0` |
| `dns.mx.found` | `true` |

If none of tiers 2–3 fired but few or no tier-4 signals are present either
(mostly nulls — a domain/address with almost no footprint either way), don't
default to Trust. Say the check came back clean but thin, and name which
fields were null, so the requester knows it's a weak "no red flags" rather
than a strong "verified good."

## 5. Own-domain audit (additional output, only when the target is the requester's own domain)

This only applies when the user is auditing their own domain's outbound
config — not when triaging someone else's inbound address. If it's
ambiguous which case applies, ask. Requires `check_dns_auth.py` to have run;
`check_reputation.py` alone can't answer this (it inspects one address, not
DNS).

- **SPF** (`dns.spf`):
  - `found` is `false`: no SPF record at all — anyone can forge this
    domain's envelope sender. Action item: publish
    `v=spf1 include:<your mail provider's SPF include> -all`.
  - `found` is `true` but `strict` is `false` (`all_mechanism` is `~all`,
    `?all`, `+all`, or absent): tighten the record to hard-fail (`-all`).
  - `multiple_records` is `true`: multiple SPF TXT records is itself a
    misconfiguration (RFC 7208) — consolidate into exactly one record.
- **DMARC** (`dns.dmarc`):
  - `found` is `false`: publish a `_dmarc.<domain>` TXT record, e.g.
    `v=DMARC1; p=quarantine; pct=100; rua=mailto:dmarc-reports@<domain>`
    (`p=quarantine` is a reasonable first step before tightening to
    `p=reject` once the domain owner has reviewed aggregate reports).
  - `found` is `true` but `enforced` is `false`: name why — `policy` is
    `"none"` (monitoring only, not enforcing), `pct` is `< 100` (only
    partially enforced), or `multiple_records` is `true` (per RFC 7489,
    multiple `_dmarc` TXT records make the policy void regardless of what
    any individual record says — consolidate into one).
- **DKIM** (`dns.dkim`):
  - `found` is `false`: note this means none of the common
    provider-default selectors resolved (`selectors_checked` lists which
    were tried) — for a domain on a known platform (Microsoft 365, Google
    Workspace) this usually means DKIM signing was never turned on for the
    custom domain in that platform's admin console, since the standard
    selector CNAMEs would otherwise resolve. Recommend checking the mail
    platform's admin settings directly rather than assuming DKIM is
    unconfigured — a non-default selector wouldn't show up here either.
- **MX** (`dns.mx`):
  - `found` is `false`: domain can't receive mail — flag as a setup gap if
    the user expects it to.

These are action items regardless of the Trust/Caution/Block verdict — a
domain can be otherwise reputable and still have a DNS gap worth closing.

## Tuning note

These thresholds (particularly `domain_age_days < 90` and
`quality_score > 0.7`) are reasonable starting defaults, not validated
against real fraud data. Treat them as a first cut — if real usage shows
false positives/negatives, adjust the numbers in this file; nothing in
either script needs to change.

`address_risk`/`domain_risk` and `quality_score` are AbstractAPI's own
composite judgments (not decomposed further in the API response), so this
rubric leans on them directly rather than re-deriving risk from lower-level
fields the API doesn't expose individually.
