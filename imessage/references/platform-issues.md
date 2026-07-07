# Known platform issues

## Full Disk Access (TCC)

`chat.db` is protected by macOS's TCC (Transparency, Consent, and Control) system.
The terminal/app actually running Claude Code (Terminal.app, iTerm, a code editor's
integrated terminal, etc.) needs **Full Disk Access**:

System Settings -> Privacy & Security -> Full Disk Access -> add that app -> restart
the app.

Without it, `sqlite3.connect(..., uri=True)` in read-only mode raises
`sqlite3.OperationalError` (typically `unable to open database file` or
`authorization denied`). `imessage_cli.py`'s `open_db()` catches this and raises
`DbUnavailable` with a message pointing at the fix; `doctor` surfaces it as
`chat_db_readable: false`.

## AddressBook access

Contact name resolution reads
`~/Library/Application Support/AddressBook/Sources/*/AddressBook-v22.abcddb` — also
a plain SQLite file, also covered by Full Disk Access. If it's unreadable or
missing, this skill degrades gracefully: handles are shown as raw phone
numbers/emails instead of names, and `doctor` reports `address_book_found: false`
as a warning, not a failure — name resolution is a nice-to-have, not a hard
requirement to use this skill.

## Automation permission (TCC) for sending

`send` never touches `chat.db` — it shells out to `osascript`, which tells
Messages.app to deliver the text via AppleScript's `tell application "Messages" to
send`. macOS gates this separately from Full Disk Access: the first `send` call in a
session (or after an OS update) triggers an **Automation** permission prompt for
whatever app is running the script ("Terminal wants to control Messages.app" or
similar). If the user dismissed or never saw that prompt, `osascript` exits nonzero
and `send_via_applescript()` raises `SendFailed` with the fix pointer:

System Settings -> Privacy & Security -> Automation -> find the terminal/app running
Claude Code -> enable Messages.

A denied/missing grant here does not affect `doctor` or any read command — Full Disk
Access and Automation are independent TCC checks.

## iCloud multi-device sync

`chat.db` only contains what has synced to **this** Mac. If "Messages in iCloud" is
off (or a different Mac was primary), a Mac that's new to your account, or one where
Messages.app hasn't been open continuously, may only have a partial — or very
shallow — local history. It does **not** inherit another Mac's full history just by
being signed into the same Apple ID; it accumulates going forward from whenever
Messages.app was running on this device.

`doctor` heuristically flags this: if the earliest message in `chat.db` is less
than 90 days old, it emits a warning suggesting the user check whether "Messages in
iCloud" is enabled and fully synced (initial sync of a large history can reportedly
take 1-2 days). This is a heuristic, not a certainty — a genuinely new iMessage
user would also trip it harmlessly.

To fix: enable "Messages in iCloud" on all devices signed into the account
(Messages -> Settings -> iMessage on Mac; Settings -> [name] -> iCloud ->
"Messages in iCloud" on iPhone), and give it time to finish an initial sync before
re-running `doctor`.

## Why phase 1 has no daemon/scheduler

Deliberately out of scope for the initial build (see the PRD's Phase 2 section).
Everything in this skill is on-demand: open, query, close, print JSON, exit. A
future scheduled job (launchd/cron) calling `recent --since <watermark>` on an
interval is a natural next step, but the watermark should live in whatever calling
system consumes this skill's output, not be invented here.
