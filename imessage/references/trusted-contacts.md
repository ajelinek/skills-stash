# Trusted contacts

An explicit, user-maintained allow-list of handles (phone numbers/emails), stored
locally and never committed to this repo.

## Files

- `trusted_contacts.example.json` — tracked in git, always empty (`{"trusted_contacts": []}`).
  This is the schema template, not something the CLI ever reads or writes.
- `trusted_contacts.json` — the real file. Gitignored from the start, so a populated
  list can't end up in a commit even if someone runs `git add -A` in a working copy
  of this repo. Created automatically the first time `trusted-add` is run; doesn't
  need to exist beforehand (`trusted-list`/`doctor`/reads all treat a missing file as
  an empty list).

## Schema

```json
{
  "trusted_contacts": [
    { "handle": "+15551234567", "name": "Jane Doe", "note": "spouse" }
  ]
}
```

- `handle` (required) — a phone number or email exactly as it appears in `chat.db` or
  the AddressBook, e.g. from `contacts` or a message's `sender_handle`.
- `name`, `note` (optional) — for human readability only; not used for matching.

Handle matching (`is_trusted_handle` in `scripts/imessage_cli.py`) is the same loose
match used elsewhere in this skill: case-insensitive exact string, or last-10-digits
for phone numbers — so `+1 (555) 123-4567` and `+15551234567` match the same entry.

## What this does and doesn't do

`sender_trusted` is a field on every message a read command returns (`true`/`false`
for messages from others, `null` for your own messages, matching the existing
`sender_handle`/`sender_name` convention). It's a **data signal only**. This skill's
own behavior — what a read returns, what `send` requires before it fires — does not
change based on it. In particular, **trusted-sender status never substitutes for the
"no unconfirmed sends" rule** in `SKILL.md`: a message from a trusted contact is not
authorization to send anything without asking the actual user.

## Onboarding

`doctor` reports `trusted_contact_count` and, when it's `0`, a warning suggesting
`trusted-suggest` — which ranks people the user has actually exchanged messages with
by message count (excluding anyone already trusted) so the caller can ask the user
"want to add any of these?" `trusted-suggest` only surfaces candidates; it never adds
anyone on its own.

## Why this lives in the base skill, not a higher-level one

Maintaining the allow-list (the file, the matching, the `sender_trusted` signal) is
data plumbing — the same category of work as contact-name resolution or chat-guid
resolution, which this skill already does. What actually varies, and what shouldn't
live here, is *policy*: deciding that a message from a trusted sender should trigger
an autonomous reply, run unattended, or skip a confirmation. That belongs in a
separate, higher-level skill built on top of this one's read/send primitives, so that
riskier autonomous-action logic (and any watch/routine loop that pairs with it) stays
out of what is otherwise a simple, auditable fetch-and-send tool.
