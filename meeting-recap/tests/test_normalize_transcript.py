#!/usr/bin/env python3
"""Tests for normalize_transcript.py's format detection, parsing, timing,
and stats.

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

VTT_WITH_CUE_SETTINGS = """WEBVTT

1
00:00:00.000 --> 00:00:03.500 align:start position:0%
Jane: Welcome everyone.
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
        self.assertEqual(segments[0]["end_sec"], 3.5)

    def test_extracts_voice_tag_speaker(self):
        segments = normalize_transcript.parse_vtt(VTT_SAMPLE)
        self.assertEqual(segments[1]["speaker"], "John")
        self.assertEqual(segments[1]["text"], "Happy to be here.")
        self.assertEqual(segments[1]["timestamp_sec"], 3.5)
        self.assertEqual(segments[1]["end_sec"], 7.0)

    def test_ignores_trailing_cue_settings(self):
        segments = normalize_transcript.parse_vtt(VTT_WITH_CUE_SETTINGS)
        self.assertEqual(segments[0]["timestamp_sec"], 0.0)
        self.assertEqual(segments[0]["end_sec"], 3.5)


class ParseSrtTests(unittest.TestCase):
    def test_parses_two_cues(self):
        segments = normalize_transcript.parse_srt(SRT_SAMPLE)
        self.assertEqual(len(segments), 2)
        self.assertEqual(segments[0]["speaker"], "Jane")
        self.assertEqual(segments[1]["speaker"], "John")
        self.assertEqual(segments[1]["timestamp_sec"], 3.5)
        self.assertEqual(segments[1]["end_sec"], 7.0)


class ParseLabeledTests(unittest.TestCase):
    def test_parses_leading_timestamp(self):
        segments = normalize_transcript.parse_labeled(LABELED_WITH_TIMESTAMPS)
        self.assertEqual(len(segments), 3)
        self.assertEqual(segments[0]["speaker"], "Jane")
        self.assertEqual(segments[0]["timestamp_sec"], 0.0)
        self.assertIsNone(segments[0]["end_sec"])
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
        self.assertIsNone(segments[0]["end_sec"])


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

    def test_duration_falls_back_to_span_of_start_times_when_no_end_times_recorded(self):
        stats = normalize_transcript.compute_stats(normalize_transcript.parse_labeled(LABELED_WITH_TIMESTAMPS))
        self.assertEqual(stats["duration_sec"], 20.0)
        self.assertEqual(stats["duration_basis"], "start_times_only")


class DurationCalculationTests(unittest.TestCase):
    """The crux of the sliding-ruler feature: duration must span the
    transcript's first recorded start time through its *last recorded end
    time*, not just its last recorded start time."""

    def test_vtt_duration_uses_last_cues_recorded_end_not_its_start(self):
        stats = normalize_transcript.compute_stats(normalize_transcript.parse_vtt(VTT_SAMPLE))
        # Last cue starts at 3.5s and ends at 7.0s. Using its start (the old,
        # wrong behavior) would give 3.5; the correct span is 7.0.
        self.assertEqual(stats["start_sec"], 0.0)
        self.assertEqual(stats["end_sec"], 7.0)
        self.assertEqual(stats["duration_sec"], 7.0)
        self.assertEqual(stats["duration_basis"], "recorded_end_times")

    def test_srt_duration_uses_recorded_end_times(self):
        stats = normalize_transcript.compute_stats(normalize_transcript.parse_srt(SRT_SAMPLE))
        self.assertEqual(stats["duration_sec"], 7.0)
        self.assertEqual(stats["duration_basis"], "recorded_end_times")

    def test_estimates_duration_from_word_count_when_no_timestamps(self):
        segments = normalize_transcript.parse_plain(PLAIN_TEXT * 3)
        stats = normalize_transcript.compute_stats(segments)
        self.assertEqual(stats["duration_basis"], "estimated_from_word_count")
        expected = (stats["word_count"] / normalize_transcript.ESTIMATED_WORDS_PER_MINUTE) * 60
        self.assertAlmostEqual(stats["duration_sec"], expected)
        self.assertTrue(any("rough estimate" in w for w in stats["warnings"]))

    def test_unknown_duration_when_no_timestamps_and_no_words(self):
        stats = normalize_transcript.compute_stats([])
        self.assertIsNone(stats["duration_sec"])
        self.assertEqual(stats["duration_basis"], "unknown")


