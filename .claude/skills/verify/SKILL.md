---
name: verify
description: Launches the verifier agent to check that tests are green, the implementation actually fulfills the requirement (not just passes its own tests), and surfaces anything missing to the user. Promotes requirements to status done, or blocked with a specific reason. Use when the user says "/verify" or after /implement finishes a batch.
---

# Verify

Thin launcher for the `verifier` agent. Verification is deliberately a
single agent running three checks in sequence (not three separate agents)
because they share context -- which requirement, which tests, which code
-- and are almost always wanted together.

## Boot-up

1. Read `CLAUDE.md`, `.harness/backlog.json` (regenerate first if stale).
2. Collect every requirement with `status: implementing` (i.e. code
   exists, not yet verified). If the user named one, narrow to that.
3. If none qualify, say so.

## Delegating

Launch the `verifier` agent (fresh context) per requirement (or a batch)
with:
- The full `requirements/req-NNN-*.md` (especially acceptance criteria).
- The test file(s) and implementation files involved.
- Instruction to run the three checks, in order, and stop/report clearly
  at whichever one fails rather than continuing past a red state:
  1. **Tests green**: run the relevant test suite, report pass/fail exactly.
  2. **Requirement coverage**: re-read the acceptance criteria one by one
     and check each is actually exercised by a test and satisfied by the
     implementation -- not just "tests pass" but "the tests that exist
     cover what was asked." Flag any acceptance criterion with no
     corresponding test.
  3. **Gaps for the user**: anything the requirement implies that neither
     tests nor code address, anything ambiguous that got resolved by
     assumption during implementation and should be confirmed by a human.

## Reviewing the result

1. Report results to the user plainly: what's actually verified vs. what's
   flagged.
2. If all three checks pass clean: update `requirements/req-NNN-*.md` to
   `status: done`.
3. If anything fails or is flagged: update to `status: blocked`, and write
   the specific reason into the requirement file (a `## Verification notes`
   section) so it's visible without digging through session history.
4. Ask the user how to proceed on anything blocked (back to `/implement`,
   back to `/requirements` if the requirement itself was wrong, or
   accepted as a known gap).

## Before ending the session (clean-campsite checklist)

1. `python3 .harness/rebuild_index.py`.
2. Commit new/updated files.
3. Append to `.harness/SESSION_LOG.md`: what's now done, what's blocked
   and why, explicit resume line for blocked items.
