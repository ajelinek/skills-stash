#!/usr/bin/env python3
"""Tests for check_reputation.py's pure fetch/normalize logic.

No real network calls -- _http_get is mocked throughout, so this suite runs
offline and never spends the (rate-limited, free-tier) API quota.
"""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "check_reputation.py"

spec = importlib.util.spec_from_file_location("check_reputation", SCRIPT_PATH)
check_reputation = importlib.util.module_from_spec(spec)
sys.modules["check_reputation"] = check_reputation
spec.loader.exec_module(check_reputation)


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
        env = {"ABSTRACTAPI_API_KEY": "k2"}
        self.assertEqual(check_reputation.missing_env_vars(env), [])

    def test_reports_missing_name(self):
        env = {}
        self.assertEqual(check_reputation.missing_env_vars(env), ["ABSTRACTAPI_API_KEY"])

    def test_blank_value_counts_as_missing(self):
        env = {"ABSTRACTAPI_API_KEY": ""}
        self.assertEqual(check_reputation.missing_env_vars(env), ["ABSTRACTAPI_API_KEY"])


class EnvFileFallbackTests(unittest.TestCase):
    def test_missing_file_returns_empty(self):
        self.assertEqual(check_reputation.load_env_file("/nonexistent/.env"), {})

    def test_parses_key_value_lines_and_skips_comments(self):
        with tempfile.NamedTemporaryFile("w", suffix=".env", delete=False) as f:
            f.write('# comment\nABSTRACTAPI_API_KEY=abc123\n\nOTHER="quoted-value"\n')
            path = f.name
        try:
            values = check_reputation.load_env_file(path)
            self.assertEqual(values["ABSTRACTAPI_API_KEY"], "abc123")
            self.assertEqual(values["OTHER"], "quoted-value")
        finally:
            Path(path).unlink()

    def test_real_env_vars_win_over_file_fallback(self):
        env = {"ABSTRACTAPI_API_KEY": "real-value"}
        check_reputation.apply_env_file_fallback(env, {"ABSTRACTAPI_API_KEY": "file-value"})
        self.assertEqual(env["ABSTRACTAPI_API_KEY"], "real-value")

    def test_file_fills_in_when_missing_from_env(self):
        env = {}
        check_reputation.apply_env_file_fallback(env, {"ABSTRACTAPI_API_KEY": "file-value"})
        self.assertEqual(env["ABSTRACTAPI_API_KEY"], "file-value")


class FetchReputationTests(unittest.TestCase):
    @patch("check_reputation._http_get")
    def test_success(self, mock_get):
        mock_get.return_value = (200, json.dumps({"email_address": "a@b.com"}).encode())
        result = check_reputation.fetch_reputation("a@b.com", "key")
        self.assertTrue(result["ok"])
        self.assertEqual(result["raw"]["email_address"], "a@b.com")

    @patch("check_reputation._http_get")
    def test_401_reported_as_invalid_key(self, mock_get):
        mock_get.return_value = (401, b"")
        result = check_reputation.fetch_reputation("a@b.com", "bad-key")
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "invalid_api_key")
        self.assertEqual(result["status_code"], 401)

    @patch("check_reputation._http_get")
    def test_429_reported_as_rate_limited(self, mock_get):
        mock_get.return_value = (429, b"")
        result = check_reputation.fetch_reputation("a@b.com", "key")
        self.assertEqual(result["error"], "rate_limited")

    @patch("check_reputation._http_get")
    def test_timeout(self, mock_get):
        mock_get.side_effect = TimeoutError("timed out")
        result = check_reputation.fetch_reputation("a@b.com", "key")
        self.assertEqual(result["error"], "timeout")
        self.assertFalse(result["ok"])

    @patch("check_reputation._http_get")
    def test_network_error(self, mock_get):
        mock_get.side_effect = OSError("boom")
        result = check_reputation.fetch_reputation("a@b.com", "key")
        self.assertEqual(result["error"], "network_error")


