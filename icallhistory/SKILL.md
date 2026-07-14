---
name: icallhistory
description: >
  Query local Mac/iPhone call history — cellular phone calls, FaceTime Audio, and
  FaceTime Video — by date range, contact, or direction, and resolve numbers to
  contact names via the local AddressBook. Trigger on requests like "who called me",
  "what numbers have I called", "show my missed calls", "did I call <person>", "call
  history with <person>", or "correlate my calls with my texts". Read-only and
  local-only: no calls are placed, no data is written back, no analysis is performed
  on its own — reads return structured JSON for the caller to reason about. Only
  works for Claude Code running locally on macOS with Full Disk Access granted (not
  from a cloud/remote session) — this is the Mac/iPhone Continuity call log, not a
  generic telephony API.
---

# icallhistory

Read-only access to the Mac's local call history via a bundled, stdlib-only Python
CLI. Opens `~/Library/Application Support/CallHistoryDB/CallHistory.storedata`
read-only, queries, closes, and prints one JSON object to stdout — no persistent
process, no writes, ever. This is a **separate database from iMessage** (`chat.db`);
see "Correlating with iMessage" below for how to use both together.

## Non-goals (read before using)

- **No placing calls.** There is no AppleScript/Automation equivalent here to the
  imessage skill's `send` — Apple doesn't expose a reliable way to originate a phone
  or FaceTime call by script, and a Mac can't place a cellular call at all without an
  iPhone relaying it. This skill is read-only, full stop.
- **No summarization or analysis.** Reads return data; deciding who to call back or
  what a pattern of calls means is the caller's job.
- **No writes to CallHistory.storedata.** Every command opens the database read-only.
- **No scheduling/daemon.** On-demand only; there is no background watcher, no
  polling for inbound calls.
- **No voicemail content.** CallHistory.storedata records call metadata only (who,
  when, how long, answered or not) — it has no voicemail audio or transcripts.

## Running commands

Invoke the bundled script with Bash, from this skill's own directory:

```bash
python3 <skill_dir>/scripts/icallhistory_cli.py <command> [args...]
```

Replace `<skill_dir>` with wherever this skill is installed (the directory
containing this SKILL.md). Every command prints a single JSON object to stdout —
parse it and use the data; don't try to eyeball raw output as the final answer.

### First time in a session: run `doctor`

```bash
python3 <skill_dir>/scripts/icallhistory_cli.py doctor
```

Reports whether `CallHistory.storedata` and the AddressBook are readable, the total
call count, the local date range, and how many of those calls were real cellular
phone calls (as opposed to FaceTime). If `call_history_db_readable` is false, tell
the user to grant **Full Disk Access** to the terminal/app running Claude Code
(System Settings -> Privacy & Security -> Full Disk Access), then try again. If
`warnings` flags zero phone calls or a shallow date range, see "Continuity Calling"
below before assuming the data doesn't exist — this is the single most common
surprise with this skill.

### Everyday commands

| Command | Purpose |
|---|---|
| `calls [--since DATE] [--until DATE] [--handle H] [--direction incoming\|outgoing] [--type phone\|facetime_video\|facetime_audio\|third_party_app] [--missed-only] [--limit N] [--offset N]` | List calls newest-first, with `contact_name` resolved via the local AddressBook. Defaults to all local history if `--since` is omitted. |
| `contacts [--query NAME] [--handle HANDLE]` | Resolve name -> handle or handle -> name via the local AddressBook (same lookup the imessage skill uses). |

`DATE` accepts ISO 8601 (`2026-06-30`, `2026-06-30T14:00:00`), `today`/`yesterday`,
or relative phrases like `7 days ago` — identical parsing to the imessage skill, so
the two compose cleanly when scoping both to the same window.

`--handle` accepts a phone number or an Apple ID email, in any of the formats the
AddressBook or CallHistory itself stores them in (loose digit-matching handles
punctuation differences like `(555) 123-4567` vs `+15551234567`).

Each call record (indented here for readability; actual stdout is compact
single-line JSON):

```json
{
  "date_iso": "2026-07-10T14:32:05-04:00",
  "direction": "outgoing",
  "answered": true,
  "missed": false,
  "duration_seconds": 184,
  "call_type": "phone",
  "handle": "+15551234567",
  "contact_name": "Jane Doe",
  "service_provider": null
}
```

`missed` is `true` only for unanswered **incoming** calls (the same definition the
Phone/FaceTime apps' "Missed" list uses) — an unanswered outgoing call just has
`answered: false`, `direction: "outgoing"`.

## Correlating with iMessage

This skill and the `imessage` skill are independent (no shared code, installable
separately), but both resolve contacts from the same local AddressBook and use the
same `--handle` matching convention — so to answer "everything with Jane, calls and
texts together," call both and merge on `handle`/`sender_handle`:

```
icallhistory calls --handle "+15551234567" --since "30 days ago"
imessage     search --handle "+15551234567" --since "30 days ago"
```

Merge the two JSON results yourself (sort by `date_iso`); neither skill reaches into
the other's database. If you only have a name, resolve it once with either skill's
`contacts --query NAME` (they hit the same AddressBook, so results match) to get the
canonical handle to pass to both.

## Continuity Calling — read this before concluding "no calls found"

`CallHistory.storedata` only has **real cellular phone calls** if this Mac has
Continuity Calling ("Calls From iPhone") turned on — FaceTime -> Settings/Preferences
-> Calls From iPhone, Mac and iPhone on the same Apple ID and Wi-Fi network. Without
it, this database only has FaceTime Audio/Video calls placed from the Mac itself:
`doctor`'s `phone_call_count` will be `0` and it'll warn. Even when on, it's not an
iCloud-backed continuous sync like iMessage — calls only relay while both devices
were actually near each other on the same network — so treat results as useful but
possibly incomplete, not an authoritative log of every call the phone made. See
[references/platform-issues.md](references/platform-issues.md) for detail.

## Known limitations

- `service_provider` is surfaced as a raw passthrough string — Apple doesn't publicly
  document its exact contents (carrier name vs. an `"iPhone"` literal for a
  Continuity-relayed call vs. a third-party app identifier all appear to be possible),
  so don't over-interpret it.
- Unrecognized `ZCALLTYPE` values (e.g. from newer macOS releases) surface as
  `other_<code>` rather than a guessed label — `--type` can only filter on the four
  known names (`phone`, `facetime_video`, `facetime_audio`, `third_party_app`).
- Group FaceTime calls aren't specifically handled or tested in this phase — this
  skill targets 1:1 call records.
- Contact resolution reflects the AddressBook **right now**; a call from a number
  since removed from Contacts resolves to a raw number, same graceful-degradation
  behavior as the imessage skill.

See [references/schema.md](references/schema.md) for the `ZCALLRECORD` table layout
and the Core Data timestamp conversion, and
[references/platform-issues.md](references/platform-issues.md) for TCC permissions
and the Continuity Calling caveat in full.
