#!/usr/bin/env python3
"""Tests for check_dns_auth.py's pure parsing/normalize logic.

No real DNS queries -- _dig is mocked throughout, so this suite runs
offline and doesn't depend on network access or `dig` being installed.
"""
import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "check_dns_auth.py"

spec = importlib.util.spec_from_file_location("check_dns_auth", SCRIPT_PATH)
check_dns_auth = importlib.util.module_from_spec(spec)
sys.modules["check_dns_auth"] = check_dns_auth
spec.loader.exec_module(check_dns_auth)


class DomainFromArgTests(unittest.TestCase):
    def test_extracts_domain_from_email(self):
        self.assertEqual(check_dns_auth.domain_from_arg("Adam@Shadetreeit.biz"), "shadetreeit.biz")

    def test_bare_domain_passthrough(self):
        self.assertEqual(check_dns_auth.domain_from_arg("Shadetreeit.biz"), "shadetreeit.biz")

    def test_strips_whitespace(self):
        self.assertEqual(check_dns_auth.domain_from_arg("  example.com  "), "example.com")


class IsValidDomainTests(unittest.TestCase):
    def test_valid_domain(self):
        self.assertTrue(check_dns_auth.is_valid_domain("example.com"))
        self.assertTrue(check_dns_auth.is_valid_domain("mail.example.co.uk"))

    def test_invalid_domain(self):
        self.assertFalse(check_dns_auth.is_valid_domain(""))
        self.assertFalse(check_dns_auth.is_valid_domain("not a domain"))
        self.assertFalse(check_dns_auth.is_valid_domain("nodots"))


class ParseTxtLineTests(unittest.TestCase):
    def test_single_quoted_segment(self):
        self.assertEqual(check_dns_auth._parse_txt_line('"v=spf1 include:_spf.google.com -all"'),
                          "v=spf1 include:_spf.google.com -all")

    def test_multiple_quoted_segments_concatenated(self):
        self.assertEqual(check_dns_auth._parse_txt_line('"v=DKIM1; k=rsa; " "p=ABC123"'),
                          "v=DKIM1; k=rsa; p=ABC123")

    def test_unquoted_fallback(self):
        self.assertEqual(check_dns_auth._parse_txt_line("plain-text"), "plain-text")


class ParseTagListTests(unittest.TestCase):
    def test_parses_spaced_tags(self):
        tags = check_dns_auth._parse_tag_list("v=DMARC1; p=reject; pct=100; rua=mailto:a@b.com")
        self.assertEqual(tags["p"], "reject")
        self.assertEqual(tags["pct"], "100")
        self.assertEqual(tags["rua"], "mailto:a@b.com")

    def test_ignores_malformed_segments(self):
        tags = check_dns_auth._parse_tag_list("v=DMARC1;;p=none")
        self.assertEqual(tags["p"], "none")


class SpfAllQualifierTests(unittest.TestCase):
    def test_hard_fail(self):
        self.assertEqual(check_dns_auth._spf_all_qualifier("v=spf1 include:_spf.google.com -all"), "-all")

    def test_soft_fail(self):
        self.assertEqual(check_dns_auth._spf_all_qualifier("v=spf1 include:_spf.google.com ~all"), "~all")

    def test_permissive(self):
        self.assertEqual(check_dns_auth._spf_all_qualifier("v=spf1 +all"), "+all")

    def test_no_all_mechanism(self):
        self.assertIsNone(check_dns_auth._spf_all_qualifier("v=spf1 include:_spf.google.com"))


class ParseSpfTests(unittest.TestCase):
    def test_not_found(self):
        result = check_dns_auth.parse_spf([])
        self.assertFalse(result["found"])
        self.assertFalse(result["strict"])
        self.assertIsNone(result["all_mechanism"])

    def test_strict_hard_fail(self):
        result = check_dns_auth.parse_spf(["v=spf1 include:_spf.google.com -all"])
        self.assertTrue(result["found"])
        self.assertTrue(result["strict"])
        self.assertFalse(result["multiple_records"])

    def test_soft_fail_is_not_strict(self):
        result = check_dns_auth.parse_spf(["v=spf1 include:_spf.google.com ~all"])
        self.assertFalse(result["strict"])

    def test_multiple_records_flagged(self):
        result = check_dns_auth.parse_spf(["v=spf1 -all", "v=spf1 include:other.com -all"])
        self.assertTrue(result["multiple_records"])


class ParseDmarcTests(unittest.TestCase):
    def test_not_found(self):
        result = check_dns_auth.parse_dmarc([])
        self.assertFalse(result["found"])
        self.assertFalse(result["enforced"])

    def test_enforced_reject(self):
        result = check_dns_auth.parse_dmarc(["v=DMARC1; p=reject; pct=100; rua=mailto:d@example.com"])
        self.assertTrue(result["found"])
        self.assertEqual(result["policy"], "reject")
        self.assertTrue(result["enforced"])
        self.assertEqual(result["rua"], ["mailto:d@example.com"])

    def test_policy_none_is_not_enforced(self):
        result = check_dns_auth.parse_dmarc(["v=DMARC1; p=none"])
        self.assertFalse(result["enforced"])

    def test_partial_pct_is_not_enforced(self):
        result = check_dns_auth.parse_dmarc(["v=DMARC1; p=reject; pct=50"])
        self.assertFalse(result["enforced"])

    def test_missing_pct_defaults_to_100(self):
        result = check_dns_auth.parse_dmarc(["v=DMARC1; p=reject"])
        self.assertEqual(result["pct"], 100)
        self.assertTrue(result["enforced"])

    def test_multiple_records_never_enforced(self):
        result = check_dns_auth.parse_dmarc(["v=DMARC1; p=reject", "v=DMARC1; p=reject"])
        self.assertTrue(result["multiple_records"])
        self.assertFalse(result["enforced"])

    def test_subdomain_policy_falls_back_to_p(self):
        result = check_dns_auth.parse_dmarc(["v=DMARC1; p=quarantine"])
        self.assertEqual(result["subdomain_policy"], "quarantine")


