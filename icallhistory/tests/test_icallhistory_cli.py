#!/usr/bin/env python3
"""Tests for icallhistory_cli.py against synthetic CallHistory.storedata / AddressBook
fixtures. No real macOS CallHistory.storedata is required (or assumed) — this builds
sqlite databases with the same schema icallhistory_cli.py queries, so the whole
pipeline is exercised without touching a real call history database.
"""
import importlib.util
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import datetime, timedelta
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "icallhistory_cli.py"

spec = importlib.util.spec_from_file_location("icallhistory_cli", SCRIPT_PATH)
icallhistory_cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(icallhistory_cli)

APPLE_EPOCH_OFFSET = icallhistory_cli.APPLE_EPOCH_OFFSET


def to_core_data_seconds(days_ago: float) -> float:
    unix_seconds = time.time() - days_ago * 86400
    return unix_seconds - APPLE_EPOCH_OFFSET


class ArgNamespace:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def argparse_ns(**kwargs):
    return ArgNamespace(**kwargs)


# --------------------------------------------------------------------------------
# Core Data timestamp conversion — the trickiest correctness risk here: ZDATE is
# seconds since 2001-01-01, NOT nanoseconds like chat.db's message.date. These tests
# exist specifically to catch a regression that accidentally applies chat.db's
# nanosecond scaling to this database's plain-seconds column.
# --------------------------------------------------------------------------------

class CoreDataTimestampTests(unittest.TestCase):
    def test_epoch_zero_is_the_2001_reference_date(self):
        expected = datetime.fromtimestamp(APPLE_EPOCH_OFFSET).astimezone()
        self.assertEqual(icallhistory_cli.core_data_ts_to_dt(0.0), expected)

    def test_none_returns_none(self):
        self.assertIsNone(icallhistory_cli.core_data_ts_to_dt(None))

    def test_round_trip_dt_to_seconds_and_back(self):
        original = datetime(2026, 7, 10, 14, 32, 5).astimezone()
        seconds = icallhistory_cli.dt_to_core_data_ts(original)
        self.assertEqual(icallhistory_cli.core_data_ts_to_dt(seconds), original)

    def test_seconds_not_nanoseconds_regression(self):
        # A record timestamped ~1 day ago, encoded the way this skill's own fixtures
        # (and presumably a real CallHistory.storedata) encode it: plain seconds
        # since the 2001 epoch. If ZDATE were ever mis-decoded using chat.db's
        # nanosecond scaling instead, this would come back decades off rather than
        # ~1 day off.
        seconds = to_core_data_seconds(1.0)
        decoded = icallhistory_cli.core_data_ts_to_dt(seconds)
        expected = datetime.now().astimezone() - timedelta(days=1)
        self.assertLess(abs((decoded - expected).total_seconds()), 5)


class DateBoundaryTests(unittest.TestCase):
    def test_bare_iso_date_and_named_days_are_bare_days(self):
        self.assertTrue(icallhistory_cli._is_bare_day("2026-06-30"))
        self.assertTrue(icallhistory_cli._is_bare_day("today"))
        self.assertTrue(icallhistory_cli._is_bare_day("yesterday"))
        self.assertFalse(icallhistory_cli._is_bare_day("2026-06-30T14:00:00"))
        self.assertFalse(icallhistory_cli._is_bare_day("7 days ago"))

    def test_until_boundary_extends_bare_date_to_end_of_day(self):
        dt = icallhistory_cli.until_boundary("2026-06-30")
        self.assertEqual((dt.hour, dt.minute, dt.second), (23, 59, 59))

    def test_until_boundary_leaves_explicit_timestamp_alone(self):
        dt = icallhistory_cli.until_boundary("2026-06-30T14:00:00")
        self.assertEqual((dt.hour, dt.minute, dt.second), (14, 0, 0))

    def test_today_is_floored_to_midnight_like_yesterday(self):
        dt = icallhistory_cli.parse_when("today")
        self.assertEqual((dt.hour, dt.minute, dt.second, dt.microsecond), (0, 0, 0, 0))


