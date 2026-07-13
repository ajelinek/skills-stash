---
name: email-domain-reputation
description: >
  Checks the reputation of an email address and its domain by querying
  EmailRep and Abstract API Email Validation, merging the results, and
  producing a plain-English Trust / Caution / Block verdict with the
  specific signals that drove it. Trigger on requests like "check the
  reputation of this email", "is this sender legit", "is this email safe",
  "verify this domain", or "audit my domain's SPF/DMARC setup". Runs as a
  Dockerized CLI so no local Python dependencies are needed and API keys
  never enter this session's context. Requires a one-time `.env` setup
  (see below) before first use — low-volume only (~250 EmailRep
  queries/month on the free tier), not a bulk-screening tool.
---

# Email/Domain Reputation Check

Fetches signals from two APIs, merges them into one JSON object, and hands
that JSON to you (Claude) to interpret against a fixed rubric — judgment
lives here in the skill instructions, not hardcoded in the script, so the
rubric can be tuned without touching code.

```
you → docker compose run --rm reputation-check <email>
        → scripts/check_reputation.py
            → EmailRep API   (needs EMAILREP_API_KEY, EMAILREP_USER_AGENT)
            → Abstract API   (needs ABSTRACTAPI_API_KEY)
        → merged JSON on stdout
    → you apply references/interpretation-rules.md, reply in plain English
```

## One-time setup

1. `cd` into this skill's own directory (the one containing this SKILL.md).
2. Copy `.env.example` to `.env` and fill in real values:
   - `EMAILREP_API_KEY` — from https://emailrep.io (free tier: 250
     queries/month, 10/day on a rolling 24h window)
   - `EMAILREP_USER_AGENT` — any stable identifying string
   - `ABSTRACTAPI_API_KEY` — from
     https://www.abstractapi.com/api/email-verification-validation-api
3. Never put real key values anywhere except `.env`. `.env` is gitignored;
   `.claude/settings.json` in this directory denies `Read(./.env)` so this
   session can't load the raw keys into its own context either — that deny
   rule is the actual control here, not a nice-to-have, since Claude Code
   will otherwise auto-load `.env` files it encounters.
4. Keys are read only from the environment (via Compose's `env_file`) —
   never pass a key as a CLI argument, which would leak it into shell
   history and the process list.

If `.env` doesn't exist yet, tell the user to create it from `.env.example`
and stop — don't try to guess or fabricate key values.

## Running a check

From this skill's directory:

```bash
docker compose run --rm reputation-check <email>
```

This prints exactly one JSON object to stdout — parse it, don't eyeball raw
output as the final answer. Every field the rubric needs lives under
`signals`; `sources.emailrep`/`sources.abstractapi` report whether each API
call actually succeeded; `partial: true` means one of them failed and the
result is based on the other alone.

## Interpreting the result

Read [references/interpretation-rules.md](references/interpretation-rules.md)
and apply it to the JSON's `signals` object. It defines, in priority order:

1. When there's not enough data to judge at all.
2. Block-level signals (any one → Block).
3. Caution-level signals (any one → Block having already been ruled out).
4. Trust-supporting signals (used to affirmatively call it Trust).
5. The own-domain SPF/DMARC audit add-on — only relevant when the target
   *is* the requester's own domain (ask if it's ambiguous which case this
   is), surfaced as action items with the specific DNS record to fix.

Always name the specific signals that drove the verdict — "Block: sender's
domain is 4 days old and uses a disposable-email provider" is useful,
"Block: looks suspicious" is not.

## Error handling

The script fails fast, before any network call, on:

- **Missing env var(s)** — exits non-zero with a `fatal_error` JSON naming
  which variable(s) are unset. Tell the user which one(s), point at
  `.env.example`, and stop.
- **Invalid email format** — exits non-zero with a `fatal_error` JSON. Don't
  retry with a guessed correction; ask the user to confirm the address.

Once past that point, each API's failure is independent and doesn't block
the other's result:

- **401 (bad key)** — reported per-source in `sources.<name>.error` as
  `invalid_api_key`; the other API's result still comes through.
- **429 (rate limit)** — reported as `rate_limited`; the script does not
  retry or back off (low-volume use case — not worth the complexity). If
  EmailRep hits this, mention its daily/monthly quota explicitly.
- **Timeout / network error** — reported as `timeout`/`network_error`; the
  other source's result is still returned. Say plainly that the verdict is
  based on partial data.

## Security notes

- Full API responses (breach history, social profiles — PII) print to
  stdout for this one request only. Don't redirect them to a persistent log
  file or repeat them back verbatim beyond what the verdict needs.
- This skill only ever reads/reports reputation and mail-auth config — it
  never modifies DNS records. The SPF/DMARC "action items" in the own-domain
  audit are recommendations for the user to apply themselves.

## Non-goals

- Not a bulk/high-volume screener — no queueing, no batch mode. A burst of
  testing during setup can burn a real chunk of EmailRep's monthly quota;
  test sparingly with a couple of known addresses, not a loop.
- Not a DNS enforcement tool — reports SPF/DMARC config state, doesn't
  change records.
- No persistent history of past lookups in this version.
