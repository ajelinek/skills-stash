#!/usr/bin/env python3
"""Tests for check_reputation.py's pure fetch/normalize/merge logic.

No real network calls -- requests.get is mocked throughout, so this suite runs
offline and never spends the (rate-limited, free-tier) API quota.
"""
import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "check_reputation.py"

spec = importlib.util.spec_from_file_location("check_reputation", SCRIPT_PATH)
check_reputation = importlib.util.module_from_spec(spec)
sys.modules["check_reputation"] = check_reputation
spec.loader.exec_module(check_reputation)


class FakeResponse:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json_data = json_data if json_data is not None else {}

    def json(self):
        return self._json_data


class EmailValidationTests(unittest.TestCase):
    def test_valid_email(self):
        self.assertTrue(check_reputation.is_valid_email("person@example.com"))

    def test_invalid_email_missing_at(self):
        self.assertFalse(check_reputation.is_valid_email("not-an-email"))

    def test_invalid_email_missing_tld(self):
        self.assertFalse(check_reputation.is_valid_email("person@localhost"))

    def test_invalid_email_empty(self):
        self.assertFalse(check_reputation.is_valid_email(""))
        self.assertFalse(check_reputation.is_valid_email(None))

    def test_domain_from_email(self):
        self.assertEqual(check_reputation.domain_from_email("Person@Example.COM"), "example.com")


class MissingEnvVarsTests(unittest.TestCase):
    def test_all_present(self):
        env = {
            "EMAILREP_API_KEY": "k1",
            "EMAILREP_USER_AGENT": "ua",
            "ABSTRACTAPI_API_KEY": "k2",
        }
        self.assertEqual(check_reputation.missing_env_vars(env), [])

    def test_reports_each_missing_name(self):
        env = {"EMAILREP_API_KEY": "k1"}
        missing = check_reputation.missing_env_vars(env)
        self.assertIn("EMAILREP_USER_AGENT", missing)
        self.assertIn("ABSTRACTAPI_API_KEY", missing)
        self.assertNotIn("EMAILREP_API_KEY", missing)

    def test_blank_value_counts_as_missing(self):
        env = {"EMAILREP_API_KEY": "", "EMAILREP_USER_AGENT": "ua", "ABSTRACTAPI_API_KEY": "k2"}
        self.assertEqual(check_reputation.missing_env_vars(env), ["EMAILREP_API_KEY"])


class FetchEmailRepTests(unittest.TestCase):
    @patch("check_reputation.requests.get")
    def test_success(self, mock_get):
        mock_get.return_value = FakeResponse(200, {"reputation": "high", "details": {}})
        result = check_reputation.fetch_emailrep("a@b.com", "key", "ua")
        self.assertTrue(result["ok"])
        self.assertEqual(result["raw"]["reputation"], "high")

    @patch("check_reputation.requests.get")
    def test_401_reported_as_invalid_key(self, mock_get):
        mock_get.return_value = FakeResponse(401)
        result = check_reputation.fetch_emailrep("a@b.com", "bad-key", "ua")
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "invalid_api_key")
        self.assertEqual(result["status_code"], 401)

    @patch("check_reputation.requests.get")
    def test_429_reported_as_rate_limited(self, mock_get):
        mock_get.return_value = FakeResponse(429)
        result = check_reputation.fetch_emailrep("a@b.com", "key", "ua")
        self.assertEqual(result["error"], "rate_limited")

    @patch("check_reputation.requests.get")
    def test_timeout(self, mock_get):
        mock_get.side_effect = check_reputation.requests.exceptions.Timeout()
        result = check_reputation.fetch_emailrep("a@b.com", "key", "ua")
        self.assertEqual(result["error"], "timeout")
        self.assertFalse(result["ok"])


class FetchAbstractApiTests(unittest.TestCase):
    @patch("check_reputation.requests.get")
    def test_success(self, mock_get):
        mock_get.return_value = FakeResponse(200, {"quality_score": "0.8"})
        result = check_reputation.fetch_abstractapi("a@b.com", "key")
        self.assertTrue(result["ok"])

    @patch("check_reputation.requests.get")
    def test_network_error(self, mock_get):
        mock_get.side_effect = check_reputation.requests.exceptions.ConnectionError("boom")
        result = check_reputation.fetch_abstractapi("a@b.com", "key")
        self.assertEqual(result["error"], "network_error")


class NormalizeEmailRepTests(unittest.TestCase):
    def test_flattens_details_and_top_level(self):
        raw = {
            "reputation": "high",
            "suspicious": False,
            "references": 42,
            "details": {
                "blacklisted": False,
                "malicious_activity_recent": False,
                "disposable": True,
                "new_domain": True,
                "days_since_domain_creation": 12,
                "spf_strict": True,
                "dmarc_enforced": False,
                "profiles": ["twitter"],
            },
        }
        signals = check_reputation.normalize_emailrep(raw)
        self.assertEqual(signals["reputation"], "high")
        self.assertEqual(signals["references"], 42)
        self.assertTrue(signals["is_disposable"])
        self.assertTrue(signals["new_domain"])
        self.assertEqual(signals["domain_age_days"], 12)
        self.assertTrue(signals["spf_strict"])
        self.assertFalse(signals["dmarc_enforced"])
        self.assertEqual(signals["profiles"], ["twitter"])

    def test_empty_raw_returns_empty_dict(self):
        self.assertEqual(check_reputation.normalize_emailrep(None), {})
        self.assertEqual(check_reputation.normalize_emailrep({}), {})


