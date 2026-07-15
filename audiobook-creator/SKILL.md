---
name: audiobook-creator
description: >
  Converts a document (markdown, .txt, Word .docx, PDF, or pasted text) into
  a real, chaptered .m4b audiobook using local, offline neural TTS (Kokoro-82M)
  -- no cloud API, no per-use cost, no data ever leaving the machine. Supports
  two modes: Plain narration (exact-text reading, one voice, maximum fidelity)
  and Story mode (rewrites dry/dense source material into an engaging themed
  narrative -- noir detective, true-crime podcast, kids' bedtime story,
  sports-commentary energy, whatever theme the user names -- with automatic
  narrator/character multi-voice assignment). Output is one .m4b file with
  chapter markers embedded via FFMETADATA1 (not raw MP3s or an .m3u playlist),
  so it gets real chapter navigation, resume position, and speed controls in
  Apple Books, Podcasts, Overcast, and other audiobook apps. Trigger this
  whenever the user wants to listen to a document instead of reading it --
  "turn this into an audiobook," "make this something I can listen to on my
  commute/drive/walk," "read this to me," "narrate this doc," "convert this
  report into a story," mentions of .m4b / audiobook / TTS / text-to-speech /
  narration applied to a document, or dry/technical source material they want
  turned into something more engaging to listen to. Also trigger when they
  want the result delivered to a specific folder (e.g. one synced to their
  phone via OneDrive) rather than left in the working directory.
---

# Audiobook Creator

## What this is

Turns written documents into real audiobook files you can listen to away
from a screen. Two mechanically different halves, and it matters which is
which: **you** (the calling model) do the parts that need actual
comprehension -- reading the extracted text, deciding chapter boundaries,
and for story mode, rewriting dry content into an engaging narrative and
deciding which lines get which voice. The **bundled scripts** do the parts
that are pure mechanism once your decisions exist -- text extraction,
speech synthesis, audio concatenation, chapter-timestamp math, and encoding.
Don't try to do the scripts' job by hand, and don't try to make the scripts
do your job -- see [references/script-schema.md](references/script-schema.md)
for the exact handoff between the two halves.

## Setup

- **`ffmpeg`** must be on PATH (`brew install ffmpeg` on macOS if it's
  missing). `build_audiobook.py` checks this itself and fails with a clear
  message rather than a cryptic error if it's absent -- you don't need to
  check it yourself first.
