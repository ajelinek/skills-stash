# Extraction Rules

These are the judgment calls that turn normalized segments into a trustworthy
recap. They exist because the survey of ~18 competing meeting-recap skills
done to build this one found the same handful of failure modes recurring
almost everywhere: invented owner names, decisions presented with the same
confidence as guesses, and no distinction between "we decided X" and
"someone floated the idea of X."

## Deciding vs. discussing

A line only counts as a **decision** if the transcript shows actual
agreement, not just a proposal on the table. Use these as heuristics, not a
rigid parser:

- **Decision language:** "we've decided," "agreed," "let's go with," "final
  call is," "confirmed," or a proposal that a subsequent line explicitly
  accepts ("sounds good," "yes let's do that," "+1").
- **Not a decision (task language):** "we should," "can you," "I'll handle,"
  "someone needs to" -- these are action-item candidates, not decisions.
- **Not a decision (open idea):** "what if," "I wonder," "maybe we could,"
  "thoughts on," "not sure yet" -- these belong in Open Questions, never in
  Decisions, even if they sound confident.

**Reversed or superseded decisions:** meetings backtrack. If something is
decided early and then changed later in the same transcript, record only the
final state as *the* decision. A short parenthetical -- "(revised from the
earlier plan to ship Thursday)" -- is worth including when the reversal
itself is material; skip it when the earlier version was clearly just
thinking out loud.

If a meeting made no real decisions (pure brainstorm, status update, etc.),
say so in one line rather than omitting the section or stretching a
discussion point to look like one.

## Action items that are actually actionable

Every action item needs three things. If the transcript doesn't supply one,
use the fallback -- never invent a plausible-sounding substitute:

| Field | Required form | Fallback when absent from the transcript |
|---|---|---|
| Task | One sentence, verb-first ("Send the updated deck," not "Deck stuff") | -- (if there's no clear task, it isn't an action item) |
| Owner | A name that actually appears in the transcript or speaker list | `UNASSIGNED` |
| Due date | A concrete date, or the relative phrase actually used ("by Friday") | `TBD` |

Do not add a status/progress field -- a single transcript is a snapshot and
cannot know whether something later got done; claiming otherwise is a
fabrication risk, not a feature.

