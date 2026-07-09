#!/usr/bin/env python3
"""
parse_export.py -- Normalize a Claude.ai/Cowork data export into compact,
analysis-ready files.

A Claude data export (Settings > Account > Export Data) is a zip containing:
  - conversations.json   (required) -- every conversation + its chat_messages
  - memories.json         (optional) -- Claude's own synthesized memory of the user
  - projects/*.json       (optional) -- one file per project (name/description/uuid)
  - users.json            (optional) -- account identity, not used here

Raw conversations.json can be tens of thousands of lines and is expensive to
read directly. This script does the deterministic, mechanical extraction --
one JSON object per conversation with the fields a human (or Claude) needs to
spot recurring workflows -- so the analysis step never has to touch raw
message content unless it drills into a specific conversation.

Output (written to --out-dir):
  conversations.jsonl   one line per conversation, sorted oldest -> newest
  projects_index.json   project uuid -> {name, description, created_at}
  memory_context.md     memories.json content verbatim (if present), for
                         cross-referencing Claude's own synthesized context
  stats.json            corpus-level counts (date range, project coverage, etc.)

Usage:
  python3 parse_export.py --export-dir /path/to/export --out-dir /path/to/output
"""
import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "for",
    "with", "is", "are", "was", "were", "be", "been", "being", "this",
    "that", "these", "those", "it", "its", "as", "at", "by", "from", "how",
    "what", "when", "where", "why", "who", "which", "do", "does", "did",
    "can", "could", "should", "would", "will", "i", "my", "me", "you",
    "your", "we", "our", "us", "not", "no", "yes", "have", "has", "had",
    "about", "into", "if", "so", "than", "then", "up", "out", "just",
    "get", "got", "like", "using", "use", "want", "need", "help", "im",
    "am", "all", "some", "there", "their", "them", "also", "still",
}

WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9\-']{2,}")


def extract_keywords(*texts, top_n=8):
    """Cheap frequency-based keyword extraction -- no ML dependency needed.
    Good enough to group conversations by shared vocabulary; Claude does the
    real semantic clustering downstream using these as a starting hint."""
    counts = Counter()
    for text in texts:
        if not text:
            continue
        for w in WORD_RE.findall(text.lower()):
            if w not in STOPWORDS:
                counts[w] += 1
    return [w for w, _ in counts.most_common(top_n)]


def first_human_text(chat_messages, max_chars=300):
    for m in chat_messages:
        if m.get("sender") == "human":
            t = (m.get("text") or "").strip()
            if t:
                return t[:max_chars]
    return ""


def tool_names_used(chat_messages):
    names = set()
    for m in chat_messages:
        for block in m.get("content") or []:
            if block.get("type") == "tool_use":
                name = block.get("name")
                if name:
                    names.add(name)
    return sorted(names)


def load_projects(export_dir: Path):
    projects = {}
    proj_dir = export_dir / "projects"
    if proj_dir.is_dir():
        for f in proj_dir.glob("*.json"):
            try:
                d = json.loads(f.read_text())
            except (json.JSONDecodeError, OSError):
                continue
            uuid = d.get("uuid") or f.stem
            projects[uuid] = {
                "name": d.get("name", ""),
                "description": (d.get("description") or "")[:500],
                "created_at": d.get("created_at"),
            }
    return projects


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--export-dir", required=True, help="Path to the unzipped export folder")
    ap.add_argument("--out-dir", required=True, help="Where to write normalized output")
    args = ap.parse_args()

    export_dir = Path(args.export_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    conv_path = export_dir / "conversations.json"
    if not conv_path.exists():
        print(
            f"ERROR: {conv_path} not found. This skill requires a Claude data export "
            "(Settings > Account > Export Data on claude.ai), which contains "
            "conversations.json. A Claude Code CLI session log (~/.claude/projects/*.jsonl) "
            "is a different format and is not supported by this script.",
            file=sys.stderr,
        )
        sys.exit(1)

    conversations = json.loads(conv_path.read_text())
    projects = load_projects(export_dir)

    records = []
    project_conv_counts = Counter()
    for c in conversations:
        chat_messages = c.get("chat_messages", []) or []
        human_msgs = [m for m in chat_messages if m.get("sender") == "human"]
        assistant_msgs = [m for m in chat_messages if m.get("sender") == "assistant"]
        total_words = sum(
            len((m.get("text") or "").split()) for m in chat_messages
        )
        project = c.get("project") or {}
        project_uuid = project.get("uuid")
        if project_uuid:
            project_conv_counts[project_uuid] += 1

        name = c.get("name") or "(untitled)"
        summary = c.get("summary") or ""
        first_msg = first_human_text(chat_messages)
        keywords = extract_keywords(name, summary, first_msg)

        records.append({
            "uuid": c.get("uuid"),
            "name": name,
            "summary": summary,
            "project_uuid": project_uuid,
            "project_name": projects.get(project_uuid, {}).get("name") if project_uuid else None,
            "created_at": c.get("created_at"),
            "updated_at": c.get("updated_at"),
            "human_message_count": len(human_msgs),
            "assistant_message_count": len(assistant_msgs),
            "total_words": total_words,
            "first_human_message": first_msg,
            "tool_names_used": tool_names_used(chat_messages),
            "keywords": keywords,
        })

    records.sort(key=lambda r: r.get("created_at") or "")

    with open(out_dir / "conversations.jsonl", "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    with open(out_dir / "projects_index.json", "w") as f:
        for uuid, info in projects.items():
            info["conversation_count"] = project_conv_counts.get(uuid, 0)
        json.dump(projects, f, indent=2)

    # memory_context.md -- verbatim pass-through of Claude's own synthesized
    # memory of the user, if the export included it. This is high-signal:
    # Claude has already noticed recurring themes across conversations.
    mem_path = export_dir / "memories.json"
    with open(out_dir / "memory_context.md", "w") as f:
        if mem_path.exists():
            try:
                mem = json.loads(mem_path.read_text())
                entry = mem[0] if isinstance(mem, list) and mem else (mem if isinstance(mem, dict) else {})
                f.write("# Global memory\n\n")
                f.write((entry.get("conversations_memory") or "*(none)*") + "\n\n")
                proj_mem = entry.get("project_memories") or {}
                for uuid, text in proj_mem.items():
                    pname = projects.get(uuid, {}).get("name", uuid)
                    f.write(f"# Project memory: {pname} ({uuid})\n\n{text}\n\n")
            except (json.JSONDecodeError, OSError) as e:
                f.write(f"*(memories.json present but unreadable: {e})*\n")
        else:
            f.write("*(no memories.json in this export)*\n")

    dates = [r["created_at"] for r in records if r.get("created_at")]
    stats = {
        "conversation_count": len(records),
        "project_count": len(projects),
        "date_range": {"earliest": min(dates) if dates else None, "latest": max(dates) if dates else None},
        "conversations_with_project": sum(1 for r in records if r.get("project_uuid")),
        "conversations_without_project": sum(1 for r in records if not r.get("project_uuid")),
        "has_memory_context": mem_path.exists(),
    }
    with open(out_dir / "stats.json", "w") as f:
        json.dump(stats, f, indent=2)

    print(f"Parsed {len(records)} conversations across {len(projects)} projects.")
    print(f"Output written to {out_dir}")


if __name__ == "__main__":
    main()
