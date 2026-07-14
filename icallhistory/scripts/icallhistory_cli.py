#!/usr/bin/env python3
"""Query local Mac/iPhone call history (~/Library/Application Support/CallHistoryDB/
CallHistory.storedata) — cellular phone calls, FaceTime Audio, and FaceTime Video.

Read-only, stdlib-only: open the database read-only, query, close, print one JSON
object to stdout. No writes to CallHistory.storedata, no network calls, no daemon —
same shape as the imessage skill's imessage_cli.py, applied to a different local
database. This skill cannot place calls; see SKILL.md's Non-goals for why.

See ../references/ for the ZCALLRECORD schema and known platform caveats (TCC
permissions, and the Continuity Calling requirement for real cellular calls to
appear here at all) this module works around.
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

def call_history_db_path() -> str:
    return os.environ.get("ICALLHISTORY_DB_PATH") or str(
        Path.home() / "Library/Application Support/CallHistoryDB/CallHistory.storedata"
    )


def address_book_sources_dir() -> str:
    return os.environ.get("ICALLHISTORY_ADDRESSBOOK_DIR") or str(
        Path.home() / "Library/Application Support/AddressBook/Sources"
    )


# --------------------------------------------------------------------------------
# Date handling (identical semantics to the imessage skill's imessage_cli.py, so the
# two skills' --since/--until arguments behave the same way for a caller composing
# both. Duplicated rather than imported — every skill in this repo is self-contained.)
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


# --------------------------------------------------------------------------------
# Core Data timestamp conversion
#
# ZDATE is a Core Data / NSDate "reference date" value: seconds (a float) since
# 2001-01-01 00:00:00 UTC. This is NOT the same unit as chat.db's message.date,
# which the Messages app schema stores as *nanoseconds* since the same epoch —
# a well-documented iMessage-specific quirk that does not apply here. Verified
# against two independent, maintained forensics parsers (mac_apt and iLEAPP) that
# both read ZCALLRECORD in production: see references/schema.md for sources.
# --------------------------------------------------------------------------------

def core_data_ts_to_dt(seconds: Optional[float]) -> Optional[datetime]:
    if seconds is None:
        return None
    return datetime.fromtimestamp(seconds + APPLE_EPOCH_OFFSET).astimezone()


def dt_to_core_data_ts(dt: datetime) -> float:
    return dt.timestamp() - APPLE_EPOCH_OFFSET


def iso(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat(timespec="seconds") if dt else None


# --------------------------------------------------------------------------------
# Database access
# --------------------------------------------------------------------------------

class DbUnavailable(Exception):
    pass


def open_db(path: Optional[str] = None) -> sqlite3.Connection:
    db_path = path or call_history_db_path()
    if not os.path.exists(db_path):
        raise DbUnavailable(f"CallHistory.storedata not found at {db_path}.")
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        conn.execute("SELECT 1 FROM ZCALLRECORD LIMIT 1")
        return conn
    except sqlite3.OperationalError as exc:
        raise DbUnavailable(
            f"Cannot read {db_path}: {exc}. Grant Full Disk Access to the terminal/app "
            f"running this script (System Settings -> Privacy & Security -> Full Disk Access)."
        ) from exc


# ZCALLTYPE code -> name. 0/1/8/16 are the documented, widely-observed values (see
# references/schema.md); anything else surfaces as "other_<code>" rather than a
# guessed label — macOS 26's Continuity/Phone-app changes may introduce new codes
# this skill hasn't seen yet.
CALL_TYPE_NAMES = {0: "third_party_app", 1: "phone", 8: "facetime_video", 16: "facetime_audio"}
CALL_TYPE_CODES = {v: k for k, v in CALL_TYPE_NAMES.items()}


def _call_type_name(code: Optional[int]) -> str:
    if code is None:
        return "unknown"
    return CALL_TYPE_NAMES.get(code, f"other_{code}")


def _call_dict(row: sqlite3.Row, address_book: dict[str, str]) -> dict[str, Any]:
    address = row["address"]
    direction = "outgoing" if row["originated"] else "incoming"
    answered = bool(row["answered"])
    duration = row["duration"]
    return {
        "date_iso": iso(core_data_ts_to_dt(row["date"])),
        "direction": direction,
        "answered": answered,
        "missed": direction == "incoming" and not answered,
        "duration_seconds": int(round(duration)) if duration is not None else 0,
        "call_type": _call_type_name(row["call_type"]),
        "handle": address,
        "contact_name": resolve_handle_to_name(address_book, address),
        # Best-effort passthrough — Apple doesn't document this column's exact
        # contents (carrier name, "iPhone" literal for a Continuity-relayed call,
        # a third-party app identifier, ...) so it's surfaced raw, not interpreted.
        "service_provider": row["service_provider"],
    }


# --------------------------------------------------------------------------------
# AddressBook (contacts) resolution — same approach and same real on-disk database
# as the imessage skill's imessage_cli.py, duplicated rather than imported (every
# skill in this repo is self-contained; see build.sh, which zips each top-level
# skill directory independently for standalone install).
# --------------------------------------------------------------------------------

def _address_book_dbs() -> list[str]:
    sources_dir = address_book_sources_dir()
    if not os.path.isdir(sources_dir):
        return []
    try:
        entries = sorted(os.listdir(sources_dir))
    except PermissionError:
        # TCC can let isdir() see the directory while still denying listdir() on it
        # (observed on real macOS: Full Disk Access not yet granted). Treat like "no
        # sources" so callers fall back to raw handles instead of crashing outright.
        return []
    found = []
    for entry in entries:
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
                    # Normalize to bare "+<digits>" rather than keying on the raw string —
                    # AddressBook can store the same number with different punctuation
                    # across sources, but CallHistory's ZADDRESS is always the clean form.
                    cache["+" + digits] = name

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
    db_path = call_history_db_path()
    result: dict[str, Any] = {
        "call_history_db_path": db_path,
        "call_history_db_exists": os.path.exists(db_path),
        "call_history_db_readable": False,
        "call_count": None,
        "phone_call_count": 0,
        "earliest_call_date": None,
        "latest_call_date": None,
        "address_book_dir": address_book_sources_dir(),
        "address_book_found": False,
        "contact_count": 0,
        "warnings": [],
        "errors": [],
        "ok": False,
    }

    try:
        conn = open_db(db_path)
        result["call_history_db_readable"] = True
        row = conn.execute(
            "SELECT COUNT(*) as c, MIN(ZDATE) as min_d, MAX(ZDATE) as max_d FROM ZCALLRECORD"
        ).fetchone()
        result["call_count"] = row["c"]
        earliest = core_data_ts_to_dt(row["min_d"])
        latest = core_data_ts_to_dt(row["max_d"])
        result["earliest_call_date"] = iso(earliest)
        result["latest_call_date"] = iso(latest)

        phone_row = conn.execute(
            f"SELECT COUNT(*) as c FROM ZCALLRECORD WHERE ZCALLTYPE = {CALL_TYPE_CODES['phone']}"
        ).fetchone()
        result["phone_call_count"] = phone_row["c"]
        conn.close()

        if result["call_count"]:
            if result["phone_call_count"] == 0:
                result["warnings"].append(
                    "No cellular phone calls found here — only FaceTime/other call types, if any. "
                    "If you expected real phone calls to show up, turn on Continuity Calling: on this "
                    "Mac, FaceTime -> Settings -> 'Calls From iPhone', with both devices signed into the "
                    "same Apple ID and on the same Wi-Fi network. See references/platform-issues.md."
                )
            if earliest is not None:
                shallow_threshold_days = 90
                history_days = (datetime.now().astimezone() - earliest).days
                if history_days < shallow_threshold_days:
                    result["warnings"].append(
                        f"Local call history only spans {history_days} day(s). Continuity Calling syncs "
                        f"opportunistically — both devices need to have been near each other on the same "
                        f"network — so this Mac may not have your full history even with the feature on."
                    )
        else:
            result["warnings"].append("CallHistory.storedata is readable but contains zero call records.")
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
            "No AddressBook database found — contact names won't resolve, only raw numbers/emails. "
            "This is optional; grant Full Disk Access if you want name resolution."
        )

    result["ok"] = result["call_history_db_readable"] and result["call_count"] not in (None, 0)
    return result


def cmd_calls(args: argparse.Namespace) -> dict[str, Any]:
    conn = open_db()
    address_book = load_address_book()

    where: list[str] = []
    params: list[Any] = []

    since = parse_when(args.since) if args.since else None
    until = until_boundary(args.until) if args.until else None
    if since:
        where.append("ZDATE >= ?")
        params.append(dt_to_core_data_ts(since))
    if until:
        where.append("ZDATE <= ?")
        params.append(dt_to_core_data_ts(until))

    if args.handle:
        digits = _normalize_digits(args.handle)
        if len(digits) >= 10:
            where.append("(ZADDRESS = ? OR ZADDRESS LIKE ?)")
            params.extend([args.handle, "%" + digits[-10:]])
        else:
            where.append("ZADDRESS = ?")
            params.append(args.handle)

    if args.direction:
        where.append("ZORIGINATED = ?")
        params.append(1 if args.direction == "outgoing" else 0)

    if args.call_type:
        where.append("ZCALLTYPE = ?")
        params.append(CALL_TYPE_CODES[args.call_type])

    if args.missed_only:
        where.append("ZORIGINATED = 0 AND ZANSWERED = 0")

    where_sql = " AND ".join(where) if where else "1=1"

    total = conn.execute(f"SELECT COUNT(*) as c FROM ZCALLRECORD WHERE {where_sql}", params).fetchone()["c"]

    rows = conn.execute(
        f"""
        SELECT ZDATE as date, ZDURATION as duration, ZADDRESS as address,
               ZORIGINATED as originated, ZANSWERED as answered, ZCALLTYPE as call_type,
               ZSERVICE_PROVIDER as service_provider
        FROM ZCALLRECORD
        WHERE {where_sql}
        ORDER BY ZDATE DESC
        LIMIT ? OFFSET ?
        """,
        [*params, args.limit, args.offset],
    ).fetchall()

    calls = [_call_dict(r, address_book) for r in rows]
    conn.close()
    return {
        "since": iso(since),
        "until": iso(until),
        "calls": calls,
        "count": len(calls),
        "total_matching": total,
        "has_more": args.offset + len(calls) < total,
    }


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


# --------------------------------------------------------------------------------
# CLI wiring
# --------------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="icallhistory_cli.py", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("doctor", help="Preflight check: DB/AddressBook access, call count, date range.")
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("calls", help="List calls (phone + FaceTime), newest first, with contact names resolved.")
    p.add_argument("--since", help="Default: all local history.")
    p.add_argument("--until")
    p.add_argument("--handle", help="Filter to one phone number or Apple ID (email).")
    p.add_argument("--direction", choices=["incoming", "outgoing"])
    p.add_argument("--type", dest="call_type", choices=list(CALL_TYPE_CODES.keys()))
    p.add_argument("--missed-only", action="store_true", help="Incoming and not answered.")
    p.add_argument("--limit", type=int, default=100)
    p.add_argument("--offset", type=int, default=0)
    p.set_defaults(func=cmd_calls)

    p = sub.add_parser("contacts", help="Resolve name<->handle via AddressBook.")
    p.add_argument("--query")
    p.add_argument("--handle")
    p.set_defaults(func=cmd_contacts)

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
