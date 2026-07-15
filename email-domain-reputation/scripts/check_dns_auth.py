#!/usr/bin/env python3
"""
check_dns_auth.py -- Query live public DNS for a domain's SPF, DMARC, MX,
and (best-effort) DKIM records and normalize them into one JSON object on
stdout.

This is independent of check_reputation.py and needs no API key -- SPF,
DMARC, and MX are public DNS records, so this queries public resolvers
(1.1.1.1, 8.8.8.8 as fallback) directly via the system `dig` command rather
than depending on any third-party API's cache, which may be stale, rate
limited, or (as observed with AbstractAPI's spf_strict/dmarc_enforced
fields) simply empty for lesser-known domains. `dig` is used instead of a
hand-rolled DNS client for correctness -- EDNS/TCP-fallback/compression
edge cases are easy to get subtly wrong, and `dig` already handles them.

Stdlib only aside from the `dig` binary itself (present by default on macOS
and most Linux distros; install `dnsutils`/`bind-utils` if missing).

DKIM has no discoverable record without knowing the mail provider's
selector, so this checks a short list of common provider-default selectors
on a best-effort basis -- absence of a hit does NOT mean DKIM isn't
configured, only that none of the common selectors matched.

Usage:
    python3 check_dns_auth.py <email-or-domain>

Exit codes:
    0 -- ran to completion; stdout is the normalized JSON. Per-section query
         failures don't abort the run -- they're reported in "errors".
    1 -- fatal error before any DNS query (invalid domain, `dig` not found);
         stdout is a JSON object with a "fatal_error" key.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys

DIG_TIMEOUT_SECONDS = 6
DOMAIN_RE = re.compile(
    r"^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
    r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$"
)

# Common DKIM selector defaults by provider. Best-effort only -- a provider
# using a non-default or randomized selector won't be found here.
COMMON_DKIM_SELECTORS = (
    "google",       # Google Workspace
    "selector1",    # Microsoft 365
    "selector2",    # Microsoft 365
    "default",      # generic / many ESPs
    "dkim",         # generic
    "k1",           # Mailchimp/Mandrill
    "s1",           # SendGrid
    "s2",           # SendGrid
    "mail",         # generic
)


def domain_from_arg(value):
    value = (value or "").strip().lower()
    if "@" in value:
        value = value.rsplit("@", 1)[-1]
    return value


def is_valid_domain(domain):
    return bool(DOMAIN_RE.match(domain or ""))


def _dig_available():
    return shutil.which("dig") is not None


def _dig(name, rtype, timeout=DIG_TIMEOUT_SECONDS):
    try:
        proc = subprocess.run(
            ["dig", "+short", "+time=3", "+tries=1", rtype, name],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise TimeoutError(f"dig timed out querying {rtype} {name}") from exc
    except FileNotFoundError as exc:
        raise RuntimeError("dig not found") from exc
    if proc.returncode != 0:
        raise OSError(proc.stderr.strip() or f"dig exited {proc.returncode} querying {rtype} {name}")
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def _parse_txt_line(line):
    """dig wraps each character-string of a TXT record in double quotes;
    multi-string records need those segments concatenated."""
    quoted = re.findall(r'"((?:[^"\\]|\\.)*)"', line)
    if quoted:
        return "".join(quoted)
    return line.strip('"')


def _parse_tag_list(record):
    tags = {}
    for part in record.split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        key, _, value = part.partition("=")
        tags[key.strip().lower()] = value.strip()
    return tags


def fetch_mx(domain):
    records = []
    for line in _dig(domain, "MX"):
        parts = line.split()
        if len(parts) == 2 and parts[0].isdigit():
            records.append({"preference": int(parts[0]), "exchange": parts[1].rstrip(".")})
    records.sort(key=lambda r: r["preference"])
    return records


def fetch_spf(domain):
    txts = [_parse_txt_line(line) for line in _dig(domain, "TXT")]
    return [t for t in txts if t.lower().startswith("v=spf1")]


def fetch_dmarc(domain):
    txts = [_parse_txt_line(line) for line in _dig(f"_dmarc.{domain}", "TXT")]
    return [t for t in txts if t.lower().startswith("v=dmarc1")]


def fetch_dkim(domain, selectors=COMMON_DKIM_SELECTORS):
    found = {}
    for selector in selectors:
        try:
            txts = [_parse_txt_line(line) for line in _dig(f"{selector}._domainkey.{domain}", "TXT")]
        except Exception:
            continue
        record = next((t for t in txts if "v=dkim1" in t.lower() or "p=" in t.lower()), None)
        if record:
            found[selector] = {"has_public_key": bool(_parse_tag_list(record).get("p"))}
    return found


def _spf_all_qualifier(record):
    match = re.search(r"(?:^|\s)([-~?+]?)all\b", record)
    if not match:
        return None
    return (match.group(1) or "+") + "all"


def parse_spf(records):
    qualifiers = [q for q in (_spf_all_qualifier(r) for r in records) if q]
    return {
        "records": records,
        "found": bool(records),
        "multiple_records": len(records) > 1,
        "all_mechanism": qualifiers[0] if qualifiers else None,
        "strict": qualifiers[0] == "-all" if qualifiers else False,
    }


def parse_dmarc(records):
    if not records:
        return {
            "found": False, "record": None, "policy": None, "subdomain_policy": None,
            "pct": None, "rua": [], "enforced": False, "multiple_records": False,
        }
    record = records[0]
    tags = _parse_tag_list(record)
    policy = tags.get("p")
    pct = int(tags["pct"]) if tags.get("pct", "").isdigit() else 100
    rua = [addr.strip() for addr in tags.get("rua", "").split(",") if addr.strip()]
    multiple = len(records) > 1
    return {
        "found": True,
        "record": record,
        "policy": policy,
        "subdomain_policy": tags.get("sp", policy),
        "pct": pct,
        "rua": rua,
        # Multiple _dmarc TXT records make DMARC invalid per RFC 7489, regardless
        # of what any individual record says -- so this can't be "enforced".
        "enforced": (not multiple) and policy in ("reject", "quarantine") and pct == 100,
        "multiple_records": multiple,
    }


def _safe(fn, *args):
    try:
        return fn(*args), None
    except Exception as exc:
        return None, str(exc)


def build_output(domain):
    mx, mx_error = _safe(fetch_mx, domain)
    spf_records, spf_error = _safe(fetch_spf, domain)
    dmarc_records, dmarc_error = _safe(fetch_dmarc, domain)
    dkim_found, dkim_error = _safe(fetch_dkim, domain)

    errors = {
        "mx": mx_error, "spf": spf_error, "dmarc": dmarc_error, "dkim": dkim_error,
    }

    return {
        "domain": domain,
        "mx": {"records": mx or [], "found": bool(mx)},
        "spf": parse_spf(spf_records or []),
        "dmarc": parse_dmarc(dmarc_records or []),
        "dkim": {
            "selectors_checked": list(COMMON_DKIM_SELECTORS),
            "selectors_found": dkim_found or {},
            "found": bool(dkim_found),
        },
        "errors": {k: v for k, v in errors.items() if v},
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Query DNS for SPF/DMARC/MX/DKIM configuration.")
    parser.add_argument("target", help="Email address or bare domain to audit")
    args = parser.parse_args(argv)

    domain = domain_from_arg(args.target)
    if not is_valid_domain(domain):
        print(json.dumps({"fatal_error": "invalid_domain", "target": args.target}))
        return 1

    if not _dig_available():
        print(json.dumps({
            "fatal_error": "dig_not_found",
            "detail": "Install bind-utils/dnsutils (Linux) or use a host with dig "
                       "(macOS ships it by default); this check requires it.",
        }))
        return 1

    print(json.dumps(build_output(domain), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
