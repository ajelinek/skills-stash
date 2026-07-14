---
name: meeting-recap
description: >
  Turns a meeting/call transcript (pasted text, a file, or a VTT/SRT/Otter/
  Zoom/Teams-style export) into a short, skimmable recap: key decisions,
  action items (owner + due date), topics discussed, and open questions --
  built to be read in under a minute, not a wall of text. Trigger on
  requests like "summarize this meeting/call/transcript", "write meeting
  notes/minutes", "what did we decide", "give me the action items from this
  call", "recap this standup/sync/1:1/interview", or whenever the user
  pastes or hands over a transcript and asks what happened. Distinguishes an
  actual decision from mere discussion, never fabricates names/owners/
  deadlines (flags them as UNASSIGNED/TBD/"unclear from transcript" instead
  of guessing), and scales structure to the meeting's actual length and
  complexity on a sliding ruler -- the same rigor for a 10-minute standup,
  a 2-hour planning session, a full-day workshop, or a multi-day offsite,
  without forcing any of them into the same rigid template. Not for
  behavioral/communication
  coaching feedback (filler words, conflict avoidance, speaking-time
  balance, leadership patterns) -- that's a different kind of tool; this one
  is strictly about what happened, what was decided, and what's owed.
---

# Meeting Recap

## What this is

