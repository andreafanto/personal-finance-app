---
name: remember
description: Captures confirmed domain knowledge into the harness's working memory (knowledge/kn-NNNN-*.md) -- glossary terms, domain rules, conventions/style guide, constraints, context facts -- and routes decisions to proposed ADRs. Also supersedes or retracts existing entries. Its main trigger is opening a merge/pull request -- the memory-gate hook blocks MR/PR creation until this skill has run in MR mode. Also use when the user says "/remember", "remember that...", "note this down", "add to the glossary/style guide", "that's a rule", "write an ADR for this".
---

# Remember

Goal: turn knowledge that came up in conversation into durable memory
entries that a cold-start session or an isolated agent can read and apply
correctly. The schema is in `knowledge/README.md`. Follow it exactly.

## When it runs

- **MR mode (the main trigger).** Opening a merge/pull request is the
  signal to save memory. `.claude/hooks/memory-gate.sh` blocks
  `gh pr create`, `glab mr create`, `git push -o merge_request.create`,
  and MCP create-PR/MR tools. The block stays until
  `.harness/.memory-captured` holds the current HEAD sha. When it
  blocks, run this skill in MR mode, then retry the same MR command.
- **Explicit mode.** The user asks to remember a specific thing. Capture
  it right away. No MR is needed.

Dialogue skills do not capture at session end. They only add unconfirmed
`Knowledge candidates:` notes to their `.harness/SESSION_LOG.md` entry,
so MR mode has something to work from after the conversation is gone.

## Boot-up

1. Read `knowledge/README.md` (schema and "what goes where").
2. Run `python3 .harness/rebuild_index.py`, then read `knowledge/INDEX.md`.
   You need the current entries and tags to avoid duplicates.
3. MR mode only: find the base branch with
   `git merge-base HEAD origin/main`, falling back to `main`. Everything
   between the base and HEAD is "this MR".

## 1. Collect candidates

- **Explicit mode:** the user's text ("remember that X") is the one
  candidate.
- **MR mode:** gather from all of these sources, because the
  conversations that produced the work may be long gone:
  - `Knowledge candidates:` lines in the `.harness/SESSION_LOG.md`
    entries added on this branch (`git diff <base>...HEAD -- .harness/SESSION_LOG.md`)
  - the branch diff of `problems/`, `requirements/`, `architecture/`,
    `domain-vision.md`. Look at terms defined in requirement text, rules
    that apply beyond one requirement, and conventions set by new ADRs
  - conventions that the code on the branch establishes and that the user
    stated or approved (not ones you infer from the code alone)
  - the current conversation, if there is one
- In either mode, keep only knowledge the user **stated or confirmed**:
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

1. If anything changed, commit the new and changed files in
   `knowledge/` and `architecture/ADRs/`, plus `.harness/knowledge.json`,
   on the current branch. Append a `.harness/SESSION_LOG.md` entry that
   lists the ids written, superseded, or retracted, and include it in
   the same commit.
2. **MR mode:** open the MR gate:
   `git rev-parse HEAD > .harness/.memory-captured`. Write it **after**
   the commit, because the gate compares against HEAD. Write it also
   when nothing was worth capturing. "Reviewed, nothing new" is a valid
   outcome, and the user's confirmation of that outcome counts as the
   capture.
3. **MR mode:** retry the MR command that the gate blocked. Add a
   `## Working memory` section to the MR description that lists each
   id added, superseded, or retracted with its summary, or says
   "reviewed, nothing new". Reviewers then see memory changes next to
   the code changes that caused them.

If more commits land on the branch after capture, HEAD moves and the
gate closes again. The next MR command (for example a new MR from the
same branch) then triggers another capture, which only needs to look at
commits since the previous capture.
