# Output Template

The default recap is short by construction, not by luck -- every rule below
exists to stop one specific way these things balloon. If the user
explicitly asks for full minutes, a longer document, or a specific other
format, give them that instead; this is the default when they just want to
know what happened.

## The template

```markdown
# <Meeting title or topic> -- <date, if known>

**TL;DR:** <1-3 sentences. A reader who stops here should still know what
happened and whether anything is owed to them.>

## Decisions
- **<what was decided>** -- <who/how, in a few words>
(If none: "No decisions were made -- this was a `<discussion/status/brainstorm>` session.")

## Action Items
| Owner | Action | Due |
|---|---|---|
| <name or UNASSIGNED> | <verb-first task> | <date or TBD> |
(If none: "No action items came out of this meeting.")

## Topics Discussed
- **<topic>** -- <1-3 bullets, not a paragraph>
(Omit entirely for a single-topic/short meeting where the TL;DR already covers it.)

## Open Questions
- <what's unresolved> -- <who's expected to weigh in, if known>
(If none: "No open questions.")
```

## Hard rules, and the reasoning behind each

- **TL;DR is mandatory and comes first.** Someone who reads one line should
  still walk away knowing the gist -- everything below is for whoever needs
  more than that.
- **Every bullet is one or two sentences, never a paragraph.** If a point
  needs more room than that to make sense, it belongs in expanded notes
  (Step 4 of SKILL.md), offered on request -- not stretched into the default
  recap.
- **A section with nothing in it still gets a one-line "None," not
  silence.** Test this by asking: could the user tell the difference
  between "I checked and there's nothing here" and "I forgot to check"? If
  not, say it explicitly.
- **3-5 topic clusters, not one bucket per utterance.** A flat list of
  fifteen bullet points is not skimmable no matter how short each bullet is.
- **Bullets and tables, not prose paragraphs.** Busy readers scan; a recap's
  job is to let them skip the full meeting, not to reproduce it in miniature.
- **Whole default recap should be readable in under a minute.** As a rough
  budget: well under ~150 words for a short/simple meeting, and well under
  ~400 words even for a dense hour-long one. If you're well past that,
  you're including detail that belongs in expanded notes, not the recap.

## A worked example

Input (labeled transcript, ~4 minutes, 3 speakers):

```
0:00 Alice: Hey team, quick sync on the launch date.
0:15 Bob: I think we should push to next Friday given QA is behind.
0:30 Alice: Agreed, let's go with next Friday. Bob can you own the QA checklist?
0:40 Bob: Yep on it, will have it done by Wednesday.
0:50 Carol: What about the marketing email, is that still going out Thursday?
1:00 Alice: Good question, let's leave that open for now.
```

Output:

```markdown
# Launch Date Sync -- (date not stated in transcript)

**TL;DR:** Launch pushed to next Friday because QA is behind; Bob owns the
QA checklist by Wednesday. Marketing email timing is still unresolved.

## Decisions
- **Launch date moved to next Friday** -- agreed by Alice and Bob due to QA being behind schedule.

## Action Items
| Owner | Action | Due |
|---|---|---|
| Bob | Complete the QA checklist | Wednesday |

## Open Questions
- Is the marketing email still going out Thursday? -- raised by Carol, left open by Alice.
```

Notice what's *not* here: no "Topics Discussed" section (the whole four
minutes was one topic, already covered by the TL;DR and the sections above),
no invented meeting date (the transcript never stated one, so it says so
rather than guessing), and no participants list padded out with roles nobody
mentioned.

## When the default isn't enough

If the user wants more after seeing the recap -- the full blow-by-blow, a
specific topic expanded, verbatim quotes for a contested point -- go back to
the source transcript and pull exactly that, rather than having generated it
up front on the chance it might be wanted. See SKILL.md Step 4.
