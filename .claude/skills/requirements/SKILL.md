---
name: requirements
description: The recallable requirements-engineering skill. Interviews the user in depth on one problem at a time to produce requirements/req-NNN-slug.md. Always resumable -- invoking this with no argument picks up wherever the last interview left off, or starts the next undefined problem. Use whenever the user wants to dig into requirements, resume a stalled requirements session, or says "let's do requirements" / "/requirements".
---

# Requirements

Goal: for one problem at a time, understand deeply enough to write
requirements someone could implement and test against, through interview,
not assumption.

This is the harness's resumability anchor. It must always be safe to walk
away mid-interview and come back later -- to this skill, by name -- and
pick up exactly where you left off.

## Boot-up (do this first, every time)

1. Read `CLAUDE.md`, `domain-vision.md`.
2. Read `.harness/backlog.json` (regenerate first with
   `python3 .harness/rebuild_index.py` if it looks stale).
3. Determine what to work on, in this priority order:
   a. If the user named a specific problem/requirement id, use that.
   b. Else, if any requirement is `status: requirements_gathering`
      (an interview was started but not finished), resume that one --
      read the partial `requirements/req-NNN-*.md` file, especially its
      "Open questions" section, and pick up from there. Tell the user
      explicitly what you're resuming and roughly where it was left.
   c. Else, pick the oldest `problem` with `status: defined` that has no
      corresponding requirement file yet, and start a fresh interview.
   d. If nothing qualifies, tell the user everything has requirements
      already and ask whether to revisit one or run /define-problem first.

## The interview

For the chosen problem, read its `problems/prob-NNN-*.md` file fully first.
Then interview the user to surface, for this one problem:

- **Functional needs**: what must the system actually do, concretely.
- **Actors**: who/what triggers this, who consumes the result.
- **Rules and edge cases**: boundaries, invalid states, what happens when
  things go wrong or data is missing/ambiguous.
- **Non-functional constraints**: anything about performance, data
  integrity, privacy that matters here specifically (don't repeat generic
  harness-wide constraints already in CLAUDE.md -- only what's specific to
  this requirement).
- **Acceptance criteria**: phrased so they're directly testable. Prefer
  Given/When/Then where it fits naturally; don't force it where plain
  bullet criteria are clearer.
- **Explicit non-goals** for this requirement, distinct from the parent
  problem's out-of-scope section.

Interview technique:
- Ask one focused question at a time, not a checklist dump.
- When the user gives a vague answer, ask for a concrete example.
- Surface conflicts with existing requirements or the domain vision if you
  spot any, and resolve them in dialogue rather than silently picking one.
- It's fine, and expected, to end a session with unresolved questions --
  write them into the file's "Open questions" section rather than guessing.

## Writing the file

`requirements/req-NNN-slug.md`, where NNN matches the parent problem's
number and slug matches its slug (one requirement file per problem, per
the harness's problem:requirement = 1:1 model):

```markdown
---
id: req-NNN
type: requirement
title: "Mirrors the problem title"
problem_id: prob-NNN
status: requirements_gathering
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# Requirements: <title>

## Functional requirements

## Actors

## Rules and edge cases

## Non-functional constraints (specific to this requirement)

## Acceptance criteria

Given/When/Then or bullet form, testable.

## Explicit non-goals

## Open questions

Anything still unresolved -- this is what the next /requirements session
resumes from.
```

Set `status: requirements_ready` only when the user explicitly confirms
they're satisfied and there are no blocking open questions left (non-
blocking "nice to know later" questions can remain listed).

## Before ending the session (clean-campsite checklist)

1. `python3 .harness/rebuild_index.py`.
2. Commit new/updated files (confirm with user if unrelated uncommitted
   work exists).
3. Append to `.harness/SESSION_LOG.md` with an exact resume line -- this
   is the most important log entry in the whole harness, since /requirements
   existing to always be resumable depends on it. Name the requirement id
   and the precise next question/topic if the interview isn't finished.
