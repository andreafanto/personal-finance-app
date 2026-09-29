#!/usr/bin/env python3
"""
Rebuilds .harness/backlog.json (machine-readable) and .harness/PROGRESS.md
(human-readable) from the YAML frontmatter of every problem, requirement,
and ADR file in the repo.

Frontmatter is kept intentionally flat (scalar key: value pairs only, no
nested structures) so this script needs no YAML library.

It also rebuilds the working memory: knowledge/INDEX.md (the compact,
LLM-readable digest every skill reads at boot-up) and .harness/knowledge.json,
from knowledge/kn-*.md plus the ADRs, and validates entries against the
schema in knowledge/README.md.

Usage: python3 .harness/rebuild_index.py [--check]
Run from the repo root, or from anywhere -- paths are resolved relative
to this script's location. With --check, exits non-zero if any knowledge
entry fails validation (indexes are still written either way).
"""
import json
import re
import sys
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
            item = {
                "id": fields.get("id", path.stem),
                "type": fields.get("type", item_type),
                "title": fields.get("title", path.stem),
                "status": fields.get("status", "unknown"),
                "problem_id": fields.get("problem_id", ""),
                "file": str(path.relative_to(ROOT)),
                "updated": fields.get("updated", fields.get("created", "")),
            }
            if "frontend" in fields:
                item["frontend"] = fields["frontend"]
                item["design_verified"] = fields.get("design_verified", "false")
            items.append(item)
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
            gate = ""
            if item.get("frontend") == "yes":
                verified = item.get("design_verified", "false")
                gate = " ⛔ design not verified" if verified != "true" else " ✅ design verified"
            lines.append(f"- **{item['id']}** [{item['type']}] {item['title']}{parent} -- `{item['file']}`{gate}")
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


# --- Working memory (knowledge/) --------------------------------------------

KNOWLEDGE_DIR = ROOT / "knowledge"
KNOWLEDGE_KINDS = ["term", "rule", "convention", "constraint", "fact"]
KNOWLEDGE_STATUSES = ["active", "superseded", "retracted"]
KNOWLEDGE_REQUIRED = ["id", "type", "kind", "title", "summary", "status",
                      "source", "created", "updated"]
SUMMARY_MAX = 200
ID_PATTERN = re.compile(r"^(kn-\d{4}|adr-\d{4}|req-\d{3}|prob-\d{3})$")
KN_FILE_RE = re.compile(r"^(kn-\d{4})-[a-z0-9-]+$")


def entry_body(text):
    """Markdown after the frontmatter, minus the leading '# title' line."""
    body = FRONTMATTER_RE.sub("", text, count=1).strip()
    lines = body.splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    return "\n".join(lines).strip()


def split_list(value):
    return [v.strip() for v in value.split(",") if v.strip()]


def collect_knowledge():
    entries = []
    if not KNOWLEDGE_DIR.exists():
        return entries
    for path in sorted(KNOWLEDGE_DIR.glob("kn-*.md")):
        text = path.read_text(encoding="utf-8")
        fields = parse_frontmatter(text)
        fields["file"] = str(path.relative_to(ROOT))
        fields["_stem"] = path.stem
        fields["_body"] = entry_body(text)
        entries.append(fields)
    return entries


def validate_knowledge(entries, known_ids):
    """Returns a list of human-readable problems. known_ids covers every id
    that a knowledge entry may reference (kn, adr, req, prob)."""
    errors = []
    seen = {}
    by_id = {e.get("id"): e for e in entries}
    for e in entries:
        where = e["file"]
        missing = [k for k in KNOWLEDGE_REQUIRED if not e.get(k)]
        if missing:
            errors.append(f"{where}: missing required field(s): {', '.join(missing)}")
        m = KN_FILE_RE.match(e["_stem"])
        if not m:
            errors.append(f"{where}: filename must be kn-NNNN-lowercase-slug.md")
        elif e.get("id") and e["id"] != m.group(1):
            errors.append(f"{where}: id {e['id']} does not match filename prefix {m.group(1)}")
        if e.get("id") in seen:
            errors.append(f"{where}: duplicate id {e['id']} (also in {seen[e['id']]})")
        seen[e.get("id")] = where
        if e.get("type") and e["type"] != "knowledge":
            errors.append(f"{where}: type must be 'knowledge'")
        if e.get("kind") and e["kind"] not in KNOWLEDGE_KINDS:
            errors.append(f"{where}: kind '{e['kind']}' not one of {', '.join(KNOWLEDGE_KINDS)}"
                          " (decisions belong in architecture/ADRs/)")
        if e.get("status") and e["status"] not in KNOWLEDGE_STATUSES:
            errors.append(f"{where}: status '{e['status']}' not one of {', '.join(KNOWLEDGE_STATUSES)}")
        if len(e.get("summary", "")) > SUMMARY_MAX:
            errors.append(f"{where}: summary is {len(e['summary'])} chars, max {SUMMARY_MAX}")
        for field in ("related", "supersedes", "superseded_by"):
            for ref in split_list(e.get(field, "")):
                if not ID_PATTERN.match(ref):
                    errors.append(f"{where}: {field} '{ref}' is not a valid id")
                elif ref not in known_ids:
                    errors.append(f"{where}: {field} '{ref}' does not exist")
        if e.get("status") == "superseded":
            succ = e.get("superseded_by", "")
            if not succ:
                errors.append(f"{where}: status superseded but superseded_by is empty")
            elif succ in by_id and e.get("id") not in split_list(by_id[succ].get("supersedes", "")):
                errors.append(f"{where}: superseded_by {succ}, but {succ} does not list it in supersedes")
        elif e.get("superseded_by"):
            errors.append(f"{where}: superseded_by is set but status is '{e.get('status')}'")
    return errors


