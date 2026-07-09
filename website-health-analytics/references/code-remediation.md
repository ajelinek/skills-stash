# Code Remediation

The 9-step engine that turns a confirmed anomaly into a concrete code fix.
This is the skill's differentiator — everything upstream (normalize, detect,
the 5-layer framework in
[analysis-rules.md](analysis-rules.md)) exists to feed this.

## Contents

1. [The 9 steps](#the-9-steps)
2. [Metric → suspect-file table](#metric--suspect-file-table)
3. [Confidence levels](#confidence-levels)
4. [Output template](#output-template)
5. [Growth Mode](#growth-mode)
6. [Worked example: regression](#worked-example-regression)
7. [Worked example: growth](#worked-example-growth)

## The 9 steps

1. **Confirm real.** If the anomaly's date is still inside a data-lag window
   (GA4 ~24–48h, GSC 2–3d), stop here and report "unconfirmed, re-check"
   rather than proceeding. This is layer 1 of
   [analysis-rules.md](analysis-rules.md); do not skip it just because a
   user is impatient for a fix.
2. **Localize.** Determine which dimension moved (layers 2–3 of
   analysis-rules.md — device, channel, page, country, query). This narrows
   which files are even plausible suspects in step 5.
3. **Window selection.** Pick the lookback window: `correlation.windowHours`
   for most metrics; use `correlation.gscWindowDays` instead when the
   anomaly is GSC-sourced (clicks, impressions, avgPosition), since GSC's
   own reporting lag means a shorter hour-based window would miss the
   actual cause.
4. **Run correlate-window.mjs.**
   ```bash
   node <skill_dir>/scripts/correlate-window.mjs \
     --config .claude/website-health-analytics.json \
     --date <anomaly-date> \
     [--window-hours N] [--repo org/name]
   ```
   See [github-correlation.md](github-correlation.md) for how to read the
   ranked `candidates` output.
5. **Inspect top candidates' diffs**, filtered by which files are plausible
   given the metric (the table below). Pull diffs with `gh api
   repos/{repo}/commits/{sha}` or `gh pr diff {n}` — see
   github-correlation.md's "follow-up commands" section.
6. **Cross-reference `accountCorrelations`** when the anomaly looks
   cohort-scoped (e.g. only affects one team's test accounts, or a PR
   author's own usage shows up in the affected data) — see
   [firebase-auth.md](firebase-auth.md).
7. **Form a hypothesis with explicit confidence** — see
   [Confidence levels](#confidence-levels) below. Never state a root cause
   without stating how confident it is; never fabricate a mechanism that
   the diff doesn't actually support.
8. **Output per finding**, using the [Output template](#output-template)
   below: metric observation → code-level cause (file:line, from the diff
   hunks you already pulled) → concrete fix → severity (P0–P3) → one
   paragraph explaining why. Structure it so it can be handed directly to a
   coding agent to implement.
9. **Growth Mode** when there's no regression to explain — see
   [below](#growth-mode).

## Metric → suspect-file table

Use this to filter which changed files in a candidate's diff are worth
inspecting first — it is a prioritization aid, not an exclusion list; a
surprising cause can still live outside this table.

| Metric | Suspect files/areas |
| --- | --- |
| `signups` | Auth/signup routes and components, Firebase init/config, redirect logic after signup |
| `conversions` | CTA components, checkout flow, event-binding attributes (ids/classes used by GA4 triggers), tag manager snippets |
| `clicks` / `impressions` | Meta tags, canonical tags, `robots.txt`, sitemap config, structured data, route deletions/renames, redirects |
| Performance-shaped drops (any metric, gradual decline) | New dependencies, large asset additions, render-blocking script/style additions |

## Confidence levels

State one of these explicitly with every hypothesis — never omit it, never
upgrade it past what the evidence supports:

- **High** — temporal proximity, the changed file(s), and the affected
  dimension all align (e.g. a CTA component was edited 3 hours before a
  conversions drop localized to the page that CTA lives on).
- **Medium** — two of the three align (e.g. temporal + file align, but the
  dimension localization was inconclusive).
- **Low** — proximity in time only, with no file or dimension corroboration.
  This is the honest answer when correlate-window.mjs surfaces a plausible
  candidate but the diff doesn't clearly touch anything relevant — say so
  rather than reaching for a more satisfying story.

## Output template

```
Metric: <metric> <direction> on <date> (<actual> vs baseline <baseline>, Δ<delta>)
Cause: <file>:<line> — <one-line description of what changed>
Fix: <patch snippet or precise instruction>
Severity: P0–P3
Confidence: High/Medium/Low — <what aligned>
Why: <one paragraph>
```

## Growth Mode

For "growth ideas, nothing broken" requests, or step 9 when no regression
was found:

- Skip steps 1, 3, and 4 (no anomaly to confirm, no window to correlate).
- Use the companion GSC skill's documented queries to pull top-impression,
  low-CTR queries and pages.
- Localize to specific pages (layer 3 of analysis-rules.md, applied
  proactively rather than reactively).
- Propose file-referenced improvements: missing schema markup, thin
  content, missing internal links, slow routes.
- Severity is always **P3**.
- Use the same [output template](#output-template) — a growth suggestion is
  structured identically to a regression finding, just without a "cause"
  tied to a recent diff.

## Worked example: regression

**Metric:** `conversions` dropped 38% on 2026-07-06 (actual 26 vs baseline 42).

1. Confirm real — GA4 data for 07-06 is now >48h old; drop persists on
   re-check. Confirmed.
2. Localize — GA4 breakdown by page shows the drop concentrated entirely on
   `/pricing`; other pages flat.
3. Window — `correlation.windowHours` (48h) lookback from 07-06.
4. `correlate-window.mjs --date 2026-07-06` returns, closest first: a
   merged PR #482 "Refactor pricing CTA markup", merged 9 hours before the
   anomaly window's affected sessions began.
5. `gh pr diff 482` shows `src/components/PricingCta.astro` changed —
   `id="pricing-upgrade-cta"` was removed during the markup refactor (the
   button kept its visual style but lost the id).
6. `accountCorrelations` — not needed; this isn't cohort-scoped.
7. Hypothesis: the GA4 conversion event is bound via a GTM trigger on
   `#pricing-upgrade-cta`; removing the id means the button no longer fires
   the event even though clicks on it still happen. Confidence: **High** —
   temporal (9h before), file (the exact CTA component for the localized
   page), and dimension (`/pricing`-only drop) all align.
8. Output:
   ```
   Metric: conversions dropped 38% on 2026-07-06 (26 vs baseline 42, Δ-0.38)
   Cause: src/components/PricingCta.astro:14 — id="pricing-upgrade-cta" was
     removed in PR #482's markup refactor
   Fix: restore the id on the CTA button:
     <button id="pricing-upgrade-cta" class="btn-primary">Upgrade</button>
   Severity: P0
   Confidence: High — temporal, file, and dimension all align
   Why: the GA4 conversion event fires off a GTM trigger keyed to this id;
     removing it during an otherwise-cosmetic refactor silently stopped
     conversion tracking without breaking the button's visible behavior.
   ```

## Worked example: growth

**Trigger:** "any growth ideas from search data?" — no active regression.

1–4. Skipped (Growth Mode).
5. GSC query (via the companion skill's documented pivot) for top-impression,
   low-CTR pages over the trailing 28 days surfaces `/docs/faq` — high
   impressions, CTR well below the site average, average position 4.2 (good
   ranking, but not converting impressions into clicks).
6. Not applicable.
7. Hypothesis: the page ranks well but its search snippet is a plain meta
   description with no rich result, so it doesn't stand out against
   competitors that show FAQ rich snippets. Checking
   `src/pages/docs/faq.astro` confirms no `FAQPage` JSON-LD is present.
   Confidence: **Medium** — the page-level signal (high impressions, low
   CTR, no FAQ schema present) is clear, but CTR improvement from adding
   schema is an estimate, not a guarantee.
8. Output:
   ```
   Metric: /docs/faq — high impressions, low CTR relative to its position
     (avg position 4.2, trailing 28d)
   Cause: src/pages/docs/faq.astro — no FAQPage structured data; the page
     doesn't qualify for a rich FAQ snippet in search results
   Fix: add FAQPage JSON-LD using the astro-seo skill's FAQ component
     (see astro-seo's JsonLd.astro) with this page's existing Q&A content
   Severity: P3
   Confidence: Medium — page-level signal is clear; CTR lift is an estimate
   Why: this page already ranks well (position 4.2) but its plain snippet
     doesn't compete visually with rich-result competitors in the same
     results page; FAQ schema is a low-risk, high-plausibility CTR lever.
   ```
