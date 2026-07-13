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
  complexity instead of forcing one rigid template on a 10-minute standup
  and a 2-hour planning session alike. Not for behavioral/communication
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
a flat `segments` list (`speaker`, `timestamp_sec`, `text`), and `stats`.

Check `stats` before doing anything else:

- **`warnings`** -- surface these to the user plainly (very short
  transcript, no speaker labels detected, no structural segmentation found)
  rather than silently producing a confident-looking recap anyway.
- **`word_count`** / **`duration_sec`** -- use these plus the content itself
  to judge the meeting's size and type; see the meeting-type adaptivity
  section of [references/extraction-rules.md](references/extraction-rules.md).
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
  just because the *input* did
- A cheap final self-check against the source transcript before presenting

## Step 3: Write the recap

Use the exact template and the hard length rules in
[references/output-template.md](references/output-template.md) -- read it
before writing the first recap. The short version: a mandatory one-to-three
sentence TL;DR first, then only the sections that actually apply, bullets
and tables (never paragraphs), nothing longer than 1-2 sentences per bullet,
and the whole thing readable in under a minute regardless of how long the
source meeting was.

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
- No cross-meeting comparison or trend-tracking; this is a single-transcript
  tool.

## Supporting files

| File | Purpose |
| --- | --- |
| `references/extraction-rules.md` | Decision-vs-discussion heuristics, action-item rules, topic clustering, confidence signaling, meeting-type adaptivity, long-transcript handling, the pre-presentation self-check |
| `references/output-template.md` | The exact recap template, the reasoning behind each length rule, and a fully worked example |
| `scripts/normalize_transcript.py` | Stdlib-only transcript format detection and normalization (VTT/SRT/labeled/plain) |
