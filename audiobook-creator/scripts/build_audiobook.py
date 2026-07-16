#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10,<3.14"
# dependencies = ["kokoro-onnx==0.5.0", "soundfile>=0.13", "numpy>=2.0"]
# ///
"""
Deterministic synthesis -> concatenation -> chaptering -> encode stage of the
audiobook-creator pipeline. Everything upstream of this script (extraction,
mode selection, story rewriting, voice-role assignment) is judgment work done
by the calling model. This script just turns an already-decided script.json
into a finished .m4b -- no creative decisions happen here.

Usage:
    uv run build_audiobook.py <script.json>

Run with no arguments (or --help) to see the script.json schema.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unicodedata
import urllib.request
from pathlib import Path

import numpy as np
import soundfile as sf

VOICE_ROSTER = {
    "af_heart": "Female, US, neutral/warm (plain-mode default)",
    "bf_isabella": "Female, UK",
    "af_nicole": "Female, US, alt timbre",
    "am_michael": "Male, US, neutral (plain-mode default if male requested)",
    "bm_george": "Male, UK",
    "am_fenrir": "Male, US, deeper/distinct timbre",
}

MODEL_DIR = Path.home() / ".cache" / "audiobook-creator" / "models"
MODEL_FILE = MODEL_DIR / "kokoro-v1.0.int8.onnx"
VOICES_FILE = MODEL_DIR / "voices-v1.0.bin"
MODEL_BASE_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"

SAMPLE_RATE = 24000
LINE_GAP_MS = 250  # silence between lines within a chapter (voice/beat changes)
CHAPTER_GAP_MS = 600  # silence appended at the end of each chapter


def fail(message: str) -> "None":
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def check_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        fail(
            "ffmpeg is not installed or not on PATH. Install it (e.g. `brew install "
            "ffmpeg` on macOS) and try again -- it's a required system dependency, "
            "not something pip/uv can install for you."
        )


def download_with_progress(url: str, dest: Path) -> None:
    tmp_dest = dest.with_suffix(dest.suffix + ".partial")
    print(f"Downloading {dest.name} ...", file=sys.stderr)
    last_reported = -1

    def report(block_num: int, block_size: int, total_size: int) -> None:
        nonlocal last_reported
        if total_size <= 0:
            return
        done = min(block_num * block_size, total_size)
        pct = done * 100 // total_size
        # Report in coarse steps -- this runs non-interactively, so a \r-driven
        # progress bar just spams the log with thousands of lines instead of
        # overwriting in place.
        if pct >= last_reported + 10 or done >= total_size:
            print(f"  {dest.name}: {pct}% ({done // 1_000_000}MB/{total_size // 1_000_000}MB)",
                  file=sys.stderr)
            last_reported = pct

    try:
        urllib.request.urlretrieve(url, tmp_dest, reporthook=report)
    except Exception as e:
        tmp_dest.unlink(missing_ok=True)
        fail(f"Failed to download {url}: {e}. Check your network connection and retry.")
    tmp_dest.rename(dest)


def ensure_models() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    if not MODEL_FILE.exists():
        download_with_progress(f"{MODEL_BASE_URL}/kokoro-v1.0.int8.onnx", MODEL_FILE)
    if not VOICES_FILE.exists():
        download_with_progress(f"{MODEL_BASE_URL}/voices-v1.0.bin", VOICES_FILE)


def slugify(title: str) -> str:
    normalized = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", normalized).strip("-").lower()
    return slug or "audiobook"


def escape_ffmetadata(value: str) -> str:
    # Per https://ffmpeg.org/ffmpeg-formats.html#Metadata-1 -- '=', ';', '#',
    # '\' and a leading whitespace need a backslash escape inside FFMETADATA1.
    escaped = re.sub(r"([=;#\\])", r"\\\1", value)
    return escaped.replace("\n", " ")


def load_script(path: Path) -> dict:
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        fail(f"{path} is not valid JSON: {e}")
    except FileNotFoundError:
        fail(f"script file not found: {path}")

    for field in ("title", "output_dir", "chapters"):
        if field not in data:
            fail(f"script.json is missing required field: {field!r}")
    if not isinstance(data["chapters"], list) or not data["chapters"]:
        fail("script.json 'chapters' must be a non-empty list")

    for i, chapter in enumerate(data["chapters"]):
        if not chapter.get("title"):
            fail(f"chapter {i} is missing a title")
        lines = chapter.get("lines")
        if not isinstance(lines, list) or not lines:
            fail(f"chapter {i} ({chapter.get('title')!r}) has no lines")
        for j, line in enumerate(lines):
            voice = line.get("voice")
            text = line.get("text", "").strip()
            speed = line.get("speed")
            if voice not in VOICE_ROSTER:
                fail(
                    f"chapter {i} line {j} uses unknown voice {voice!r}. "
                    f"Valid voices: {', '.join(VOICE_ROSTER)}"
                )
            if not text:
                fail(f"chapter {i} line {j} has empty text")
            if speed is not None and (not isinstance(speed, (int, float)) or speed < 0.5 or speed > 2.0):
                fail(f"chapter {i} line {j} has invalid speed {speed!r}. Must be a number between 0.5 and 2.0")
            line["text"] = text

    return data


def synthesize(script: dict, speed: float) -> tuple[np.ndarray, list[dict]]:
    from kokoro_onnx import Kokoro

    print("Loading TTS model ...", file=sys.stderr)
    kokoro = Kokoro(str(MODEL_FILE), str(VOICES_FILE))
    lang = script.get("lang", "en-us")

    chapters = script["chapters"]
    audio_parts: list[np.ndarray] = []
    chapter_marks: list[dict] = []
    cursor_ms = 0
    line_gap = np.zeros(int(SAMPLE_RATE * LINE_GAP_MS / 1000), dtype=np.float32)
    chapter_gap = np.zeros(int(SAMPLE_RATE * CHAPTER_GAP_MS / 1000), dtype=np.float32)

    total_lines = sum(len(c["lines"]) for c in chapters)
    line_num = 0

    for ci, chapter in enumerate(chapters):
        start_ms = cursor_ms
        for li, line in enumerate(chapter["lines"]):
            line_num += 1
            # Use per-line speed if specified, otherwise use global speed
            line_speed = line.get("speed", speed)
            print(
                f"  [{line_num}/{total_lines}] chapter {ci + 1}/{len(chapters)} "
                f"({chapter['title']!r}) voice={line['voice']} speed={line_speed}",
                file=sys.stderr,
            )
            samples, sr = kokoro.create(line["text"], voice=line["voice"], speed=line_speed, lang=lang)
            assert sr == SAMPLE_RATE
            audio_parts.append(samples)
            cursor_ms += int(len(samples) / SAMPLE_RATE * 1000)
            if li < len(chapter["lines"]) - 1:
                audio_parts.append(line_gap)
                cursor_ms += LINE_GAP_MS
        audio_parts.append(chapter_gap)
        cursor_ms += CHAPTER_GAP_MS
        chapter_marks.append({"title": chapter["title"], "start_ms": start_ms, "end_ms": cursor_ms})

    combined = np.concatenate(audio_parts)
    return combined, chapter_marks


def write_ffmetadata(chapters: list[dict], dest: Path) -> None:
    lines = [";FFMETADATA1"]
    for c in chapters:
        lines.append("[CHAPTER]")
        lines.append("TIMEBASE=1/1000")
        lines.append(f"START={c['start_ms']}")
        lines.append(f"END={c['end_ms']}")
        lines.append(f"title={escape_ffmetadata(c['title'])}")
    dest.write_text("\n".join(lines) + "\n")


def encode_m4b(wav_path: Path, chapters_path: Path, out_path: Path, script: dict) -> None:
    cmd = [
        "ffmpeg", "-y",
        "-i", str(wav_path),
        "-i", str(chapters_path),
        "-map_metadata", "1",
        "-c:a", "aac", "-b:a", "128k",
        "-metadata", f"title={script['title']}",
        "-metadata", "genre=Audiobook",
    ]
    if script.get("source"):
        cmd += ["-metadata", f"comment=Source: {script['source']}"]
    cmd += ["-f", "mp4", str(out_path), "-loglevel", "error"]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        fail(f"ffmpeg encode failed:\n{result.stderr}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("script_path", type=Path, help="Path to a script.json (see references/script-schema.md)")
    parser.add_argument("--speed", type=float, default=1.0, help="Playback speed multiplier, 0.5-2.0 (default 1.0)")
    args = parser.parse_args()

    check_ffmpeg()
    script = load_script(args.script_path)

    output_dir = Path(script["output_dir"]).expanduser()
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        fail(f"can't create output directory {output_dir}: {e}")

    ensure_models()

    t0 = time.time()
    combined, chapter_marks = synthesize(script, args.speed)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        wav_path = tmp_path / "combined.wav"
        chapters_path = tmp_path / "chapters.txt"
        sf.write(wav_path, combined, SAMPLE_RATE)
        write_ffmetadata(chapter_marks, chapters_path)

        out_path = output_dir / f"{slugify(script['title'])}.m4b"
        encode_m4b(wav_path, chapters_path, out_path, script)

    runtime = time.time() - t0
    summary = {
        "file": str(out_path),
        "runtime_seconds": round(runtime, 1),
        "total_duration_seconds": round(len(combined) / SAMPLE_RATE, 1),
        "chapter_count": len(chapter_marks),
        "chapters": [{"title": c["title"], "start_ms": c["start_ms"], "end_ms": c["end_ms"]} for c in chapter_marks],
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