A vague mention ("we should really follow up on the vendor thing at some
point") that never gets a task, owner, or timeframe attached is **not** an
action item -- put it in Open Questions/Parking Lot instead of dressing it up
with a table row it doesn't earn.

## Topic clustering

- If the meeting had a stated agenda, use it as the organizing backbone
  instead of inventing new topic buckets.
- Otherwise, merge related sub-threads into a small number of meaningfully
  distinct clusters -- aim for **3-5**, not one bucket per utterance. Working
  memory for a scanned list holds a handful of grouped items well; a longer
  flat list stops being skimmable regardless of how short each line is.
- Each topic gets 1-3 bullets, not a paragraph. If a topic genuinely needs
  more than that to make sense, it's a candidate for the expanded notes
  offered in Step 4 of SKILL.md, not the default recap.
- Skip pure noise: greetings, "can everyone hear me," recording/logistics
  chatter, and scheduling-only exchanges -- unless scheduling *was* the
  point of the meeting.

## Open questions / parking lot

Keep this structurally separate from Decisions so nothing undecided can be
mistaken for something settled. Each entry: what's unresolved, and who (if
anyone) is expected to answer it. An item can appear here even if it also
has a related action item elsewhere (e.g. "Bob will investigate pricing" as
an action item, "what pricing tier makes sense" as the still-open question
it's meant to resolve).

## Confidence and uncertainty signaling

Never silently guess. Concretely:

- **Names:** only use names that appear in the transcript (or the `speakers`
  list from `normalize_transcript.py`). Never invent an owner because the
  table looks incomplete without one.
- **Ambiguous attribution:** when speaker labels are missing or a comment's
  origin is genuinely unclear, say so in first person ("I couldn't tell from
  the transcript who said this") rather than picking a plausible name, and
  rather than a generic passive hedge ("it is unclear").
- **Ambiguous decisions:** if something reads as *probably* decided but the
  wording is genuinely ambiguous, mark it inline with `(unclear from
  transcript)` instead of asserting it flatly either way.
- Don't manufacture a confidence caveat for content that's actually clear --
  reserve these markers for genuine ambiguity, or they stop meaning anything.

## Meeting-type adaptivity

Infer the shape from the transcript itself (stats from
`normalize_transcript.py` plus content) rather than forcing one template on
every meeting:

- **Very short / single-topic (standup, quick sync):** the TL;DR plus
  whichever of Decisions/Action Items/Open Questions actually have content
  is enough -- don't force a "Topics Discussed" section that would just
  repeat the TL;DR.
- **1:1 or single-subject call:** the whole meeting may *be* one topic; skip
  topic clustering and go straight to what was decided/actioned.
- **Standard sync, planning, or review:** the full template applies.
- **Brainstorm / exploratory session:** it's normal and expected to have few
  or zero decisions and many open questions -- say that plainly rather than
  padding the Decisions section to look substantive.

A section that legitimately has nothing in it still gets a one-line "None"
rather than silently disappearing -- an omitted section reads as "forgot to
check," a stated "None" reads as "checked, nothing here."

## Long transcripts

The normalized `stats.word_count` (and `duration_sec`, if timestamps exist)
tells you how much material you're working with -- but a longer input should
almost never mean a longer *output*. For a very long or multi-hour
transcript, work through it in sequence (by natural agenda breaks if there
are any, or in large sequential passes otherwise) and keep a running list of
candidate decisions/action items/topics as you go, so nothing from later in
the meeting gets dropped just because it's furthest from the end of your
context -- then compress that running list down to the same short recap
format as any other meeting. Length of input and length of output are
separate variables; only the second one is under a hard budget (see
[output-template.md](output-template.md)).

## Worked example: a trickier case

Real meetings backtrack and leave things half-assigned. From a ~4-minute,
3-speaker sync (trimmed):

```
0:30 Dev: I think we should go with option B, the three-column layout.
0:45 Marcus: I like option C better, the toggle felt cleaner.
0:55 Priya: What if we did a hybrid -- three columns with the toggle on top?
1:05 Dev: Let's go with that then.
1:15 Priya: Agreed, that's the plan. Dev can you own building that by Wednesday?
...
1:32 Marcus: Actually, on second thought, let's just go with option B as-is, no
             toggle -- the survey data says the toggle didn't move the needle.
1:50 Priya: Good catch. Final answer: plain three-column layout, no toggle.
             Dev, same timeline, Wednesday.
...
2:45 Priya: Someone needs to review the legal language in email two before we send.
3:05 Priya: Let's leave that one open, not sure whose job that actually is.
```

This resolves to:

```markdown
## Decisions
- **Pricing page will use the plain three-column layout, no toggle** --
  agreed by Priya and Dev based on survey data. (Revised from an earlier
  in-meeting decision to add a toggle on top of the three columns.)

## Action Items
| Owner | Action | Due |
|---|---|---|
| Dev | Build the pricing page redesign (three columns, no toggle) | Wednesday |
| UNASSIGNED | Review the legal language in email two before sending | TBD |
```

Two things to notice: the hybrid-with-toggle plan never appears as if it
were also a decision (it was superseded before the meeting ended, so only
the final state is recorded, with a one-line note since the reversal was
material to the outcome); and the legal-review item still qualifies as an
action item -- the *task* is clear and necessary even though the transcript
explicitly leaves the *owner* unresolved, which is exactly what `UNASSIGNED`
is for.

## Before presenting: one quick self-check

Re-read your drafted Decisions and Action Items once against the source
transcript before showing them to the user. You're checking specifically
for: a name that doesn't actually appear in the transcript, a decision that
was actually just a suggestion, and a due date you inferred rather than one
that was stated. This is a cheap single pass, not a second full analysis --
its only job is to catch the specific fabrication risks above before they
reach the user.
