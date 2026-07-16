# Kokoro Prosody & Expression Guide

Kokoro is a lightweight TTS engine (82M parameters) that achieves natural,
expressive narration without complex emotional markup. Instead, it uses:
**punctuation, voice selection, and speed control** to shape how text is read.
Understanding these tools prevents flat, monotone audiobooks.

## 1. Speed Control

**Global speed** (applied to every line):
```bash
uv run scripts/build_audiobook.py script.json --speed 0.9
```

**Per-line speed** (override for specific lines in `script.json`):
```json
{
  "chapters": [{
    "lines": [
      {"voice": "af_heart", "text": "Action sequence here!", "speed": 1.15},
      {"voice": "af_heart", "text": "A moment of quiet reflection.", "speed": 0.85}
    ]
  }]
}
```

**Recommended ranges:**
- **0.85–0.95:** Dramatic, serious, or meditative content; lowers energy for emphasis
- **0.95–1.05:** Natural audiobook narration (default); neutral pacing
- **1.05–1.15:** Energetic passages, dialogue, action sequences; adds urgency
- **1.15+:** Fast-paced advertising, announcements, or comedic timing
- **0.5–0.85:** Very slow for particularly solemn or important moments

**When to use per-line speed:**
- Slower (0.85–0.9) for emotional peaks, plot twists, or warnings
- Faster (1.1–1.2) for dialogue, action, or comedic beats
- Revert to normal (1.0) for regular narration between peaks

## 2. Voice Selection

Six curated voices available; choose to match content tone. See
[voice-roster.md](voice-roster.md) for full descriptions and use cases.

**For plain mode:** Pick one voice for the entire narration. `af_heart` (warm
female) is the default; `am_michael` is the standard male choice.

**For story mode:** Assign voices to different characters and narrators.
Different voices naturally convey different emotional registers—use this to
reinforce character personality or narrative perspective.

**Voice psychology matters:** A warm, intimate voice makes a personal essay
feel closer; a deeper voice adds gravitas to instruction; distinct timbres
make character dialogue unambiguous.

## 3. Punctuation-Driven Prosody

Kokoro's core prosody mechanism. Everything below affects intonation and pacing
*without* requiring special markup—just use these punctuation marks naturally.

### Punctuation Effects

| Mark | Effect | Use for |
|---|---|---|
| **`.` (period)** | Full stop, long pause, intonation resets | Clear sentence boundaries; separates thoughts |
| **`,` (comma)** | Short breath pause, keeps flow | Clauses within a sentence; natural breathing |
| **`;` (semicolon)** | Mid-length pause (between comma and period) | Connecting related but distinct ideas |
| **`:` (colon)** | Pause with forward anticipation | Introducing a list, explanation, or quotation |
| **`—` (em-dash)** | Parenthetical pause, lighter interruption | Asides, sudden thoughts, or interjections |
| **`…` (ellipsis)** | Trailing pause with falling intonation | Dramatic effect, trailing off, suspense |
| **`?` (question mark)** | Rising intonation on yes/no questions | Questions expecting an answer |
| **`!` (exclamation)** | Higher energy and emphasis | Excitement, urgency, or strong emotion (one is sufficient; stacking `!!!` adds nothing) |

### Best Practices for Punctuation

**Break long clauses:** Don't write "When the character stepped into the room he saw the painting on the wall and gasped." Instead: "When the character stepped into the room, he saw the painting on the wall. He gasped."

**Vary sentence structure:** Mix short sentences (for impact) with longer ones
(for flow). This creates natural rhythm and prevents monotone pacing.

**Use em-dashes for asides:** "She walked—slowly, carefully—toward the exit."
This creates a natural pause around the aside.

**Strategic ellipsis for drama:** "He reached for the handle… and pulled."
The ellipsis adds suspense before the reveal.

## 4. Emphasis & Stress Markup

Use bracket notation to add emphasis to specific words:

```
This is the [best](+2) outcome possible.
That was the [worst](−2) mistake.
```

- `[word](+1)` or `[word](+2)`: Raises stress/emphasis on that word
- `[word](−1)` or `[word](−2)`: Lowers stress/emphasis on that word

**Common use cases:**
- Highlighting key terms: "The `[kernel](+1)` of the problem..."
- Softening unnecessary details: "We used a `[standard](−1)` approach."
- Emotional peaks: "I `[love](+2)` this."

**Does NOT work:**
- ALL CAPS ("I CAN'T BELIEVE IT") — ignored by Kokoro
- Decimal speeds in brackets like `[text](.05)` — use the `speed` field instead
- Multiple stacked marks like `!!!` or `!!!` — only the first counts

## 5. Capitalization for Clarity