class NormalizeReputationTests(unittest.TestCase):
    SAMPLE_RAW = {
        "email_address": "johnsmith@gmail.com",
        "suggested_correction": None,
        "email_deliverability": {
            "status": "undeliverable",
            "status_detail": "invalid_mailbox",
            "is_format_valid": True,
            "is_smtp_valid": False,
            "is_mx_valid": True,
        },
        "email_sender": {
            "email_provider_name": "Google",
            "organization_name": "Gmail",
        },
        "email_domain": {
            "domain": "gmail.com",
            "domain_age": 11293,
            "is_live_site": True,
            "is_risky_tld": False,
        },
        "email_quality": {
            "score": 0.0,
            "is_free_email": True,
            "is_username_suspicious": False,
            "is_disposable": False,
            "is_catchall": False,
            "is_role": False,
            "is_dmarc_enforced": True,
            "is_spf_strict": False,
        },
        "email_risk": {
            "address_risk_status": "high",
            "domain_risk_status": "low",
        },
        "email_breaches": {
            "total_breaches": 329,
            "date_first_breached": "2008-07-01",
            "date_last_breached": "2026-06-18",
        },
    }

    def test_flattens_nested_groups(self):
        signals = check_reputation.normalize_reputation(self.SAMPLE_RAW)
        self.assertEqual(signals["deliverability_status"], "undeliverable")
        self.assertFalse(signals["deliverable"])
        self.assertTrue(signals["valid_mx"])
        self.assertEqual(signals["domain_age_days"], 11293)
        self.assertFalse(signals["is_risky_tld"])
        self.assertEqual(signals["quality_score"], 0.0)
        self.assertTrue(signals["is_free_email"])
        self.assertEqual(signals["address_risk"], "high")
        self.assertEqual(signals["domain_risk"], "low")
        self.assertEqual(signals["total_breaches"], 329)
        self.assertTrue(signals["data_breach"])

    def test_deliverable_status_maps_true(self):
        raw = dict(self.SAMPLE_RAW, email_deliverability={"status": "deliverable"})
        signals = check_reputation.normalize_reputation(raw)
        self.assertTrue(signals["deliverable"])

    def test_zero_breaches_is_not_a_data_breach(self):
        raw = dict(self.SAMPLE_RAW, email_breaches={"total_breaches": 0})
        signals = check_reputation.normalize_reputation(raw)
        self.assertFalse(signals["data_breach"])

    def test_empty_raw_returns_empty_dict(self):
        self.assertEqual(check_reputation.normalize_reputation(None), {})
        self.assertEqual(check_reputation.normalize_reputation({}), {})


class BuildOutputTests(unittest.TestCase):
    def test_full_success(self):
        result = {
            "ok": True, "error": None, "detail": None,
            "raw": {"email_domain": {"domain_age": 100}},
        }
        output = check_reputation.build_output("person@example.com", result)
        self.assertEqual(output["domain"], "example.com")
        self.assertTrue(output["source"]["ok"])
        self.assertEqual(output["signals"]["domain_age_days"], 100)

    def test_error_result(self):
        result = {"ok": False, "error": "invalid_api_key", "detail": "401", "raw": None}
        output = check_reputation.build_output("person@example.com", result)
        self.assertFalse(output["source"]["ok"])
        self.assertEqual(output["source"]["error"], "invalid_api_key")
        self.assertEqual(output["signals"], {})

    def test_output_is_json_serializable(self):
        result = {"ok": True, "error": None, "detail": None, "raw": {}}
        output = check_reputation.build_output("person@example.com", result)
        json.dumps(output)  # must not raise


class MainTests(unittest.TestCase):
    @patch.dict("os.environ", {}, clear=True)
    @patch("check_reputation.ENV_FILE_PATH", "/nonexistent/.env")
    def test_missing_env_vars_exits_nonzero_before_any_call(self):
        with patch("check_reputation._http_get") as mock_get:
            exit_code = check_reputation.main(["a@b.com"])
            mock_get.assert_not_called()
        self.assertEqual(exit_code, 1)

    @patch.dict("os.environ", {"ABSTRACTAPI_API_KEY": "k2"}, clear=True)
    def test_invalid_email_exits_nonzero_before_any_call(self):
        with patch("check_reputation._http_get") as mock_get:
            exit_code = check_reputation.main(["not-an-email"])
            mock_get.assert_not_called()
        self.assertEqual(exit_code, 1)

    @patch.dict("os.environ", {"ABSTRACTAPI_API_KEY": "k2"}, clear=True)
    @patch("check_reputation._http_get")
    def test_happy_path_exits_zero(self, mock_get):
        mock_get.return_value = (200, json.dumps({"email_address": "person@example.com"}).encode())
        exit_code = check_reputation.main(["person@example.com"])
        self.assertEqual(exit_code, 0)

    @patch.dict("os.environ", {}, clear=True)
    @patch("check_reputation._http_get")
    def test_env_file_fills_in_missing_var(self, mock_get):
        mock_get.return_value = (200, json.dumps({"email_address": "person@example.com"}).encode())
        with tempfile.NamedTemporaryFile("w", suffix=".env", delete=False) as f:
            f.write("ABSTRACTAPI_API_KEY=file-key\n")
            path = f.name
        try:
            with patch("check_reputation.ENV_FILE_PATH", path):
                exit_code = check_reputation.main(["person@example.com"])
            self.assertEqual(exit_code, 0)
        finally:
            Path(path).unlink()


if __name__ == "__main__":
    unittest.main()
