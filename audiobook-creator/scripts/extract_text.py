#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10,<3.14"
# dependencies = ["markitdown[docx,pdf]>=0.1"]
# ///
"""
Extracts clean text (headings preserved as markdown `#`/`##`/...) from a
.md, .txt, .docx, or .pdf file and prints it to stdout.

.md/.txt are read directly. .docx/.pdf go through markitdown, which is the
one dependency that covers both uniformly and preserves heading structure.

Usage:
    uv run extract_text.py <path>

On failure (corrupted file, scanned/image-only PDF with no text layer,
unsupported extension) prints a clear reason to stderr and exits non-zero --
never a silent empty result.
"""

import sys
from pathlib import Path

DIRECT_READ_EXTS = {".md", ".txt"}
MARKITDOWN_EXTS = {".docx", ".pdf"}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: extract_text.py <path>")

    path = Path(sys.argv[1]).expanduser()
    if not path.exists():
        fail(f"file not found: {path}")

    ext = path.suffix.lower()

    if ext in DIRECT_READ_EXTS:
        try:
            text = path.read_text(encoding="utf-8", errors="strict")
        except UnicodeDecodeError as e:
            fail(f"{path} is not valid UTF-8 text: {e}")
        except OSError as e:
            fail(f"couldn't read {path}: {e}")
    elif ext in MARKITDOWN_EXTS:
        try:
            from markitdown import MarkItDown
        except ImportError:
            fail("markitdown is not installed -- this script should be run with `uv run` "
                 "so its inline dependencies are resolved automatically.")
        try:
            result = MarkItDown().convert(str(path))
            text = result.text_content
        except Exception as e:
            fail(f"couldn't extract text from {path}: {e}")
    else:
        fail(
            f"unsupported file type {ext!r} for {path}. Supported: "
            f"{', '.join(sorted(DIRECT_READ_EXTS | MARKITDOWN_EXTS))}"
        )

    if not text.strip():
        if ext == ".pdf":
            fail(
                f"{path} produced no extractable text. This usually means it's a "
                "scanned/image-only PDF with no text layer -- markitdown can't OCR it."
            )
        fail(f"{path} produced no extractable text.")

    print(text)


if __name__ == "__main__":
    main()
