---
name: cc-data-analyzer
description: >
  Analyzes a user's existing Claude conversations and projects to recommend a
  cleaner setup: what custom Skills would remove recurring manual work, what
  Projects should exist, how current chats should be grouped into them, and
  what description and file/folder structure each Project needs. Always stops
  after presenting the plan for review — never reorganizes anything on its
  own. Only if the user explicitly asks, and only after confirming a
  browser-automation tool is actually available in this environment, offers to
  carry out the plan directly in the Claude.ai UI. Trigger on "analyze my
  Claude chats/projects", "help me organize my Claude workspace", "what skills
  should I create", "audit/clean up my projects", "reorganize my chats", or
  similar requests to turn a sprawling set of conversations into structure.
---

# CC Data Analyzer

This is a two-path skill. **Path A (analysis and recommendations) always
runs and is the deliverable on its own.** Path B (using a browser tool to
execute the plan) is optional, gated, and only ever offered — never assumed.

Do not skip straight to recommendations. Confirm you actually have the data
in hand first — a plan built on a guessed-at inventory is worse than no plan.

## Path A: Analyze and recommend

### Step 1: Get the data

There's no single standard way to pull a user's Claude conversation/project
history, so ask rather than assume. Check, in order:

1. **Tool access in this environment** — search for a tool that can list or
   export the user's Claude conversations/projects (via `ToolSearch` or
   equivalent). If one exists, use it.
2. **A data export** — Claude.ai's Settings -> Account lets a user export
   their data as a JSON/HTML bundle. If the user has one, ask for the file
   path.
3. **Manual rundown** — if neither of the above is available, ask the user to
   describe their current chats/projects directly: rough count, names, what
   each is about, which ones are active vs. dormant. Say plainly that the
   plan will only be as good as this input.

Don't proceed to Step 2 until you have real data by one of these paths —
flag it to the user if all three come up empty rather than inventing content.

### Step 2: Understand it

Work through the data looking for:

- **Topic clusters** — chats that are really the same kind of work spread
  across multiple threads (a sign they belong in one Project).
- **Recurring patterns** — the same multi-step process being manually
  re-explained or re-solved chat after chat (a sign a Skill should exist).
- **Existing structure vs. reality** — where current Projects (if any) no
  longer match what the chats inside them are actually about.
- **Stale vs. active** — old one-off threads that don't need a home vs. live
  work that does.

Keep this analysis visible to the user in summary form — don't jump straight
from raw data to a polished plan with no visibility into the reasoning.

### Step 3: Produce the plan

Output a single structured plan, in this order:

1. **Skills to create** — for each: proposed name, one-line trigger
   description, and *why* (the specific repeated pattern it would capture).
2. **Projects** — for each: proposed name, description, and which existing
   chats should move into it.
3. **File/folder structure per project** — what reference files, instructions,
   or knowledge docs each Project should hold, and why.
4. **Leftovers** — chats that don't fit any recommended Project; say what you
   propose doing with them (archive, leave standalone, etc.) rather than
   silently dropping them from the plan.

### Step 4: Get explicit review

Present the plan and stop. Ask the user to confirm, edit, or reject pieces of
it. Nothing in Path B happens until they've reacted to the plan — a plan
that's merely "presented" is not the same as one that's "approved."

## Path B: Offer to execute (opt-in, gated — never automatic)

Only after Step 4's plan has been reviewed:

1. **Check availability first.** Search for a browser-automation /
   computer-use tool (e.g. via `ToolSearch`) in this environment. Do not tell
   the user it's available without having actually confirmed it.
2. **If unavailable:** say so, and stop here — hand over the reviewed plan as
   the deliverable (e.g. a checklist) for the user to execute by hand.
3. **If available:** ask the user, explicitly, whether they want you to use it
   to carry out the approved plan (create the Projects, move the chats, set
   descriptions, set up files/folders) directly in the Claude.ai UI. Make
   clear this requires them to be logged into Claude in the browser the tool
   controls.
4. **Never do this automatically.** A prior approval in an earlier session
   doesn't carry over — ask again each time this path is used, and only act
   on the plan as reviewed in Step 4, not on a re-interpretation of it.
5. If they say yes, work through the approved plan one Project at a time,
   confirming as you go rather than silently running the whole batch — see
   [references/browser-execution.md](references/browser-execution.md) for
   the general approach. Report back what was actually done vs. skipped.

## Non-goals

- Not a general chat summarizer — the output is a reorganization plan, not a
  digest of what was discussed.
- Not a bulk-delete tool. This skill only ever proposes moves/groupings/new
  structure; deletion of anything isn't part of Path A or Path B.
- Not a substitute for the user's own judgment on naming/scope — the plan is
  a strong starting proposal, not a final answer.
