# Data Normalization

The canonical dataset contract that `normalize-timeseries.mjs` produces, and
every downstream script (`detect-anomalies.mjs`) and reference file assumes.

## Contents

1. [Running the script](#running-the-script)
2. [Raw-file naming convention](#raw-file-naming-convention)
3. [The canonical dataset](#the-canonical-dataset)
4. [Timezone rules](#timezone-rules)
5. [Null vs. zero](#null-vs-zero)
6. [Working directory](#working-directory)

## Running the script

```bash
node <skill_dir>/scripts/normalize-timeseries.mjs \
  --config .claude/website-health-analytics.json \
  --in .claude/wha-work \
  [--out .claude/wha-work/daily-metrics.json]
```

This is a pure transform — no network or CLI calls. It reads whatever raw
JSON files are present in `--in`, tolerates missing sources (warns and
continues rather than failing), and prints the canonical dataset to stdout.
If `--out` is given, it also writes the same JSON to that file.

## Raw-file naming convention

Save fetched data into the working dir using these prefixes so the script
can identify each source:

| Prefix | Source | Produced by |
| --- | --- | --- |
| `ga4-*.json` | GA4 report output | `google-analytics-cli`'s documented commands |
| `gsc-*.json` | GSC query output | `google-search-console-cli`'s documented commands |
| `firebase-users-*.json` | Raw `firebase auth:export` output | `firebase auth:export` — see [firebase-auth.md](firebase-auth.md) |
| `github-events.json` | Deploy/PR/commit candidates | `correlate-window.mjs`, or raw `gh` output |

Any other filename in the directory is ignored. Multiple files sharing a
prefix (e.g. several `ga4-*.json` pulls for different date ranges) are all
read and merged.

## The canonical dataset

One JSON object keyed by ISO date, in the configured timezone:

```json
{
  "meta": {
    "timezone": "America/New_York",
    "generatedAt": "2026-07-08T12:00:00Z",
    "sources": ["ga4", "gsc", "firebase"],
    "warnings": []
  },
  "days": {
    "2026-07-01": {
      "sessions": 1234,
      "activeUsers": 1100,
      "conversions": 41,
      "newUsers": 300,
      "clicks": 220,
      "impressions": 9100,
      "ctr": 0.024,
      "avgPosition": 12.3,
      "signups": 38,
      "signupsByProvider": { "google.com": 20, "password": 18 },
      "deploys": [
        { "sha": "a1b2c3", "at": "2026-07-01T14:22:00Z", "source": "deployment|run|pr" }
      ]
    }
  }
}
```

`meta.sources` lists which of `ga4` / `gsc` / `firebase` / `github` actually
had at least one raw file present. `meta.warnings` records anything skipped
(missing source, unparseable file, etc.) — check it before trusting a
"clean" run. The full JSON Schema for this shape lives at
[examples/daily-metrics.schema.json](../examples/daily-metrics.schema.json).

## Timezone rules

- GA4 and GSC report dates are already in the property's own timezone —
  pass them through unchanged; do not re-convert.
- Firebase (`createdAt`) and GitHub (`at`) timestamps are UTC epoch
  values/ISO strings — convert them to the configured `timezone` before
  bucketing into a day.
- All three sources must land in the same local calendar day for the
  cross-source anomaly correlation to mean anything — this is why the
  conversion step matters, not just cosmetics.

## Null vs. zero

- A day with **no data reported at all** for a metric (the source has
  nothing for that date, e.g. GA4 hasn't processed it yet) → `null`.
- A day where the source explicitly reported the day **with zero rows**
  (e.g. GSC returned the date with zero clicks) → `0`.

Never zero-fill a day that simply wasn't in the raw response — that would
make a data-lag gap look like a real drop to `detect-anomalies.mjs`. Only
zero-fill when the source itself vouched for the day.

## Working directory

Use a gitignored working directory in the target project for all raw pulls
and the normalized output:

```
.claude/wha-work/
```

Add it to `.gitignore` alongside the local config file during setup (see
[setup.md](setup.md)). It holds raw GA4/GSC/Firebase/GitHub JSON, the
normalized `daily-metrics.json`, and any intermediate anomaly/correlation
output — nothing in it should ever be committed, both because it's
regenerable and because Firebase exports contain PII (see
[firebase-auth.md](firebase-auth.md)).
