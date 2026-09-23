# Personal Finance App

## Overview

A self-hosted, web-based personal finance app. Built primarily for personal use, but architected so it could be run by other users/households too (open-source-minded, not a commercial SaaS).

## Who it's for

- Primary user: me, managing my own household finances.
- Secondary: designed so others could self-host and use it for their own finances (multi-user from the data model up), even though there's no monetization plan.

## Business model

Free / open-source, multi-user. No subscription tiers, no billing, no multi-tenant SaaS infrastructure needed.

## Data entry model

Manual entry only. No bank sync (Open Banking/Plaid) and no CSV/OFX import in scope. Users type in transactions themselves.

## Accounts & currency

- Single currency.
- Multiple accounts per user (e.g. checking, savings, credit card, cash).
- No multi-currency support.

## Privacy & security

- Self-hosted / local-first: no dependency on third-party cloud services for core functionality.
- Data stored on infrastructure the user controls (e.g. Docker + Postgres/SQLite).

## Platform

Web app (responsive enough for occasional mobile browser use, not a native app).

## MVP scope: Budgeting & Spending Tracker

### Core entities

- **Accounts** — checking, savings, credit card, cash, etc. Each has a name, type, and running balance.
- **Transactions** — date, amount, account, category, payee/description, optional notes/tags.
- **Categories** — hierarchical (e.g. Food > Groceries, Food > Restaurants), user-customizable.
- **Budgets** — monthly (or custom period) spending limits per category.

### Must-have features

1. Manual transaction entry (quick-add, plus edit/delete)
2. Category management (create/edit/merge/archive categories)
3. Monthly budget setting per category, with rollover option
4. Budget vs. actual view (progress bars, over/under indicators)
5. Spending breakdown by category (period-over-period comparison)
6. Search/filter transactions (by date, category, account, amount, text)
7. Recurring transaction templates (rent, salary) to speed up manual entry
8. Multi-user support from the data model up, even if MVP UI is single-user first

### Explicitly out of scope for MVP

- Transfers between accounts (not treated separately from income/expense in MVP)
- Data export (CSV/JSON)
- Net worth / investment tracking
- Bill reminders / subscription detection
- Savings goals
- Bank sync
- Multi-currency support

## Non-functional / business requirements

- **Self-hosted / local-first**: no dependency on a third-party cloud service for core function.
- **Multi-user capable architecture**: auth + data scoping designed in from the start, even though MVP UI may only expose single-user flows.
- **Simplicity of deployment**: easy self-hosting (e.g. single Docker Compose setup, minimal external dependencies) over exotic infra, since others may run this too.
- **Web app**: responsive for occasional mobile browser use.

## Future (post-MVP) directions

Not in current scope, but noted as the long-term feature areas this app is meant to grow into:

- Net worth & investment tracking (assets, liabilities, investment performance)
- Bill & subscription management (payment reminders, forgotten subscription detection)
- Goal-based saving (progress tracking toward specific savings goals)
- Account transfers as a distinct transaction type
- Data export/portability (CSV/JSON)

---

## The harness

This project uses a project-local harness of skills and agents to take
problems from a vague idea through to verified, implemented code. It lives
entirely under `.claude/`, `.harness/`, `problems/`, `requirements/`, and
`architecture/` in this repo.

### Rule: every backlog item starts with the orchestrator

Whenever anyone starts (or resumes) work on an item in the backlog -- any
problem or requirement in `.harness/backlog.json`, whatever its status --
the first action is to invoke `/orchestrate`, never a stage skill
directly. The orchestrator reads the item's status and open gates, then
either runs the next stage itself (from `architecture_ready` on) or hands
off to the right interactive skill (`/requirements`,
`/architecture-session`, `/design-frontend`) for dialogue stages.

- `/orchestrate` is a main-conversation skill, not a subagent: it must be
  able to launch worker agents and stop for human gates, and a subagent
  can do neither.
- The only exception is `/define-problem` for a brand-new problem, since
  it isn't in the backlog yet.
- Invoking a stage skill directly (e.g. `/implement`) is still allowed
  when the user explicitly asks for it by name.

### The flow

```
/define-problem  -->  problems/prob-NNN-*.md   (+ domain-vision.md)
       |
       v
/requirements  -->  requirements/req-NNN-*.md   (recallable/resumable -- see below)
       |
       +--<-- /design-frontend  (feeds architecture)
       +--<-- /analyse-legacy   (feeds architecture, if applicable)
       v
/architecture-session  -->  architecture/architecture-documentation.md
                              + architecture/ADRs/adr-NNNN-*.md
       |
       v
/generate-tests  -->  test-generator agent  -->  src/test/java/...
       |
       v
/implement  -->  implementer agent  -->  src/main/java/...
       |
       v
[gate, UI requirements only] /design-frontend verification mode
       -->  built UI checked against the Figma design recorded earlier
       -->  mismatch found?  YES --> design_verified: false, STOP -- back to
                                      /implement or /design-frontend, /verify refuses to run
                              NO  --> design_verified: true, proceed
       |
       v
/verify  -->  verifier agent  -->  status: done | blocked
```

