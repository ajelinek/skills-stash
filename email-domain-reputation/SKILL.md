---
name: email-domain-reputation
description: >
  Checks the reputation of an email address and its domain by querying
  EmailRep and Abstract API Email Validation, merging the results, and
  producing a plain-English Trust / Caution / Block verdict with the
  specific signals that drove it. Trigger on requests like "check the
  reputation of this email", "is this sender legit", "is this email safe",
  "verify this domain", or "audit my domain's SPF/DMARC setup". The fetch
  script is stdlib-only Python (no pip install, no container) — low-volume
  only (~250 EmailRep queries/month on the free tier), not a bulk-screening
  tool. Requires a one-time API key setup (see below) before first use.
---

# Email/Domain Reputation Check

A single stdlib-only Python script fetches signals from two APIs and merges
them into one JSON object; you (Claude) interpret that JSON against a fixed
rubric. Judgment lives in this skill's instructions, not hardcoded in the
script, so the rubric can be tuned without touching code.

```
you → python3 scripts/check_reputation.py <email>
        → EmailRep API   (needs EMAILREP_API_KEY, EMAILREP_USER_AGENT)
        → Abstract API   (needs ABSTRACTAPI_API_KEY)
        → merged JSON on stdout
    → you apply references/interpretation-rules.md, reply in plain English
```

## API keys to get (one-time)

Two free accounts, three values total:

| Variable | Where to get it |
|---|---|
| `EMAILREP_API_KEY` | https://emailrep.io — free tier: 250 queries/month, 10/day (rolling 24h window) |
| `EMAILREP_USER_AGENT` | Not a real credential — any stable identifying string works, e.g. `your-name-reputation-check` |
| `ABSTRACTAPI_API_KEY` | https://www.abstractapi.com/api/email-verification-validation-api |

## Where to put them

The script reads from the real environment first, and only falls back to a
local `.env` file (next to this SKILL.md) for whichever variables aren't
already set — so pick whichever of these matches how you're running Claude:

- **Claude Code on the web / a cloud session (like this one):** set them as
  real environment variables in the environment's own settings (Environment
  Variables, in that environment's configuration) rather than a file. They
  get injected directly into `os.environ` for every session in that
  environment — there's no file for Claude to accidentally read in the
  first place.
- **Claude Code CLI or Desktop on your own machine:** copy `.env.example` to
  `.env` in this skill's directory and fill in real values. `.env` is
  gitignored, and this directory's `.claude/settings.json` denies
  `Read(./.env)` — so even on a local machine, Claude Code can't load the
  raw keys into its own context. That deny rule is the actual control here,
  not a nice-to-have: Claude Code will otherwise auto-load `.env` files it
  encounters.

Either way: never pass a key as a CLI argument — that would leak it into
shell history and the process list. If neither a real env var nor `.env`
supplies a required value, tell the user which one is missing and point
them at this section rather than guessing.

## Running a check

```bash
python3 scripts/check_reputation.py <email>
```

No install step — the script only uses Python's standard library. It
prints exactly one JSON object to stdout — parse it, don't eyeball raw
output as the final answer. Every field the rubric needs lives under
`signals`; `sources.emailrep`/`sources.abstractapi` report whether each API
call actually succeeded; `partial: true` means one of them failed and the
result is based on the other alone.

## Interpreting the result

Read [references/interpretation-rules.md](references/interpretation-rules.md)
and apply it to the JSON's `signals` object. It defines, in priority order:

1. When there's not enough data to judge at all.
2. Block-level signals (any one → Block).
3. Caution-level signals (any one → Caution, having already ruled out Block).
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
  which variable(s) are unset. Tell the user which one(s) and point them at
  "Where to put them" above, then stop.
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
