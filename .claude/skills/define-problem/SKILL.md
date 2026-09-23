---
name: define-problem
description: Runs a Socratic dialogue with the user to define a single problem clearly, writes problems/prob-NNN-slug.md, and updates the domain vision statement. Use when the user wants to explore, scope, or add a new problem the harness should eventually solve -- not for requirements detail (that's /requirements) or architecture (that's /architecture-session).
---

# Define Problem

Goal: turn a vague idea into a sharply-stated problem definition, through
dialogue, not through writing prose at the user. You are a skeptical
collaborator here, not a stenographer -- your job includes pushing back.

## Boot-up (do this first, every time)

1. Read `CLAUDE.md` at the repo root.
2. Read `domain-vision.md`.
3. Read `.harness/PROGRESS.md` and `.harness/backlog.json` if they exist,
   so you know what problems already exist and don't duplicate one.
4. Skim `problems/*.md` titles/status if PROGRESS.md is stale or missing.

## If domain-vision.md is still a template (unfilled)

Before defining any specific problem, have a short dialogue to fill it in:
what is this system, who is it for, what does success look like, what's
explicitly out of scope. Keep it tight -- a few exchanges, not an essay.
Write the answers into `domain-vision.md`, replacing the TODOs. This can
and should be revisited later as problems reveal the vision was wrong;
don't treat it as sacred once written.

## The dialogue

1. Ask the user what problem they want to explore. Take whatever they give
   you -- a feature idea, a pain point, a complaint -- as a *starting*
   point, not the final statement.
2. Interrogate it. Useful moves, pick what fits:
   - "What actually happens today, concretely, that's a problem?"
   - "Is this the problem, or a symptom of something else?"
   - "Who is affected, and how often?"
   - "What would 'solved' look like? How would you know?"
   - "What's explicitly NOT part of this problem?"
   - "What have you already ruled out, and why?"
   - Name any assumption you see them making and ask if it's load-bearing.
3. Push back on anything vague, overly broad, or solution-shaped-disguised-
   as-a-problem (e.g. "I need a dashboard" is a solution; the problem is
   whatever makes them want a dashboard). Don't accept the first phrasing.
4. Keep going until you and the user are both satisfied the problem is
   stated precisely enough that someone else could read it and know what's
   in and out of scope. Don't rush this -- but don't manufacture disagreement
   either; when it's genuinely clear, say so and move to writing it up.

## Writing the file

Determine the next sequential id by checking existing `problems/prob-*.md`
files (or `.harness/backlog.json`). Slugify the title (lowercase, hyphens).

Write `problems/prob-NNN-slug.md`:

```markdown
---
id: prob-NNN
type: problem
title: "Short problem title"
status: defined
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: comma, separated, flat, list
---

# Problem: <title>

## Statement

One or two sentences, precise.

## Context / evidence

Why this is real, concretely -- not hypothetical.

## Who's affected and how

## In scope

## Explicitly out of scope

## Open questions

Anything still unresolved that a /requirements session should probe further.
```

Use `status: draft` instead of `defined` if the user wants to stop before
the dialogue converges (see clean-campsite handling below).

## Before ending the session (clean-campsite checklist)

1. Run `python3 .harness/rebuild_index.py` so the backlog/progress tracker
   reflect the new/updated problem file.
2. If this is a git repo with changes, stage and commit the new/updated
   files (ask the user first if uncommitted work already existed that
   wasn't yours).
3. Append an entry to `.harness/SESSION_LOG.md`: what problem was defined
   (or how far the dialogue got if incomplete), and an explicit "resume
   here" line -- e.g. "continue the /define-problem dialogue for prob-004,
   we'd gotten as far as scoping out multi-account edge cases" or "run
   /requirements for prob-003, no problems left undefined."
