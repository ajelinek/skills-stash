#!/usr/bin/env python3
"""
check_reputation.py -- Fetch + merge email/domain reputation signals from
EmailRep (emailrep.io) and Abstract API Email Validation into one normalized
JSON object on stdout.

Fetch and normalization only -- no trust/caution/block verdict is computed
here. That judgment is deliberately left to the caller (see
../references/interpretation-rules.md) so the rubric can be tuned without
touching this script.

Usage:
    python3 check_reputation.py <email>

Required environment variables (never accepted as CLI args -- keeping keys
out of shell history and process listings is the whole point of routing
them through Docker Compose's env_file instead):
    EMAILREP_API_KEY
    EMAILREP_USER_AGENT
    ABSTRACTAPI_API_KEY

Exit codes:
    0 -- ran to completion; stdout is the merged JSON. A source-level error
         (bad key, rate limit, timeout) still exits 0 -- the JSON's
         "sources"/"partial" fields describe what happened, and a partial
         result is still a usable one.
    1 -- fatal error before any network call (missing env var(s), invalid
         email format); stdout is a JSON object with a "fatal_error" key.
"""
import argparse
import json
import os
import re
import sys
from urllib.parse import quote

import requests

EMAILREP_URL_TMPL = "https://emailrep.io/{email}"
ABSTRACTAPI_URL = "https://emailvalidation.abstractapi.com/v1/"
REQUEST_TIMEOUT_SECONDS = 10

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

REQUIRED_ENV_VARS = ("EMAILREP_API_KEY", "EMAILREP_USER_AGENT", "ABSTRACTAPI_API_KEY")


def is_valid_email(email):
    return bool(EMAIL_RE.match(email or ""))


def domain_from_email(email):
    return email.rsplit("@", 1)[-1].lower()


def missing_env_vars(env):
    return [name for name in REQUIRED_ENV_VARS if not env.get(name)]


def _error_result(kind, detail=None, status_code=None):
    return {"ok": False, "error": kind, "detail": detail, "status_code": status_code, "raw": None}


def fetch_emailrep(email, api_key, user_agent, timeout=REQUEST_TIMEOUT_SECONDS):
    url = EMAILREP_URL_TMPL.format(email=quote(email, safe=""))
    headers = {"Key": api_key, "User-Agent": user_agent, "Accept": "application/json"}
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
    except requests.exceptions.Timeout:
        return _error_result("timeout", "EmailRep request timed out")
    except requests.exceptions.RequestException as exc:
        return _error_result("network_error", str(exc))

    if resp.status_code == 401:
        return _error_result("invalid_api_key", "EmailRep rejected the API key (401)", 401)
    if resp.status_code == 429:
        return _error_result("rate_limited", "EmailRep rate limit hit (429)", 429)
    if resp.status_code != 200:
        return _error_result("http_error", f"EmailRep returned HTTP {resp.status_code}", resp.status_code)

    try:
        data = resp.json()
    except ValueError:
        return _error_result("invalid_response", "EmailRep response was not valid JSON")

    return {"ok": True, "error": None, "detail": None, "status_code": 200, "raw": data}


def fetch_abstractapi(email, api_key, timeout=REQUEST_TIMEOUT_SECONDS):
    params = {"api_key": api_key, "email": email}
    try:
        resp = requests.get(ABSTRACTAPI_URL, params=params, timeout=timeout)
    except requests.exceptions.Timeout:
        return _error_result("timeout", "Abstract API request timed out")
    except requests.exceptions.RequestException as exc:
        return _error_result("network_error", str(exc))

    if resp.status_code == 401:
        return _error_result("invalid_api_key", "Abstract API rejected the API key (401)", 401)
    if resp.status_code == 429:
        return _error_result("rate_limited", "Abstract API rate limit hit (429)", 429)
    if resp.status_code != 200:
        return _error_result("http_error", f"Abstract API returned HTTP {resp.status_code}", resp.status_code)

    try:
        data = resp.json()
    except ValueError:
        return _error_result("invalid_response", "Abstract API response was not valid JSON")

    return {"ok": True, "error": None, "detail": None, "status_code": 200, "raw": data}


def _bool_or_none(value):
    return value if isinstance(value, bool) else None


def normalize_emailrep(raw):
    """Flatten EmailRep's {top-level, details{}} shape into the shared signal vocabulary."""
    if not raw:
        return {}
    details = raw.get("details") or {}
    return {
        "reputation": raw.get("reputation"),
        "suspicious": _bool_or_none(raw.get("suspicious")),
        "references": raw.get("references"),
        "domain_reputation": details.get("domain_reputation"),
        "domain_exists": _bool_or_none(details.get("domain_exists")),
        "blacklisted": _bool_or_none(details.get("blacklisted")),
        "malicious_activity": _bool_or_none(details.get("malicious_activity")),
        "malicious_activity_recent": _bool_or_none(details.get("malicious_activity_recent")),
        "credentials_leaked": _bool_or_none(details.get("credentials_leaked")),
        "credentials_leaked_recent": _bool_or_none(details.get("credentials_leaked_recent")),
        "data_breach": _bool_or_none(details.get("data_breach")),
        "first_seen": details.get("first_seen"),
        "last_seen": details.get("last_seen"),
        "new_domain": _bool_or_none(details.get("new_domain")),
        "domain_age_days": details.get("days_since_domain_creation"),
        "suspicious_tld": _bool_or_none(details.get("suspicious_tld")),
        "is_free_email": _bool_or_none(details.get("free_provider")),
        "is_disposable": _bool_or_none(details.get("disposable")),
        "deliverable": _bool_or_none(details.get("deliverable")),
        "is_catchall": _bool_or_none(details.get("accept_all")),
        "valid_mx": _bool_or_none(details.get("valid_mx")),
        "spoofable": _bool_or_none(details.get("spoofable")),
        "spf_strict": _bool_or_none(details.get("spf_strict")),
        "dmarc_enforced": _bool_or_none(details.get("dmarc_enforced")),
        "profiles": details.get("profiles"),
    }