The same tail, orchestrated (`/orchestrate`, many requirements at once):

```
architecture_ready reqs
   |  fan out per req
   v
test-generator || test-critic  -->  runs/<id>/tests-*.json, critic-*.json
   |  GATE-4 tests approved
   v
foundation implementer (alone)  -->  implementer || implementer (worktrees)
   |  GATE-3 migrations, GATE-5 suspect/gap flags, GATE-7 merge
   v
verifier suite (once)  -->  verifier coverage || design-checker (UI reqs)
   |  GATE-6 design direction, GATE-7 done with known gaps
   v
orchestrator: statuses + rebuild_index + session log + commit
```

Architecture is not a one-shot step -- `/architecture-session` is
re-entered whenever new input arrives (new requirements, frontend design,
legacy-system findings) to amend the current-state doc and add ADRs.

From `architecture_ready` onward, `/orchestrate` can drive the whole
tail of the flow (tests -> implement -> verify -> design check) for many
requirements at once, in parallel, stopping at the human gates. The
launcher skills still work on their own. See "Orchestration" below.

For any requirement with a UI (`frontend: yes`), the flow is not strictly
linear at the end: implementation must pass through `/design-frontend`'s
verification mode before `/verify` will even start. See "Design
verification gate" below.

### Boot-up ritual

Every skill in this harness reads, in this order, before doing anything
else:

1. `CLAUDE.md` (this file)
2. `domain-vision.md`
3. `.harness/backlog.json` and `.harness/PROGRESS.md` (regenerate first
   with `python3 .harness/rebuild_index.py` if they look stale relative to
   the `problems/`, `requirements/`, `architecture/ADRs/` files)
4. `architecture/architecture-documentation.md` + relevant ADRs
5. Whatever specific problem/requirement file is the active item for that
   session

### The pipeline states

Every problem and requirement file carries a `status` field in its YAML
frontmatter. Requirements move through a fixed pipeline; problems only use
`draft`/`defined`. Never skip states, and never hand-edit
`.harness/backlog.json` or `.harness/PROGRESS.md` directly -- they're
generated by `.harness/rebuild_index.py` from the frontmatter.

```
defined -> requirements_gathering -> requirements_ready -> architecture_ready
        -> tests_generated -> implementing -> verifying -> done
(blocked can apply at any point; ADRs use proposed | accepted | superseded)
```

### Design verification gate

Any requirement with UI is marked `frontend: yes` in its frontmatter by
`/design-frontend` during the design dialogue, along with a `figma:`
reference recorded in `architecture/diagrams/frontend-<topic>.md`. Once
implemented, `/design-frontend` is re-entered in verification mode to pull
the current Figma design (via the Figma MCP tools) and compare it point by
point against the built UI.

- Match: `design_verified: true`, clear to run `/verify`.
- Mismatch: `design_verified: false`, findings written to the frontend
  design doc, and **`/verify` refuses to run for that requirement at all**
  until it's resolved -- either the implementation is fixed or the design
  doc is updated and re-verified. A requirement with `frontend: yes` can
  never reach `status: done` without a clean pass through this gate.
- A requirement with no `frontend` field (or `frontend: no`) has no UI and
  skips this gate entirely.

`.harness/PROGRESS.md` shows a ⛔/✅ marker next to any item with
`frontend: yes` so the gate's state is visible at a glance.

### Orchestration

`/orchestrate` fans work out to worker agents and stops at human gates.
The full contract is `.harness/ORCHESTRATION.md`; the essentials:

- **Parallel stages:** test-generator and test-critic per requirement;
  implementer per requirement in its own git worktree (only after a
  foundation step runs alone, and only across requirements whose
  `modules` don't overlap); verifier split into one whole-suite run
  (never parallel) followed by per-requirement coverage checks in
  parallel with design-checker for UI requirements. Stages also pipeline
  across requirements.
- **Result envelopes:** every worker ends with a small JSON envelope
  (`stage`, `req`, `verdict: ok|needs_human|failed`, `files_touched`,
  `tests`, `flags[]`, `next`). The orchestrator writes it to
  `.harness/runs/<run-id>/<stage>-<req>.json`, validates it with
  `python3 .harness/validate_result.py`, routes on `verdict` + blocking
  flags only, and passes the file into the next stage's prompt.
  `RUN.md` in the same directory is the run's state and gate-decision
  record; run files are committed.
- **Single writer:** only the orchestrator (or a launcher skill run
  standalone) writes frontmatter, run files, the session log, commits,
  merges, and assigns sequence numbers. Workers write only their own code
  area.
- **Human gates** (automatic moves may only go backwards or to
  `blocked`; forward past a gate needs a human):
  GATE-1 requirement sign-off, GATE-2 ADR acceptance, GATE-3 any DB
  schema migration, GATE-4 test approval, GATE-5 `test_suspect`/`arch_gap`
  flags, GATE-6 "change the design" on a mismatch, GATE-7 merging worktree
  branches and `done` with known gaps. GATE-1/2 live in the interactive
  skills; the orchestrator refuses items that haven't passed them.
- **Retry limit:** 2 implement retries per requirement per run, then
  escalate.

### Skills (interactive -- run in the main conversation so they can talk
to you)

