---
name: imessage-read
description: >
  Query local iMessage history by date range, contact, or search term, and resolve
  contacts to chat IDs — read-only, no sending. Trigger on requests like "what did
  <person> say", "show my recent texts", "find the message where...", "who have I
  been talking to", or "get the chat_guid for <person>" so a reply can be sent.
  Does not summarize, analyze, or interpret message content — it returns structured
  JSON for the caller to reason about. Does not send messages: hand the chat_guid
  this skill resolves to the existing `imessage:reply` tool for that.
---

# iMessage Read

Read-only access to `~/Library/Messages/chat.db` via a bundled, stdlib-only Python
CLI. Every invocation opens the database read-only, queries, closes, and prints one
JSON object to stdout — there is no persistent process and no write path anywhere in
this skill.

## Non-goals (read before using)

- **No summarization or analysis.** This skill returns data; interpreting it
  ("what needs a reply", "summarize this week") is the caller's job.
- **No sending.** This skill's job ends at resolving a `chat_guid`. Sending goes
  through the already-configured `imessage:reply` tool (from the Anthropic
  `imessage` plugin) — never attempt to send through this skill's own script.
- **No scheduling/daemon.** On-demand only; there is no background watcher.

## Running commands

Invoke the bundled script with Bash, from this skill's own directory:

```bash
python3 <skill_dir>/scripts/imessage_cli.py <command> [args...]
```

Replace `<skill_dir>` with wherever this skill is installed (the directory
containing this SKILL.md). Every command prints a single JSON object to stdout —
parse it and use the data; don't try to eyeball raw output as the final answer.

### First time in a session: run `doctor`

```bash
python3 <skill_dir>/scripts/imessage_cli.py doctor
```

Reports whether `chat.db` and the AddressBook are readable, the total message count,
and the local date range. If `chat_db_readable` is false, tell the user to grant
**Full Disk Access** to the terminal/app running Claude Code (System Settings ->
Privacy & Security -> Full Disk Access), then try again. If `warnings` mentions a
shallow history window, this Mac's local history may be incomplete — see
[references/platform-issues.md](references/platform-issues.md) for the iCloud sync
explanation before assuming the data doesn't exist.

### Everyday commands

| Command | Purpose |
|---|---|
| `chats [--since DATE] [--contact QUERY] [--limit N]` | List conversations: guid, display name/participants, last activity, message count. |
| `recent [--since DATE] [--until DATE] [--limit N] [--include-reactions]` | **Start here for "what have people been saying" requests.** All messages across all chats in a date range, grouped by chat — no contact lookup needed first. Defaults to the last 7 days if `--since` is omitted. |
| `messages --chat-guid GUID [--since DATE] [--until DATE] [--limit N] [--offset N] [--include-reactions]` | Paginated messages for one already-known chat. |
| `search --query TEXT [--handle HANDLE] [--since DATE] [--until DATE] [--limit N] [--include-reactions]` | Full-text search, optionally scoped to a handle and/or date range. Finds matches in both the plain `text` column and macOS 14+'s `attributedBody`-only messages (see below) — don't roll your own SQL against this DB, it'll miss the latter. |
| `contacts [--query NAME] [--handle HANDLE]` | Resolve name -> handle or handle -> name via the local AddressBook. |
| `resolve-chat --handle HANDLE_OR_NAME` | Resolve a phone/email/contact-name to the `chat_guid` needed for `imessage:reply`. Resolves to the 1:1 DM specifically; for a group, use `chats --contact` instead. |

`DATE` accepts ISO 8601 (`2026-06-30`, `2026-06-30T14:00:00`), `today`/`yesterday`,
or relative phrases like `7 days ago`.

### Handing off to send

```
[this skill: recent / search / resolve-chat] --> chat_guid + message data (JSON)
        v
[you, in conversation: decide what needs a reply, draft the text]
        v
[imessage:reply tool, fully-qualified name] --> sends
```

Call `resolve-chat --handle <phone, email, or contact name>` to get the `chat_guid`,
then call the plugin's `imessage:reply` tool directly with that guid and the drafted
text. Never write to `chat.db` or shell out to `osascript`/AppleScript from this
skill — that's the existing plugin's job and it's already wired up.

## Reactions are filtered by default

Tapbacks (love/like/laugh/etc.) and unsend/edit system messages show up in `chat.db`
as their own message rows with readable-looking text (e.g. `Reacted ❤️ to
"..."`). All read commands exclude these by default since they aren't real
conversation content; pass `--include-reactions` to see them anyway.

## Known limitations

- `sender_name`/`sender_handle` are `None`/`"Me"` for your own messages — this skill
  doesn't attempt self-handle detection (the existing send plugin already handles
  self-chat specially).
- Edited/unsent messages aren't specially flagged in this phase; you'll see whatever
  is currently in `text`/`attributedBody` for that row.
- `search` without `--since`/`--until` scans the full local history's
  attributedBody-only messages to decode and match them (SQL can't text-match inside
  a binary blob). This is normally fast (tens of milliseconds even over tens of
  thousands of messages — see `tests/test_imessage_cli.py`), but a narrower date range
  is always cheaper on very large histories.

See [references/schema.md](references/schema.md) for the `chat.db` table layout,
[references/attributed-body.md](references/attributed-body.md) for how the
macOS 14+ NULL-text decode works and why, and
[references/platform-issues.md](references/platform-issues.md) for TCC permissions
and the iCloud multi-device sync caveat.
