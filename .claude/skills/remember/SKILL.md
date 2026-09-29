---
name: remember
description: Captures confirmed domain knowledge from the current conversation into the harness's working memory (knowledge/kn-NNNN-*.md) -- glossary terms, domain rules, conventions/style guide, constraints, context facts -- and routes decisions to proposed ADRs. Also supersedes or retracts existing entries. Use when the user says "/remember", "remember that...", "note this down", "add to the glossary/style guide", "that's a rule", "write an ADR for this", or when a dialogue skill reaches its capture step.
---

# Remember

Goal: turn knowledge that came up in conversation into durable memory
entries that a cold-start session or an isolated agent can read and apply
correctly. The schema is in `knowledge/README.md`. Follow it exactly.

## Boot-up

1. Read `knowledge/README.md` (schema and "what goes where").
2. Run `python3 .harness/rebuild_index.py`, then read `knowledge/INDEX.md`.
   You need the current entries and tags to avoid duplicates.

## 1. Collect candidates

- If the user gave explicit text ("remember that X"), that is the one
  candidate.
- If invoked with no text, or from a dialogue skill's capture step, scan
  the conversation for knowledge the user **stated or confirmed**:
  - words the user defined, or used with a specific meaning -> `term`
  - "always / never / must / can't / only if" statements about the
    domain -> `rule`
  - how things should be named, written, formatted, structured -> `convention`
  - limits on scope, performance, privacy, deployment -> `constraint`
  - facts about the user, household, or environment that shape
    decisions -> `fact`
  - "we chose X over Y because..." -> an **ADR**, not a knowledge entry
- Drop anything that is:
  - only your inference, not something the user said or agreed to
  - already stated in CLAUDE.md, a requirement file, or an ADR (link it
    with `related` if a new entry depends on it)
  - only useful for this conversation

## 2. Check against memory

For each candidate, search the index (and `grep -ril` on `knowledge/`
for key words):

- **Same fact already exists:** skip it. Or, if the new wording is
  clearer or adds an example, propose an in-place edit.
- **Contradicts an active entry:** do not choose silently. Show both to
  the user and ask which is true now. If the new one wins, it supersedes
  the old one (see step 4).
- **New:** propose it.

## 3. Confirm with the user

Show all proposals in one message, compactly:

```
1. [rule] Budget rollover carries unspent amount only
   "At period end, a category's unspent budget adds to next period's limit; overspend does not reduce it."
   why: user wants rollover to reward saving (req-003 interview) · tags: budget, rollover
2. [supersedes kn-0004] ...
3. [ADR, proposed] Use SQLite as the default store ...
```

Ask the user to accept, edit, or drop each one. Write only what they
accept. Nothing is written to memory without confirmation.

## 4. Write

**Knowledge entry:**
- Next id = highest existing `kn-NNNN` + 1, zero-padded to 4 digits.
  Include retired entries, because ids are never reused.
- File `knowledge/kn-NNNN-<slug>.md`, following the README template:
  frontmatter, then statement, **Why:**, **How to apply:**, optional
  **Example:**.
- `summary` must make sense alone, because it is all an agent sees in
  the index. Max 200 chars. Be concrete: "Amounts are stored as integer
  minor units (cents)", not "Amount storage convention".
- `source`: the active item id if there is one, else
  `session <today> /<skill that is running>`.
- Superseding: new entry gets `supersedes: kn-OLD`. Old entry gets
  `status: superseded`, `superseded_by: kn-NEW`, and a bumped `updated`.
- Retracting: `status: retracted`, bumped `updated`, and a
  `**Retracted <date>:** <reason>` line at the end of the body.

**ADR (decision-shaped candidate):**
- Next id = highest existing `adr-NNNN` + 1. Use the template in
  `architecture/ADRs/README.md` with `status: proposed`.
- Fill Context, Decision, Alternatives considered, and Consequences from
  the conversation. If the alternatives were not discussed, write
  that down. Do not invent a comparison.
- Tell the user that acceptance (GATE-2) and the update to
  `architecture-documentation.md` happen in `/architecture-session`.
  This skill does not accept ADRs.

## 5. Validate and index

Run `python3 .harness/rebuild_index.py --check`. Fix every reported
error before you continue. Show the user the new lines in
`knowledge/INDEX.md`.

## Before ending

- **If this skill ran standalone:** commit the new and changed files in
  `knowledge/` and `architecture/ADRs/` plus `.harness/knowledge.json`.
  Then append a `.harness/SESSION_LOG.md` entry that lists the ids
  written, superseded, or retracted.
- **If a dialogue skill called it at its capture step:** do not commit
  or log. The calling skill's clean-campsite checklist covers that.
