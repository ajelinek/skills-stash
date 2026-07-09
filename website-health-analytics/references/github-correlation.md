# GitHub Correlation

`correlate-window.mjs` finds candidate deploys, workflow runs, PRs, and
commits that precede a confirmed anomaly. This file explains what it runs,
why, how to read its output, and the follow-up commands you run yourself
afterward — it does not repeat the script's own `--help` output.

## Contents

1. [Running it](#running-it)
2. [Why gh, and why four surfaces](#why-gh-and-why-four-surfaces)
3. [The lookback window](#the-lookback-window)
4. [Reading the output](#reading-the-output)
5. [What the script does NOT do](#what-the-script-does-not-do)

## Running it

```bash
node <skill_dir>/scripts/correlate-window.mjs \
  --config .claude/website-health-analytics.json \
  --date 2026-07-08 \
  [--window-hours 48] [--buffer-hours 6] [--repo org/name]
```

`--date` is the anomaly's ISO date (from `detect-anomalies.mjs` output).
`--window-hours` and `--buffer-hours` default to
`correlation.windowHours` / `correlation.bufferHours` from the config file
if omitted. `--repo` restricts to one repo; otherwise every repo in
`githubRepos` is queried.

## Why `gh`, and why four surfaces

There is no single `gh` command that returns "everything that shipped in a
time window" — deployments, CI runs, merged PRs, and raw commits are four
separate surfaces with no unified API, and there is no native `gh
deployment` command at all (deployments only exist via the REST API). The
script shells to `gh` four times per repo to cover all of them:

1. **Deployments** — `gh api repos/{repo}/deployments --jq ...`, preferring
   `environment=production` entries when present, falling back to all
   deployments if none are tagged production.
2. **Workflow runs** — `gh run list --repo {repo} --status success --json
   databaseId,workflowName,conclusion,createdAt,headSha,headBranch --limit
   50`, filtered to the window client-side.
3. **Merged PRs** — `gh pr list --repo {repo} --state merged --search
   "merged:{from}..{to}" --json
   number,title,mergedAt,mergeCommit,author,files --limit 50`.
4. **Raw commits** — `gh api
   "repos/{repo}/commits?since={from}&until={to}" --jq ...` (sha, author,
   date, message), which catches anything pushed directly without a PR.

A repo that never uses GitHub Deployments (common) will simply return no
candidates from surface 1 — the script warns and continues per-endpoint
rather than failing the whole run.

One quiet failure mode to know about: `gh pr list --search` returns an empty
list (exit 0) even for a nonexistent or misconfigured repo, so surface 3
produces no warning when the repo name is wrong. If **all four** surfaces
come back empty for a window where you know changes shipped, verify the
`githubRepos` entries in the config before concluding nothing was deployed.

## The lookback window

Candidate causes must **precede** the effect, so the window looks backward
from the anomaly date, not forward:

```
[anomalyDate 00:00 local - windowHours, anomalyDate 23:59 local + bufferHours]
```

The buffer on the end absorbs clock skew between when GA4 records a session
and when CI actually finished deploying — a deploy that completes at
23:50 local shouldn't be excluded just because the anomaly's affected
sessions were logged a few minutes into the next UTC day.

## Reading the output

```json
{
  "window": { "from": "...", "to": "...", "hours": 48 },
  "candidates": [
    {
      "type": "deployment|workflow_run|pr|commit",
      "repo": "org/repo",
      "sha": "...",
      "prNumber": 123,
      "title/message": "...",
      "author": "...",
      "at": "...",
      "hoursBeforeAnomaly": 14.5,
      "filesChangedCount": 7
    }
  ]
}
```

Candidates are ranked **closest-preceding-the-anomaly first** —
`hoursBeforeAnomaly` ascending. Start your diff inspection at the top of the
list; a candidate 40 hours before the anomaly is a much weaker suspect than
one 2 hours before it, all else equal. `filesChangedCount` is a cheap signal
for triage — a one-line commit is a faster check than a 200-file dependency
bump, but don't rule out the latter without looking.

## What the script does NOT do

`correlate-window.mjs` never fetches diffs — matching a candidate's changed
files against the metric→suspect-file table
([code-remediation.md](code-remediation.md) step 5) is the agent's job,
after correlation. Pull diffs yourself:

```bash
gh api repos/{repo}/commits/{sha}          # files + patch hunks for a commit
gh pr diff {n}                              # full diff for a merged PR
gh pr view {n} --json files,title,body      # PR metadata + file list without the diff body
```

Use `gh api repos/{repo}/commits/{sha}` when the candidate is a commit or
deployment SHA; use `gh pr diff {n}` / `gh pr view {n}` when the candidate
is a PR. For workflow runs, resolve `headSha` back to a commit or PR first.
