# Setup

First-run workflow to get `check-setup.mjs` to report `ready: true`. Run
through these steps in order; each one unblocks the next.

## Contents

1. [Install the companion skills](#1-install-the-companion-skills)
2. [Authenticate `gh`](#2-authenticate-gh)
3. [Authenticate `firebase`](#3-authenticate-firebase)
4. [Create a GCP service account](#4-create-a-gcp-service-account)
5. [Create the config files](#5-create-the-config-files)
6. [Rerun the preflight](#6-rerun-the-preflight)
7. [Optional: schedule the daily health check](#7-optional-schedule-the-daily-health-check)

## 1. Install the companion skills

This skill cannot talk to GA4 or GSC on its own:

```bash
npx skills add Bin-Huang/google-analytics-cli
npx skills add Bin-Huang/google-search-console-cli
```

Both ship their own SKILL.md with full command documentation — read those
when you get to the fetch step of the pipeline, not this file. Verify they
installed correctly once you've completed step 6 below (`check-setup.mjs`
checks both binaries).

## 2. Authenticate `gh`

```bash
gh auth status
```

If not authenticated:

```bash
gh auth login
```

`gh` is used for deploy/commit/PR correlation
(see [github-correlation.md](github-correlation.md)) and needs no project-specific
configuration beyond being logged in with access to the repos listed in
`githubRepos`.

## 3. Authenticate `firebase`

```bash
firebase login
```

On a headless machine (no browser available), use:

```bash
firebase login --no-localhost
```

Confirm the active project matches the one whose Auth users you want to
export:

```bash
firebase projects:list
firebase use <project-id>
```

## 4. Create a GCP service account

GA4 and GSC access both go through a single service account:

1. Create (or pick) a Google Cloud project.
2. Enable two APIs on that project:
   - **Google Analytics Data API**
   - **Google Search Console API**
3. Create a service account in that project.
4. Create and download a JSON key for it.
5. Grant the service account's email access on both properties:
   - **GA4 property** — add it as a user with **Viewer** role (GA4 Admin →
     Property Access Management).
   - **GSC property** — add it as an owner/user with **Full** access
     (Search Console → Settings → Users and permissions). GSC does not have
     a read-only "Viewer" tier for API access the same way GA4 does — grant
     Full.

Keep the downloaded JSON key out of version control. Its path goes in the
local config file (step 5) as `googleApplicationCredentials`.

## 5. Create the config files

Copy the two templates into the target project and fill in real values —
ask the user for anything you don't already know (site URLs, GA4 property
ID, repo names, timezone, credential path, identity mappings):

```bash
mkdir -p .claude
cp <skill_dir>/examples/website-health-analytics.json .claude/website-health-analytics.json
cp <skill_dir>/examples/website-health-analytics.local.json .claude/website-health-analytics.local.json
```

Edit both files:

- `.claude/website-health-analytics.json` — **committed**. `timezone`,
  `sites[]` (`name`, `gscSiteUrl`, `ga4PropertyId`), `githubRepos`,
  `correlation` windows, `anomalyThresholds`. None of these values are
  secrets.
- `.claude/website-health-analytics.local.json` — **gitignored**.
  `googleApplicationCredentials` (absolute path to the service-account JSON
  key from step 4) and `accountCorrelations` (GitHub username ↔ Firebase UID
  ↔ Google email ↔ display name, used for cohort-scoped investigation — see
  [firebase-auth.md](firebase-auth.md)).

Add the local file to `.gitignore`:

```bash
echo ".claude/website-health-analytics.local.json" >> .gitignore
```

## 6. Rerun the preflight

```bash
node <skill_dir>/scripts/check-setup.mjs \
  --config .claude/website-health-analytics.json \
  --local-config .claude/website-health-analytics.local.json
```

Fix whichever checks report `fail` and rerun until `ready` is `true`. A
`warn` (e.g. `firebaseCli` version check skipped for speed) does not block
`ready`.

## 7. Optional: schedule the daily health check

This skill does not own scheduling. Once setup is complete, optionally wire
[daily-health-check.md](daily-health-check.md)'s workflow to a recurring job
— the user's own cron, CI schedule, or the `/schedule` skill if available.
