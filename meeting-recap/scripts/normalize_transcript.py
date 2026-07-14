#!/usr/bin/env python3
"""
normalize_transcript.py -- Detect the format of a raw meeting transcript and
normalize it into one JSON object on stdout: a flat list of {speaker,
timestamp_sec, end_sec, text} segments plus stats (word count, speaker list,
meeting duration, a recommended recap length/structure tier, and warnings
about thin, unstructured, or multi-session input).

Stdlib only -- no pip install, no venv, no container needed to run this.

Why this exists: raw transcripts show up in wildly different shapes (WebVTT
export, SRT, a pasted "Name: text" chat log, Otter/Zoom/Teams timestamp-
prefixed lines, or just an unstructured paste with no speaker markers at
all). Guessing at structure freehand for every request wastes effort and is
easy to get subtly wrong; this script does the mechanical parsing once so
the recap-writing skill can reason about clean, structured data -- and so it
can flag *up front* when a transcript is too short, too unstructured, or too
long for a flat recap to stay skimmable, instead of silently producing one
anyway.

Formats detected: "vtt", "srt", "labeled" (timestamp-optional "Speaker:
text" lines), "plain" (no speaker/timestamp structure -- paragraphs only).

Meeting duration is computed from the transcript's own recorded timing --
the first segment's start time through the *last segment's recorded end
time* (not its start time) whenever the format actually records cue end
times (WebVTT/SRT do; a plain timestamp-prefixed line only records when a
turn started, not when it ended). Word-count-based estimation is used only
as a last resort, when the transcript carries no timestamps at all, and is
always labeled as an estimate via `duration_basis` rather than presented
with the same confidence as a real, recorded span.

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
DAY_MARKER_RE = re.compile(r"\bday\s+(\d+|one|two|three|four|five|six|seven)\b", re.IGNORECASE)

SHORT_TRANSCRIPT_WORD_THRESHOLD = 150

# Rough conversational speech rate, used ONLY to estimate a meeting's
# duration when the transcript has no timestamps at all. Recorded
# timestamps always take precedence over this estimate -- see
# `duration_basis` in compute_stats().
ESTIMATED_WORDS_PER_MINUTE = 150

# A gap at least this long between one segment's (recorded or inferred) end
# and the next segment's start is treated as a likely break between
# sessions (a lunch break, end of a workshop block, overnight) rather than
# a pause within one continuous conversation. Tune freely.
SESSION_GAP_THRESHOLD_SEC = 20 * 60

# The sliding ruler: how much structure and length a recap should have,
# keyed off the meeting's actual duration. Ordered shortest-to-longest;
# `max_duration_sec` is the upper bound of each tier (None = open-ended).
# This is the tunable "variable" the recap-writing skill reads from --
# retuning the recap format means editing these numbers, not the reasoning
# in references/output-template.md.
#
# The entry-point word budget barely grows past "extended" on purpose: once
# a meeting has enough content that it wouldn't fit a handful of scannable
# topic clusters, the answer is to push detail into per-session/per-day
# sub-sections (see references/output-template.md), not to keep inflating
# the one summary everyone reads first.
LENGTH_TIERS = [
    {
        "name": "micro",
        "label": "Micro (≤15 min)",
        "max_duration_sec": 15 * 60,
        "structure": "flat",
        "cluster_unit": "topics",
        "cluster_count_range": "0 (omit)",
        "entry_point_word_budget": {"min": 40, "max": 80},
    },
    {
        "name": "short",
        "label": "Short (15-30 min)",
        "max_duration_sec": 30 * 60,
        "structure": "flat",
        "cluster_unit": "topics",
        "cluster_count_range": "0-2",
        "entry_point_word_budget": {"min": 80, "max": 150},
    },
    {
        "name": "standard",
        "label": "Standard (30-60 min)",
        "max_duration_sec": 60 * 60,
        "structure": "flat",
        "cluster_unit": "topics",
        "cluster_count_range": "3-5",
        "entry_point_word_budget": {"min": 150, "max": 350},
    },
    {
        "name": "extended",
        "label": "Extended (1-3 hr)",
        "max_duration_sec": 3 * 3600,
        "structure": "flat",
        "cluster_unit": "topics",
        "cluster_count_range": "4-6",
        "entry_point_word_budget": {"min": 250, "max": 450},
    },
    {
        "name": "half_day",
        "label": "Half-day (3-5 hr)",
        "max_duration_sec": 5 * 3600,
        "structure": "hierarchical",
        "cluster_unit": "sessions",
        "cluster_count_range": "3-6",
        "entry_point_word_budget": {"min": 200, "max": 350},
    },
    {
        "name": "full_day",
        "label": "Full-day (5-8 hr)",
        "max_duration_sec": 8 * 3600,
        "structure": "hierarchical",
        "cluster_unit": "sessions",
        "cluster_count_range": "4-8",
        "entry_point_word_budget": {"min": 250, "max": 400},
    },
    {
        "name": "multi_day",
        "label": "Multi-day (>8 hr, or spans multiple days)",
        "max_duration_sec": None,
        "structure": "hierarchical",
        "cluster_unit": "days",
        "cluster_count_range": "1 chunk/day + cross-day rollup",
        "entry_point_word_budget": {"min": 300, "max": 500},
    },
]


def _timestamp_to_seconds(ts):
    """Parses H:MM:SS(.mmm) / MM:SS / HH:MM:SS,mmm into seconds. Missing
    higher units are assumed zero (e.g. "12:04" -> 0h 12m 4s)."""
    parts = [float(p) for p in ts.replace(",", ".").split(":")]
    while len(parts) < 3:
        parts.insert(0, 0.0)
    hours, minutes, seconds = parts
    return hours * 3600 + minutes * 60 + seconds


def _first_token(s):
    parts = s.strip().split()
    return parts[0] if parts else ""


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
    text. Captures both the cue's start AND its recorded end time (WebVTT
    cue-settings text that sometimes trails the end timestamp, e.g.
    "align:start position:0%", is discarded via _first_token)."""
    segments = []
    for block in re.split(r"\n\s*\n", text.replace("\r\n", "\n")):
        lines = [line for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        ts_line_index = next((i for i, line in enumerate(lines) if "-->" in line), None)
        if ts_line_index is None:
            continue
        start_ts, _, end_ts = lines[ts_line_index].partition("-->")
        start_token = _first_token(start_ts)
        end_token = _first_token(end_ts)
        cue_text = " ".join(lines[ts_line_index + 1:]).strip()
        if not cue_text:
            continue
        speaker, remaining = extract_inline_speaker(cue_text)
        segments.append({
            "speaker": speaker,
            "timestamp_sec": _timestamp_to_seconds(start_token) if start_token else None,
            "end_sec": _timestamp_to_seconds(end_token) if end_token else None,
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
                "end_sec": None,  # a leading timestamp marks only when the turn started
                "text": match.group(3).strip(),
            })
            continue
        match = LABELED_LINE_RE.match(line)
        if match:
            segments.append({
                "speaker": match.group(1).strip(),
                "timestamp_sec": None,
                "end_sec": None,
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
    return [
        {"speaker": None, "timestamp_sec": None, "end_sec": None, "text": " ".join(p.split())}
        for p in paragraphs
    ]


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


def detect_session_breaks(segments):
    """Flags gaps that look like a break between sessions rather than a
    pause within one conversation. Uses each segment's recorded end time
    when available, falling back to its start time (the best we can do for
    formats that don't record an end per turn)."""
    breaks = []
    previous_end = None
    previous_index = None
    for i, seg in enumerate(segments):
        start = seg.get("timestamp_sec")
        if start is None:
            continue
        if previous_end is not None:
            gap = start - previous_end
            if gap >= SESSION_GAP_THRESHOLD_SEC:
                breaks.append({
                    "after_segment_index": previous_index,
                    "before_segment_index": i,
                    "gap_sec": gap,
                })
        previous_end = seg.get("end_sec") if seg.get("end_sec") is not None else start
        previous_index = i
    return breaks


def detect_day_markers(segments):
    """Best-effort textual hints ("Day 2", "Day Three") that a transcript
    spans multiple calendar days. A hint, not a verdict -- a passing remark
    can false-positive, so it's surfaced as evidence for the skill's own
    judgment rather than silently forcing multi-day handling."""
    hints = []
    for i, seg in enumerate(segments):
        match = DAY_MARKER_RE.search(seg["text"])
        if match:
            hints.append({
                "segment_index": i,
                "timestamp_sec": seg.get("timestamp_sec"),
                "matched_text": match.group(0),
            })
    return hints


def recommend_tier(duration_sec, duration_basis, day_marker_hints):
    """Looks up the sliding-ruler tier (see LENGTH_TIERS) for this meeting's
    duration. Explicit day markers ("Day 2") win outright, since a single
    file's timestamp span can't be trusted to reflect a whole multi-day
    event's true length."""
    if day_marker_hints:
        matched = LENGTH_TIERS[-1]
    elif duration_sec is None:
        matched = None
    else:
        matched = next(
            (t for t in LENGTH_TIERS if t["max_duration_sec"] is None or duration_sec <= t["max_duration_sec"]),
            LENGTH_TIERS[-1],
        )

    if matched is None:
        return {
            "name": "unknown",
            "label": "Unknown (not enough data to estimate meeting length)",
            "max_duration_sec": None,
            "structure": "flat",
            "cluster_unit": "topics",
            "cluster_count_range": "3-5",
            "entry_point_word_budget": {"min": 150, "max": 350},
            "basis": duration_basis,
        }

    return {**matched, "basis": duration_basis}


def compute_stats(segments):
    speakers = sorted({s["speaker"] for s in segments if s["speaker"]})
    starts = [s["timestamp_sec"] for s in segments if s["timestamp_sec"] is not None]
    ends = [s["end_sec"] for s in segments if s.get("end_sec") is not None]
    word_count = sum(len(s["text"].split()) for s in segments)

    start_sec = min(starts) if starts else None
    # Prefer the latest *recorded end* time across all segments; only fall
    # back to the latest known start time when the format never records an
    # end at all (see parse_labeled).
    end_sec = max(ends) if ends else (max(starts) if starts else None)

    if start_sec is not None and end_sec is not None and end_sec > start_sec:
        duration_sec = end_sec - start_sec
        duration_basis = "recorded_end_times" if ends else "start_times_only"
    elif word_count:
        duration_sec = (word_count / ESTIMATED_WORDS_PER_MINUTE) * 60
        duration_basis = "estimated_from_word_count"
    else:
        duration_sec = None
        duration_basis = "unknown"

    day_marker_hints = detect_day_markers(segments)

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
    if duration_basis == "estimated_from_word_count":
        warnings.append(
            "No timestamps found -- meeting length is a rough estimate from word "
            f"count (~{ESTIMATED_WORDS_PER_MINUTE} words/min). Treat the recommended "
            "recap tier below as a starting point, not a precise measurement."
        )

    return {
        "segment_count": len(segments),
        "word_count": word_count,
        "speaker_count": len(speakers),
        "speakers": speakers,
        "has_speakers": bool(speakers),
        "has_timestamps": bool(starts),
        "start_sec": start_sec,
        "end_sec": end_sec,
        "duration_sec": duration_sec,
        "duration_basis": duration_basis,
        "possible_session_breaks": detect_session_breaks(segments),
        "day_marker_hints": day_marker_hints,
        "recommended_tier": recommend_tier(duration_sec, duration_basis, day_marker_hints),
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