class CliFixtureTestCase(unittest.TestCase):
    """Builds a synthetic ZCALLRECORD + AddressBook DB and drives the CLI end-to-end."""

    JANE = "+15551234567"
    BOB = "+15559876543"
    UNKNOWN = "+19999999999"

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, "CallHistory.storedata")
        self.addressbook_dir = os.path.join(self.tmpdir, "AddressBook", "Sources")
        os.makedirs(os.path.join(self.addressbook_dir, "SOURCE1"), exist_ok=True)

        self._build_call_history_db()
        self._build_address_book()

        self._old_db_env = os.environ.get("ICALLHISTORY_DB_PATH")
        self._old_ab_env = os.environ.get("ICALLHISTORY_ADDRESSBOOK_DIR")
        os.environ["ICALLHISTORY_DB_PATH"] = self.db_path
        os.environ["ICALLHISTORY_ADDRESSBOOK_DIR"] = self.addressbook_dir

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        for var, old in (
            ("ICALLHISTORY_DB_PATH", self._old_db_env),
            ("ICALLHISTORY_ADDRESSBOOK_DIR", self._old_ab_env),
        ):
            if old is None:
                os.environ.pop(var, None)
            else:
                os.environ[var] = old

    def _build_call_history_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.executescript(
            """
            CREATE TABLE ZCALLRECORD (
                Z_PK INTEGER PRIMARY KEY,
                ZDATE REAL,
                ZDURATION REAL,
                ZADDRESS TEXT,
                ZORIGINATED INTEGER,
                ZANSWERED INTEGER,
                ZCALLTYPE INTEGER,
                ZSERVICE_PROVIDER TEXT
            );
            """
        )
        # pk, days_ago, duration, address, originated, answered, call_type, service_provider
        rows = [
            (1, 3.0, 184, self.JANE, 1, 1, 1, None),        # outgoing, answered, phone
            (2, 2.0, 0, self.JANE, 0, 0, 1, None),           # incoming, missed, phone
            (3, 1.0, 600, self.JANE, 0, 1, 8, None),         # incoming, answered, facetime_video
            (4, 5.0, 45, self.BOB, 1, 1, 16, None),          # outgoing, answered, facetime_audio
            (5, 40.0, 0, self.UNKNOWN, 0, 0, 1, "Verizon"),  # incoming, missed, phone (oldest -> shallow-history)
            (6, 0.5, 999, self.JANE, 1, 1, 0, "com.example.voip"),  # outgoing, answered, third_party_app (newest)
            (7, 6.0, 0, self.BOB, 1, 0, 1, None),            # outgoing, UNANSWERED, phone (not "missed")
        ]
        for pk, days_ago, duration, address, originated, answered, call_type, provider in rows:
            conn.execute(
                """INSERT INTO ZCALLRECORD
                   (Z_PK, ZDATE, ZDURATION, ZADDRESS, ZORIGINATED, ZANSWERED, ZCALLTYPE, ZSERVICE_PROVIDER)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (pk, to_core_data_seconds(days_ago), duration, address, originated, answered, call_type, provider),
            )
        conn.commit()
        conn.close()

    def _build_address_book(self):
        ab_path = os.path.join(self.addressbook_dir, "SOURCE1", "AddressBook-v22.abcddb")
        conn = sqlite3.connect(ab_path)
        conn.executescript(
            """
            CREATE TABLE ZABCDRECORD (Z_PK INTEGER PRIMARY KEY, ZFIRSTNAME TEXT, ZLASTNAME TEXT);
            CREATE TABLE ZABCDPHONENUMBER (ZOWNER INTEGER, ZFULLNUMBER TEXT);
            CREATE TABLE ZABCDEMAILADDRESS (ZOWNER INTEGER, ZADDRESS TEXT);
            """
        )
        conn.execute("INSERT INTO ZABCDRECORD (Z_PK, ZFIRSTNAME, ZLASTNAME) VALUES (1, 'Jane', 'Doe')")
        conn.execute(f"INSERT INTO ZABCDPHONENUMBER (ZOWNER, ZFULLNUMBER) VALUES (1, '{self.JANE}')")
        conn.execute("INSERT INTO ZABCDRECORD (Z_PK, ZFIRSTNAME, ZLASTNAME) VALUES (2, 'Bob', 'Smith')")
        conn.execute(f"INSERT INTO ZABCDPHONENUMBER (ZOWNER, ZFULLNUMBER) VALUES (2, '{self.BOB}')")
        conn.commit()
        conn.close()

    # ---- doctor ----

    def test_doctor_reports_access_and_counts(self):
        result = icallhistory_cli.cmd_doctor(argparse_ns())
        self.assertTrue(result["ok"])
        self.assertTrue(result["call_history_db_readable"])
        self.assertEqual(result["call_count"], 7)
        self.assertEqual(result["phone_call_count"], 4)  # rows 1, 2, 5, 7
        self.assertTrue(result["address_book_found"])
        self.assertEqual(result["contact_count"], 2)
        # Earliest record is 40 days ago, under the 90-day shallow-history threshold.
        self.assertTrue(any("history" in w.lower() for w in result["warnings"]))

    # ---- calls: listing, ordering, contact resolution ----

    def test_calls_lists_newest_first_with_contact_names(self):
        result = icallhistory_cli.cmd_calls(argparse_ns(
            since=None, until=None, handle=None, direction=None, call_type=None,
            missed_only=False, limit=100, offset=0,
        ))
        self.assertEqual(result["count"], 7)
        self.assertEqual(result["total_matching"], 7)
        self.assertFalse(result["has_more"])
        newest = result["calls"][0]
        self.assertEqual(newest["call_type"], "third_party_app")
        self.assertEqual(newest["contact_name"], "Jane Doe")
        oldest = result["calls"][-1]
        self.assertIsNone(oldest["contact_name"])  # unknown number, no AddressBook match

    def test_calls_since_filters_out_older_records(self):
        result = icallhistory_cli.cmd_calls(argparse_ns(
            since="4 days ago", until=None, handle=None, direction=None, call_type=None,
            missed_only=False, limit=100, offset=0,
        ))
        # Within the last 4 days: rows 1 (3d), 2 (2d), 3 (1d), 6 (0.5d) — all Jane.
        # Excluded: row 4 (Bob, 5d), row 5 (Unknown, 40d), row 7 (Bob, 6d).
        handles = [c["handle"] for c in result["calls"]]
        self.assertNotIn(self.UNKNOWN, handles)
        self.assertNotIn(self.BOB, handles)
        self.assertEqual(result["count"], 4)

    def test_calls_filters_by_handle_with_digit_normalization(self):
        # Same loose matching the imessage skill uses: a differently-punctuated
        # number should still match the canonical "+1..." form stored in ZADDRESS.
        # Jane has 4 rows in the fixture: 1, 2, 3, 6.
        result = icallhistory_cli.cmd_calls(argparse_ns(
            since=None, until=None, handle="(555) 123-4567", direction=None, call_type=None,
            missed_only=False, limit=100, offset=0,
        ))
        self.assertEqual(result["count"], 4)
        self.assertTrue(all(c["handle"] == self.JANE for c in result["calls"]))

    def test_calls_filters_by_direction(self):
        outgoing = icallhistory_cli.cmd_calls(argparse_ns(
            since=None, until=None, handle=None, direction="outgoing", call_type=None,
            missed_only=False, limit=100, offset=0,
        ))
        self.assertEqual(outgoing["count"], 4)  # rows 1, 4, 6, 7
        self.assertTrue(all(c["direction"] == "outgoing" for c in outgoing["calls"]))

        incoming = icallhistory_cli.cmd_calls(argparse_ns(
            since=None, until=None, handle=None, direction="incoming", call_type=None,
            missed_only=False, limit=100, offset=0,
        ))
        self.assertEqual(incoming["count"], 3)  # rows 2, 3, 5

    def test_missed_only_excludes_unanswered_outgoing(self):
        # Row 7 is outgoing + unanswered — that's a real thing ("they didn't pick
        # up"), but it is not a "missed call" in the Phone-app sense, which only
        # applies to incoming calls.
        result = icallhistory_cli.cmd_calls(argparse_ns(
            since=None, until=None, handle=None, direction=None, call_type=None,
            missed_only=True, limit=100, offset=0,
        ))
        self.assertEqual(result["count"], 2)  # rows 2, 5
        self.assertTrue(all(c["missed"] for c in result["calls"]))
        self.assertTrue(all(c["direction"] == "incoming" for c in result["calls"]))

    def test_unanswered_outgoing_call_has_missed_false(self):
        result = icallhistory_cli.cmd_calls(argparse_ns(
            since=None, until=None, handle=self.BOB, direction="outgoing", call_type=None,
            missed_only=False, limit=100, offset=0,
        ))
        unanswered = next(c for c in result["calls"] if not c["answered"])
        self.assertFalse(unanswered["missed"])

    def test_calls_filters_by_type(self):
        result = icallhistory_cli.cmd_calls(argparse_ns(
            since=None, until=None, handle=None, direction=None, call_type="facetime_video",
            missed_only=False, limit=100, offset=0,
        ))
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["calls"][0]["contact_name"], "Jane Doe")

    def test_calls_pagination(self):
        page1 = icallhistory_cli.cmd_calls(argparse_ns(
            since=None, until=None, handle=None, direction=None, call_type=None,
            missed_only=False, limit=2, offset=0,
        ))
        self.assertEqual(page1["count"], 2)
        self.assertEqual(page1["total_matching"], 7)
        self.assertTrue(page1["has_more"])

        last_page = icallhistory_cli.cmd_calls(argparse_ns(
            since=None, until=None, handle=None, direction=None, call_type=None,
            missed_only=False, limit=2, offset=6,
        ))
        self.assertEqual(last_page["count"], 1)
        self.assertFalse(last_page["has_more"])

    # ---- contacts ----

    def test_contacts_resolve_handle_to_name(self):
        result = icallhistory_cli.cmd_contacts(argparse_ns(query=None, handle=self.JANE))
        self.assertEqual(result["contacts"][0]["name"], "Jane Doe")

    def test_contacts_resolve_name_to_handle(self):
        result = icallhistory_cli.cmd_contacts(argparse_ns(query="Bob", handle=None))
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["contacts"][0]["handle"], "+" + icallhistory_cli._normalize_digits(self.BOB))


class DoctorContinuityWarningTests(unittest.TestCase):
    """A Mac without Continuity Calling ('Calls From iPhone') enabled only ever sees
    FaceTime calls placed directly from the Mac — doctor should call that out
    specifically, since it's easy to mistake for this skill not working at all."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, "CallHistory.storedata")
        conn = sqlite3.connect(self.db_path)
        conn.executescript(
            """
            CREATE TABLE ZCALLRECORD (
                Z_PK INTEGER PRIMARY KEY, ZDATE REAL, ZDURATION REAL, ZADDRESS TEXT,
                ZORIGINATED INTEGER, ZANSWERED INTEGER, ZCALLTYPE INTEGER, ZSERVICE_PROVIDER TEXT
            );
            """
        )
        conn.execute(
            "INSERT INTO ZCALLRECORD (Z_PK, ZDATE, ZDURATION, ZADDRESS, ZORIGINATED, ZANSWERED, ZCALLTYPE) "
            "VALUES (1, ?, 120, 'someone@icloud.com', 1, 1, 16)",
            (to_core_data_seconds(1.0),),
        )
        conn.commit()
        conn.close()

        self._old_db_env = os.environ.get("ICALLHISTORY_DB_PATH")
        self._old_ab_env = os.environ.get("ICALLHISTORY_ADDRESSBOOK_DIR")
        os.environ["ICALLHISTORY_DB_PATH"] = self.db_path
        os.environ["ICALLHISTORY_ADDRESSBOOK_DIR"] = os.path.join(self.tmpdir, "nonexistent")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        for var, old in (
            ("ICALLHISTORY_DB_PATH", self._old_db_env),
            ("ICALLHISTORY_ADDRESSBOOK_DIR", self._old_ab_env),
        ):
            if old is None:
                os.environ.pop(var, None)
            else:
                os.environ[var] = old

    def test_zero_phone_calls_triggers_continuity_warning(self):
        result = icallhistory_cli.cmd_doctor(argparse_ns())
        self.assertEqual(result["phone_call_count"], 0)
        self.assertTrue(any("calls from iphone" in w.lower() for w in result["warnings"]))


class CliSubprocessSmokeTest(unittest.TestCase):
    """End-to-end smoke test: invoke the script as a real subprocess and parse stdout,
    exactly how the skill instructs Claude to call it."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, "CallHistory.storedata")
        conn = sqlite3.connect(self.db_path)
        conn.executescript(
            """
            CREATE TABLE ZCALLRECORD (
                Z_PK INTEGER PRIMARY KEY, ZDATE REAL, ZDURATION REAL, ZADDRESS TEXT,
                ZORIGINATED INTEGER, ZANSWERED INTEGER, ZCALLTYPE INTEGER, ZSERVICE_PROVIDER TEXT
            );
            """
        )
        conn.execute(
            "INSERT INTO ZCALLRECORD (Z_PK, ZDATE, ZDURATION, ZADDRESS, ZORIGINATED, ZANSWERED, ZCALLTYPE) "
            "VALUES (1, ?, 60, '+15551234567', 1, 1, 1)",
            (to_core_data_seconds(0.1),),
        )
        conn.commit()
        conn.close()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_doctor_via_subprocess(self):
        env = dict(os.environ)
        env["ICALLHISTORY_DB_PATH"] = self.db_path
        env["ICALLHISTORY_ADDRESSBOOK_DIR"] = os.path.join(self.tmpdir, "nonexistent")
        proc = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "doctor"],
            capture_output=True, text=True, env=env, timeout=10,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["call_count"], 1)

    def test_calls_via_subprocess(self):
        env = dict(os.environ)
        env["ICALLHISTORY_DB_PATH"] = self.db_path
        env["ICALLHISTORY_ADDRESSBOOK_DIR"] = os.path.join(self.tmpdir, "nonexistent")
        proc = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "calls", "--since", "7 days ago"],
            capture_output=True, text=True, env=env, timeout=10,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["calls"][0]["call_type"], "phone")


class NoNetworkTest(unittest.TestCase):
    def test_script_has_no_network_calls(self):
        source = SCRIPT_PATH.read_text()
        for banned in ("requests", "socket", "urllib", "http.client", "httplib"):
            self.assertNotIn(banned, source, f"found banned network-related token: {banned}")


if __name__ == "__main__":
    unittest.main()