- `/define-problem` -- Socratic dialogue to scope a new problem.
- `/requirements` -- **the recallable one.** Always resumable: invoke it
  with no argument and it figures out whether to resume an in-progress
  interview or start the next undefined problem. This is how you get back
  into requirements engineering after any break, long or short.
- `/architecture-session` -- broad architecture dialogue, re-entrant.
- `/design-frontend` -- frontend/UI structure dialogue grounded in Figma,
  feeds architecture. Re-entrant post-implementation in **verification
  mode**, where it checks the built UI against the Figma design and gates
  `/verify` on the result -- see "Design verification gate" above.
- `/analyse-legacy` -- describes an existing/legacy system, feeds
  architecture. Skip if there's no legacy system.
- `/generate-tests`, `/implement`, `/verify` -- thin launchers that hand
  the mechanical work to an agent, then review the result with you before
  it counts as done. These stay interactive at the review step even
  though drafting/implementing/checking itself is autonomous. `/verify`
  additionally enforces the design verification gate before it will even
  start, for any requirement with `frontend: yes`.
- `/orchestrate` -- drives many requirements through the tail of the flow
  in parallel, stopping at human gates. Resumable: with no argument it
  continues the latest run with open gates.

### Agents (autonomous, isolated context, invoked by the launcher skills
above -- not meant to be talked to directly)

- `test-generator` -- drafts JUnit 5 tests from a requirement.
- `implementer` -- writes production code to satisfy tests + requirement.
  Never edits tests; stops and reports if a test looks wrong.
- `test-critic` -- read-only adversarial review of drafted tests against
  the acceptance criteria, so the human's test review shrinks to its
  flags.
- `verifier` -- three checks (tests green, requirement coverage, flagged
  gaps). `full` mode runs all three in sequence (standalone `/verify`);
  under `/orchestrate` it runs as one `suite` pass over the merged tree,
  then `coverage` passes per requirement in parallel.
- `design-checker` -- read-only comparison of built UI against its Figma
  design; the autonomous half of `/design-frontend` verification mode.

Every agent ends its report with the result envelope defined in
`.harness/ORCHESTRATION.md`.

### File/ID conventions

- `problems/prob-NNN-slug.md`, `requirements/req-NNN-slug.md` (NNN and
  slug mirror the parent problem), `architecture/ADRs/adr-NNNN-slug.md`.
- IDs are sequential and never reused, even if a problem/requirement is
  later abandoned -- mark it `status: blocked` or note it as superseded,
  don't renumber.
- Frontmatter stays flat (scalar `key: value` only, comma-separated for
  list-like fields such as `tags`) so `.harness/rebuild_index.py` can
  parse it without a YAML library.
- Requirements at `architecture_ready` or later carry
  `modules: a, b` (set by `/architecture-session`; `core` for shared
  foundations, and a missing field counts as `core`). `/orchestrate` uses
  it to decide what can be implemented in parallel.
- Worker results live in `.harness/runs/<YYYYMMDD-HHMM>/` as
  `<stage>-<req>.json` plus `RUN.md`.
- Requirements with a UI additionally carry `frontend: yes` and
  `design_verified: true|false`, set by `/design-frontend` (design dialogue
  and verification mode respectively). See "Design verification gate"
  above.

### Java/build conventions (assumed default -- flag if this should change)

Standard Maven layout: `src/main/java/...`, `src/test/java/...`, JUnit 5.
No `pom.xml` exists yet -- `/implement`'s first real run should set one up
following whatever the architecture session decides for dependencies.

### Clean-campsite checklist (every skill does this before a session ends)

1. Run `python3 .harness/rebuild_index.py` so the backlog/progress tracker
   reflect reality.
2. Leave git clean: commit new/updated files (confirm with the user first
   if unrelated uncommitted work is present that isn't part of this
   session).
3. Commit any `.harness/runs/` files written this session; list (don't
   delete) unmerged worktree branches.
4. Append an entry to `.harness/SESSION_LOG.md` with an explicit "resume
   here" line -- specific enough that a cold read of just that line tells
   you exactly what to do next.
