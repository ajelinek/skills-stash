---
name: email-domain-reputation
description: >
  Checks the reputation of an email address and audits its domain's mail
  authentication (SPF/DMARC/MX/DKIM) via two independent scripts, producing
  a plain-English Trust / Caution / Block verdict plus concrete DNS action
  items. Trigger on requests like "check the reputation of this email", "is
  this sender legit", "is this email safe", "verify this domain", "audit my
  domain's SPF/DMARC setup", "is this domain spoofable", or "check DNS mail
  auth". Both scripts are stdlib-only Python (no pip install, no
  container); the reputation check needs a one-time free-tier API key (see
  below), the DNS audit needs none — it queries public DNS directly.
---

# Email/Domain Reputation Check

Two independent stdlib-only Python scripts each fetch and normalize signals
into one JSON object; you (Claude) interpret that JSON against a fixed
rubric. Judgment lives in this skill's instructions, not hardcoded in the
scripts, so the rubric can be tuned without touching code.

```
you → python3 scripts/check_reputation.py <email>
        → AbstractAPI Email Reputation   (needs ABSTRACTAPI_API_KEY)
        → normalized JSON on stdout
  → python3 scripts/check_dns_auth.py <email-or-domain>
        → live public DNS -- SPF/DMARC/MX/DKIM   (no key needed)
        → normalized JSON on stdout
    → you apply references/interpretation-rules.md to both, reply in plain English
```

AbstractAPI acquired EmailRep and merged it into the one reputation
endpoint — there is no longer a separate EmailRep API to call, and the two
used to require three env vars between them. Now there's exactly one.
Neither script reads the other's output or requires the other to run.

## API key to get (one-time)

| Variable | Where to get it |
|---|---|
| `ABSTRACTAPI_API_KEY` | https://www.abstractapi.com/api/email-verification-validation-api — a key issued from either abstractapi.com **or** emailrep.io works, since EmailRep signups now provision an AbstractAPI key under the hood. |

## Where to put it

The script reads from the real environment first, and only falls back to a
local `.env` file (next to this SKILL.md) if it isn't already set — so pick
whichever of these matches how you're running Claude:

- **Claude Code on the web / a cloud session (like this one):** set it as a
  real environment variable in the environment's own settings (Environment
  Variables, in that environment's configuration) rather than a file. It
  gets injected directly into `os.environ` for every session in that
  environment — there's no file for Claude to accidentally read in the
  first place.
- **Claude Code CLI or Desktop on your own machine:** copy `.env.example` to
  `.env` in this skill's directory and fill in the real value. `.env` is
  gitignored, and this directory's `.claude/settings.json` denies
  `Read(./.env)` — so even on a local machine, Claude Code can't load the
  raw key into its own context. That deny rule is the actual control here,
  not a nice-to-have: Claude Code will otherwise auto-load `.env` files it
  encounters.

Either way: never pass the key as a CLI argument — that would leak it into
shell history and the process list. If neither a real env var nor `.env`
supplies it, tell the user it's missing and point them at this section
rather than guessing.

## Running a check

Run whichever script fits the request, or both together for a full email
evaluation:

```bash
python3 scripts/check_reputation.py <email>            # AbstractAPI reputation signals
python3 scripts/check_dns_auth.py <email-or-domain>     # live SPF/DMARC/MX/DKIM via DNS
```

- **Evaluating an email address** ("is this sender legit", "check this
  email", "verify this domain") — run **both**. `check_dns_auth.py` accepts
  the same email argument and extracts the domain itself, so there's no
  need to parse it out first. Feed both JSON outputs into
  references/interpretation-rules.md together — a domain with no SPF/DMARC
  is more spoofable regardless of what the reputation API says about the
  specific address.
- **Auditing your own domain's outbound mail config** ("audit my SPF/DMARC
  setup") — `check_dns_auth.py <domain>` alone is enough; the reputation
  API inspects a specific address, not your DNS, so it has nothing to add
  here.
- **Just want AbstractAPI's read on one address, no DNS lookups needed** —
  run `check_reputation.py` alone.

No install step — both scripts only use Python's standard library
(`check_dns_auth.py` also needs the system `dig` binary, present by default
on macOS/most Linux). Each prints exactly one JSON object to stdout — parse
it, don't eyeball raw output as the final answer.

## Interpreting the result

Read [references/interpretation-rules.md](references/interpretation-rules.md)
and apply it to the JSON `signals` object (from check_reputation.py) and/or
the DNS `mx`/`spf`/`dmarc`/`dkim` objects (from check_dns_auth.py),
depending on which you ran. It defines, in priority order:

1. When there's not enough data to judge at all.
2. Block-level signals (any one → Block).
3. Caution-level signals (any one → Caution, having already ruled out Block).
4. Trust-supporting signals (used to affirmatively call it Trust).
5. The own-domain SPF/DMARC/DKIM audit add-on — only relevant when the
   target *is* the requester's own domain (ask if it's ambiguous which
   case this is), surfaced as action items with the specific DNS record to
   fix.

Always name the specific signals that drove the verdict — "Block: sender's
domain is 4 days old and uses a disposable-email provider" is useful,
"Block: looks suspicious" is not.

## Error handling

Both scripts fail fast, before any network call, on invalid input, and
exit non-zero with a `fatal_error` JSON:

- **check_reputation.py — missing env var**: names `ABSTRACTAPI_API_KEY`.
  Tell the user and point them at "Where to put it" above, then stop.
- **check_reputation.py / check_dns_auth.py — invalid email or domain
  format**: don't retry with a guessed correction; ask the user to confirm.
- **check_dns_auth.py — `dig` not found**: tell the user to install
  `dnsutils`/`bind-utils`, or that this check needs a host that has `dig`.

Past that point, exit code is still 0 even if a lookup itself failed:

- `check_reputation.py`'s `source.ok`/`source.error` report the API call's
  outcome: `invalid_api_key` (401), `rate_limited` (429, no retry/backoff —
  mention the plan's quota explicitly), or `timeout`/`network_error`.
- `check_dns_auth.py`'s `errors` object reports per-section failures (e.g.
  `errors.dmarc`) without blocking the other sections — say plainly which
  section's result is missing rather than presenting partial data as
  complete.

## Security notes

- `check_reputation.py`'s full API response (breach history — PII) prints
  to stdout for this one request only. Don't redirect it to a persistent
  log file or repeat it back verbatim beyond what the verdict needs.
  `check_dns_auth.py`'s output is all public DNS data (SPF/DMARC/MX/DKIM
  records are published for any mail server to read), so it carries no
  comparable sensitivity.
- This skill only ever reads/reports reputation and mail-auth config — it
  never modifies DNS records. The SPF/DMARC/DKIM "action items" in the
  own-domain audit are recommendations for the user to apply themselves.

## Non-goals

- Not a bulk/high-volume screener — no queueing, no batch mode. A burst of
  testing during setup can burn a real chunk of the reputation API's
  free-tier quota; test sparingly with a couple of known addresses, not a
  loop. (`check_dns_auth.py` queries public DNS directly, so it has no
  comparable quota concern.)
- Not a DNS enforcement tool — reports SPF/DMARC/DKIM config state, doesn't
  change records.
- `check_dns_auth.py`'s DKIM check is best-effort against a short list of
  common provider-default selectors — it cannot discover a non-default or
  randomized selector, so a "not found" result means "not found under a
  common selector," not "DKIM is definitely not configured."
- No persistent history of past lookups in this version.
