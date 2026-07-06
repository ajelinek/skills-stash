#!/usr/bin/env python3
"""Read-only query tool for the local iMessage database (~/Library/Messages/chat.db).

Every subcommand opens the database read-only, queries, closes, and prints one JSON
object to stdout. No writes, no network calls, no persistent process. Sending is out
of scope — hand `resolve-chat`'s chat_guid to the existing imessage plugin's `reply` tool.

See ../references/ for the chat.db schema, the attributedBody decode approach, and
known platform caveats (macOS 14+ NULL text column, iCloud multi-device sync, TCC
permissions) this module works around.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

APPLE_EPOCH_OFFSET = 978307200  # 2001-01-01 00:00:00 UTC, in Unix epoch seconds


# --------------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------------

def chat_db_path() -> str:
    return os.environ.get("IMESSAGE_DB_PATH") or str(Path.home() / "Library/Messages/chat.db")


def address_book_sources_dir() -> str:
    return os.environ.get("IMESSAGE_ADDRESSBOOK_DIR") or str(
        Path.home() / "Library/Application Support/AddressBook/Sources"
    )


# --------------------------------------------------------------------------------
# Date handling
# --------------------------------------------------------------------------------

_RELATIVE_RE = re.compile(
    r"^\s*(\d+)\s*(second|minute|hour|day|week|month|year)s?\s+ago\s*$", re.IGNORECASE
)
_UNIT_SECONDS = {
    "second": 1,
    "minute": 60,
    "hour": 3600,
    "day": 86400,
    "week": 86400 * 7,
    "month": 86400 * 30,
    "year": 86400 * 365,
}


def parse_when(value: str) -> datetime:
    """Parse a CLI date argument. Accepts ISO 8601 ('2026-06-30', '2026-06-30T14:00:00'),
    the shorthands 'today'/'now'/'yesterday', or relative phrases like '7 days ago'."""
    text = value.strip()
    low = text.lower()

    if low == "now":
        return datetime.now().astimezone()
    if low == "today":
        return datetime.now().astimezone().replace(hour=0, minute=0, second=0, microsecond=0)
    if low == "yesterday":
        return (datetime.now().astimezone() - timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

    m = _RELATIVE_RE.match(text)
    if m:
        n, unit = int(m.group(1)), m.group(2).lower()
        return datetime.now().astimezone() - timedelta(seconds=n * _UNIT_SECONDS[unit])

    iso = text
    if iso.endswith("Z"):
        iso = iso[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(iso)
    except ValueError as exc:
        raise ValueError(
            f"Could not parse date {value!r}. Use ISO 8601 (2026-06-30), "
            f"'today'/'yesterday', or 'N days ago'."
        ) from exc
    if dt.tzinfo is None:
        dt = dt.astimezone()
    return dt


def _is_bare_day(value: str) -> bool:
    """True for date args that name a whole calendar day rather than an instant:
    'today', 'yesterday', or a bare ISO date with no time component."""
    low = value.strip().lower()
    if low in ("today", "yesterday"):
        return True
    return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value.strip()))


def until_boundary(value: str) -> datetime:
    """Parse an --until argument, extending whole-day values to the end of that day
    so `--until 2026-06-30` includes all of June 30th instead of stopping at its
    midnight (parse_when's normal return for a bare day)."""
    dt = parse_when(value)
    if _is_bare_day(value):
        dt = dt.replace(hour=23, minute=59, second=59, microsecond=999999)
    return dt


def apple_ns_to_dt(ns: Optional[int]) -> Optional[datetime]:
    if not ns:
        return None
    return datetime.fromtimestamp(ns / 1_000_000_000 + APPLE_EPOCH_OFFSET).astimezone()


def dt_to_apple_ns(dt: datetime) -> int:
    return int((dt.timestamp() - APPLE_EPOCH_OFFSET) * 1_000_000_000)


def iso(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat(timespec="seconds") if dt else None


# --------------------------------------------------------------------------------
# attributedBody (NSArchiver typedstream) decoding
#
# macOS 14+ sometimes leaves message.text NULL and stores the text only inside the
# attributedBody blob, an NSKeyedArchiver/NSArchiver-encoded NSAttributedString.
# Two independent open-source implementations were compared byte-for-byte against
# five real reference blobs (see references/attributed-body.md for the writeup and
# tests/test_imessage_cli.py for the reproducible test). The marker-scan approach
# below (locate the `0x01 0x2B` type marker, or fall back to scanning past a literal
# "NSString" class reference) decoded all five fixtures correctly, including a message
# with legitimate trailing whitespace that a competing implementation's `.trim()`
# call corrupted. Ported and adapted from that algorithm; this is a best-effort
# heuristic parser for the common single-string case, not a full typedstream reader.
# --------------------------------------------------------------------------------

def _read_length(blob: bytes, offset: int) -> tuple[int, int]:
    """Return (length, offset_of_data) for the variable-length size prefix at offset."""
    if offset >= len(blob):
        return -1, offset
    first = blob[offset]
    if first < 0x80:
        return first, offset + 1
    if first == 0x81:
        if offset + 3 > len(blob):
            return -1, offset
        return int.from_bytes(blob[offset + 1 : offset + 3], "little"), offset + 3
    if first == 0x82:
        if offset + 5 > len(blob):
            return -1, offset
        return int.from_bytes(blob[offset + 1 : offset + 5], "little"), offset + 5
    return -1, offset


def _find_text_marker(blob: bytes) -> int:
    # Primary: the 0x01 0x2B byte pair that precedes the length-prefixed string data.
    for i in range(len(blob) - 1):
        if blob[i] == 0x01 and blob[i + 1] == 0x2B:
            return i + 1

    # Fallback: scan forward from a literal "NSString" class reference for a
    # plausible length-prefixed run of printable text.
    idx = blob.find(b"NSString")
    if idx >= 0:
        for i in range(idx + 8, min(idx + 50, len(blob) - 1)):
            length, data_offset = _read_length(blob, i)
            if 0 < length < 100_000 and data_offset + length <= len(blob):
                candidate = blob[data_offset : data_offset + length]
                try:
                    decoded = candidate.decode("utf-8")
                except UnicodeDecodeError:
                    continue
                # Any printable Unicode character counts here, not just ASCII —
                # a candidate.isprintable() check (rather than a \x20-\x7e byte-range
                # check) so messages written entirely in non-Latin scripts (Chinese,
                # Japanese, Korean, Cyrillic, Arabic, ...) still pass this heuristic.
                if any(ch.isprintable() for ch in decoded) and not re.search(r"[\x00-\x08]", decoded):
                    return i - 1
    return -1


def extract_text_from_attributed_body(blob: Optional[bytes]) -> Optional[str]:
    """Best-effort extraction of plain text from an attributedBody NSArchiver blob.
    Returns None if the blob is missing, malformed, or doesn't match the expected
    shape — callers should fall back to the `text` column in that case."""
    if not blob or len(blob) < 20:
        return None
    if blob[0] != 0x04 or blob[1] != 0x0B:  # typedstream magic
        return None

    marker = _find_text_marker(blob)
    if marker < 0:
        return None

    length_offset = marker + 1
    if length_offset >= len(blob):
        return None

    length, data_offset = _read_length(blob, length_offset)
    if length <= 0 or data_offset + length > len(blob):
        return None

    try:
        text = blob[data_offset : data_offset + length].decode("utf-8")
    except UnicodeDecodeError:
        return None
    return text or None


def resolve_message_text(text: Optional[str], attributed_body: Optional[bytes]) -> Optional[str]:
    if text:
        return text
    if attributed_body:
        return extract_text_from_attributed_body(attributed_body)
    return None


# --------------------------------------------------------------------------------
# Database access
# --------------------------------------------------------------------------------

class DbUnavailable(Exception):
    pass


def open_db(path: Optional[str] = None) -> sqlite3.Connection:
    db_path = path or chat_db_path()
    if not os.path.exists(db_path):
        raise DbUnavailable(f"chat.db not found at {db_path}.")
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        conn.execute("SELECT 1 FROM message LIMIT 1")
        return conn
    except sqlite3.OperationalError as exc:
        raise DbUnavailable(
            f"Cannot read {db_path}: {exc}. Grant Full Disk Access to the terminal/app "
            f"running this script (System Settings -> Privacy & Security -> Full Disk Access)."
        ) from exc


# Reactions (tapbacks) and edit/unsend placeholders show up as their own "message" rows
# with associated_message_type != 0. They aren't real conversation content, so read
# commands exclude them by default (--include-reactions opts back in). Lesson learned
# from comparing reference implementations: without this filter, `recent`/`search`
# results get polluted with synthetic strings like 'Reacted ❤️ to "..."'.
REACTION_FILTER_SQL = "m.associated_message_type = 0"

MESSAGE_COLUMNS = """
    m.ROWID as rowid, m.guid, m.text, m.attributedBody, m.handle_id, m.is_from_me,
    m.date, m.cache_has_attachments, m.associated_message_type
"""


def _row_message_dict(
    conn: sqlite3.Connection,
    row: sqlite3.Row,
    chat_guid: str,
    handle_names: dict[str, Optional[str]],
    attachments_by_message: dict[int, list[str]],
) -> dict[str, Any]:
    handle = None
    if not row["is_from_me"] and row["handle_id"]:
        handle = _handle_id_to_address(conn, row["handle_id"])

    text = resolve_message_text(row["text"], row["attributedBody"])
    sender_name = "Me" if row["is_from_me"] else (resolve_handle_to_name(handle_names, handle) or handle)

    rowid = row["rowid"]
    attachment_paths = attachments_by_message.get(rowid, [])

    return {
        "message_guid": row["guid"],
        "chat_guid": chat_guid,
        "date_iso": iso(apple_ns_to_dt(row["date"])),
        "sender_handle": handle,
        "sender_name": sender_name,
        "is_from_me": bool(row["is_from_me"]),
        "text": text,
        "has_attachment": bool(row["cache_has_attachments"]),
        "attachment_paths": attachment_paths,
    }


_handle_cache: dict[int, Optional[str]] = {}


def _handle_id_to_address(conn: sqlite3.Connection, handle_id: int) -> Optional[str]:
    if handle_id in _handle_cache:
        return _handle_cache[handle_id]
    row = conn.execute("SELECT id FROM handle WHERE ROWID = ?", (handle_id,)).fetchone()
    value = row["id"] if row else None
    _handle_cache[handle_id] = value
    return value


def _attachments_for_messages(conn: sqlite3.Connection, message_rowids: list[int]) -> dict[int, list[str]]:
    if not message_rowids:
        return {}
    placeholders = ",".join("?" for _ in message_rowids)
    rows = conn.execute(
        f"""
        SELECT maj.message_id as message_id, a.filename as filename
        FROM message_attachment_join maj
        JOIN attachment a ON a.ROWID = maj.attachment_id
        WHERE maj.message_id IN ({placeholders})
        """,
        message_rowids,
    ).fetchall()
    out: dict[int, list[str]] = {}
    for row in rows:
        if row["filename"]:
            out.setdefault(row["message_id"], []).append(os.path.expanduser(row["filename"]))
    return out


def _chat_participants(conn: sqlite3.Connection, chat_rowid: int, names: dict[str, Optional[str]]) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT h.id as id
        FROM handle h
        JOIN chat_handle_join chj ON chj.handle_id = h.ROWID
        WHERE chj.chat_id = ?
        ORDER BY h.id
        """,
        (chat_rowid,),
    ).fetchall()
    return [{"handle": r["id"], "name": resolve_handle_to_name(names, r["id"]) or r["id"]} for r in rows]


def _chat_stats(conn: sqlite3.Connection, chat_rowid: int) -> tuple[Optional[int], int]:
    row = conn.execute(
        f"""
        SELECT MAX(m.date) as last_date, COUNT(*) as c
        FROM message m
        JOIN chat_message_join cmj ON cmj.message_id = m.ROWID
        WHERE cmj.chat_id = ? AND {REACTION_FILTER_SQL}
        """,
        (chat_rowid,),
    ).fetchone()
    return row["last_date"], row["c"]


def _chat_dict(conn: sqlite3.Connection, row: sqlite3.Row, names: dict[str, Optional[str]]) -> dict[str, Any]:
    # Callers that already computed last_message_date/message_count (cmd_chats, which
    # needs them anyway to filter/sort) pass them through the row to avoid a second
    # query per chat; callers whose SELECT didn't project them (resolve-chat) get
    # them computed here on demand.
    row_keys = row.keys()
    if "last_message_date" in row_keys and "message_count" in row_keys:
        last_message_date, message_count = row["last_message_date"], row["message_count"]
    else:
        last_message_date, message_count = _chat_stats(conn, row["rowid"])
    return {
        "chat_guid": row["guid"],
        "display_name": row["display_name"] or None,
        "participants": _chat_participants(conn, row["rowid"], names),
        "last_message_date": iso(apple_ns_to_dt(last_message_date)),
        "message_count": message_count,
    }


# --------------------------------------------------------------------------------
# AddressBook (contacts) resolution
# --------------------------------------------------------------------------------

def _address_book_dbs() -> list[str]:
    sources_dir = address_book_sources_dir()
    if not os.path.isdir(sources_dir):
        return []
    found = []
    for entry in sorted(os.listdir(sources_dir)):
        candidate = os.path.join(sources_dir, entry, "AddressBook-v22.abcddb")
        if os.path.exists(candidate):
            found.append(candidate)
    return found


def _normalize_digits(value: str) -> str:
    return re.sub(r"\D", "", value)


def load_address_book() -> dict[str, str]:
    """Map normalized handle (last-10-digits phone, or lowercase email) -> full name."""
    cache: dict[str, str] = {}
    for db_path in _address_book_dbs():
        try:
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row
        except sqlite3.OperationalError:
            continue
        try:
            for row in conn.execute(
                """
                SELECT r.ZFIRSTNAME as first, r.ZLASTNAME as last, p.ZFULLNUMBER as number
                FROM ZABCDRECORD r
                JOIN ZABCDPHONENUMBER p ON r.Z_PK = p.ZOWNER
                WHERE p.ZFULLNUMBER IS NOT NULL
                """
            ):
                name = " ".join(x for x in (row["first"], row["last"]) if x).strip()
                if not name or not row["number"]:
                    continue
                digits = _normalize_digits(row["number"])
                if len(digits) >= 10:
                    cache[digits[-10:]] = name
                if row["number"].startswith("+"):
                    cache[row["number"]] = name

            for row in conn.execute(
                """
                SELECT r.ZFIRSTNAME as first, r.ZLASTNAME as last, e.ZADDRESS as address
                FROM ZABCDRECORD r
                JOIN ZABCDEMAILADDRESS e ON r.Z_PK = e.ZOWNER
                WHERE e.ZADDRESS IS NOT NULL
                """
            ):
                name = " ".join(x for x in (row["first"], row["last"]) if x).strip()
                if not name or not row["address"]:
                    continue
                cache[row["address"].lower()] = name
        except sqlite3.OperationalError:
            pass
        finally:
            conn.close()
    return cache


def resolve_handle_to_name(address_book: dict[str, str], handle: Optional[str]) -> Optional[str]:
    if not handle:
        return None
    lower = handle.lower()
    if lower in address_book:
        return address_book[lower]
    if handle in address_book:
        return address_book[handle]
    digits = _normalize_digits(handle)
    if len(digits) >= 10 and digits[-10:] in address_book:
        return address_book[digits[-10:]]
    return None


def find_handles_by_name(address_book: dict[str, str], query: str) -> list[str]:
    # load_address_book() indexes each phone number under two keys: a canonical
    # "+"-prefixed form and a bare last-10-digits form (a fuzzy-match aid for handles
    # that don't carry the "+"). Both map to the same contact, so a name search must
    # only surface the canonical form (or the email) — otherwise one contact with a
    # phone number shows up twice.
    q = query.lower()
    return [
        key for key, name in address_book.items()
        if q in name.lower() and (key.startswith("+") or "@" in key)
    ]


# --------------------------------------------------------------------------------
# Commands
# --------------------------------------------------------------------------------

def cmd_doctor(args: argparse.Namespace) -> dict[str, Any]:
    db_path = chat_db_path()
    result: dict[str, Any] = {
        "chat_db_path": db_path,
        "chat_db_exists": os.path.exists(db_path),
        "chat_db_readable": False,
        "message_count": None,
        "earliest_message_date": None,
        "latest_message_date": None,
        "address_book_dir": address_book_sources_dir(),
        "address_book_found": False,
        "contact_count": 0,
        "warnings": [],
        "errors": [],
        "ok": False,
    }

    try:
        conn = open_db(db_path)
        result["chat_db_readable"] = True
        row = conn.execute("SELECT COUNT(*) as c, MIN(date) as min_d, MAX(date) as max_d FROM message").fetchone()
        result["message_count"] = row["c"]
        earliest = apple_ns_to_dt(row["min_d"])
        latest = apple_ns_to_dt(row["max_d"])
        result["earliest_message_date"] = iso(earliest)
        result["latest_message_date"] = iso(latest)
        conn.close()

        if earliest is not None:
            shallow_threshold_days = 90
            history_days = (datetime.now().astimezone() - earliest).days
            if history_days < shallow_threshold_days:
                result["warnings"].append(
                    f"Local history only spans {history_days} day(s). If you expected more, "
                    f"this Mac may not have 'Messages in iCloud' enabled/fully synced — chat.db "
                    f"only contains what synced to this device. Initial iCloud sync of a large "
                    f"history can take 1-2 days."
                )
        if result["message_count"] == 0:
            result["warnings"].append("chat.db is readable but contains zero messages.")
    except DbUnavailable as exc:
        result["errors"].append(str(exc))

    sources = _address_book_dbs()
    result["address_book_found"] = bool(sources)
    if sources:
        try:
            book = load_address_book()
            result["contact_count"] = len(set(book.values()))
            if not book:
                result["warnings"].append("AddressBook database(s) found but no contacts resolved from them.")
        except Exception as exc:  # pragma: no cover - defensive
            result["errors"].append(f"Failed to read AddressBook: {exc}")
    else:
        result["warnings"].append(
            "No AddressBook database found — contact names won't resolve, only raw handles. "
            "This is optional; grant Contacts/Full Disk Access if you want name resolution."
        )

    result["ok"] = result["chat_db_readable"] and result["message_count"] not in (None, 0)
    return result


def cmd_chats(args: argparse.Namespace) -> dict[str, Any]:
    conn = open_db()
    address_book = load_address_book()

    where = ["message_count > 0"]
    params: list[Any] = []
    if args.since:
        where.append("last_message_date >= ?")
        params.append(dt_to_apple_ns(parse_when(args.since)))
    where_sql = " AND ".join(where)

    # Wrapped in an outer SELECT so the WHERE clause can filter on the computed
    # last_message_date/message_count aliases (SQLite won't resolve SELECT-list
    # aliases in a WHERE clause at the same query level).
    query = f"""
        SELECT * FROM (
            SELECT
              c.ROWID as rowid, c.guid as guid, c.display_name as display_name,
              (SELECT MAX(m.date) FROM message m
                 JOIN chat_message_join cmj ON cmj.message_id = m.ROWID
                 WHERE cmj.chat_id = c.ROWID AND {REACTION_FILTER_SQL}) as last_message_date,
              (SELECT COUNT(*) FROM message m
                 JOIN chat_message_join cmj ON cmj.message_id = m.ROWID
                 WHERE cmj.chat_id = c.ROWID AND {REACTION_FILTER_SQL}) as message_count
            FROM chat c
        ) t
        WHERE {where_sql}
    """
    filtered = conn.execute(query, params).fetchall()

    chats = [_chat_dict(conn, r, address_book) for r in filtered]

    if args.contact:
        q = args.contact.lower()
        chats = [
            c for c in chats
            if (c["display_name"] and q in c["display_name"].lower())
            or any(q in (p["name"] or "").lower() or q in p["handle"].lower() for p in c["participants"])
        ]

    chats.sort(key=lambda c: c["last_message_date"] or "", reverse=True)
    chats = chats[: args.limit]
    conn.close()
    return {"chats": chats, "count": len(chats)}


def _messages_for_chat(
    conn: sqlite3.Connection,
    chat_row: sqlite3.Row,
    address_book: dict[str, str],
    since: Optional[datetime],
    until: Optional[datetime],
    limit: int,
    offset: int,
    include_reactions: bool,
) -> tuple[list[dict[str, Any]], int]:
    where = ["cmj.chat_id = ?"]
    params: list[Any] = [chat_row["rowid"]]
    if not include_reactions:
        where.append(REACTION_FILTER_SQL)
    if since:
        where.append("m.date >= ?")
        params.append(dt_to_apple_ns(since))
    if until:
        where.append("m.date <= ?")
        params.append(dt_to_apple_ns(until))
    where_sql = " AND ".join(where)

    total = conn.execute(
        f"SELECT COUNT(*) as c FROM message m JOIN chat_message_join cmj ON cmj.message_id = m.ROWID WHERE {where_sql}",
        params,
    ).fetchone()["c"]

    rows = conn.execute(
        f"""
        SELECT {MESSAGE_COLUMNS}
        FROM message m
        JOIN chat_message_join cmj ON cmj.message_id = m.ROWID
        WHERE {where_sql}
        ORDER BY m.date ASC
        LIMIT ? OFFSET ?
        """,
        [*params, limit, offset],
    ).fetchall()

    attachments = _attachments_for_messages(conn, [r["rowid"] for r in rows])
    messages = [_row_message_dict(conn, r, chat_row["guid"], address_book, attachments) for r in rows]
    return messages, total


def cmd_messages(args: argparse.Namespace) -> dict[str, Any]:
    conn = open_db()
    address_book = load_address_book()

    chat_row = conn.execute(
        "SELECT ROWID as rowid, guid, display_name FROM chat WHERE guid = ?", (args.chat_guid,)
    ).fetchone()
    if not chat_row:
        conn.close()
        return {"error": f"No chat found with guid {args.chat_guid!r}", "messages": [], "count": 0}

    since = parse_when(args.since) if args.since else None
    until = until_boundary(args.until) if args.until else None
    messages, total = _messages_for_chat(
        conn, chat_row, address_book, since, until, args.limit, args.offset, args.include_reactions
    )
    conn.close()
    return {
        "chat_guid": args.chat_guid,
        "messages": messages,
        "count": len(messages),
        "total_matching": total,
        "has_more": args.offset + len(messages) < total,
    }


def cmd_recent(args: argparse.Namespace) -> dict[str, Any]:
    conn = open_db()
    address_book = load_address_book()

    since = parse_when(args.since) if args.since else parse_when("7 days ago")
    until = until_boundary(args.until) if args.until else None

    where = [REACTION_FILTER_SQL if not args.include_reactions else "1=1", "m.date >= ?"]
    params: list[Any] = [dt_to_apple_ns(since)]
    if until:
        where.append("m.date <= ?")
        params.append(dt_to_apple_ns(until))
    where_sql = " AND ".join(where)

    # ORDER BY ... DESC + LIMIT so that when a window has more matches than
    # `limit`, we keep the most recent ones (what "recent" promises) rather than
    # the oldest; messages are put back into chronological order per-chat below.
    rows = conn.execute(
        f"""
        SELECT {MESSAGE_COLUMNS}, cmj.chat_id as chat_id
        FROM message m
        JOIN chat_message_join cmj ON cmj.message_id = m.ROWID
        WHERE {where_sql}
        ORDER BY m.date DESC
        LIMIT ?
        """,
        [*params, args.limit],
    ).fetchall()

    chat_rowids = sorted({r["chat_id"] for r in rows})
    chat_rows = {}
    if chat_rowids:
        placeholders = ",".join("?" for _ in chat_rowids)
        for r in conn.execute(f"SELECT ROWID as rowid, guid, display_name FROM chat WHERE ROWID IN ({placeholders})", chat_rowids):
            chat_rows[r["rowid"]] = r

    attachments = _attachments_for_messages(conn, [r["rowid"] for r in rows])

    grouped: dict[int, dict[str, Any]] = {}
    for r in rows:
        chat_row = chat_rows.get(r["chat_id"])
        if not chat_row:
            continue
        bucket = grouped.get(r["chat_id"])
        if bucket is None:
            # Only query participants once per chat (not once per message) —
            # dict.setdefault() would evaluate its default argument, and therefore
            # this query, on every row regardless of whether the key exists yet.
            bucket = {
                "chat_guid": chat_row["guid"],
                "display_name": chat_row["display_name"] or None,
                "participants": _chat_participants(conn, r["chat_id"], address_book),
                "messages": [],
            }
            grouped[r["chat_id"]] = bucket
        bucket["messages"].append(_row_message_dict(conn, r, chat_row["guid"], address_book, attachments))

    # rows came back newest-first (see the ORDER BY above); flip each chat's
    # messages back to chronological order for readability.
    for bucket in grouped.values():
        bucket["messages"].reverse()

    chats = sorted(grouped.values(), key=lambda c: c["messages"][-1]["date_iso"] if c["messages"] else "", reverse=True)
    conn.close()
    return {
        "since": iso(since),
        "until": iso(until),
        "chats": chats,
        "chat_count": len(chats),
        "message_count": len(rows),
    }


def cmd_search(args: argparse.Namespace) -> dict[str, Any]:
    conn = open_db()
    address_book = load_address_book()

    base_where = [REACTION_FILTER_SQL if not args.include_reactions else "1=1"]
    params: list[Any] = []
    if args.handle:
        base_where.append("h.id = ?")
        params.append(args.handle)
    if args.since:
        base_where.append("m.date >= ?")
        params.append(dt_to_apple_ns(parse_when(args.since)))
    if args.until:
        base_where.append("m.date <= ?")
        params.append(dt_to_apple_ns(until_boundary(args.until)))
    base_where_sql = " AND ".join(base_where)

    # SQL LIKE only reaches the `text` column. A pure-SQL search would silently
    # miss messages whose text lives only in attributedBody (see references/ —
    # this is the exact macOS 14+ gap the reference implementations warned about).
    # So: LIKE-match the indexed text column directly, and separately pull the
    # (smaller) set of text-NULL/attributedBody-present rows in the same scope to
    # decode and substring-match in Python, then merge the two result sets.
    like_query = "%" + args.query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"

    text_rows = conn.execute(
        f"""
        SELECT {MESSAGE_COLUMNS}, cmj.chat_id as chat_id
        FROM message m
        JOIN chat_message_join cmj ON cmj.message_id = m.ROWID
        LEFT JOIN handle h ON h.ROWID = m.handle_id
        WHERE {base_where_sql} AND m.text LIKE ? ESCAPE '\\'
        ORDER BY m.date DESC
        LIMIT ?
        """,
        [*params, like_query, args.limit],
    ).fetchall()

    # Bounded (unlike text_rows' plain LIMIT, this scans+decodes every candidate
    # row before the final merge/truncation below) so a full-history search on a
    # very large chat.db can't blow past this command's perf budget; a narrower
    # --since/--until is still the fast path on huge local histories.
    blob_rows = conn.execute(
        f"""
        SELECT {MESSAGE_COLUMNS}, cmj.chat_id as chat_id
        FROM message m
        JOIN chat_message_join cmj ON cmj.message_id = m.ROWID
        LEFT JOIN handle h ON h.ROWID = m.handle_id
        WHERE {base_where_sql} AND m.text IS NULL AND m.attributedBody IS NOT NULL
        ORDER BY m.date DESC
        LIMIT ?
        """,
        [*params, max(args.limit * 25, 2000)],
    ).fetchall()

    query_lower = args.query.lower()
    matched_blob_rows = []
    for r in blob_rows:
        decoded = extract_text_from_attributed_body(r["attributedBody"])
        if decoded and query_lower in decoded.lower():
            matched_blob_rows.append(r)

    combined = {r["rowid"]: r for r in (*text_rows, *matched_blob_rows)}
    rows = sorted(combined.values(), key=lambda r: r["date"], reverse=True)[: args.limit]

    chat_rowids = sorted({r["chat_id"] for r in rows})
    chat_guids: dict[int, str] = {}
    if chat_rowids:
        placeholders = ",".join("?" for _ in chat_rowids)
        for r in conn.execute(f"SELECT ROWID as rowid, guid FROM chat WHERE ROWID IN ({placeholders})", chat_rowids):
            chat_guids[r["rowid"]] = r["guid"]

    attachments = _attachments_for_messages(conn, [r["rowid"] for r in rows])
    results = [
        _row_message_dict(conn, r, chat_guids.get(r["chat_id"], ""), address_book, attachments) for r in rows
    ]
    conn.close()
    return {"query": args.query, "handle": args.handle, "results": results, "count": len(results)}


def cmd_contacts(args: argparse.Namespace) -> dict[str, Any]:
    address_book = load_address_book()
    if args.handle:
        name = resolve_handle_to_name(address_book, args.handle)
        return {"contacts": [{"handle": args.handle, "name": name}], "count": 1 if name else 0}
    if args.query:
        keys = find_handles_by_name(address_book, args.query)
        contacts = [{"handle": k, "name": address_book[k]} for k in keys]
        return {"contacts": contacts, "count": len(contacts)}
    contacts = [{"handle": k, "name": v} for k, v in sorted(address_book.items(), key=lambda kv: kv[1])]
    return {"contacts": contacts, "count": len(contacts)}


def cmd_resolve_chat(args: argparse.Namespace) -> dict[str, Any]:
    conn = open_db()
    address_book = load_address_book()

    handles_to_try: list[str] = []
    query = args.handle.strip()

    # Already looks like a chat guid or a handle address.
    if query.startswith(("iMessage;", "SMS;", "+")) or "@" in query:
        handles_to_try = [query]
    else:
        handles_to_try = find_handles_by_name(address_book, query)
        # find_handles_by_name returns normalized keys (last-10-digits or lowercase
        # email); recover a dialable form for the handle table lookup below.
        handles_to_try = handles_to_try or [query]

    candidates: list[dict[str, Any]] = []
    seen_guids: set[str] = set()
    group_only = False

    for h in handles_to_try:
        if h.startswith(("iMessage;", "SMS;")):
            rows = conn.execute("SELECT ROWID as rowid, guid, display_name FROM chat WHERE guid = ?", (h,)).fetchall()
            for r in rows:
                if r["guid"] in seen_guids:
                    continue
                seen_guids.add(r["guid"])
                candidates.append(_chat_dict(conn, r, address_book))
            continue

        digits = _normalize_digits(h)
        # A handle/name query identifies one person; restrict candidates to 1:1 DMs
        # (chat_size == 1) since "reply to this person" should resolve to their
        # direct chat, not a group they also happen to be in. Rows where the
        # handle only turns up in group chats are counted (group_only) rather
        # than silently discarded, so the caller can tell "not found" apart from
        # "found, but only in groups" instead of getting an empty result either way.
        rows = conn.execute(
            """
            SELECT c.ROWID as rowid, c.guid as guid, c.display_name as display_name,
              (SELECT COUNT(*) FROM chat_handle_join chj2 WHERE chj2.chat_id = c.ROWID) as chat_size
            FROM chat c
            JOIN chat_handle_join chj ON chj.chat_id = c.ROWID
            JOIN handle ha ON ha.ROWID = chj.handle_id
            WHERE (ha.id = ? OR (length(?) >= 10 AND replace(replace(replace(ha.id,'-',''),' ',''),'(','') LIKE '%' || ?))
            """,
            (h, digits, digits[-10:] if len(digits) >= 10 else h),
        ).fetchall()
        for r in rows:
            if r["chat_size"] != 1:
                group_only = True
                continue
            if r["guid"] in seen_guids:
                continue
            seen_guids.add(r["guid"])
            candidates.append(_chat_dict(conn, r, address_book))

    conn.close()
    result: dict[str, Any] = {"query": args.handle, "candidates": candidates, "count": len(candidates)}
    if len(candidates) == 1:
        result["chat_guid"] = candidates[0]["chat_guid"]
    elif not candidates and group_only:
        result["note"] = (
            "This handle/name only matches group chats, not a 1:1 DM. "
            "Use `chats --contact <name>` to find the group instead."
        )
    return result


# --------------------------------------------------------------------------------
# CLI wiring
# --------------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="imessage_cli.py", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("doctor", help="Preflight check: DB/AddressBook access, message count, date range.")
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("chats", help="List conversations.")
    p.add_argument("--since")
    p.add_argument("--contact")
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(func=cmd_chats)

    p = sub.add_parser("messages", help="Paginated messages for one known chat.")
    p.add_argument("--chat-guid", required=True)
    p.add_argument("--since")
    p.add_argument("--until")
    p.add_argument("--limit", type=int, default=100)
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--include-reactions", action="store_true")
    p.set_defaults(func=cmd_messages)

    p = sub.add_parser("recent", help="All messages across all chats in a date range, grouped by chat.")
    p.add_argument("--since", help="Default: '7 days ago'.")
    p.add_argument("--until")
    p.add_argument("--limit", type=int, default=500)
    p.add_argument("--include-reactions", action="store_true")
    p.set_defaults(func=cmd_recent)

    p = sub.add_parser("search", help="Full-text search, optionally scoped by handle and/or date range.")
    p.add_argument("--query", required=True)
    p.add_argument("--handle")
    p.add_argument("--since")
    p.add_argument("--until")
    p.add_argument("--limit", type=int, default=100)
    p.add_argument("--include-reactions", action="store_true")
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("contacts", help="Resolve name<->handle via AddressBook.")
    p.add_argument("--query")
    p.add_argument("--handle")
    p.set_defaults(func=cmd_contacts)

    p = sub.add_parser("resolve-chat", help="Resolve a handle or contact name to a chat_guid for the send plugin.")
    p.add_argument("--handle", required=True)
    p.set_defaults(func=cmd_resolve_chat)

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        output = args.func(args)
    except DbUnavailable as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stdout)
        return 1
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stdout)
        return 1
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