class DigTests(unittest.TestCase):
    @patch("check_dns_auth.subprocess.run")
    def test_success_returns_lines(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="10 mail.example.com.\n", stderr="")
        result = check_dns_auth._dig("example.com", "MX")
        self.assertEqual(result, ["10 mail.example.com."])

    @patch("check_dns_auth.subprocess.run")
    def test_empty_output_returns_empty_list(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
        result = check_dns_auth._dig("example.com", "TXT")
        self.assertEqual(result, [])

    @patch("check_dns_auth.subprocess.run")
    def test_nonzero_returncode_raises(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="connection refused")
        with self.assertRaises(OSError):
            check_dns_auth._dig("example.com", "TXT")

    @patch("check_dns_auth.subprocess.run")
    def test_timeout_raises_timeout_error(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="dig", timeout=6)
        with self.assertRaises(TimeoutError):
            check_dns_auth._dig("example.com", "TXT")

    @patch("check_dns_auth.subprocess.run")
    def test_missing_binary_raises_runtime_error(self, mock_run):
        mock_run.side_effect = FileNotFoundError()
        with self.assertRaises(RuntimeError):
            check_dns_auth._dig("example.com", "TXT")


class FetchFunctionTests(unittest.TestCase):
    @patch("check_dns_auth._dig")
    def test_fetch_mx_sorts_by_preference(self, mock_dig):
        mock_dig.return_value = ["20 backup.example.com.", "10 primary.example.com."]
        records = check_dns_auth.fetch_mx("example.com")
        self.assertEqual([r["exchange"] for r in records], ["primary.example.com", "backup.example.com"])

    @patch("check_dns_auth._dig")
    def test_fetch_spf_filters_non_spf_txt(self, mock_dig):
        mock_dig.return_value = ['"google-site-verification=abc123"', '"v=spf1 -all"']
        records = check_dns_auth.fetch_spf("example.com")
        self.assertEqual(records, ["v=spf1 -all"])

    @patch("check_dns_auth._dig")
    def test_fetch_dmarc_queries_underscore_subdomain(self, mock_dig):
        mock_dig.return_value = ['"v=DMARC1; p=reject"']
        check_dns_auth.fetch_dmarc("example.com")
        mock_dig.assert_called_once_with("_dmarc.example.com", "TXT")

    @patch("check_dns_auth._dig")
    def test_fetch_dkim_only_reports_hits(self, mock_dig):
        def side_effect(name, rtype):
            if name.startswith("google."):
                return ['"v=DKIM1; k=rsa; p=ABC123"']
            raise OSError("NXDOMAIN")
        mock_dig.side_effect = side_effect
        found = check_dns_auth.fetch_dkim("example.com", selectors=("google", "selector1"))
        self.assertEqual(list(found.keys()), ["google"])
        self.assertTrue(found["google"]["has_public_key"])


class BuildOutputTests(unittest.TestCase):
    @patch("check_dns_auth.fetch_dkim")
    @patch("check_dns_auth.fetch_dmarc")
    @patch("check_dns_auth.fetch_spf")
    @patch("check_dns_auth.fetch_mx")
    def test_aggregates_all_sections(self, mock_mx, mock_spf, mock_dmarc, mock_dkim):
        mock_mx.return_value = [{"preference": 10, "exchange": "mail.example.com"}]
        mock_spf.return_value = ["v=spf1 -all"]
        mock_dmarc.return_value = ["v=DMARC1; p=reject"]
        mock_dkim.return_value = {}
        output = check_dns_auth.build_output("example.com")
        self.assertTrue(output["mx"]["found"])
        self.assertTrue(output["spf"]["strict"])
        self.assertTrue(output["dmarc"]["enforced"])
        self.assertFalse(output["dkim"]["found"])
        self.assertEqual(output["errors"], {})

    @patch("check_dns_auth.fetch_dkim")
    @patch("check_dns_auth.fetch_dmarc")
    @patch("check_dns_auth.fetch_spf")
    @patch("check_dns_auth.fetch_mx")
    def test_one_section_failing_does_not_block_others(self, mock_mx, mock_spf, mock_dmarc, mock_dkim):
        mock_mx.side_effect = OSError("dns timeout")
        mock_spf.return_value = ["v=spf1 -all"]
        mock_dmarc.return_value = []
        mock_dkim.return_value = {}
        output = check_dns_auth.build_output("example.com")
        self.assertFalse(output["mx"]["found"])
        self.assertIn("mx", output["errors"])
        self.assertTrue(output["spf"]["found"])


class MainTests(unittest.TestCase):
    def test_invalid_domain_exits_nonzero_before_any_call(self):
        with patch("check_dns_auth._dig") as mock_dig:
            exit_code = check_dns_auth.main(["not a domain"])
            mock_dig.assert_not_called()
        self.assertEqual(exit_code, 1)

    @patch("check_dns_auth._dig_available", return_value=False)
    def test_dig_not_found_exits_nonzero(self, mock_available):
        exit_code = check_dns_auth.main(["example.com"])
        self.assertEqual(exit_code, 1)

    @patch("check_dns_auth._dig_available", return_value=True)
    @patch("check_dns_auth._dig")
    def test_happy_path_accepts_email_argument(self, mock_dig, mock_available):
        mock_dig.return_value = []
        exit_code = check_dns_auth.main(["person@example.com"])
        self.assertEqual(exit_code, 0)


if __name__ == "__main__":
    unittest.main()
