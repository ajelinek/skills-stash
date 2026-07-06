#!/usr/bin/env python3
"""Tests for imessage_cli.py against synthetic chat.db / AddressBook fixtures.

No real macOS chat.db is required (or assumed) — this builds sqlite databases with
the same schema imessage_cli.py queries, so the whole pipeline is exercised without
touching a real Messages database. The attributedBody hex fixtures are copied
verbatim from a real, published reference implementation's test suite (see
../references/attributed-body.md) so the decoder is checked against known-good
real-world blobs, not just hand-crafted ones.
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
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "imessage_cli.py"

spec = importlib.util.spec_from_file_location("imessage_cli", SCRIPT_PATH)
imessage_cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(imessage_cli)

APPLE_EPOCH_OFFSET = imessage_cli.APPLE_EPOCH_OFFSET

# Real attributedBody blobs, byte-for-byte from a published reference implementation's
# test fixtures (daveremy/imessage-mcp, src/__tests__/fixtures/typedstream-blobs.ts).
SHORT_MESSAGE = bytes.fromhex(
    "040b73747265616d747970656481e803840140848484124e5341747472696275746564537472696e"
    "67008484084e534f626a656374008592848484084e53537472696e67019484012b0159868402694901"
    "01928484840c4e5344696374696f6e617279009484016901928496961d5f5f6b494d4d657373616765"
    "506172744174747269627574654e616d658692848484084e534e756d626572008484074e5356616c75"
    "65009484012a84999900868686"
)
SHORT_MESSAGE_TEXT = "Y"

MEDIUM_MESSAGE = bytes.fromhex(
    "040b73747265616d747970656481e803840140848484124e5341747472696275746564537472696e"
    "67008484084e534f626a656374008592848484084e53537472696e67019484012b194f6b2c206e70"
    "2c207468616e6b7320666f7220747279696e6786840269490119928484840c4e5344696374696f6e"
    "617279009484016901928496961d5f5f6b494d4d657373616765506172744174747269627574654e"
    "616d658692848484084e534e756d626572008484074e5356616c7565009484012a84999900868686"
)
MEDIUM_MESSAGE_TEXT = "Ok, np, thanks for trying"

LONG_MESSAGE = bytes.fromhex(
    "040b73747265616d747970656481e803840140848484194e534d757461626c65417474726962"
    "75746564537472696e67008484124e5341747472696275746564537472696e67008484084e53"
    "4f626a6563740085928484840f4e534d757461626c65537472696e67018484084e5353747269"
    "6e67019584012b8115014920616d206f6b2077697468206e6f7420686176696e672043686172"
    "6c69652073696e63652068652069736ee28099742070617274206f662074686520726567756c"
    "61722067726f75702e20205769746820352074686572652069736ee280997420656e6f756768"
    "2068697474696e672e2020492063616e20646f203520627574206974206265636f6d6573206d"
    "6f7265206f6620612063617264696f20776f726b6f757420726174686572207468616e206869"
    "7474696e672061206c6f74206f662062616c6c732e2020496620796f752077616e7420636172"
    "64696f20492063616e2072756e20746865206865636b206f7574206f6620796f752077697468"
    "20352e2020596f75722063616c6c204a656e2e2020868402694901811101928484840c4e5344"
    "696374696f6e617279009584016901928498981d5f5f6b494d4d657373616765506172744174"
    "747269627574654e616d658692848484084e534e756d626572008484074e5356616c75650095"
    "84012a849b9b00868686"
)
LONG_MESSAGE_TEXT = (
    "I am ok with not having Charlie since he isn’t part of the regular group.  "
    "With 5 there isn’t enough hitting.  I can do 5 but it becomes more of a cardio "
    "workout rather than hitting a lot of balls.  If you want cardio I can run the heck "
    "out of you with 5.  Your call Jen.  "
)

EMOJI_MESSAGE = bytes.fromhex(
    "040b73747265616d747970656481e803840140848484124e5341747472696275746564537472"
    "696e67008484084e534f626a656374008592848484084e53537472696e67019484012b205265"
    "616374656420f09f989220746f20e2809c4e6f2074726561747320e2809d8684026949011a92"
    "8484840c4e5344696374696f6e617279009484016901928496961d5f5f6b494d4d6573736167"
    "65506172744174747269627574654e616d658692848484084e534e756d626572008484074e53"
    "56616c7565009484012a84999900868686"
)
EMOJI_MESSAGE_TEXT = 'Reacted \U0001F612 to “No treats ”'

MALFORMED_BLOB = bytes.fromhex("deadbeefcafebabe")
TINY_BLOB = bytes.fromhex("040b")


def to_apple_ns(days_ago: float) -> int:
    unix_seconds = time.time() - days_ago * 86400
    return int((unix_seconds - APPLE_EPOCH_OFFSET) * 1_000_000_000)


class AttributedBodyDecodeTests(unittest.TestCase):
    """Acceptance criterion: 5 spot-checked attributedBody-only messages decode
    correctly. These particular blobs are real ones pulled from a published,
    tested reference implementation, not synthetic ones we invented ourselves."""

    def test_short(self):
        self.assertEqual(imessage_cli.extract_text_from_attributed_body(SHORT_MESSAGE), SHORT_MESSAGE_TEXT)

    def test_medium(self):
        self.assertEqual(imessage_cli.extract_text_from_attributed_body(MEDIUM_MESSAGE), MEDIUM_MESSAGE_TEXT)

    def test_emoji(self):
        self.assertEqual(imessage_cli.extract_text_from_attributed_body(EMOJI_MESSAGE), EMOJI_MESSAGE_TEXT)

    def test_long_message_uses_0x81_length_encoding(self):
        # 277 characters, so the length prefix must use the 3-byte 0x81 uint16
        # encoding tier rather than the single-byte tier the other fixtures exercise.
        self.assertEqual(imessage_cli.extract_text_from_attributed_body(LONG_MESSAGE), LONG_MESSAGE_TEXT)

    def test_malformed_blob_returns_none(self):
        self.assertIsNone(imessage_cli.extract_text_from_attributed_body(MALFORMED_BLOB))

    def test_tiny_blob_returns_none(self):
        self.assertIsNone(imessage_cli.extract_text_from_attributed_body(TINY_BLOB))

    def test_none_and_empty(self):
        self.assertIsNone(imessage_cli.extract_text_from_attributed_body(None))
        self.assertIsNone(imessage_cli.extract_text_from_attributed_body(b""))


class CliFixtureTestCase(unittest.TestCase):
    """Builds a synthetic chat.db + AddressBook DB and drives the CLI end-to-end."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, "chat.db")
        self.addressbook_dir = os.path.join(self.tmpdir, "AddressBook", "Sources")
        os.makedirs(os.path.join(self.addressbook_dir, "SOURCE1"), exist_ok=True)

        self._build_chat_db()
        self._build_address_book()

        self._old_db_env = os.environ.get("IMESSAGE_DB_PATH")
        self._old_ab_env = os.environ.get("IMESSAGE_ADDRESSBOOK_DIR")
        os.environ["IMESSAGE_DB_PATH"] = self.db_path
        os.environ["IMESSAGE_ADDRESSBOOK_DIR"] = self.addressbook_dir
        imessage_cli._handle_cache.clear()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        for var, old in (("IMESSAGE_DB_PATH", self._old_db_env), ("IMESSAGE_ADDRESSBOOK_DIR", self._old_ab_env)):
            if old is None:
                os.environ.pop(var, None)
            else:
                os.environ[var] = old

    def _build_chat_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.executescript(
            """
            CREATE TABLE message (
                ROWID INTEGER PRIMARY KEY, guid TEXT, text TEXT, attributedBody BLOB,
                handle_id INTEGER, is_from_me INTEGER, date INTEGER,
                cache_has_attachments INTEGER, associated_message_guid TEXT,
                associated_message_type INTEGER, service TEXT
            );
            CREATE TABLE chat (
                ROWID INTEGER PRIMARY KEY, guid TEXT, chat_identifier TEXT,
                display_name TEXT, style INTEGER, service_name TEXT
            );
            CREATE TABLE handle (ROWID INTEGER PRIMARY KEY, id TEXT, service TEXT);
            CREATE TABLE chat_message_join (chat_id INTEGER, message_id INTEGER);
            CREATE TABLE chat_handle_join (chat_id INTEGER, handle_id INTEGER);
            CREATE TABLE attachment (
                ROWID INTEGER PRIMARY KEY, filename TEXT, mime_type TEXT,
                total_bytes INTEGER, transfer_name TEXT
            );
            CREATE TABLE message_attachment_join (message_id INTEGER, attachment_id INTEGER);
            """
        )

        # Handles
        conn.execute("INSERT INTO handle (ROWID, id, service) VALUES (1, '+15551234567', 'iMessage')")
        conn.execute("INSERT INTO handle (ROWID, id, service) VALUES (2, '+15559876543', 'iMessage')")

        # Chats: 1 = DM with Jane, 2 = group with Jane + Bob
        conn.execute(
            "INSERT INTO chat (ROWID, guid, chat_identifier, display_name, style, service_name) "
            "VALUES (1, 'iMessage;-;+15551234567', '+15551234567', NULL, 45, 'iMessage')"
        )
        conn.execute(
            "INSERT INTO chat (ROWID, guid, chat_identifier, display_name, style, service_name) "
            "VALUES (2, 'iMessage;+;chat123456', 'chat123456', 'Weekend Crew', 43, 'iMessage')"
        )
        conn.execute("INSERT INTO chat_handle_join (chat_id, handle_id) VALUES (1, 1)")
        conn.execute("INSERT INTO chat_handle_join (chat_id, handle_id) VALUES (2, 1)")
        conn.execute("INSERT INTO chat_handle_join (chat_id, handle_id) VALUES (2, 2)")

        messages = [
            # rowid, guid, text, attributedBody, handle_id, is_from_me, days_ago, has_attachment, assoc_type
            (1, "m-1", "Hey are we still on for Saturday?", None, 1, 0, 3.0, 0, 0),
            (2, "m-2", "Yes! See you at 10", None, None, 1, 2.95, 0, 0),
            (3, "m-3", None, SHORT_MESSAGE, 1, 0, 2.0, 0, 0),
            (4, "m-4", None, MEDIUM_MESSAGE, 1, 0, 1.0, 0, 0),
            (5, "m-5", "who's driving Saturday", None, 2, 0, 5.0, 0, 0),
            (6, "m-6", None, EMOJI_MESSAGE, 2, 0, 4.99, 0, 2001),  # tapback reaction
            (7, "m-7", "Check this photo out", None, 1, 0, 0.5, 1, 0),
            (8, "m-8", "ancient history message", None, 1, 0, 40.0, 0, 0),
        ]
        chat_for_message = {1: 1, 2: 1, 3: 1, 4: 1, 5: 2, 6: 2, 7: 1, 8: 1}

        for rowid, guid, text, blob, handle_id, is_from_me, days_ago, has_att, assoc_type in messages:
            conn.execute(
                """INSERT INTO message
                   (ROWID, guid, text, attributedBody, handle_id, is_from_me, date,
                    cache_has_attachments, associated_message_guid, associated_message_type, service)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, 'iMessage')""",
                (rowid, guid, text, blob, handle_id, is_from_me, to_apple_ns(days_ago), has_att, assoc_type),
            )
            conn.execute(
                "INSERT INTO chat_message_join (chat_id, message_id) VALUES (?, ?)",
                (chat_for_message[rowid], rowid),
            )

        conn.execute("INSERT INTO attachment (ROWID, filename, mime_type, total_bytes, transfer_name) "
                     "VALUES (1, '/tmp/photo.jpg', 'image/jpeg', 12345, 'photo.jpg')")
        conn.execute("INSERT INTO message_attachment_join (message_id, attachment_id) VALUES (7, 1)")

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
        conn.execute("INSERT INTO ZABCDPHONENUMBER (ZOWNER, ZFULLNUMBER) VALUES (1, '+15551234567')")
        conn.execute("INSERT INTO ZABCDRECORD (Z_PK, ZFIRSTNAME, ZLASTNAME) VALUES (2, 'Bob', 'Smith')")
        conn.execute("INSERT INTO ZABCDPHONENUMBER (ZOWNER, ZFULLNUMBER) VALUES (2, '+15559876543')")
        conn.commit()
        conn.close()

    # ---- doctor ----

    def test_doctor_reports_access_and_counts(self):
        result = imessage_cli.cmd_doctor(argparse_ns())
        self.assertTrue(result["ok"])
        self.assertTrue(result["chat_db_readable"])
        self.assertEqual(result["message_count"], 8)
        self.assertTrue(result["address_book_found"])
        self.assertEqual(result["contact_count"], 2)
        # 40-day-old earliest message is older than the 90-day shallow-history threshold's
        # complement in this fixture (spans ~40 days), so we expect the shallow-history warning.
        self.assertTrue(any("history" in w.lower() for w in result["warnings"]))

    # ---- chats ----

    def test_chats_lists_conversations_with_names(self):
        result = imessage_cli.cmd_chats(argparse_ns(since=None, contact=None, limit=20))
        self.assertEqual(result["count"], 2)
        dm = next(c for c in result["chats"] if c["chat_guid"] == "iMessage;-;+15551234567")
        self.assertEqual(dm["participants"], [{"handle": "+15551234567", "name": "Jane Doe"}])

    def test_chats_filters_by_contact(self):
        result = imessage_cli.cmd_chats(argparse_ns(since=None, contact="Bob", limit=20))
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["chats"][0]["chat_guid"], "iMessage;+;chat123456")

    # ---- messages ----

    def test_messages_decodes_attributed_body_and_resolves_names(self):
        result = imessage_cli.cmd_messages(
            argparse_ns(chat_guid="iMessage;-;+15551234567", since=None, until=None,
                        limit=100, offset=0, include_reactions=False)
        )
        texts = [m["text"] for m in result["messages"]]
        self.assertIn(SHORT_MESSAGE_TEXT, texts)
        self.assertIn(MEDIUM_MESSAGE_TEXT, texts)
        by_text = {m["text"]: m for m in result["messages"]}
        jane_msg = by_text["Hey are we still on for Saturday?"]
        self.assertEqual(jane_msg["sender_name"], "Jane Doe")
        self.assertFalse(jane_msg["is_from_me"])
        me_msg = by_text["Yes! See you at 10"]
        self.assertTrue(me_msg["is_from_me"])
        self.assertEqual(me_msg["sender_name"], "Me")

    def test_messages_includes_attachment_paths(self):
        result = imessage_cli.cmd_messages(
            argparse_ns(chat_guid="iMessage;-;+15551234567", since=None, until=None,
                        limit=100, offset=0, include_reactions=False)
        )
        photo_msg = next(m for m in result["messages"] if m["text"] == "Check this photo out")
        self.assertTrue(photo_msg["has_attachment"])
        self.assertEqual(photo_msg["attachment_paths"], ["/tmp/photo.jpg"])

    def test_messages_unknown_chat_guid(self):
        result = imessage_cli.cmd_messages(
            argparse_ns(chat_guid="iMessage;-;+19999999999", since=None, until=None,
                        limit=100, offset=0, include_reactions=False)
        )
        self.assertIn("error", result)
        self.assertEqual(result["count"], 0)

    # ---- recent ----

    def test_recent_default_since_excludes_old_message_and_groups_by_chat(self):
        result = imessage_cli.cmd_recent(
            argparse_ns(since=None, until=None, limit=500, include_reactions=False)
        )
        all_texts = [m["text"] for c in result["chats"] for m in c["messages"]]
        self.assertNotIn("ancient history message", all_texts)  # 40 days ago, outside default 7-day window
        self.assertIn(SHORT_MESSAGE_TEXT, all_texts)
        self.assertEqual(result["chat_count"], 2)
        # Reactions excluded by default
        self.assertNotIn(EMOJI_MESSAGE_TEXT, all_texts)

    def test_recent_include_reactions(self):
        result = imessage_cli.cmd_recent(
            argparse_ns(since=None, until=None, limit=500, include_reactions=True)
        )
        all_texts = [m["text"] for c in result["chats"] for m in c["messages"]]
        self.assertIn(EMOJI_MESSAGE_TEXT, all_texts)

    def test_recent_explicit_since_includes_old_message(self):
        result = imessage_cli.cmd_recent(
            argparse_ns(since="90 days ago", until=None, limit=500, include_reactions=False)
        )
        all_texts = [m["text"] for c in result["chats"] for m in c["messages"]]
        self.assertIn("ancient history message", all_texts)

    # ---- search ----

    def test_search_finds_plain_text_column_match(self):
        result = imessage_cli.cmd_search(
            argparse_ns(query="Saturday", handle=None, since=None, until=None, limit=100, include_reactions=False)
        )
        self.assertGreaterEqual(result["count"], 2)

    def test_search_finds_attributed_body_only_match(self):
        # This is the crux acceptance case: MEDIUM_MESSAGE has NULL `text`, so a search
        # implementation that only does `WHERE text LIKE` would silently miss this.
        result = imessage_cli.cmd_search(
            argparse_ns(query="trying", handle=None, since=None, until=None, limit=100, include_reactions=False)
        )
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["results"][0]["text"], MEDIUM_MESSAGE_TEXT)

    def test_search_excludes_reactions_by_default(self):
        result = imessage_cli.cmd_search(
            argparse_ns(query="Reacted", handle=None, since=None, until=None, limit=100, include_reactions=False)
        )
        self.assertEqual(result["count"], 0)

    def test_search_scoped_by_handle(self):
        result = imessage_cli.cmd_search(
            argparse_ns(query="driving", handle="+15559876543", since=None, until=None, limit=100, include_reactions=False)
        )
        self.assertEqual(result["count"], 1)

    # ---- contacts ----

    def test_contacts_resolve_handle_to_name(self):
        result = imessage_cli.cmd_contacts(argparse_ns(query=None, handle="+15551234567"))
        self.assertEqual(result["contacts"][0]["name"], "Jane Doe")

    def test_contacts_resolve_name_to_handle(self):
        result = imessage_cli.cmd_contacts(argparse_ns(query="Jane", handle=None))
        self.assertEqual(result["count"], 1)

    # ---- resolve-chat ----

    def test_resolve_chat_by_handle(self):
        result = imessage_cli.cmd_resolve_chat(argparse_ns(handle="+15551234567"))
        self.assertEqual(result["chat_guid"], "iMessage;-;+15551234567")

    def test_resolve_chat_by_name(self):
        result = imessage_cli.cmd_resolve_chat(argparse_ns(handle="Jane"))
        self.assertIn("iMessage;-;+15551234567", [c["chat_guid"] for c in result["candidates"]])