- **`uv`** runs the scripts. Each script declares its own dependencies
  inline (PEP 723), so `uv run <skill_dir>/scripts/<script>.py ...` handles
  installing everything into an isolated environment automatically -- no
  separate install step, no virtualenv to manage. If `uv` isn't available,
  fall back to `pip install -r <skill_dir>/requirements.txt` in a Python
  3.10-3.13 virtualenv (kokoro-onnx doesn't yet support 3.14) and run the
  scripts with that interpreter directly.
- **First run only:** the Kokoro TTS model (~115MB, quantized) downloads
  automatically to `~/.cache/audiobook-creator/models/` the first time
  `build_audiobook.py` runs. It's cached after that -- every subsequent run
  is fully offline. This needs network access once; if it fails, the script
  reports it clearly and it's safe to just rerun.

## Step 1: Get the source text

**File input** (`.md`, `.txt`, `.docx`, `.pdf`):

```bash
uv run <skill_dir>/scripts/extract_text.py <path>
```

Prints clean text to stdout with heading structure preserved as markdown
(`#`, `##`, ...). `.md`/`.txt` are read directly; `.docx`/`.pdf` go through
`markitdown`. If it fails (corrupted file, a scanned/image-only PDF with no
text layer, unsupported extension), it reports the specific reason to
stderr and exits non-zero -- surface that reason to the user rather than
retrying blindly or silently skipping the file. If you're processing
several files, one bad file should never take down the rest.

**Pasted text** (no file): you already have it in the conversation --
there's no extraction step. Use whatever heading structure it has, or ask
the user for a title/chapter breakdown if it's unstructured prose.

## Step 2: Pick a mode

- **No theme given → Plain mode.** Verbatim reading, one voice.
- **User names a theme** ("noir detective story," "kids' bedtime
  adventure," etc.) **→ Story mode.** If they want story mode but aren't
  sure what theme to ask for, offer a few varied examples -- don't force a
  fixed dropdown; theme stays freeform.

## Step 3: Build `script.json`

Both modes produce the same intermediate structure -- see
[references/script-schema.md](references/script-schema.md) for the full
schema, required fields, and validation rules. The short version: a list of
chapters, each with a title and a list of `{voice, text}` lines.

**Plain mode:**
- Pick one voice from [references/voice-roster.md](references/voice-roster.md)
  -- default `af_heart`, or `am_michael` if the user wants male, or whatever
  they name explicitly. Every line in the whole document uses that one voice.
- H1 headings become chapter boundaries, in order, titled from the heading
  text. No H1 headings at all → the whole document is a single chapter.
- Strip markdown syntax (`**bold**`, `[text](url)`, etc.) when writing each
  line's `text` -- it's read aloud exactly as written, so anything left in
  that shouldn't be spoken gets spoken. Split each chapter into one line per
  paragraph; this is what gives the audio natural pause points, and costs
  nothing since it's still one voice throughout.
- No embellishment, no rewriting, no interpretation -- if in doubt, prefer
  the more literal reading.

**Story mode:**
- Read [references/story-mode-guide.md](references/story-mode-guide.md)
  before writing anything -- it covers how to rewrite for the requested
  theme while preserving the source's actual information, and how to decide
  whether/how to split lines across a narrator voice and a second voice.
- The chapter structure doesn't have to mirror the source's own headings --
  build whatever chapter breaks serve the narrative you're writing.

## Step 4: Run the build

```bash
uv run <skill_dir>/scripts/build_audiobook.py <path-to-script.json>
```

This is the deterministic half: synthesizes every line with Kokoro,
concatenates with short pauses between lines and longer ones between
chapters, tracks cumulative timestamps into real chapter markers, and
encodes the result as AAC in an `.m4b` container with the chapters embedded
via `FFMETADATA1` and `genre=Audiobook` set (the tag that gets Apple
Books/Podcasts/Overcast to treat it as an audiobook -- resume position,
speed controls, real chapter navigation, instead of one flat unnavigable
file). Takes an optional `--speed 0.5-2.0` (default `1.0`).

It validates the whole script up front -- missing fields, empty chapters,
an unknown voice ID -- and fails on the first problem before synthesizing
any audio, so a mistake in `script.json` costs seconds, not the full
runtime.

On success it prints one JSON object to stdout with the output file path,
runtime, total duration, and the chapter list.

## Step 5: Report back

Tell the user the file path, total runtime, and chapter count/titles --
never just "done." If `output_dir` wasn't already specified, **ask for it
before running anything** -- it's a required field with no default (see
below), and it's wasted synthesis time to build the file somewhere the user
didn't ask for and then move it.

## Output directory: always required, never assumed

`script.json`'s `output_dir` must come from the user, explicitly, every
time -- never hardcode it, never default to the working directory or a
"reasonable-looking" guess. In practice this is usually a local folder
that's synced to OneDrive (or similar), so the finished file shows up on
their phone with zero extra steps -- but this skill only writes to a local
folder; whatever sync client is watching it does the rest. If the file
isn't showing up on the phone, that's a sync-client problem, not something
to debug here.

## Non-goals

- **No voice cloning or custom voices.** The roster is fixed at the 6
  curated IDs in [references/voice-roster.md](references/voice-roster.md).
- **No manual voice-to-role override in story mode.** Assignment is
  automatic, per document. If it's off on a given line, that's worth
  mentioning in your summary to the user, not something to work around
  mid-pipeline.
- **No background music, sound effects, or audio mixing** beyond narration
  and chapter markers.
- **Not a OneDrive/cloud-upload integration.** Writes to a local folder,
  full stop.
- **Not real-time/streaming narration.** Produces a finished file, not a
  live read-aloud.
- **Not a bulk/batch tool.** One document, one `.m4b`, one deliberate run.

## Known limitations

- **`ffmpeg` is a hard system dependency**, not pip/uv-installable. If it's
  missing, `build_audiobook.py` says so plainly rather than failing deep
  inside a subprocess call.
- **Story mode has no deterministic quality guarantee.** The rewrite's tone,
  length, and pacing depend on your judgment each run -- there's no fixed
  template enforcing consistency between two runs of the same source.
- **Automatic voice-role assignment is heuristic, not rule-based.** It can
  occasionally put a line on the wrong voice. No manual override exists yet.
- **CPU-only synthesis.** Kokoro-82M runs faster than real-time on a modern
  Mac (roughly half the audio's own duration, per local testing), but a
  long document still takes real wall-clock time -- set expectations with
  the user for anything book-length rather than a short doc.

## Supporting files

| File | Purpose |
|---|---|
| `scripts/extract_text.py` | Text extraction for `.md`/`.txt` (direct read) and `.docx`/`.pdf` (via `markitdown`); reports a specific failure reason rather than a silent empty result |
| `scripts/build_audiobook.py` | The deterministic core: validates `script.json`, ensures the Kokoro model is cached, synthesizes every line, concatenates with pacing gaps, tracks chapter timestamps, encodes to `.m4b` with embedded `FFMETADATA1` chapters and audiobook metadata |
| `references/script-schema.md` | The full `script.json` schema, field-by-field, plus what validation runs before synthesis and what comes back on success |
| `references/voice-roster.md` | The 6 curated voice IDs, their roles/notes, and how to choose between them in each mode |
| `references/story-mode-guide.md` | How to rewrite source material into a themed narrative without fabricating content, and how to decide on narrator/character voice splits |
| `requirements.txt` | Fallback dependency list for a manual `pip install` if `uv` isn't available |
