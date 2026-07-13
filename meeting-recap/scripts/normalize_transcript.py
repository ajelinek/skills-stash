#!/usr/bin/env python3
"""
normalize_transcript.py -- Detect the format of a raw meeting transcript and
normalize it into one JSON object on stdout: a flat list of {speaker,
timestamp_sec, text} segments plus stats (word count, speaker list, whether
timestamps/speaker labels exist, and warnings about thin or unstructured
input).

Stdlib only -- no pip install, no venv, no container needed to run this.

Why this exists: raw transcripts show up in wildly different shapes (WebVTT
export, SRT, a pasted "Name: text" chat log, Otter/Zoom/Teams timestamp-
prefixed lines, or just an unstructured paste with no speaker markers at
all). Guessing at structure freehand for every request wastes effort and is
easy to get subtly wrong; this script does the mechanical parsing once so
the recap-writing skill can reason about clean, structured data -- and so it
can flag *up front* when a transcript is too short or too unstructured to
support a confident recap, instead of silently producing one anyway.

Formats detected: "vtt", "srt", "labeled" (timestamp-optional "Speaker:
text" lines), "plain" (no speaker/timestamp structure -- paragraphs only).

Usage:
    python3 normalize_transcript.py <path>       # read a file
    python3 normalize_transcript.py -             # read stdin (default)
    python3 normalize_transcript.py <path> --format labeled   # skip detection

Exit codes:
    0 -- ran to completion; stdout is the normalized JSON.
    1 -- fatal error (unreadable file, empty input); stdout is a JSON object
         with a "fatal_error" key.
"""
import argparse
import json
import re
import sys

TIMESTAMP_ARROW_RE = re.compile(r"\d{2}:\d{2}:\d{2}[.,]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[.,]\d{3}")
VTT_VOICE_TAG_RE = re.compile(r"^<v\s+([^>]+)>(.*?)(?:</v>)?$", re.DOTALL)
CUE_SPEAKER_RE = re.compile(r"^([A-Za-z][\w'.\- ]{0,40}?):\s+(.+)$", re.DOTALL)
LABELED_LINE_TS_RE = re.compile(r"^\[?(\d{1,2}(?::\d{2}){1,2})\]?\s+([A-Za-z][\w'.\- ]{0,40}?):\s+(.+)$")
LABELED_LINE_RE = re.compile(r"^([A-Za-z][\w'.\- ]{0,40}?):\s+(.+)$")
SHORT_TRANSCRIPT_WORD_THRESHOLD = 150


def _timestamp_to_seconds(ts):
    """Parses H:MM:SS(.mmm) / MM:SS / HH:MM:SS,mmm into seconds. Missing
    higher units are assumed zero (e.g. "12:04" -> 0h 12m 4s)."""
    parts = [float(p) for p in ts.replace(",", ".").split(":")]
    while len(parts) < 3:
        parts.insert(0, 0.0)
    hours, minutes, seconds = parts
    return hours * 3600 + minutes * 60 + seconds


def extract_inline_speaker(cue_text):
    """Pulls a speaker out of one cue's text, if present, via either WebVTT's
    <v Name>...</v> voice tag or a plain "Name: text" prefix."""
    stripped = cue_text.strip()
    voice_match = VTT_VOICE_TAG_RE.match(stripped)
    if voice_match:
        return voice_match.group(1).strip(), voice_match.group(2).strip()
    speaker_match = CUE_SPEAKER_RE.match(stripped)
    if speaker_match:
        return speaker_match.group(1).strip(), speaker_match.group(2).strip()
    return None, stripped


