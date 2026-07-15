#!/usr/bin/env python3
"""
check_reputation.py -- Fetch + normalize email/domain reputation signals from
AbstractAPI's Email Reputation endpoint into one JSON object on stdout.

AbstractAPI acquired EmailRep and merged it into this single endpoint --
there is no separate EmailRep API to call anymore, and a key issued from
either abstractapi.com or emailrep.io works here.

Stdlib only -- no pip install, no venv, no container needed to run this.

Fetch and normalization only -- no trust/caution/block verdict is computed
here. That judgment is deliberately left to the caller (see
../references/interpretation-rules.md) so the rubric can be tuned without
touching this script.

Usage:
    python3 check_reputation.py <email>

Required, read from the real environment first:
    ABSTRACTAPI_API_KEY
If missing from os.environ, a `.env` file next to this skill's SKILL.md
(KEY=value per line) is used to fill it in -- a real environment variable
(e.g. injected by a cloud dev environment) always wins over the file. Keys
are never accepted as CLI args, to keep them out of shell history and
process listings.

Exit codes:
    0 -- ran to completion; stdout is the normalized JSON. A source-level
         error (bad key, rate limit, timeout) still exits 0 -- the JSON's
         "source"/"ok" fields describe what happened.
    1 -- fatal error before any network call (missing env var, invalid
         email format); stdout is a JSON object with a "fatal_error" key.
"""
import argparse
import json
import os
import re
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request

ABSTRACTAPI_URL = "https://emailreputation.abstractapi.com/v1/"
REQUEST_TIMEOUT_SECONDS = 10

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

REQUIRED_ENV_VARS = ("ABSTRACTAPI_API_KEY",)

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE_PATH = os.path.join(SKILL_DIR, ".env")


def load_env_file(path):
    """Parse a simple KEY=value .env file. Returns {} if it doesn't exist."""
    if not os.path.isfile(path):
        return {}
    values = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def apply_env_file_fallback(env, file_values):
    """Fill in only the keys `env` doesn't already have -- real env vars win."""
    for key, value in file_values.items():
        env.setdefault(key, value)


def is_valid_email(email):
    return bool(EMAIL_RE.match(email or ""))


def domain_from_email(email):
    return email.rsplit("@", 1)[-1].lower()


def missing_env_vars(env):
    return [name for name in REQUIRED_ENV_VARS if not env.get(name)]


def _error_result(kind, detail=None, status_code=None):
    return {"ok": False, "error": kind, "detail": detail, "status_code": status_code, "raw": None}


def _http_get(url, headers, timeout):
    """Returns (status_code, raw_bytes) for any HTTP response, including
    4xx/5xx. Raises TimeoutError for timeouts, OSError for other network
    failures (DNS, connection refused, etc.)."""
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()
    except (socket.timeout, TimeoutError) as exc:
        raise TimeoutError(str(exc)) from exc
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, (socket.timeout, TimeoutError)):
            raise TimeoutError(str(exc.reason)) from exc
        raise OSError(str(exc.reason)) from exc


def fetch_reputation(email, api_key, timeout=REQUEST_TIMEOUT_SECONDS):
    query = urllib.parse.urlencode({"api_key": api_key, "email": email})
    url = f"{ABSTRACTAPI_URL}?{query}"
    try:
        status, body = _http_get(url, {}, timeout)
    except TimeoutError:
        return _error_result("timeout", "Abstract API request timed out")
    except OSError as exc:
        return _error_result("network_error", str(exc))

    if status == 401:
        return _error_result("invalid_api_key", "Abstract API rejected the API key (401)", 401)
    if status == 429:
        return _error_result("rate_limited", "Abstract API rate limit hit (429)", 429)
    if status != 200:
        return _error_result("http_error", f"Abstract API returned HTTP {status}", status)

    try:
        data = json.loads(body)
    except ValueError:
        return _error_result("invalid_response", "Abstract API response was not valid JSON")

    return {"ok": True, "error": None, "detail": None, "status_code": 200, "raw": data}


def _bool_or_none(value):
    return value if isinstance(value, bool) else None


def normalize_reputation(raw):
    """Flatten AbstractAPI's nested email_* groups into a flat signal dict."""
    if not raw:
        return {}
    deliverability = raw.get("email_deliverability") or {}
    sender = raw.get("email_sender") or {}
    domain = raw.get("email_domain") or {}
    quality = raw.get("email_quality") or {}
    risk = raw.get("email_risk") or {}
    breaches = raw.get("email_breaches") or {}

    total_breaches = breaches.get("total_breaches")
    deliverable = {"deliverable": True, "undeliverable": False}.get(deliverability.get("status"))

    return {
        "suggested_correction": raw.get("suggested_correction") or None,

        "deliverability_status": deliverability.get("status"),
        "deliverable": deliverable,
        "is_valid_format": _bool_or_none(deliverability.get("is_format_valid")),
        "smtp_valid": _bool_or_none(deliverability.get("is_smtp_valid")),
        "valid_mx": _bool_or_none(deliverability.get("is_mx_valid")),

        "email_provider_name": sender.get("email_provider_name"),
        "organization_name": sender.get("organization_name"),

        "domain_age_days": domain.get("domain_age"),
        "is_risky_tld": _bool_or_none(domain.get("is_risky_tld")),
        "is_live_site": _bool_or_none(domain.get("is_live_site")),

        "quality_score": quality.get("score"),
        "is_free_email": _bool_or_none(quality.get("is_free_email")),
        "is_username_suspicious": _bool_or_none(quality.get("is_username_suspicious")),
        "is_disposable": _bool_or_none(quality.get("is_disposable")),
        "is_catchall": _bool_or_none(quality.get("is_catchall")),
        "is_role": _bool_or_none(quality.get("is_role")),
        "spf_strict": _bool_or_none(quality.get("is_spf_strict")),
        "dmarc_enforced": _bool_or_none(quality.get("is_dmarc_enforced")),

        "address_risk": risk.get("address_risk_status"),
        "domain_risk": risk.get("domain_risk_status"),

        "total_breaches": total_breaches,
        "data_breach": (total_breaches > 0) if isinstance(total_breaches, int) else None,
        "date_first_breached": breaches.get("date_first_breached"),
        "date_last_breached": breaches.get("date_last_breached"),
    }


def build_output(email, result):
    return {
        "email": email,
        "domain": domain_from_email(email),
        "signals": normalize_reputation(result.get("raw")),
        "source": {
            "ok": result["ok"],
            "error": result["error"],
            "detail": result["detail"],
        },
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Fetch and normalize email reputation signals.")
    parser.add_argument("email", help="Email address to check")
    args = parser.parse_args(argv)

    env = dict(os.environ)
    apply_env_file_fallback(env, load_env_file(ENV_FILE_PATH))

    missing = missing_env_vars(env)
    if missing:
        print(json.dumps({"fatal_error": "missing_env_vars", "missing": missing}))
        return 1

    if not is_valid_email(args.email):
        print(json.dumps({"fatal_error": "invalid_email", "email": args.email}))
        return 1

    result = fetch_reputation(args.email, env["ABSTRACTAPI_API_KEY"])

    print(json.dumps(build_output(args.email, result), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