def knowledge_record(e):
    return {
        "id": e.get("id", e["_stem"]),
        "kind": e.get("kind", ""),
        "title": e.get("title", ""),
        "summary": e.get("summary", ""),
        "status": e.get("status", ""),
        "tags": split_list(e.get("tags", "")),
        "related": split_list(e.get("related", "")),
        "source": e.get("source", ""),
        "updated": e.get("updated", ""),
        "file": e["file"],
    }


def write_knowledge(entries, adrs):
    records = [knowledge_record(e) for e in entries]
    (ROOT / ".harness" / "knowledge.json").write_text(
        json.dumps({"knowledge": records, "adrs": adrs}, indent=2) + "\n", encoding="utf-8")

    if not KNOWLEDGE_DIR.exists():
        return
    lines = [
        "# Working Memory Index",
        "",
        f"_Generated {datetime.now().isoformat(timespec='seconds')} by .harness/rebuild_index.py -- do not edit by hand._",
        "",
        "Every line below is a confirmed, current piece of project knowledge. The",
        "summary is the fact itself; open the file for **Why** and **How to apply**.",
        "Treat active entries as binding unless the user overrides them in-session.",
        "Write new entries with `/remember`; query with `/recall`. Schema: `knowledge/README.md`.",
        "",
    ]
    active = [r for r in records if r["status"] == "active"]
    headings = {
        "term": "Glossary (domain terms)",
        "rule": "Domain rules",
        "constraint": "Constraints",
        "convention": "Conventions & style guide",
        "fact": "Context facts",
    }
    for kind in KNOWLEDGE_KINDS:
        group = [r for r in active if r["kind"] == kind]
        if not group:
            continue
        lines += [f"## {headings[kind]}", ""]
        for r in group:
            tags = f" `{' '.join('#' + t for t in r['tags'])}`" if r["tags"] else ""
            lines.append(f"- **{r['id']}** {r['title']} -- {r['summary']}{tags} -> `{r['file']}`")
        lines.append("")

    live_adrs = [a for a in adrs if a["status"] in ("accepted", "proposed")]
    if live_adrs:
        lines += ["## Architectural decisions (ADRs)", ""]
        for a in live_adrs:
            marker = "" if a["status"] == "accepted" else " _(proposed -- not yet binding)_"
            lines.append(f"- **{a['id']}** {a['title']}{marker} -> `{a['file']}`")
        lines.append("")

    if not active and not live_adrs:
        lines += ["_No knowledge recorded yet. Use `/remember` to capture some._", ""]

    retired = [r for r in records if r["status"] != "active"]
    retired += [a for a in adrs if a["status"] == "superseded"]
    if retired:
        lines += ["## Retired (do not apply -- kept for history)", ""]
        for r in retired:
            lines.append(f"- ~~{r['id']}~~ {r['title']} ({r['status']}) -> `{r['file']}`")
        lines.append("")

    (KNOWLEDGE_DIR / "INDEX.md").write_text("\n".join(lines), encoding="utf-8")