def _tri_state(field):
    if not isinstance(field, dict):
        return None
    return _bool_or_none(field.get("value"))


def normalize_abstractapi(raw):
    """Flatten Abstract API's {value, text} tri-state fields into plain booleans."""
    if not raw:
        return {}
    quality_score = raw.get("quality_score")
    try:
        quality_score = float(quality_score) if quality_score not in (None, "") else None
    except (TypeError, ValueError):
        quality_score = None

    deliverability = raw.get("deliverability")
    deliverable = {"DELIVERABLE": True, "UNDELIVERABLE": False}.get(deliverability)

    return {
        "autocorrect": raw.get("autocorrect") or None,
        "deliverability": deliverability,
        "deliverable": deliverable,
        "quality_score": quality_score,
        "is_valid_format": _tri_state(raw.get("is_valid_format")),
        "is_free_email": _tri_state(raw.get("is_free_email")),
        "is_disposable": _tri_state(raw.get("is_disposable_email")),
        "is_role": _tri_state(raw.get("is_role_email")),
        "is_catchall": _tri_state(raw.get("is_catchall_email")),
        "mx_found": _tri_state(raw.get("is_mx_found")),
        "smtp_valid": _tri_state(raw.get("is_smtp_valid")),
    }


def _first_non_null(*values):
    for v in values:
        if v is not None:
            return v
    return None


# Concepts both APIs report under the same name here -- EmailRep wins ties since
# reputation is its whole purpose; Abstract API only fills gaps EmailRep left null.
_SHARED_SIGNAL_KEYS = (
    "reputation", "suspicious", "references", "domain_reputation", "domain_exists",
    "blacklisted", "malicious_activity", "malicious_activity_recent",
    "credentials_leaked", "credentials_leaked_recent", "data_breach",
    "first_seen", "last_seen", "new_domain", "domain_age_days", "suspicious_tld",
    "is_free_email", "is_disposable", "deliverable", "is_catchall",
    "spoofable", "spf_strict", "dmarc_enforced", "profiles",
)


def merge_signals(emailrep_signals, abstract_signals):
    er = emailrep_signals or {}
    ab = abstract_signals or {}
    merged = {key: _first_non_null(er.get(key), ab.get(key)) for key in _SHARED_SIGNAL_KEYS}
    merged["valid_mx"] = _first_non_null(er.get("valid_mx"), ab.get("mx_found"))
    # Abstract-API-only concepts -- no EmailRep equivalent to merge against.
    merged["is_role"] = ab.get("is_role")
    merged["is_valid_format"] = ab.get("is_valid_format")
    merged["smtp_valid"] = ab.get("smtp_valid")
    merged["quality_score"] = ab.get("quality_score")
    merged["autocorrect"] = ab.get("autocorrect")
    return merged


def build_output(email, emailrep_result, abstract_result):
    signals = merge_signals(
        normalize_emailrep(emailrep_result.get("raw")),
        normalize_abstractapi(abstract_result.get("raw")),
    )
    return {
        "email": email,
        "domain": domain_from_email(email),
        "signals": signals,
        "sources": {
            "emailrep": {
                "ok": emailrep_result["ok"],
                "error": emailrep_result["error"],
                "detail": emailrep_result["detail"],
            },
            "abstractapi": {
                "ok": abstract_result["ok"],
                "error": abstract_result["error"],
                "detail": abstract_result["detail"],
            },
        },
        "partial": not (emailrep_result["ok"] and abstract_result["ok"]),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Fetch and merge email reputation signals.")
    parser.add_argument("email", help="Email address to check")
    args = parser.parse_args(argv)

    missing = missing_env_vars(os.environ)
    if missing:
        print(json.dumps({"fatal_error": "missing_env_vars", "missing": missing}))
        return 1

    if not is_valid_email(args.email):
        print(json.dumps({"fatal_error": "invalid_email", "email": args.email}))
        return 1

    emailrep_result = fetch_emailrep(
        args.email, os.environ["EMAILREP_API_KEY"], os.environ["EMAILREP_USER_AGENT"]
    )
    abstract_result = fetch_abstractapi(args.email, os.environ["ABSTRACTAPI_API_KEY"])

    print(json.dumps(build_output(args.email, emailrep_result, abstract_result), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
