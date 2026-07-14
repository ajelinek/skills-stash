# Reorganization analysis

Given the parsed export (or the lower-fidelity data from the main skill
file's Step 1, tiers 2-3), answer: how should the user's *existing* chats
and Projects be restructured?

## Reconstruct project membership first if the link field is missing

Check `stats.json`'s `conversations_with_project` before anything else. Many
export schemas simply don't include a per-conversation project reference --
`project_uuid` reads as null on every record even when Projects exist and
most chats genuinely belong to one in the UI. If `stats.json` has a `notes`
entry about this (or `conversations_with_project` is 0 while `project_count`
is not), **do not report those chats as unaffiliated with any project.**
Instead, infer real membership per conversation by cross-referencing:

- `memory_context.md`'s per-project `project_memories` sections -- Claude's
  own synthesized summary of what each project's conversations are about.
- Topic/keyword/name similarity between a conversation and each project's
  name/description in `projects_index.json`.

Only treat a chat as genuinely project-less once you've checked it against
both signals and found no match -- not because the raw link field was empty.

## What to look for

Work through the data looking for:

- **Topic clusters** -- chats that are really the same kind of work spread
  across multiple threads (a sign they belong in one Project together).
- **Existing structure vs. reality** -- where current Projects (if any) no
  longer match what the chats inside them are actually about. This
  comparison depends on knowing which chats are "inside" each project --
  use the reconstructed membership above when the raw link is missing.
- **Stale vs. active** -- old one-off threads (check `updated_at` if the
  parser ran) that don't need a home vs. live work that does.

If a recurring *workflow* pattern turns up (the same multi-step process
being manually re-explained or re-solved chat after chat), that's the
automation-mining lens's territory, not this one -- note it in passing and
point the user to that analysis rather than proposing a Skill here too.
Don't duplicate that recommendation across both lenses.

Keep this analysis visible to the user in summary form -- don't jump
straight from raw data to a polished plan with no visibility into the
reasoning.

## The plan

Output a single structured plan, in this order:

1. **Projects** -- for each: proposed name, description, and which existing
   chats should move into it.
2. **File/folder structure per project** -- what reference files,
   instructions, or knowledge docs each Project should hold, and why.
3. **Leftovers** -- chats that don't fit any recommended Project; say what
   you propose doing with them (archive, leave standalone, etc.) rather
   than silently dropping them from the plan.

Then return to the main skill file's Step 4 (review) and Step 5 (optional
execution via a browser tool).
