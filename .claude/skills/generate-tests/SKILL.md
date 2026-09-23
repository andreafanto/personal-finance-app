---
name: generate-tests
description: Launches the test-generator agent to draft JUnit unit tests in Java from a requirement's acceptance criteria, then reviews the draft with the user before committing it. Use when a requirement is architecture_ready and needs tests written, or the user says "/generate-tests" or "write tests for <requirement>".
---

# Generate Tests

Thin launcher: this skill's job is to pick the right requirement(s),
delegate the mechanical drafting to the `test-generator` agent, and then
make sure a human actually looks at the result before it's treated as
done -- the agent works autonomously, but nothing here gets rubber-stamped.

## Boot-up

1. Read `CLAUDE.md`, `.harness/backlog.json` (regenerate first if stale).
2. Determine target requirement(s):
   - If the user named one, use it.
   - Else, list every requirement with `status: architecture_ready` and no
     tests generated yet, and ask the user which to do now (default: all
     of them, oldest first, if the user just says "go").
   - If none qualify, tell the user why (e.g. "req-003 is architecture_ready
     but req-004 still needs an architecture session first") and stop.

## Delegating

For each target requirement, launch the `test-generator` agent (fresh
context -- it has no memory of this conversation) with a self-contained
prompt that includes:
- The full contents of `requirements/req-NNN-*.md`.
- The relevant sections of `architecture/architecture-documentation.md`
  and any ADRs it should follow (package structure, frameworks, storage
  approach).
- Where to write the test file (standard Maven layout:
  `src/test/java/<package>/...`).
- Explicit instruction: write test *signatures and bodies* that assert the
  acceptance criteria, using JUnit 5. Where the acceptance criteria don't
  pin down exact values/behavior, write the test with a clear TODO comment
  and flag it in the agent's report rather than inventing behavior.

## Reviewing the result

When the agent reports back:
1. Show the user a summary of what was generated (file paths, test method
   names, any TODOs/flagged ambiguities the agent surfaced).
2. Ask the user to confirm, or note changes needed. Loop with the agent
   (or edit directly) until the user is satisfied -- this is the one place
   in the test-generation flow where dialogue is expected, even though
   drafting itself is autonomous.
3. Once accepted, update `requirements/req-NNN-*.md`: bump
   `status: tests_generated`, `updated` date.

## Before ending the session (clean-campsite checklist)

1. `python3 .harness/rebuild_index.py`.
2. Commit new/updated files (tests + requirement status updates).
3. Append to `.harness/SESSION_LOG.md` with a resume line -- which
   requirements now have tests, which are still pending, next step is
   normally `/implement`.
