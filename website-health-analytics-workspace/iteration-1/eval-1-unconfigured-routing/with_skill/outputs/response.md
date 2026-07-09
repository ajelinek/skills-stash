# Signups drop on shadetreeit.biz — can't dig in yet, setup is incomplete

I went to investigate this using the website-health-analytics workflow, but this project isn't configured for it yet, so I stopped before pulling any data rather than guess at partial numbers.

## What I checked

I ran the skill's preflight (`check-setup.mjs`) against this project directory. Here's the state:

| Check | Status | Detail |
| --- | --- | --- |
| GA4 CLI (`google-analytics-cli`) | ✅ pass | v1.1.1 available |
| GSC CLI (`google-search-console-cli`) | ❌ fail | not installed |
| Google service-account credentials | ❌ fail | none configured |
| `gh` CLI | ✅ pass | v2.95.0, authenticated |
| `firebase` CLI | ✅ pass | v15.18.0, logged in as shadetreeit.biz@gmail.com |
| Committed config (`.claude/website-health-analytics.json`) | ❌ fail | doesn't exist |
| Local config (`.claude/website-health-analytics.local.json`) | ❌ fail | doesn't exist |

So GitHub and Firebase auth are already good to go, but I'm missing the Google Search Console CLI, a GCP service-account credential (needed for both GA4 and GSC access), and both project config files. Without those, I can't pull GA4/GSC data or run the cross-source correlation that would tell us *why* signups look down — and I don't want to hand you a guess dressed up as an analysis.

## What I need from you before I can continue

1. **Install the two companion CLI skills** (I won't run installs on my own):
   ```
   npx skills add Bin-Huang/google-analytics-cli
   npx skills add Bin-Huang/google-search-console-cli
   ```
   The GA4 one is already present; only the Search Console one is missing.

2. **A GCP service account with API access**, used for both GA4 and GSC:
   - Enable the *Google Analytics Data API* and *Google Search Console API* on a GCP project.
   - Create a service account, download its JSON key.
   - Grant that service account **Viewer** on the shadetreeit.biz GA4 property, and **Full** access on the shadetreeit.biz Search Console property.
   - Tell me the absolute path where you'll keep that JSON key (it stays out of git).

3. **A few config values** I don't have yet, so I can write `.claude/website-health-analytics.json`:
   - GA4 property ID for shadetreeit.biz
   - GSC site URL (I'm assuming `https://shadetreeit.biz/` — confirm or correct)
   - Timezone to use for daily bucketing
   - GitHub repo(s) that back this site, for deploy/commit correlation
   - Any anomaly-threshold overrides, or I'll use the skill's defaults

Once you give me those, I'll:
- Create `.claude/website-health-analytics.json` (committed) and `.claude/website-health-analytics.local.json` (gitignored) from the skill's templates,
- Add the local config to `.gitignore`,
- Rerun the preflight until it reports `ready: true`,
- Then actually run the signup-drop investigation: pull GA4/GSC/Firebase Auth/GitHub data, normalize it into one timeline, detect the anomaly, and trace it back to a specific deploy/commit if one lines up — with severity and confidence explicitly stated, not just a hunch.

I didn't fetch anything in the meantime (e.g., a quick, uncorrelated `firebase auth:export` count) because that would give a partial, out-of-context number that's easy to misread as "the answer" — better to do this properly once the setup's in place.
