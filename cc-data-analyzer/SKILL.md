---
name: cc-data-analyzer
description: >
  Analyzes a user's Claude.ai/Cowork data export (conversations.json,
  memories.json, projects/*.json from Settings > Account > Export Data) and
  turns a sprawling conversation history into concrete next steps through
  two lenses on the same data: a workspace reorganization plan (which chats
  belong in which Projects, what folder/file structure each Project needs)
  or an automation report (which recurring workflows should become a Skill
  vs. a scheduled task, with evidence). Ask the user which lens they want,
  or run both. Trigger on "analyze my Claude chats/projects", "help me
  organize my Claude workspace", "what skills should I build", "audit my
  Claude usage", "what should I automate", "reorganize my chats", "find
  patterns in my conversations", "process management", or when the user
  hands over a data export folder and asks what to do with it. Full-strength
  analysis (and the automation lens specifically) requires an actual data
  export folder containing conversations.json -- if the user hasn't
  provided or pointed to one, ask for it rather than guessing.
---

# CC Data Analyzer

## What this is

One skill, two lenses on the same data. A Claude.ai/Cowork data export
holds everything: every conversation, every project, Claude's own
synthesized memory of the user. This skill mines it two different ways,
sharing the same parsing and clustering groundwork:

- **Reorganization** -- how should the *existing* chats/projects be
  restructured? Which chats belong together in a Project, what should that
  Project be named/described, what file structure should it hold.
- **Automation mining** -- what recurring *workflow*, done by hand across
  many chats, should become a Skill (triggered on demand) or a scheduled
  task (runs on a cadence) going forward.

Both always stop at a reviewable plan/report. Neither reorganizes,
deletes, or builds anything without the user explicitly saying so afterward.

## Step 1: Get the data

The real analytical power here (clustering, evidence-backed
recommendations) depends on the actual account-level data export from
claude.ai/Cowork -- **Settings > Account > Export Data**. Once unzipped it
contains `conversations.json` at minimum, usually alongside
`memories.json`, `projects/*.json`, and `users.json`.

Check, in order:

1. **A data export folder** -- if the user has one, ask for its path. This
   is the only tier that supports both lenses at full strength, and the
   *only* tier automation mining (Step 3, second option) accepts at all.
2. **Tool access in this environment** -- if no export, search (`ToolSearch`
   or equivalent) for a tool that can list the user's conversations/projects
   directly. This can support reorganization analysis at reduced fidelity,
   but not automation mining -- that lens needs the whole parsed corpus to
   see a pattern actually repeat, not a live listing.
3. **Manual rundown** -- if neither exists, ask the user to describe their
   current chats/projects directly: rough count, names, what each is about,
   which are active vs. dormant. Only reorganization analysis is possible
   this way, and only as well as the description given -- say so plainly.

Don't proceed on a guessed-at inventory. If the user wants automation
mining but only has tiers 2 or 3, say plainly that lens needs a real export
and offer reorganization analysis instead (or wait for the export).

This is a **different format** from a Claude Code CLI session log
(`~/.claude/projects/*.jsonl`) or a single pasted conversation transcript.
If the user says "export" but hands you one of those instead, stop and
clarify -- the parser below expects `conversations.json` and won't work on
those formats.

## Step 2: Run the parser (if a real export is available)

Raw `conversations.json` can be huge -- every message, every tool call,
every thinking block. Reading it directly wastes context and buries the
signal. Run the bundled script once, regardless of which lens (or both)
you're about to run:

```bash
python3 scripts/parse_export.py --export-dir <path-to-unzipped-export> --out-dir <workdir>
```

This writes four files to `<workdir>`, shared by both lenses:

- `conversations.jsonl` -- one compact JSON object per conversation (name,
  summary, dates, message counts, first human message, tool names used,
  extracted keywords, project link if present), sorted oldest to newest.
- `projects_index.json` -- project uuid -> name/description/conversation_count.
- `memory_context.md` -- Claude's own synthesized memory of the user,
  verbatim, if the export included `memories.json`. High-value: Claude has
  already noticed recurring themes. Treat it as a second opinion to
  cross-check your own clustering against, not ground truth.
- `stats.json` -- corpus size, date range, project coverage.

Check `stats.json` first. If `conversation_count` is very small (under 10)
or the date range is only a few days, say so plainly before producing
either lens's output -- thin data means low-confidence recommendations,
not no output. Also check `conversations_with_project` -- it's frequently
0 even when projects exist, so don't assume the `project_uuid` link works;
fall back to `memory_context.md`'s per-project sections and keyword/topic
clustering.

If Step 1 landed on tier 2 or 3 (no real export), skip this step and work
directly from whatever data you gathered.

## Step 3: Pick the lens

Ask the user which they want, unless their original request already made
it obvious:

- **"Which chats go where / how should my workspace be structured"** ->
  reorganization, see
  [references/reorganization.md](references/reorganization.md).
- **"What should I automate / what skills should I build"** -> automation
  mining, see
  [references/automation-mining.md](references/automation-mining.md).
- **Both** -- run both; they share Steps 1-2's data, so this is one export
  parsed once and read through two different lenses. Present them as two
  clearly separated sections (or two separate deliverables), not merged
  into one document -- they answer different questions and get
  reviewed/actioned independently.

## Step 4: Present and get explicit review

Whichever lens (or both), stop after presenting the output. Ask the user
to confirm, edit, or reject pieces of it. Nothing in Step 5 happens until
they've reacted -- a plan/report that's merely "presented" is not the same
as one that's "approved."

## Step 5: Offer to act (opt-in, gated -- never automatic)

Only after Step 4's review, and the two lenses lead to different follow-ups:

- **Reorganization plan approved** -> executing it (creating/renaming
  Projects, moving chats, setting up files) means driving the Claude.ai UI
  directly, which requires a browser-automation / computer-use tool to be
  available and enabled in this environment, with the user logged into
  Claude in the browser it controls. Without that tool available and
  enabled, this step cannot run at all -- hand over the plan as a checklist
  instead.
  1. Search for such a tool first (e.g. via `ToolSearch`). Don't tell the
     user it's available without having actually confirmed it.
  2. If unavailable, say so and stop -- hand over the reviewed plan as a
     checklist for the user to execute by hand.
  3. If available, ask explicitly whether they want you to carry out the
     approved plan. A prior approval from an earlier session doesn't carry
     over -- ask again each time, and act only on the plan as reviewed in
     Step 4, not a re-interpretation of it.
  4. If yes, work through it one Project at a time -- see
     [references/browser-execution.md](references/browser-execution.md).
- **Automation mining report approved** -> no browser needed. Offer to
  build the top recommendation directly: invoke `skill-creator` for a
  skill candidate, or set up a scheduled task for a schedule candidate.

## Handling sensitive content

A real data export contains the user's actual conversation history, which
may include business details, personal context, and information about
third parties. Analyze it within this session to produce the plan/report;
don't restate large verbatim chunks of private conversation content beyond
what's needed as evidence (a conversation name, date, and one-line excerpt
is enough -- not a full quote).

## Non-goals

- Not a general chat summarizer -- the output is a plan or a report, not a
  digest of what was discussed.
- Not a bulk-delete tool -- this skill only ever proposes moves, groupings,
  new structure, skills, or schedules; deletion isn't part of any step.
- Not a substitute for the user's own judgment on naming/scope -- both
  lenses produce a strong starting proposal, not a final answer.