class ArgNamespace:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def argparse_ns(**kwargs):
    return ArgNamespace(**kwargs)


class CliSubprocessSmokeTest(unittest.TestCase):
    """End-to-end smoke test: invoke the script as a real subprocess and parse stdout,
    exactly how the skill instructs Claude to call it."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, "chat.db")
        conn = sqlite3.connect(self.db_path)
        conn.executescript(
            """
            CREATE TABLE message (ROWID INTEGER PRIMARY KEY, guid TEXT, text TEXT,
                attributedBody BLOB, handle_id INTEGER, is_from_me INTEGER, date INTEGER,
                cache_has_attachments INTEGER, associated_message_guid TEXT,
                associated_message_type INTEGER, service TEXT);
            CREATE TABLE chat (ROWID INTEGER PRIMARY KEY, guid TEXT, chat_identifier TEXT,
                display_name TEXT, style INTEGER, service_name TEXT);
            CREATE TABLE handle (ROWID INTEGER PRIMARY KEY, id TEXT, service TEXT);
            CREATE TABLE chat_message_join (chat_id INTEGER, message_id INTEGER);
            CREATE TABLE chat_handle_join (chat_id INTEGER, handle_id INTEGER);
            CREATE TABLE attachment (ROWID INTEGER PRIMARY KEY, filename TEXT, mime_type TEXT,
                total_bytes INTEGER, transfer_name TEXT);
            CREATE TABLE message_attachment_join (message_id INTEGER, attachment_id INTEGER);
            """
        )
        conn.execute("INSERT INTO handle (ROWID, id, service) VALUES (1, '+15551234567', 'iMessage')")
        conn.execute("INSERT INTO chat (ROWID, guid, chat_identifier, display_name, style, service_name) "
                     "VALUES (1, 'iMessage;-;+15551234567', '+15551234567', NULL, 45, 'iMessage')")
        conn.execute("INSERT INTO chat_handle_join (chat_id, handle_id) VALUES (1, 1)")
        conn.execute("INSERT INTO message (ROWID, guid, text, handle_id, is_from_me, date, "
                     "cache_has_attachments, associated_message_type, service) "
                     "VALUES (1, 'm-1', 'hello from subprocess test', 1, 0, ?, 0, 0, 'iMessage')",
                     (to_apple_ns(0.1),))
        conn.execute("INSERT INTO chat_message_join (chat_id, message_id) VALUES (1, 1)")
        conn.commit()
        conn.close()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_doctor_via_subprocess(self):
        env = dict(os.environ)
        env["IMESSAGE_DB_PATH"] = self.db_path
        env["IMESSAGE_ADDRESSBOOK_DIR"] = os.path.join(self.tmpdir, "nonexistent")
        proc = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "doctor"],
            capture_output=True, text=True, env=env, timeout=10,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["message_count"], 1)

    def test_recent_via_subprocess(self):
        env = dict(os.environ)
        env["IMESSAGE_DB_PATH"] = self.db_path
        env["IMESSAGE_ADDRESSBOOK_DIR"] = os.path.join(self.tmpdir, "nonexistent")
        proc = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "recent", "--since", "7 days ago"],
            capture_output=True, text=True, env=env, timeout=10,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertEqual(data["message_count"], 1)


class NoNetworkTest(unittest.TestCase):
    def test_script_has_no_network_calls(self):
        source = SCRIPT_PATH.read_text()
        for banned in ("requests", "socket", "urllib", "http.client", "httplib"):
            self.assertNotIn(banned, source, f"found banned network-related token: {banned}")


if __name__ == "__main__":
    unittest.main()