class SessionBreakDetectionTests(unittest.TestCase):
    def test_flags_a_large_gap_between_segments(self):
        segments = [
            {"speaker": "A", "timestamp_sec": 0.0, "end_sec": 10.0, "text": "Morning session starts."},
            {"speaker": "B", "timestamp_sec": 10.0 + normalize_transcript.SESSION_GAP_THRESHOLD_SEC,
             "end_sec": None, "text": "Welcome back from the break."},
        ]
        breaks = normalize_transcript.detect_session_breaks(segments)
        self.assertEqual(len(breaks), 1)
        self.assertEqual(breaks[0]["after_segment_index"], 0)
        self.assertEqual(breaks[0]["before_segment_index"], 1)

    def test_no_breaks_for_a_continuous_conversation(self):
        segments = normalize_transcript.parse_labeled(LABELED_WITH_TIMESTAMPS)
        self.assertEqual(normalize_transcript.detect_session_breaks(segments), [])


class DayMarkerDetectionTests(unittest.TestCase):
    def test_detects_numeric_day_marker(self):
        segments = [{"speaker": "A", "timestamp_sec": None, "end_sec": None, "text": "Welcome back to Day 2 of the offsite."}]
        hints = normalize_transcript.detect_day_markers(segments)
        self.assertEqual(len(hints), 1)
        self.assertEqual(hints[0]["matched_text"].lower(), "day 2")

    def test_detects_spelled_out_day_marker(self):
        segments = [{"speaker": "A", "timestamp_sec": None, "end_sec": None, "text": "This is Day Three, let's continue."}]
        hints = normalize_transcript.detect_day_markers(segments)
        self.assertEqual(len(hints), 1)

    def test_no_false_positive_on_unrelated_mention(self):
        segments = [{"speaker": "A", "timestamp_sec": None, "end_sec": None, "text": "Let's circle back in a day or two."}]
        self.assertEqual(normalize_transcript.detect_day_markers(segments), [])


class RecommendTierTests(unittest.TestCase):
    def test_ten_minutes_is_micro(self):
        tier = normalize_transcript.recommend_tier(600, "recorded_end_times", [])
        self.assertEqual(tier["name"], "micro")
        self.assertEqual(tier["structure"], "flat")

    def test_exactly_thirty_minutes_is_short_not_standard(self):
        tier = normalize_transcript.recommend_tier(30 * 60, "recorded_end_times", [])
        self.assertEqual(tier["name"], "short")

    def test_two_hours_is_extended(self):
        tier = normalize_transcript.recommend_tier(2 * 3600, "recorded_end_times", [])
        self.assertEqual(tier["name"], "extended")

    def test_four_hours_is_half_day_and_hierarchical(self):
        tier = normalize_transcript.recommend_tier(4 * 3600, "recorded_end_times", [])
        self.assertEqual(tier["name"], "half_day")
        self.assertEqual(tier["structure"], "hierarchical")
        self.assertEqual(tier["cluster_unit"], "sessions")

    def test_ten_hours_is_multi_day(self):
        tier = normalize_transcript.recommend_tier(10 * 3600, "recorded_end_times", [])
        self.assertEqual(tier["name"], "multi_day")

    def test_day_marker_hints_force_multi_day_even_if_short(self):
        tier = normalize_transcript.recommend_tier(600, "recorded_end_times", [{"segment_index": 0}])
        self.assertEqual(tier["name"], "multi_day")

    def test_unknown_when_no_duration_available(self):
        tier = normalize_transcript.recommend_tier(None, "unknown", [])
        self.assertEqual(tier["name"], "unknown")

    def test_basis_is_passed_through(self):
        tier = normalize_transcript.recommend_tier(600, "estimated_from_word_count", [])
        self.assertEqual(tier["basis"], "estimated_from_word_count")


class NormalizeTests(unittest.TestCase):
    def test_end_to_end_vtt(self):
        result = normalize_transcript.normalize(VTT_SAMPLE)
        self.assertEqual(result["format_detected"], "vtt")
        self.assertEqual(len(result["segments"]), 2)
        self.assertIn("stats", result)
        self.assertEqual(result["stats"]["recommended_tier"]["name"], "micro")

    def test_format_override_skips_detection(self):
        result = normalize_transcript.normalize(LABELED_NO_TIMESTAMPS, format_override="plain")
        self.assertEqual(result["format_detected"], "plain")
        self.assertEqual(len(result["segments"]), 1)


if __name__ == "__main__":
    unittest.main()