WIKI_DIR = KNOWLEDGE_DIR / "wiki"
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def write_wiki(entries, adr_items):
    """knowledge/wiki/YYYY-MM-DD.md: one page per day with memory activity
    (entries created, changed, superseded, retracted; ADRs created or changed),
    plus knowledge/wiki/README.md listing the days. Fully regenerated from
    frontmatter dates, so there are no timestamps and no stale pages."""
    if not KNOWLEDGE_DIR.exists():
        return
    days = {}

    def add(day, section, line):
        if DATE_RE.match(day or ""):
            days.setdefault(day, {}).setdefault(section, []).append(line)

    for e in sorted(entries, key=lambda e: e.get("id", "")):
        eid, title, kind = e.get("id", e["_stem"]), e.get("title", ""), e.get("kind", "")
        status, created, updated = e.get("status", ""), e.get("created", ""), e.get("updated", "")
        link = f"../{Path(e['file']).name}"
        meta = [f"kind: `{kind}`", f"source: {e.get('source', '')}"]
        if e.get("tags"):
            meta.append("tags: " + " ".join("#" + t for t in split_list(e["tags"])))
        if e.get("supersedes"):
            meta.append(f"supersedes: {e['supersedes']}")
        later = ""
        if status == "superseded":
            later = f" _(later superseded by {e.get('superseded_by', '?')})_"
        elif status == "retracted":
            later = " _(later retracted)_"
        block = (f"### {eid} -- {title}{later}\n\n"
                 f"> {e.get('summary', '')}\n\n"
                 f"{' · '.join(meta)} · [open entry]({link})\n\n"
                 f"{e['_body']}\n")
        add(created, "new", block)
        if updated and updated != created:
            if status == "superseded":
                add(updated, "retired", f"- ~~{eid}~~ {title} -- superseded by {e.get('superseded_by', '?')} ([entry]({link}))")
            elif status == "retracted":
                add(updated, "retired", f"- ~~{eid}~~ {title} -- retracted ([entry]({link}))")
            else:
                add(updated, "changed", f"- **{eid}** {title} -- {e.get('summary', '')} ([entry]({link}))")
        elif status in ("superseded", "retracted"):
            add(created, "retired", f"- ~~{eid}~~ {title} -- {status} the same day ([entry]({link}))")

    for a in adr_items:
        fields = parse_frontmatter((ROOT / a["file"]).read_text(encoding="utf-8"))
        created, updated = fields.get("created", ""), fields.get("updated", "")
        link = f"../../{a['file']}"
        add(created, "adr", f"- **{a['id']}** {a['title']} -- `{a['status']}` ([ADR]({link}))")
        if updated and updated != created:
            add(updated, "adr", f"- **{a['id']}** {a['title']} -- now `{a['status']}` ([ADR]({link}))")

    WIKI_DIR.mkdir(exist_ok=True)
    for old in WIKI_DIR.glob("*.md"):
        old.unlink()

    sections = [
        ("new", "New entries", "new"),
        ("changed", "Changed entries", "changed"),
        ("retired", "Superseded / retracted", "retired"),
        ("adr", "Architectural decisions", "ADR"),
    ]
    index = [
        "# Memory Wiki -- daily log",
        "",
        "_Generated by .harness/rebuild_index.py from entry dates -- do not edit by hand._",
        "",
        "One page per day on which working memory changed, newest first. Each page",
        "has the full text of that day's new entries, so it can be read on its own.",
        "",
    ]
    for day in sorted(days, reverse=True):
        d = days[day]
        page = [f"# Memory Wiki -- {day}", "",
                "_Generated by .harness/rebuild_index.py -- do not edit by hand._", "",
                "[All days](README.md) · [Current index](../INDEX.md)", ""]
        for key, heading, _ in sections:
            if key in d:
                page += [f"## {heading} ({len(d[key])})", ""]
                page += d[key] if key != "new" else ["\n".join(d[key])]
                page.append("")
        (WIKI_DIR / f"{day}.md").write_text("\n".join(page), encoding="utf-8")
        counts = ", ".join(f"{len(d[k])} {label}" for k, _, label in sections if k in d)
        index.append(f"- [{day}]({day}.md) -- {counts}")
    if not days:
        index.append("_No memory activity yet._")
    index.append("")
    (WIKI_DIR / "README.md").write_text("\n".join(index), encoding="utf-8")


def main():
    items = collect()
    write_backlog_json(items)
    write_progress_md(items)
    print(f"Indexed {len(items)} item(s). Wrote .harness/backlog.json and .harness/PROGRESS.md")

    entries = collect_knowledge()
    adrs = [{"id": i["id"], "title": i["title"], "status": i["status"], "file": i["file"]}
            for i in items if i["type"] == "adr"]
    known_ids = {i["id"] for i in items} | {e.get("id") for e in entries if e.get("id")}
    errors = validate_knowledge(entries, known_ids)
    write_knowledge(entries, adrs)
    write_wiki(entries, adrs)
    print(f"Indexed {len(entries)} knowledge entr{'y' if len(entries) == 1 else 'ies'} "
          f"+ {len(adrs)} ADR(s). Wrote knowledge/INDEX.md, knowledge/wiki/ and .harness/knowledge.json")
    for err in errors:
        print(f"  knowledge error: {err}", file=sys.stderr)
    if errors and "--check" in sys.argv:
        sys.exit(1)


if __name__ == "__main__":
    main()
