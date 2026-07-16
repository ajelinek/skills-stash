# script.json schema

This is the one interface between the judgment half of the pipeline (you,
deciding chapters, rewriting for story mode, assigning voices) and the
mechanical half (`build_audiobook.py`, which just synthesizes, concatenates,
chapters, and encodes whatever you hand it). Write one of these per document,
then run:

```bash
uv run <skill_dir>/scripts/build_audiobook.py <path-to-script.json>
```

## Shape

```json
{
  "title": "The Document Title",
  "output_dir": "/absolute/path/to/where/the/user/wants/the/file",
  "source": "original-file-name-or-'pasted text'",
  "lang": "en-us",
  "chapters": [
    {
      "title": "Introduction",
      "lines": [
        {"voice": "af_heart", "text": "Plain prose, no markdown syntax -- this is read verbatim by the TTS engine."}
      ]
    }
  ]
}
```

| Field | Required | Notes |
|---|---|---|
| `title` | yes | Becomes the `.m4b` filename (slugified) and the embedded `title` tag. |
| `output_dir` | yes | Absolute path. Created if it doesn't exist. Always comes from the user -- never invent or default this. |
| `source` | no | Original filename or `"pasted text"`. Written into the file's `comment` metadata tag for provenance. |
| `lang` | no | Defaults to `en-us`. Only change this if the source content is genuinely in another language Kokoro supports. |
| `chapters` | yes | Non-empty list. Each chapter needs a non-empty `title` and a non-empty `lines` list. |
| `lines[].voice` | yes | Must be one of the 6 roster IDs in [voice-roster.md](voice-roster.md). Anything else is a hard error -- the script validates this before synthesizing anything. |
| `lines[].text` | yes | Plain prose. Strip markdown syntax (`**bold**`, `[text](url)`, etc.) before writing it here -- whatever's in `text` gets read aloud exactly as-is. For prosody techniques (emphasis, pausing, stress), see [kokoro-prosody-guide.md](kokoro-prosody-guide.md). |
| `lines[].speed` | no | Optional per-line speed override, 0.5–2.0. If omitted, uses the global `--speed` from the build command (default 1.0). Use for dramatic pacing changes (slower for serious moments, faster for energetic passages). |

## Why "lines" and not just one big block of text per chapter

Two reasons:

1. **Story mode needs per-line voice assignment.** A chapter alternating between a narrator and a character is naturally a list of `{voice, text}` pairs -- one per beat/turn.
2. **Line granularity gives you natural pause points.** `build_audiobook.py` inserts a short silence between lines within a chapter and a longer one between chapters, so switching voices doesn't sound like an abrupt jump-cut. In plain mode, splitting a chapter into one line per paragraph gets you this pacing for free even with a single voice throughout.

You don't need to chunk for the TTS engine's sake -- Kokoro handles arbitrarily long text per line internally (it splits at the phoneme level, preferring punctuation boundaries, and stitches the result back together). Chunk at the "line" level for narrative/pacing reasons, not to work around any length limit.

## Validation the script performs before synthesizing anything

`build_audiobook.py` fails fast, before spending any time on audio generation, if:

- `ffmpeg` isn't on PATH
- required top-level fields are missing
- any chapter has no title or no lines
- any line uses a voice outside the 6-voice roster
- any line's text is empty after stripping whitespace

Errors go to stderr with a specific reason -- there's no silent partial output.

## What comes back

On success, `build_audiobook.py` prints one JSON object to stdout:

```json
{
  "file": "/absolute/path/to/output/my-title.m4b",
  "runtime_seconds": 42.1,
  "total_duration_seconds": 613.4,
  "chapter_count": 3,
  "chapters": [{"title": "Introduction", "start_ms": 0, "end_ms": 45000}, ...]
}
```

Report this back to the user directly -- file path, runtime, chapter count/titles -- not just "done."
