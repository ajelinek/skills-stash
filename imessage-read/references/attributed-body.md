# Decoding `attributedBody` (macOS 14+ NULL text column)

## The problem

Starting with macOS 14 (Sonoma), some messages have `message.text = NULL` and store
the actual text only inside `message.attributedBody`: a binary blob produced by
Apple's NSArchiver/typedstream serialization of an `NSAttributedString`. A tool that
only reads `message.text` silently drops these messages — no error, they just don't
show up.

## What we compared

Per the task's request to look at prior art rather than build blind, two published,
independent implementations were pulled and compared against five real reference
`attributedBody` blobs (copied verbatim from a third project's own test fixtures —
see `tests/test_imessage_cli.py`):

1. **[daveremy/imessage-mcp](https://github.com/daveremy/imessage-mcp)**,
   `src/typedstream.ts`: scans for the `0x01 0x2B` byte pair (the type marker that
   precedes the length-prefixed string data), falling back to scanning past a
   literal `"NSString"` class reference if that marker isn't found. Length is read
   with a three-tier variable-length scheme (single byte if `< 0x80`, a `0x81` flag
   byte followed by a little-endian `uint16` for longer strings, `0x82` + `uint32`
   for longer still).

2. **[anipotts/imessage-mcp](https://github.com/anipotts/imessage-mcp)**,
   `src/db.ts`: scans for a literal `"NSString"`/`"NSMutableString"` marker, skips a
   fixed 5-byte preamble, then reads length with only two tiers (single byte, or
   `0x81` + `uint16`) — no `0x82`/`uint32` tier — and calls `.trim()` on the decoded
   result.

## Result

Both decoded the short/medium/emoji fixtures correctly. On the 277-character "long
message" fixture (which needs the `0x81` three-byte length tier), anipotts'
implementation **corrupted real message content**: its `.trim()` call stripped two
legitimate trailing spaces the sender actually typed ("...Your call Jen.  " ->
"...Your call Jen."). daveremy's decoded all five fixtures byte-for-byte correctly.

This is reproducible — see `test_decoders.py`-style comparison folded into
`tests/test_imessage_cli.py`'s `AttributedBodyDecodeTests`, which runs the real hex
fixtures through `extract_text_from_attributed_body` and asserts exact matches.

**Decision: ported daveremy's marker-scan + three-tier length algorithm**
(`extract_text_from_attributed_body` in `scripts/imessage_cli.py`), with one
change — no `.strip()`/`.trim()` on the result, since trailing/leading whitespace can
be real message content and stripping it is exactly the bug that tripped up the
implementation we didn't pick.

## The algorithm, as ported

1. Reject blobs under 20 bytes or missing the typedstream magic (`0x04 0x0B`).
2. Search for the `0x01 0x2B` marker. If found, the length prefix starts right after
   the `0x2B`.
3. If not found, fall back to locating a literal `NSString` class reference and
   scanning forward (bounded window) for a length prefix whose decoded bytes look
   like printable text (has printable ASCII, no control characters below `0x09`).
4. Read the length using the three-tier scheme described above.
5. Decode the indicated byte range as UTF-8. Return `None` on any failure at any
   step — callers fall back to the `text` column, never raise.

This is a best-effort heuristic parser for the common single-`NSString`-run case
(one message = one attributed string), not a general typedstream/NSArchiver reader.
It does not attempt to parse multiple runs, custom attributes, or non-string
archived objects.

## Known edge cases

- **Tapback reactions** also arrive as `attributedBody`-only messages with
  human-readable derived text (e.g. `Reacted 😒 to "No treats "` — this is
  literally one of the five test fixtures). They decode fine; they're filtered out
  of this skill's default output by `associated_message_type != 0`, not by the
  decoder (see `schema.md`).
- **Edited/unsent messages**: not specially handled in this phase. `date_edited`/
  `date_retracted` are read from the schema but not surfaced or acted on yet — see
  SKILL.md's "Known limitations."
- **Malformed/truncated blobs**: return `None` and fall through to the `text` column,
  never raise. Tested directly (`MALFORMED_BLOB`, `TINY_BLOB` fixtures).
