#!/usr/bin/env python3
"""
Rebuilds .harness/backlog.json (machine-readable) and .harness/PROGRESS.md
(human-readable) from the YAML frontmatter of every problem, requirement,
and ADR file in the repo.

Frontmatter is kept intentionally flat (scalar key: value pairs only, no
nested structures) so this script needs no YAML library.

Usage: python3 .harness/rebuild_index.py
Run from the repo root, or from anywhere -- paths are resolved relative
to this script's location.
"""
import json
import re
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent

SOURCES = [
    ("problem", ROOT / "problems", "prob-"),
    ("requirement", ROOT / "requirements", "req-"),
    ("adr", ROOT / "architecture" / "ADRs", "adr-"),
]

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

STATUS_ORDER = [
    "draft", "defined",
    "requirements_gathering", "requirements_ready",
    "architecture_ready", "tests_generated",
    "implementing", "verifying", "done",
    "proposed", "accepted", "superseded",
    "blocked",
]


def parse_frontmatter(text):
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    fields = {}
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip().strip('"').strip("'")
    return fields


def collect():
    items = []
    for item_type, folder, prefix in SOURCES:
        if not folder.exists():
            continue
        for path in sorted(folder.glob("*.md")):
            fields = parse_frontmatter(path.read_text(encoding="utf-8"))
            if not fields:
                continue
            items.append({
                "id": fields.get("id", path.stem),
                "type": fields.get("type", item_type),
                "title": fields.get("title", path.stem),
                "status": fields.get("status", "unknown"),
                "problem_id": fields.get("problem_id", ""),
                "file": str(path.relative_to(ROOT)),
                "updated": fields.get("updated", fields.get("created", "")),
            })
    return items


def write_backlog_json(items):
    out = ROOT / ".harness" / "backlog.json"
    out.write_text(json.dumps(items, indent=2) + "\n", encoding="utf-8")


def write_progress_md(items):
    out = ROOT / ".harness" / "PROGRESS.md"
    by_status = {}
    for item in items:
        by_status.setdefault(item["status"], []).append(item)

    lines = [
        "# Progress Tracker",
        "",
        f"_Generated {datetime.now().isoformat(timespec='seconds')} by .harness/rebuild_index.py -- do not edit by hand._",
        "",
    ]
    for status in STATUS_ORDER:
        if status not in by_status:
            continue
        lines.append(f"## {status} ({len(by_status[status])})")
        lines.append("")
        for item in by_status[status]:
            parent = f" (parent: {item['problem_id']})" if item.get("problem_id") else ""
            lines.append(f"- **{item['id']}** [{item['type']}] {item['title']}{parent} -- `{item['file']}`")
        lines.append("")

    known = set(STATUS_ORDER)
    leftover = {s: v for s, v in by_status.items() if s not in known}
    for status, entries in leftover.items():
        lines.append(f"## {status} ({len(entries)})")
        lines.append("")
        for item in entries:
            lines.append(f"- **{item['id']}** [{item['type']}] {item['title']} -- `{item['file']}`")
        lines.append("")

    if not items:
        lines.append("_Nothing tracked yet. Run /define-problem to get started._")
        lines.append("")

    out.write_text("\n".join(lines), encoding="utf-8")


def main():
    items = collect()
    write_backlog_json(items)
    write_progress_md(items)
    print(f"Indexed {len(items)} item(s). Wrote .harness/backlog.json and .harness/PROGRESS.md")


if __name__ == "__main__":
    main()
