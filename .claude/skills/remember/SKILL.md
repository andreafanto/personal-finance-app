---
name: remember
description: Captures confirmed domain knowledge into the harness's working memory (knowledge/kn-NNNN-*.md) -- glossary terms, domain rules, conventions/style guide, constraints, context facts -- and routes decisions to proposed ADRs. Also supersedes or retracts entries. Runs automatically -- the memory-signal hook flags memory-worthy user messages (new terms, corrections, rules) and the memory-gate hook runs a check before every git commit -- and also when the user says "/remember", "remember that...", "note this down", "add to the glossary/style guide", "that's a rule", "write an ADR for this", or answers "yes" to a "Save to memory?" prompt.
---

# Remember

Goal: turn knowledge that comes up while working into durable memory
entries that a cold-start session or an isolated agent can read and apply
correctly. The schema is in `knowledge/README.md`. Follow it exactly.

## When it runs

Detection is automatic. Saving always needs the user's confirmation.

1. **Live (every user message).** `.claude/hooks/memory-signal.sh`
   (UserPromptSubmit) scans each message for the signals below and
   injects a "Memory check" note when it finds one. The hook uses
   keyword heuristics, so treat its note as a hint. You are the real
   detector: also act on signals it cannot see, for example a correction
   that uses no keyword. When a message contains durable knowledge that
   is not yet recorded, finish the user's task first. Then end the reply
   with **one** line:
   `Save to memory? [rule] Rollover carries unspent amount only -- yes / edit / later / no`
   Put several candidates in one prompt. Ask at most once per reply. Do
   not ask again about something the user declined in this session.
2. **Commit check (every `git commit`).** `.claude/hooks/memory-gate.sh`
   (PreToolUse) denies the first commit attempt for any change set that
   touches paths outside `knowledge/` and `.harness/`. Then:
   - Review the change set.
   - Ask the user about any candidates.
   - Write the accepted ones and stage them.
   - Run `.claude/hooks/memory-gate.sh --mark`.
   - Retry the same commit.

   If nothing qualifies, run `--mark` and retry without asking. The mark
   is a fingerprint of the uncommitted changes, so any later edit starts
   a new check.
3. **Explicit.** The user asks to remember something. Capture it right
   away.

User answers:
- **yes**: run steps 2-5 below for that item.
- **edit**: take the user's wording, then confirm again.
- **later**: append the item to `.harness/memory-pending.md`. The next
  commit check brings it up again.
- **no**: drop it for the rest of this session.

## When to save -- the triggers

Watch for these situations. Each one names the kind it usually becomes.

| # | Situation | Example | Kind |
|---|-----------|---------|------|
| 1 | **User introduces or defines a term** | "by *household* I mean everyone sharing accounts"; a quoted or new noun that is not in the glossary | `term` |
| 2 | **User corrects you** | "no, a budget period is a calendar month, not 30 days" | whatever was wrong: `rule` / `fact` / `term`. **Supersede** the entry if one exists |
| 3 | **User uses a term differently from the glossary** | glossary says "payee" but the user says "merchant" for salary | `term`. Ask: rename, synonym, or supersede? |
| 4 | **User states an invariant** | "a transfer must never count as spending" | `rule` |
| 5 | **User sets a style, naming, or format preference** | "name it payee, not merchant"; "amounts in cents"; "dates as DD/MM" | `convention` |
| 6 | **User draws a scope line** | "savings goals are out of scope for MVP" | `constraint` |
| 7 | **User shares context about their situation** | "I have a joint account with my partner" | `fact` |
| 8 | **User chooses between alternatives** | "let's go with SQLite" | **ADR** (proposed) |
| 9 | **User rejects your proposal and gives a reason** | "no soft deletes, the audit log covers it" | `rule` / `convention` (negative knowledge) |
| 10 | **User has to explain the same thing twice** | a second explanation of how rollover works | whatever it is. The repeat shows it should have been in memory already |
| 11 | **An edge-case answer applies beyond one requirement** | "uncategorised transactions always count in 'Other'" | `rule` (a rule for one requirement stays in its file) |
| 12 | **A contradiction comes up** | `/recall` conflict, verifier flag, test disagrees with an entry | supersede or retract, after the user decides |
| 13 | **A commit sets a convention the user approved** | first repository class, error-response format, package layout | `convention` |
| 14 | **A gate outcome carries a reason** | design mismatch resolved with "change the design, because…"; ADR accepted with conditions | `rule` / `convention` |

Not triggers: one-off task instructions ("run the tests"), things you
inferred but the user never said, and anything already recorded in
CLAUDE.md, a requirement, or an ADR.

## Boot-up

1. Read `knowledge/README.md` (schema and "what goes where").
2. Run `python3 .harness/rebuild_index.py`, then read `knowledge/INDEX.md`.
   You need the current entries and tags to avoid duplicates.

## 1. Collect candidates

- **Live / explicit:** the flagged message, or the user's text.
- **Commit check:** gather from these sources:
  - the change set: `git diff --cached`, plus `git diff` for `-a`.
    Look closely at `problems/`, `requirements/`, `architecture/`,
    `domain-vision.md`, and conventions the new code sets that the user
    approved in this conversation
  - this conversation: triggers that were not yet prompted or were
    answered "later"
  - open items in `.harness/memory-pending.md`
- In every case, keep only knowledge the user **stated or confirmed**.
  Drop your own inferences, things already recorded elsewhere (link them
  with `related` instead), and anything that only matters for this
  conversation.

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

Live: use the one-line prompt above. Commit check with several items:
use one compact list (or AskUserQuestion with multiSelect):

```
1. [rule] Budget rollover carries unspent amount only
   "Unspent budget adds to next period's limit; overspend does not reduce it."
   why: user corrected the earlier assumption (req-003 interview) · tags: budget, rollover
2. [supersedes kn-0004] ...
3. [ADR, proposed] Use SQLite as the default store ...
```

Write only what the user accepts. Nothing is written to memory without
confirmation.

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
- `created` / `updated`: today. The daily wiki is built from these dates.
- For a correction (trigger 2), say in **Why:** what was wrong before.
- Superseding: new entry gets `supersedes: kn-OLD`. Old entry gets
  `status: superseded`, `superseded_by: kn-NEW`, and a bumped `updated`.
- Retracting: `status: retracted`, bumped `updated`, and a
  `**Retracted <date>:** <reason>` line at the end of the body.
- Remove the item from `.harness/memory-pending.md` if it was listed there.

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

Run `python3 .harness/rebuild_index.py --check`. This also regenerates
the daily wiki (`knowledge/wiki/`). Fix every reported error before you
continue. Tell the user the new ids in one line.

## Committing

- **Commit check:** stage the memory files (`knowledge/`,
  `architecture/ADRs/`, `.harness/knowledge.json`,
  `.harness/memory-pending.md`) into the commit that was blocked. Then
  run `--mark` and retry.
- **Live / explicit:** leave the files for the next commit. That commit
  picks them up, and the commit check then has nothing new to ask about
  them.
