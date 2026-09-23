---
name: implement
description: Launches the implementer agent to pick up all open tasks (requirements with tests_generated but not yet implemented) and write the Java code to make those tests pass. Use when the user says "/implement", "implement the code", or there's a backlog of tests_generated requirements ready to build.
---

# Implement

Thin launcher: find the open work, hand it to the `implementer` agent,
report back what it did. The agent runs autonomously and should not need
to interrupt the user mid-implementation -- if it hits a genuine ambiguity
the tests/requirements don't resolve, it should stop and report rather
than guess, and this skill surfaces that to the user.

## Boot-up

1. Read `CLAUDE.md`, `.harness/backlog.json` (regenerate first if stale).
2. Collect every requirement with `status: tests_generated`. If the user
   named a specific one, narrow to that; otherwise this is the full batch
   ("pick all the open tasks").
3. If none qualify, say so (point at what's blocking -- e.g. nothing has
   reached `tests_generated` yet, run `/generate-tests` first).

## Delegating

Launch the `implementer` agent (fresh context) with a self-contained
prompt per batch (one invocation covering all target requirements is fine
-- the agent can work through them in sequence) including:
- The full contents of each target `requirements/req-NNN-*.md` and its
  test file(s).
- `architecture/architecture-documentation.md` and relevant ADRs.
- Explicit instruction: implement the minimum correct code to satisfy the
  tests and requirements, following existing code conventions in `src/`
  once any exist. Do not modify the tests to make them pass -- if a test
  looks wrong given the requirement, stop and report the discrepancy
  instead of changing the test.
- Instruction to run the test suite itself as it goes (fast feedback loop)
  but not to treat "tests pass" alone as done -- it should also re-read
  the requirement's acceptance criteria and sanity-check coverage.

## Reviewing the result

When the agent reports back:
1. Summarize for the user: what was implemented, files touched, test
   results, and anything the agent flagged as ambiguous or unresolved.
2. For each fully implemented requirement, update
   `requirements/req-NNN-*.md`: bump `status: implementing` ->
   the agent should have already set it to reflect reality; if tests are
   green and the agent is confident, leave status as `implementing` --
   `/verify` is what promotes it to `done`. Do not self-certify here.

## Before ending the session (clean-campsite checklist)

1. `python3 .harness/rebuild_index.py`.
2. Commit new/updated files.
3. Append to `.harness/SESSION_LOG.md`: what got implemented, what's
   flagged, resume line pointing at `/verify` next (or back at this skill
   for anything the agent couldn't finish).
