# Automation mining analysis

Process mining applied to a person's own conversation history: instead of
staring at a business's event log to find repeatable processes, you're
staring at someone's Claude conversations to find the tasks they keep
re-doing by hand -- the ones that are variations on the same request,
spread across days or weeks, that never got turned into reusable
infrastructure.

This lens requires the full parsed export from the main skill file's Step
2 -- it needs the whole corpus to see a pattern actually repeat, not a
partial listing or manual rundown.

The end product is a report with two kinds of recommendations:

- **Skill candidates** -- a task the user does repeatedly with varying
  inputs, triggered on demand ("draft an outreach email for X", "build a
  dashboard for Y").
- **Schedule candidates** -- a task that should just run on a cadence
  without the user asking each time ("check my analytics every Monday",
  "summarize inbox daily").

Some clusters are genuinely both (a skill that should also run on a
schedule). Say so when that's the case rather than forcing a single bucket.

Two principles drive this lens: extraction is mechanical
(`scripts/parse_export.py` handles keywords/structure), but deciding "these
five conversations are one recurring workflow" requires actually
understanding the content -- that's your job, not the script's. And every
recommendation must cite the specific conversations (name + date) that
justify it; a recommendation with no evidence trail isn't trustworthy.

## Read and cluster

Read `conversations.jsonl`. For a small corpus, read it in one pass. For a
large one (hundreds+), page through in batches of ~50-100 and keep a
running list of candidate clusters as you go, similar to a map-reduce
summarization -- don't try to hold every conversation's full detail in
your head at once, just the emerging cluster themes.

A cluster is 2+ conversations that represent the same underlying
real-world task recurring over time, even if the wording differs each
time. Use `keywords`, `name`, `summary`, and `first_human_message`
together -- keyword overlap is a hint, not a verdict; two conversations
can share vocabulary and be unrelated, or use different words for the same
task. Cross-check candidate clusters against `memory_context.md`: if
Claude's own memory already independently describes a recurring project or
theme, that's corroborating evidence, and worth quoting.

A single one-off conversation is not a workflow. Resist the urge to
manufacture patterns out of noise to pad the report -- a short, honest
list beats a long, forced one.

## Decide skill vs. schedule vs. both

For each cluster, reason about the shape of the underlying task:

- **Leans schedule** -- the task is "fetch/check/report on X," the input
  doesn't really change between occurrences, and the user's own language
  suggests a cadence ("every day," "each week," "keep an eye on," "let me
  know when"). The value is in not having to remember to ask.
- **Leans skill** -- the task has the same shape each time but different
  inputs or content (different platform, different client, different
  dataset), and the user is actively driving each instance rather than
  wanting it to run unattended. The value is in not re-explaining the
  workflow from scratch every time.
- **Both** -- a skill that produces something, where a scheduled run of
  that skill on a cadence would also make sense (e.g., a reporting skill
  that could also just run weekly on its own).

Don't force every cluster into a recommendation. If a recurring topic is
really just the user learning/exploring (e.g., repeated questions about
how a tool works), say so and don't manufacture a skill for it -- the
report should distinguish "recurring workflow to automate" from "recurring
topic of interest," because only the former belongs in this report as a
recommendation.

## Report structure

Write the report as markdown. Use this structure:

```markdown
# Automation Mining Report: [account/export identifier or date range]

## Overview

- Conversations analyzed: N (date range: X to Y)
- Projects: N
- Data quality notes: [thin export / short date range / no memory_context / etc, or "none"]

## Recurring Workflows Found

### 1. [Workflow name]

**Evidence:** [conversation names + dates, at least 2]
**Pattern:** [what the user keeps doing, in their own domain terms]
**Recommendation:** [Skill | Scheduled task | Both]

- If skill: suggested name, one-line trigger description, what varies input-to-input
- If schedule: suggested cadence, what the task prompt would say
  **Why this and not the other:** [one sentence -- ties back to the skill-vs-schedule reasoning above]

[repeat per cluster, ranked with strongest evidence first]

## Quick Wins

Top 2-3 recommendations to act on first, and why those specifically
(strongest evidence, lowest effort to set up, or highest recurring cost of
doing it manually).

## Noted but not recommended

Recurring topics that showed up repeatedly but aren't workflow candidates
(exploration, learning, one-off troubleshooting of the same recurring
issue) -- worth naming so the user knows they were seen, without inflating
the recommendation list.
```

Then return to the main skill file's Step 4 (review) and Step 5 (optional
build offer).