Capitalize acronyms and abbreviations to add vocal dynamics. Kokoro's
pronunciation engine (G2P/Misaki layer) treats capitalized acronyms as
individual-letter pronunciation, which adds natural variety:

```
The GPU was faster than expected.
We use DNS servers globally.
Check the FAQ for details.
```

vs.

```
The gpu was faster than expected.
We use dns servers globally.
Check the faq for details.
```

The capitalized version reads with more energy and clarity.

## 6. Techniques to Prevent Monotone Reading

### Text Structure
- **Shorter sentences for impact.** Compare "The character entered and was
  shocked by what they saw" (dull) vs. "The character entered. They stopped.
  Before them: a shocking sight." (engaging)
- **Vary clause count per sentence.** Mix single-clause ("He left.") with
  multi-clause ("As the sun set over the valley, casting long shadows across
  the hills, he finally understood.")
- **Break paragraphs strategically.** Each new paragraph gets a natural pause
  in the audio (line breaks in `script.json` become `line_gap` pauses).

### Pacing & Speed
- Use slower speeds (0.9) for serious/emotional moments to add weight
- Use faster speeds (1.05–1.1) for dialogue or action to add energy
- Return to neutral (1.0) for regular narration

### Voice Diversity
- Story mode: Let different characters have different voices. This alone
  prevents monotone by forcing natural variation.
- Plain mode: Single voice throughout, so rely more heavily on punctuation,
  speed, and structure.

### Punctuation Rhythm
- Open with a short sentence (punchy)
- Build with longer, connected clauses (flow)
- Close with a short sentence (impact)

Example: "The door creaked open. Inside, shadows danced across faded
photographs and dusty shelves, each object a memory frozen in time. She took
a breath."

### Capitalization for Variety
Acronyms (GPS, FBI, TLS) read more dynamically when capitalized. This tiny
variation helps prevent droning.

## 7. Common Mistakes to Avoid

| Mistake | Why It's Wrong | Fix |
|---|---|---|
| Long paragraphs without punctuation | Creates monotone blocks | Add commas, semicolons, or break into sentences |
| ALL CAPS for emphasis | Kokoro ignores it | Use `[word](+1)` or exclamation marks instead |
| Too much punctuation | Sounds choppy and unnatural | Let natural English pacing guide you |
| Identical sentence structure throughout | Boring rhythm | Vary short + long, simple + complex |
| Same voice for everything (story mode) | Character confusion | Assign distinct voices to key characters |
| Speed 1.0 for entire document | Flat energy | Use 0.9–0.95 for serious parts, 1.05–1.1 for energy |
| Trying SSML tags or emotion markers | Kokoro doesn't parse them | Stick to punctuation and speed |

## 8. Practical Example: Before & After

### Before (Monotone)
```json
{
  "lines": [
    {
      "voice": "af_heart",
      "text": "The morning sun broke through the clouds as she walked down the quiet street thinking about everything that had happened and what it all meant."
    }
  ]
}
```

### After (Engaging)
```json
{
  "lines": [
    {"voice": "af_heart", "text": "The morning sun broke through the clouds.", "speed": 0.95},
    {"voice": "af_heart", "text": "She walked down the quiet street.", "speed": 0.9},
    {"voice": "af_heart", "text": "Thinking. Remembering. Processing.", "speed": 0.85},
    {"voice": "af_heart", "text": "And slowly, understanding came.", "speed": 0.95}
  ]
}
```

The second version:
- Uses shorter, punchier sentences
- Adds pauses between thoughts (line breaks)
- Slows down (`0.85–0.9`) for introspective moments
- Returns to normal pace (`0.95`) for narrative flow

## 9. Language Support

Kokoro supports English (US/UK variants) natively. The `lang` field in
`script.json` defaults to `en-us`; change to `en-gb` for British pronunciation
if needed. Other languages may be available depending on your Kokoro build,
but story-mode voice assignment assumes English.

## 10. When to Use What

| Scenario | Tool(s) | Example |
|---|---|---|
| Generic audiobook narration | Voice + structure | Use `af_heart`, vary sentence length |
| Dramatic or tense moment | Speed + punctuation | `"…and then it happened."`  at speed 0.9 |
| Character dialogue | Voice + structure | Assign `am_michael` to male character, `af_heart` to female |
| Important announcement | Stress + speed | `[critical](+2)` at speed 1.0 or faster |
| Quiet reflection | Speed + pauses | 0.85 speed with sentence breaks |
| Technical content | Capitalized acronyms | "The API returns JSON" (all caps for technical terms) |

---

**Bottom line:** Kokoro achieves expressiveness through *simplicity*. Master
punctuation and speed first, then layer voice selection and stress markup as
needed. The best audiobooks feel natural—let the text's structure and meaning
guide your choices.
