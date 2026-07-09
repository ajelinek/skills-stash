---
name: process-mining
description: Mines a Claude.ai/Cowork data export (conversations.json, memories.json, projects/*.json from Settings > Account > Export Data) to find recurring real-world workflows the user keeps doing by hand across conversations, then recommends specific Cowork skills to build and scheduled tasks to automate. Use this whenever the user wants to analyze their Claude conversation history, export, or usage to figure out what should be turned into a skill or a recurring/scheduled task -- phrases like "what should I automate", "what skills should I build", "audit my Claude usage", "process management", "find patterns in my conversations", or when they hand over a data export folder (containing conversations.json) and ask what to do with it. Requires an actual Claude data export folder as input -- if the user hasn't provided or pointed to one, ask for it before proceeding rather than guessing.
---

# Process Mining: Claude Export -> Skill & Schedule Recommendations

## What this is

This is process mining applied to a person's own conversation history: instead of
staring at a business's event log to find repeatable processes, you're staring at
someone's Claude conversations to find the tasks they keep re-doing by hand -- the
ones that are variations on the same request, spread across days or weeks, that
never got turned into reusable infrastructure.

The end product is a report with two kinds of recommendations:

- **Skill candidates** -- a task the user does repeatedly with varying inputs,
  triggered on demand ("draft an outreach email for X", "build a dashboard for Y").
- **Schedule candidates** -- a task that should just run on a cadence without the
  user asking each time ("check my analytics every Monday", "summarize inbox daily").

Some clusters are genuinely both (a skill that should also run on a schedule). Say so
when that's the case rather than forcing a single bucket.

## Design lineage (why it's built this way)

This skill's shape borrows from how tools like `code-insights` (melagiri/code-insights)
and `cc-insights`/`/insights` in the `awesome-claude-code-toolkit` ecosystem analyze AI
coding sessions: parse the raw logs deterministically first, then use an LLM pass to
extract structured signal (decisions, friction, recurring patterns), then synthesize
across the whole corpus into a report and generate concrete artifacts (rules, in their
case; skills and schedules, in ours). None of those tools are dependencies here --
they work off Claude Code's local `~/.claude/projects/*.jsonl` session logs, a
different file format from the account-level export this skill consumes. The
architecture is the useful part, not the code.

Two ideas carried over deliberately:

1. **Deterministic extraction, then LLM synthesis.** Don't try to hand-code a
   clustering algorithm that guesses what counts as "the same workflow" -- extracting
   keywords and structure is mechanical (the bundled script does that), but deciding
   "these five conversations about outreach emails to different platforms are one
   recurring workflow" requires actually understanding the content. That's your job,
   not the script's.
2. **Evidence-backed output, not vibes.** Every recommendation in the report must cite
   the specific conversations (name + date) that justify it. A recommendation with no
   evidence trail is not trustworthy and the user has no way to sanity-check it.

## Step 1: Confirm you have a real export, not something else

This skill requires the account-level data export you get from claude.ai or Cowork
under **Settings > Account > Export Data**. That zip, once unzipped, contains
`conversations.json` at minimum, usually alongside `memories.json`, `projects/*.json`,
and `users.json`.

This is a **different format** from a Claude Code CLI session log
(`~/.claude/projects/*.jsonl`). If the user says "Claude Code data export" but what
they actually hand you is CLI session JSONL files, or a single conversation transcript,
stop and clarify -- this skill's parser expects `conversations.json` and will not work
on those formats.

If you don't know the export folder's path yet, ask the user rather than guessing at
one. Don't proceed on a folder that's missing `conversations.json`.

## Step 2: Run the parser

Raw `conversations.json` can be huge (every message, every tool call, every thinking
block). Reading it directly wastes context and buries the signal. Run the bundled
script to normalize it first:

```bash
python3 scripts/parse_export.py --export-dir <path-to-unzipped-export> --out-dir <workdir>
```

This writes four files to `<workdir>`:

- `conversations.jsonl` -- one compact JSON object per conversation (name, summary,
  dates, message counts, first human message, tool names used, extracted keywords),
  sorted oldest to newest.
- `projects_index.json` -- project uuid -> name/description/conversation_count.
- `memory_context.md` -- Claude's own synthesized memory of the user, verbatim, if the
  export included `memories.json`. This is high-value: Claude has already noticed
  recurring themes across the user's conversations. Treat it as a second opinion to
  cross-check your own clustering against, not ground truth to defer to blindly.
- `stats.json` -- corpus size, date range, project coverage.

Check `stats.json` first. If `conversation_count` is very small (say, under 10) or the
date range is only a few days, say so plainly in the report -- recurring-pattern
detection needs enough history to actually see a pattern repeat, and a thin export
means low-confidence output, not no output.

Note: in current export formats, conversations often don't carry a reliable
`project_uuid` link back to `projects_index.json` (check `conversations_with_project`
in `stats.json` -- it's frequently 0). Don't assume project grouping works; fall back
to `memory_context.md`'s per-project sections and keyword/topic clustering instead.

## Step 3: Read and cluster

Read `conversations.jsonl`. For a small corpus, read it in one pass. For a large one
(hundreds+), page through in batches of ~50-100 and keep a running list of candidate
clusters as you go, similar to a map-reduce summarization -- don't try to hold every
conversation's full detail in your head at once, just the emerging cluster themes.

A cluster is 2+ conversations that represent the same underlying real-world task
recurring over time, even if the wording differs each time. Use `keywords`, `name`,
`summary`, and `first_human_message` together -- keyword overlap is a hint, not a
verdict; two conversations can share vocabulary and be unrelated, or use different
words for the same task. Cross-check candidate clusters against `memory_context.md`:
if Claude's own memory already independently describes a recurring project or theme,
that's corroborating evidence, and worth quoting.

A single one-off conversation is not a workflow. Resist the urge to manufacture
patterns out of noise to pad the report -- a short, honest list beats a long, forced
one.

## Step 4: Decide skill vs. schedule vs. both

For each cluster, reason about the shape of the underlying task:

- **Leans schedule** -- the task is "fetch/check/report on X," the input doesn't
  really change between occurrences, and the user's own language suggests a cadence
  ("every day," "each week," "keep an eye on," "let me know when"). The value is in
  not having to remember to ask.
- **Leans skill** -- the task has the same shape each time but different inputs or
  content (different platform, different client, different dataset), and the user is
  actively driving each instance rather than wanting it to run unattended. The value
  is in not re-explaining the workflow from scratch every time.
- **Both** -- a skill that produces something, where a scheduled run of that skill on
  a cadence would also make sense (e.g., a reporting skill that could also just run
  weekly on its own).

Don't force every cluster into a recommendation. If a recurring topic is really just
the user learning/exploring (e.g., repeated questions about how a tool works), say so
and don't manufacture a skill for it -- the report should distinguish "recurring
workflow to automate" from "recurring topic of interest," because only the former
belongs in this report as a recommendation.

## Report structure

Write the report as markdown. Use this structure:

```markdown
# Process Mining Report: [account/export identifier or date range]

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
**Why this and not the other:** [one sentence -- ties back to Step 4's reasoning]

[repeat per cluster, ranked with strongest evidence first]

## Quick Wins
Top 2-3 recommendations to act on first, and why those specifically (strongest
evidence, lowest effort to set up, or highest recurring cost of doing it manually).

## Noted but not recommended
Recurring topics that showed up repeatedly but aren't workflow candidates (exploration,
learning, one-off troubleshooting of the same recurring issue) -- worth naming so the
user knows they were seen, without inflating the recommendation list.
```

After presenting the report, offer to actually build the top recommendation --
either invoke `skill-creator` for a skill candidate, or set up a scheduled task
directly for a schedule candidate, rather than leaving the user to do it themselves.

## Handling sensitive content

This export contains the user's real conversation history, which may include
business details, personal context, and information about third parties. Analyze it
within this session to produce the report; don't restate large verbatim chunks of
private conversation content beyond what's needed as evidence (a conversation name,
date, and one-line excerpt is enough -- not a full quote).
