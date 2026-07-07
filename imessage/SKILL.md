---
name: imessage
description: >
  Query local iMessage history by date range, contact, or search term, resolve
  contacts to chat IDs, and send new iMessages. Trigger on requests like "what did
  <person> say", "show my recent texts", "find the message where...", "who have I
  been talking to", "text <person> ...", "reply to <person> saying ...", or "send a
  message to <chat>". Does not summarize, analyze, or interpret message content on
  its own — reads return structured JSON for the caller to reason about. Sending is
  a real, irreversible action: always show the user the exact drafted text and the
  resolved recipient and get explicit confirmation before calling `send`, unless the
  user already dictated the exact wording and recipient themselves.
---

# iMessage

Read and send access to iMessage via a bundled, stdlib-only Python CLI. Reads open
`~/Library/Messages/chat.db` read-only, query, close, and print one JSON object to
stdout — no persistent process, no writes to chat.db, ever. `send` never touches
chat.db either: it hands text and a `chat_guid` to `osascript`, which tells
Messages.app to deliver it via AppleScript — the same mechanism (and one of the two
permission grants) the previous separate `imessage:reply` plugin used, now folded
into this one skill so contact/chat resolution and delivery share the same code path.

## Non-goals (read before using)

- **No summarization or analysis.** Reads return data; interpreting it ("what needs
  a reply", "summarize this week") is the caller's job.
- **No unconfirmed sends.** `send` delivers immediately and there is no undo, no
  edit, no unsend from this skill. Draft the text, show the user exactly what will
  be sent and to whom, and get explicit confirmation first — unless the user's own
  message already specified the exact text and recipient, in which case that
  instruction is the confirmation.
- **No scheduling/daemon.** On-demand only; there is no background watcher, no
  polling for inbound messages.
- **No tapbacks, edits, thread replies, or attachments.** AppleScript's `send`
  command only does plain text to a chat; anything past that is out of scope.

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
explanation before assuming the data doesn't exist. `doctor` only checks read access;
see "Sending" below for the separate permission grant `send` needs.

### Everyday commands

| Command | Purpose |
|---|---|
| `chats [--since DATE] [--contact QUERY] [--limit N]` | List conversations: guid, display name/participants, last activity, message count. |
| `recent [--since DATE] [--until DATE] [--limit N] [--include-reactions]` | **Start here for "what have people been saying" requests.** All messages across all chats in a date range, grouped by chat — no contact lookup needed first. Defaults to the last 7 days if `--since` is omitted. |
| `messages --chat-guid GUID [--since DATE] [--until DATE] [--limit N] [--offset N] [--include-reactions]` | Paginated messages for one already-known chat. |
| `search --query TEXT [--handle HANDLE] [--since DATE] [--until DATE] [--limit N] [--include-reactions]` | Full-text search, optionally scoped to a handle and/or date range. Finds matches in both the plain `text` column and macOS 14+'s `attributedBody`-only messages (see below) — don't roll your own SQL against this DB, it'll miss the latter. |
| `contacts [--query NAME] [--handle HANDLE]` | Resolve name -> handle or handle -> name via the local AddressBook. |
| `resolve-chat --handle HANDLE_OR_NAME` | Resolve a phone/email/contact-name to a `chat_guid`. Resolves to the 1:1 DM specifically. Only present when `count == 1` — see "Sending" below for what to do otherwise. |
| `send (--chat-guid GUID \| --handle HANDLE_OR_NAME) --text TEXT` | Send a plain-text message via Messages.app. See "Sending" below. |

`DATE` accepts ISO 8601 (`2026-06-30`, `2026-06-30T14:00:00`), `today`/`yesterday`,
or relative phrases like `7 days ago`.

## Sending

```
[recent / search / resolve-chat] --> chat_guid + message data (JSON)
        v
[you, in conversation: decide what needs a reply, draft the exact text,
 show it + the recipient to the user, get explicit confirmation]
        v
[send --chat-guid ... --text "..."] --> delivered via Messages.app
```

`send` takes either `--chat-guid` (exact, e.g. from `resolve-chat` or `chats`) or
`--handle` (a phone/email/contact name, resolved the same way `resolve-chat` does).
`--handle` only sends when it resolves to **exactly one** chat; on 0 or >1 matches it
raises an error instead of guessing — call `resolve-chat --handle <query>` to see
`candidates` (a group-only match sets a `note` pointing you at `chats --contact`
instead) or ask the user to disambiguate, then retry `send` with an exact
`--chat-guid`.

Every message caps at 10,000 characters (`send` raises rather than silently
splitting long text — split it into multiple calls yourself if needed). The first
`send` in a session triggers a separate macOS **Automation** permission prompt
("... wants to control Messages") distinct from the Full Disk Access `doctor`
checks — if `send` fails, check System Settings -> Privacy & Security ->
Automation. This skill never writes to `chat.db`; sending only ever goes through
`osascript` talking to Messages.app.

## Reactions are filtered by default

Tapbacks (love/like/laugh/etc.) and unsend/edit system messages show up in `chat.db`
as their own message rows with readable-looking text (e.g. `Reacted ❤️ to
"..."`). `messages`, `recent`, and `search` exclude these by default since they
aren't real conversation content; pass `--include-reactions` to see them anyway.
`chats` has no `--include-reactions` flag — its `message_count` always excludes
reactions, since there's nothing scoped to a single chat request to toggle.

## Known limitations

- `sender_handle`/`sender_name` are `None`/`"Me"` for your own messages — this skill
  doesn't attempt self-handle detection.
- Edited/unsent messages aren't specially flagged in this phase; you'll see whatever
  is currently in `text`/`attributedBody` for that row.
- `search` without `--since`/`--until` scans the full local history's
  attributedBody-only messages to decode and match them (SQL can't text-match inside
  a binary blob). This is normally fast (tens of milliseconds even over tens of
  thousands of messages — see `tests/test_imessage_cli.py`), but a narrower date range
  is always cheaper on very large histories.
- `send` cannot tapback, edit, unsend, or thread-reply — AppleScript's `send` command
  only delivers plain text to a chat.
- `send` cannot attach files; text only.

See [references/schema.md](references/schema.md) for the `chat.db` table layout,
[references/attributed-body.md](references/attributed-body.md) for how the
macOS 14+ NULL-text decode works and why, and
[references/platform-issues.md](references/platform-issues.md) for TCC permissions,
the Automation permission `send` needs, and the iCloud multi-device sync caveat.