class NormalizeAbstractApiTests(unittest.TestCase):
    def test_flattens_tri_state_fields(self):
        raw = {
            "quality_score": "0.85",
            "deliverability": "DELIVERABLE",
            "is_free_email": {"value": True, "text": "TRUE"},
            "is_role_email": {"value": False, "text": "FALSE"},
            "is_disposable_email": {"value": False, "text": "FALSE"},
            "is_catchall_email": {"value": None, "text": "UNKNOWN"},
        }
        signals = check_reputation.normalize_abstractapi(raw)
        self.assertEqual(signals["quality_score"], 0.85)
        self.assertTrue(signals["deliverable"])
        self.assertTrue(signals["is_free_email"])
        self.assertFalse(signals["is_role"])
        self.assertIsNone(signals["is_catchall"])

    def test_bad_quality_score_becomes_none(self):
        signals = check_reputation.normalize_abstractapi({"quality_score": "not-a-number"})
        self.assertIsNone(signals["quality_score"])

    def test_empty_raw_returns_empty_dict(self):
        self.assertEqual(check_reputation.normalize_abstractapi(None), {})


class MergeSignalsTests(unittest.TestCase):
    def test_emailrep_takes_precedence_on_overlap(self):
        er = {"is_disposable": False}
        ab = {"is_disposable": True}
        merged = check_reputation.merge_signals(er, ab)
        self.assertFalse(merged["is_disposable"])

    def test_falls_back_to_abstractapi_when_emailrep_null(self):
        er = {"is_free_email": None}
        ab = {"is_free_email": True}
        merged = check_reputation.merge_signals(er, ab)
        self.assertTrue(merged["is_free_email"])

    def test_abstract_only_fields_pass_through(self):
        merged = check_reputation.merge_signals({}, {"is_role": True, "quality_score": 0.5})
        self.assertTrue(merged["is_role"])
        self.assertEqual(merged["quality_score"], 0.5)

    def test_valid_mx_prefers_emailrep_then_abstract_mx_found(self):
        merged = check_reputation.merge_signals({"valid_mx": None}, {"mx_found": True})
        self.assertTrue(merged["valid_mx"])


class BuildOutputTests(unittest.TestCase):
    def test_full_success(self):
        emailrep_result = {"ok": True, "error": None, "detail": None, "raw": {"reputation": "high", "details": {}}}
        abstract_result = {"ok": True, "error": None, "detail": None, "raw": {"quality_score": "0.9"}}
        output = check_reputation.build_output("person@example.com", emailrep_result, abstract_result)
        self.assertEqual(output["domain"], "example.com")
        self.assertFalse(output["partial"])
        self.assertEqual(output["signals"]["reputation"], "high")
        self.assertEqual(output["signals"]["quality_score"], 0.9)

    def test_partial_result_when_one_source_errors(self):
        emailrep_result = {"ok": False, "error": "rate_limited", "detail": "429", "raw": None}
        abstract_result = {"ok": True, "error": None, "detail": None, "raw": {"quality_score": "0.5"}}
        output = check_reputation.build_output("person@example.com", emailrep_result, abstract_result)
        self.assertTrue(output["partial"])
        self.assertEqual(output["sources"]["emailrep"]["error"], "rate_limited")
        self.assertEqual(output["signals"]["quality_score"], 0.5)

    def test_output_is_json_serializable(self):
        emailrep_result = {"ok": True, "error": None, "detail": None, "raw": {"reputation": "high", "details": {}}}
        abstract_result = {"ok": True, "error": None, "detail": None, "raw": {}}
        output = check_reputation.build_output("person@example.com", emailrep_result, abstract_result)
        json.dumps(output)  # must not raise


class MainTests(unittest.TestCase):
    @patch.dict("os.environ", {}, clear=True)
    def test_missing_env_vars_exits_nonzero_before_any_call(self):
        with patch("check_reputation.requests.get") as mock_get:
            exit_code = check_reputation.main(["a@b.com"])
            mock_get.assert_not_called()
        self.assertEqual(exit_code, 1)

    @patch.dict(
        "os.environ",
        {"EMAILREP_API_KEY": "k1", "EMAILREP_USER_AGENT": "ua", "ABSTRACTAPI_API_KEY": "k2"},
        clear=True,
    )
    def test_invalid_email_exits_nonzero_before_any_call(self):
        with patch("check_reputation.requests.get") as mock_get:
            exit_code = check_reputation.main(["not-an-email"])
            mock_get.assert_not_called()
        self.assertEqual(exit_code, 1)

    @patch.dict(
        "os.environ",
        {"EMAILREP_API_KEY": "k1", "EMAILREP_USER_AGENT": "ua", "ABSTRACTAPI_API_KEY": "k2"},
        clear=True,
    )
    @patch("check_reputation.requests.get")
    def test_happy_path_exits_zero(self, mock_get):
        mock_get.return_value = FakeResponse(200, {"reputation": "high", "details": {}})
        exit_code = check_reputation.main(["person@example.com"])
        self.assertEqual(exit_code, 0)


if __name__ == "__main__":
    unittest.main()
