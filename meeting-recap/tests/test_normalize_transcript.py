#!/usr/bin/env python3
"""Tests for normalize_transcript.py's format detection, parsing, and stats.

Pure string-in/JSON-out logic -- no filesystem or network access needed, so
this suite runs offline and instantly.
"""
import importlib.util
import sys
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "normalize_transcript.py"

spec = importlib.util.spec_from_file_location("normalize_transcript", SCRIPT_PATH)
normalize_transcript = importlib.util.module_from_spec(spec)
sys.modules["normalize_transcript"] = normalize_transcript
spec.loader.exec_module(normalize_transcript)

VTT_SAMPLE = """WEBVTT

1
00:00:00.000 --> 00:00:03.500
Jane: Welcome everyone, thanks for joining.

2
00:00:03.500 --> 00:00:07.000
<v John>Happy to be here.</v>
"""

SRT_SAMPLE = """1
00:00:00,000 --> 00:00:03,500
Jane: Welcome everyone, thanks for joining.

2
00:00:03,500 --> 00:00:07,000
John: Happy to be here.
"""

LABELED_WITH_TIMESTAMPS = """0:00 Jane: Welcome everyone, thanks for joining today.
0:12 John: Happy to be here, glad we could sync up.
0:20 John: Let's get started on the agenda.
"""

LABELED_NO_TIMESTAMPS = """Jane: Welcome everyone, thanks for joining today.
John: Happy to be here.
John: Let's get started.
"""

PLAIN_TEXT = """This meeting covered a lot of ground without any clear speaker
labels, just a continuous block of prose describing what happened.

A second paragraph continues the same unstructured recounting of events.
"""


class DetectFormatTests(unittest.TestCase):
    def test_detects_vtt(self):
        self.assertEqual(normalize_transcript.detect_format(VTT_SAMPLE), "vtt")

    def test_detects_srt(self):
        self.assertEqual(normalize_transcript.detect_format(SRT_SAMPLE), "srt")

    def test_detects_labeled_with_timestamps(self):
        self.assertEqual(normalize_transcript.detect_format(LABELED_WITH_TIMESTAMPS), "labeled")

    def test_detects_labeled_without_timestamps(self):
        self.assertEqual(normalize_transcript.detect_format(LABELED_NO_TIMESTAMPS), "labeled")

    def test_detects_plain(self):
        self.assertEqual(normalize_transcript.detect_format(PLAIN_TEXT), "plain")


class ParseVttTests(unittest.TestCase):
    def test_extracts_colon_prefixed_speaker(self):
        segments = normalize_transcript.parse_vtt(VTT_SAMPLE)
        self.assertEqual(segments[0]["speaker"], "Jane")
        self.assertEqual(segments[0]["text"], "Welcome everyone, thanks for joining.")
        self.assertEqual(segments[0]["timestamp_sec"], 0.0)

    def test_extracts_voice_tag_speaker(self):
        segments = normalize_transcript.parse_vtt(VTT_SAMPLE)
        self.assertEqual(segments[1]["speaker"], "John")
        self.assertEqual(segments[1]["text"], "Happy to be here.")
        self.assertEqual(segments[1]["timestamp_sec"], 3.5)


class ParseSrtTests(unittest.TestCase):
    def test_parses_two_cues(self):
        segments = normalize_transcript.parse_srt(SRT_SAMPLE)
        self.assertEqual(len(segments), 2)
        self.assertEqual(segments[0]["speaker"], "Jane")
        self.assertEqual(segments[1]["speaker"], "John")
        self.assertEqual(segments[1]["timestamp_sec"], 3.5)


class ParseLabeledTests(unittest.TestCase):
    def test_parses_leading_timestamp(self):
        segments = normalize_transcript.parse_labeled(LABELED_WITH_TIMESTAMPS)
        self.assertEqual(len(segments), 3)
        self.assertEqual(segments[0]["speaker"], "Jane")
        self.assertEqual(segments[0]["timestamp_sec"], 0.0)
        self.assertEqual(segments[1]["timestamp_sec"], 12.0)

    def test_parses_without_timestamp(self):
        segments = normalize_transcript.parse_labeled(LABELED_NO_TIMESTAMPS)
        self.assertEqual(len(segments), 3)
        self.assertIsNone(segments[0]["timestamp_sec"])
        self.assertEqual(segments[0]["speaker"], "Jane")

    def test_wrapped_line_continues_previous_segment(self):
        text = "Jane: This is a long point that\nkeeps going on the next line.\nJohn: My turn now."
        segments = normalize_transcript.parse_labeled(text)
        self.assertEqual(len(segments), 2)
        self.assertEqual(segments[0]["text"], "This is a long point that keeps going on the next line.")


class ParsePlainTests(unittest.TestCase):
    def test_splits_into_unattributed_paragraphs(self):
        segments = normalize_transcript.parse_plain(PLAIN_TEXT)
        self.assertEqual(len(segments), 2)
        self.assertIsNone(segments[0]["speaker"])
        self.assertIsNone(segments[0]["timestamp_sec"])


class ComputeStatsTests(unittest.TestCase):
    def test_flags_short_transcript(self):
        stats = normalize_transcript.compute_stats([{"speaker": "Jane", "timestamp_sec": None, "text": "Hi there"}])
        self.assertTrue(any("Very short transcript" in w for w in stats["warnings"]))

    def test_flags_missing_speakers(self):
        stats = normalize_transcript.compute_stats(normalize_transcript.parse_plain(PLAIN_TEXT))
        self.assertFalse(stats["has_speakers"])
        self.assertTrue(any("No speaker labels" in w for w in stats["warnings"]))

    def test_no_warnings_for_healthy_transcript(self):
        segments = normalize_transcript.parse_labeled(LABELED_WITH_TIMESTAMPS * 10)
        stats = normalize_transcript.compute_stats(segments)
        self.assertEqual(stats["warnings"], [])
        self.assertTrue(stats["has_speakers"])
        self.assertTrue(stats["has_timestamps"])

    def test_duration_is_span_of_timestamps(self):
        stats = normalize_transcript.compute_stats(normalize_transcript.parse_labeled(LABELED_WITH_TIMESTAMPS))
        self.assertEqual(stats["duration_sec"], 20.0)


class NormalizeTests(unittest.TestCase):
    def test_end_to_end_vtt(self):
        result = normalize_transcript.normalize(VTT_SAMPLE)
        self.assertEqual(result["format_detected"], "vtt")
        self.assertEqual(len(result["segments"]), 2)
        self.assertIn("stats", result)

    def test_format_override_skips_detection(self):
        result = normalize_transcript.normalize(LABELED_NO_TIMESTAMPS, format_override="plain")
        self.assertEqual(result["format_detected"], "plain")
        self.assertEqual(len(result["segments"]), 1)


if __name__ == "__main__":
    unittest.main()