def _parse_cue_blocks(text):
    """Shared block parsing for VTT/SRT: split on blank lines, find the
    "-->" timestamp line in each block, join everything after it as the cue
    text. Returns segments with speaker extracted from the cue text."""
    segments = []
    for block in re.split(r"\n\s*\n", text.replace("\r\n", "\n")):
        lines = [line for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        ts_line_index = next((i for i, line in enumerate(lines) if "-->" in line), None)
        if ts_line_index is None:
            continue
        start_ts = lines[ts_line_index].split("-->")[0].strip()
        cue_text = " ".join(lines[ts_line_index + 1:]).strip()
        if not cue_text:
            continue
        speaker, remaining = extract_inline_speaker(cue_text)
        segments.append({
            "speaker": speaker,
            "timestamp_sec": _timestamp_to_seconds(start_ts),
            "text": remaining,
        })
    return segments


def parse_vtt(text):
    return _parse_cue_blocks(text)


def parse_srt(text):
    return _parse_cue_blocks(text)


def parse_labeled(text):
    segments = []
    for raw_line in text.replace("\r\n", "\n").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = LABELED_LINE_TS_RE.match(line)
        if match:
            segments.append({
                "speaker": match.group(2).strip(),
                "timestamp_sec": _timestamp_to_seconds(match.group(1)),
                "text": match.group(3).strip(),
            })
            continue
        match = LABELED_LINE_RE.match(line)
        if match:
            segments.append({
                "speaker": match.group(1).strip(),
                "timestamp_sec": None,
                "text": match.group(2).strip(),
            })
            continue
        if segments:
            # Continuation of the previous speaker's turn (wrapped line).
            segments[-1]["text"] += " " + line
        # A leading unmatched line (e.g. a title) before any speaker turn is dropped.
    return segments


def parse_plain(text):
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text.replace("\r\n", "\n")) if p.strip()]
    if not paragraphs and text.strip():
        paragraphs = [text.strip()]
    return [{"speaker": None, "timestamp_sec": None, "text": " ".join(p.split())} for p in paragraphs]


_PARSERS = {"vtt": parse_vtt, "srt": parse_srt, "labeled": parse_labeled, "plain": parse_plain}


def detect_format(text):
    if text.lstrip("﻿ \t\r\n").startswith("WEBVTT"):
        return "vtt"
    lines = [line for line in text.splitlines() if line.strip()]
    if lines and lines[0].strip().isdigit() and any(TIMESTAMP_ARROW_RE.search(line) for line in lines[1:4]):
        return "srt"
    sample = lines[:40]
    labeled_hits = sum(1 for line in sample if LABELED_LINE_TS_RE.match(line) or LABELED_LINE_RE.match(line))
    if labeled_hits >= 2:
        return "labeled"
    return "plain"


def compute_stats(segments):
    speakers = sorted({s["speaker"] for s in segments if s["speaker"]})
    timestamps = [s["timestamp_sec"] for s in segments if s["timestamp_sec"] is not None]
    word_count = sum(len(s["text"].split()) for s in segments)

    warnings = []
    if word_count < SHORT_TRANSCRIPT_WORD_THRESHOLD:
        warnings.append(
            f"Very short transcript ({word_count} words) -- there may not be enough "
            "content for a real decisions/action-items recap. Say so plainly rather "
            "than padding the output to look complete."
        )
    if not speakers:
        warnings.append(
            "No speaker labels detected -- action-item ownership and per-person "
            "attribution will be unreliable. Prefer UNASSIGNED over guessing who said what."
        )
    if len(segments) <= 1 and word_count > 300:
        warnings.append(
            "No structural segmentation was found (single unbroken block) -- topic "
            "and speaker boundaries could not be detected mechanically."
        )

    return {
        "segment_count": len(segments),
        "word_count": word_count,
        "speaker_count": len(speakers),
        "speakers": speakers,
        "has_speakers": bool(speakers),
        "has_timestamps": bool(timestamps),
        "duration_sec": (max(timestamps) - min(timestamps)) if len(timestamps) >= 2 else None,
        "warnings": warnings,
    }


def normalize(text, format_override=None):
    fmt = format_override or detect_format(text)
    segments = _PARSERS[fmt](text)
    return {"format_detected": fmt, "segments": segments, "stats": compute_stats(segments)}


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Detect format and normalize a meeting transcript into structured JSON."
    )
    parser.add_argument("path", nargs="?", default="-", help="Transcript file path, or '-' for stdin (default)")
    parser.add_argument("--format", choices=sorted(_PARSERS), default=None, help="Skip auto-detection")
    args = parser.parse_args(argv)

    if args.path == "-":
        text = sys.stdin.read()
    else:
        try:
            with open(args.path, encoding="utf-8", errors="replace") as f:
                text = f.read()
        except OSError as exc:
            print(json.dumps({"fatal_error": "unreadable_file", "detail": str(exc)}))
            return 1

    if not text.strip():
        print(json.dumps({"fatal_error": "empty_input"}))
        return 1

    print(json.dumps(normalize(text, format_override=args.format), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
