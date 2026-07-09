# Firebase Auth Glue

`firebase auth:export` is the only source of truth for signup counts and
provider mix — GA4's signup event is directional only (see
[metric-definitions.md](metric-definitions.md)). This file covers exporting,
parsing, and diffing that data; it does not cover configuring Firebase Auth
itself (use `firebase-auth-basics` for that).

## Exporting users

```bash
firebase auth:export users.json --project <project-id>
```

Save exports into the gitignored working dir (see
[data-normalization.md](data-normalization.md)) using the
`firebase-users-*.json` naming convention so `normalize-timeseries.mjs`
picks them up automatically, e.g.:

```bash
firebase auth:export .claude/wha-work/firebase-users-2026-07-08.json --project my-app
```

## Record shape

Each entry in the exported array looks like:

```json
{
  "localId": "abc123",
  "email": "user@example.com",
  "createdAt": "1751500800000",
  "lastSignedInAt": "1751980800000",
  "providerUserInfo": [
    { "providerId": "password", "email": "user@example.com" }
  ]
}
```

Fields relevant to this skill:

- `localId` — the Firebase UID; joins to `accountCorrelations` (below).
- `createdAt` — epoch milliseconds, **as a string**. Convert to a number
  before use.
- `providerUserInfo[].providerId` — one entry per linked provider (e.g.
  `password`, `google.com`, `github.com`). A user can have more than one.

## Computing daily signups and provider mix

For each user record, convert `createdAt` to the configured timezone and
bucket by date. The count of users whose `createdAt` falls on a given day is
that day's `signups`. For `signupsByProvider`, use each user's **first**
`providerUserInfo[].providerId` (their original sign-up method) — a later
linked provider should not be double-counted as a separate signup.

This is exactly the shape `normalize-timeseries.mjs` expects from
`firebase-users-*.json` files: it reads the raw export, buckets by day in
the configured timezone, and produces `signups` and `signupsByProvider` per
day in the canonical dataset. You do not need to pre-aggregate before
handing the file to the script — hand it the raw export as downloaded.

## Diffing two exports

To find new signups, deletions, or provider changes between two points in
time, export twice and diff on `localId`:

- Present in the newer export only → new user (or re-verify against
  `createdAt` if the export cadence is long).
- Present in the older export only → deleted or disabled account.
- Same `localId`, different `providerUserInfo` → provider was linked or
  unlinked.

This is useful when an anomaly's `detect-anomalies.mjs` output flags a
signup drop and you want to confirm it's a real drop in new accounts rather
than an export timing artifact.

## PII caution

Exported user records contain email addresses and UIDs. Keep exports in the
gitignored working dir (`.claude/wha-work/` — see
[data-normalization.md](data-normalization.md)) and **never commit them**.
Treat them as sensitive for the duration of the session; there is no need to
retain them past the analysis that consumed them.

## Cohort-scoped investigation via `accountCorrelations`

`.claude/website-health-analytics.local.json` carries an
`accountCorrelations` array mapping `githubUsername` ↔ `firebaseUid` ↔
`googleEmail` ↔ `displayName`. Use it when an anomaly needs to be scoped to
a specific person or cohort — for example, confirming that a spike in
`password`-provider signups correlates with a specific teammate's test
account, or that a GitHub author who merged a suspect PR also shows up in
the affected user cohort. This mapping is manual and local; there is no
script that maintains it — update the file by hand as team membership
changes.