There is no shortage of "summarize this meeting" skills already. What almost
none of them do: enforce a real length limit (most rely on "be concise,"
which isn't a rule a model can actually be held to), or signal uncertainty
about what they extracted (a guessed owner name and a quoted one end up
looking equally confident). This skill's whole edge is discipline -- a short
recap by default, hard fallback tokens instead of invented names or dates,
and explicit uncertainty markers on anything inferred rather than stated.
It is not the tool for a coaching-style breakdown of how someone communicated
(see Non-goals) -- it answers one question: what happened, what got
decided, and what's owed to whom.

## Step 1: Get and normalize the transcript

Accepts pasted text in the conversation, a file path, or a known export
format (WebVTT `.vtt`, SubRip `.srt`, or a plain "Speaker: text" paste from
Zoom/Teams/Otter/Granola/etc.). Run the bundled parser first:

```bash
python3 <skill_dir>/scripts/normalize_transcript.py <path-or-'-'-for-stdin>
```

Replace `<skill_dir>` with wherever this skill is installed (the directory
containing this SKILL.md). It prints one JSON object: `format_detected`,
a flat `segments` list (`speaker`, `timestamp_sec`, `end_sec`, `text`), and
`stats`.

Check `stats` before doing anything else:

- **`recommended_tier`** -- the sliding-ruler tier (Micro through Multi-day)
  that sets this recap's structure and length budget; see the ruler in
  [references/output-template.md](references/output-template.md). Its
  `basis` field says whether `duration_sec` came from real recorded
  timestamps (`recorded_end_times`/`start_times_only`) or a word-count
  estimate (`estimated_from_word_count`) -- treat an estimated tier as a
  starting point, not a precise cutoff.
- **Meeting length is computed from the transcript's own first recorded
  start time through its last recorded end time** (`start_sec`/`end_sec`/
  `duration_sec`) -- not word count, whenever the format actually records
  cue end times (WebVTT/SRT do). Word count is only used to *estimate*
  duration as a last resort, when there are no timestamps at all.
- **`possible_session_breaks`** / **`day_marker_hints`** -- evidence of
  natural session or day boundaries (a large recorded gap, an explicit "Day
  2" mention). Hints, not verdicts -- corroborate with the transcript's own
  language before treating a meeting as multi-session/multi-day. See
  "Finding the session/day boundaries" in
  [references/output-template.md](references/output-template.md).
- **`warnings`** -- surface these to the user plainly (very short
  transcript, no speaker labels detected, no structural segmentation found,
  duration estimated rather than recorded) rather than silently producing a
  confident-looking recap anyway.
- If `format_detected` looks wrong given what you can actually see in the
  raw text, the parser is a heuristic and can miss unusual export formats --
  fall back to reading the raw transcript directly rather than trusting a
  bad parse.

## Step 2: Extract

Read [references/extraction-rules.md](references/extraction-rules.md) and
apply it. In brief, it covers:

- Telling an actual decision apart from mere discussion or a floated idea
  (and handling a decision that gets reversed later in the same meeting)
- What makes an action item genuinely actionable, and the hard
  `UNASSIGNED`/`TBD` fallbacks used instead of ever guessing a name or date
- Clustering topics into a handful of meaningful groups instead of one
  bucket per utterance
- Signaling confidence explicitly on anything inferred rather than stated,
  instead of presenting a guess with the same certainty as a quote
- Adapting which sections apply to the meeting's actual type and size,
  rather than forcing one rigid template on everything
- Working through a very long transcript without letting the *output* grow
  just because the *input* did -- and for a half-day-plus meeting, treating
  each session/day as its own extraction pass feeding a consolidated
  top-level rollup, per "Multi-session and multi-day meetings"
- A cheap final self-check against the source transcript before presenting

## Step 3: Write the recap

Use the exact template(s) and the hard rules in
[references/output-template.md](references/output-template.md) -- read it
before writing the first recap. The short version: look up the tier from
`stats.recommended_tier` (Micro through Multi-day), then follow that tier's
row on the sliding ruler. Every tier starts with a mandatory TL;DR, uses
bullets and tables (never paragraphs), and stays within its entry-point
word budget; Half-day and above add a short session/day index above a
per-session detail section instead of one long flat document. The point
that holds at every tier: whoever stops reading after the TL;DR should
still know what happened and what's owed to them.

## Step 4: Offer next steps -- don't do them unasked

Stop after presenting the recap. If the user wants more, two things are
reasonable to *offer*, not to do automatically:

- **Expand a section, or give the full blow-by-blow.** Go back to the
  source transcript for exactly what's requested rather than having
  pre-generated it on the chance it might be wanted.
- **Draft a follow-up email or message.** Draft it, show the user the exact
  text, and get explicit confirmation before sending it anywhere -- this
  skill never sends anything on its own behalf.

## Non-goals

- **Not a behavioral/communication coaching tool.** Filler words, conflict
  avoidance, talk-time balance, and leadership feedback are a different job
  from "what happened and what's owed" -- and answering both at once tends
  to produce a long, quote-heavy report when the user asked for a short one.
- **Not a transcription tool.** This skill expects a transcript (or raw
  notes) as input. If the user only has an audio/video file, get it
  transcribed first, then hand the transcript here.
- **Not a bulk/batch tool.** One meeting, one recap. Processing a whole
  folder of historical transcripts at once is a different, corpus-scale
  problem than this skill is built for.
- **Not a PM-tool integration.** No auto-posting to Jira/Linear/Asana/
  Notion -- output is plain markdown the user can paste anywhere themselves.
- **Doesn't track action-item status after the meeting.** A single
  transcript is a snapshot; whether something later got done isn't
  something this skill can know, so it doesn't claim to.

## Known limitations

- Attribution and structure quality depend on the transcript itself -- one
  with no speaker labels will produce meaningfully less reliable ownership,
  which `normalize_transcript.py`'s `warnings` flags up front rather than
  hiding.
- The format parser is a heuristic covering the common export shapes
  (WebVTT, SRT, labeled paste), not a universal parser for every transcript
  tool in existence -- if `format_detected` looks wrong, read the raw text
  directly instead of trusting it blindly.
- Duration is only as good as the transcript's own timestamps. WebVTT/SRT
  record a real end time per cue, so their duration is exact; a plain
  timestamp-prefixed paste only records when each turn *started*, so
  duration there is a start-to-start span (a slight underestimate); with no
  timestamps at all, duration is a rough word-count estimate --
  `duration_basis` always says which case applies.
- Session/day boundary detection (`possible_session_breaks`,
  `day_marker_hints`) is heuristic evidence, not a guarantee -- corroborate
  with the transcript's own language before restructuring around it.
- No cross-meeting comparison or trend-tracking; a multi-day event is
  handled as one connected rollup, not a history across separate,
  unrelated meetings over time.

## Supporting files

| File | Purpose |
| --- | --- |
| `references/extraction-rules.md` | Decision-vs-discussion heuristics, action-item rules, topic clustering, confidence signaling, meeting-type adaptivity, long-transcript and multi-session/multi-day handling, the pre-presentation self-check |
| `references/output-template.md` | The sliding ruler, the flat and hierarchical recap templates, the reasoning behind each rule, and worked examples |
| `scripts/normalize_transcript.py` | Stdlib-only transcript format detection, normalization, real start/end-time duration, session/day-break detection, and tier recommendation (VTT/SRT/labeled/plain) |
