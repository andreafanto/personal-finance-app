---
name: architecture-session
description: Runs a collaborative architecture dialogue with the user, maintains architecture/architecture-documentation.md as the living "current state" doc, and records individual decisions as ADRs in architecture/ADRs/. Re-invokable any time new input arrives (new requirements, /design-frontend output, /analyse-legacy output) to revisit and amend the architecture. Use for "let's talk architecture", "/architecture-session", or when requirements or new inputs suggest the architecture needs revisiting.
---

# Architecture Session

Goal: keep one coherent, current architecture picture, with every non-
trivial decision traceable to an ADR explaining why.

This skill is re-entered many times over the project's life -- after the
first pass over problems, after `/design-frontend`, after
`/analyse-legacy`, or whenever a requirement surfaces something the
current architecture doesn't account for. Each entry should feel like
"revisit and amend," not "start over."

## Boot-up (do this first, every time)

1. Read `CLAUDE.md`, `domain-vision.md`.
2. Read `architecture/architecture-documentation.md` (current state).
3. Read all `architecture/ADRs/*.md` (at least titles/status -- full text
   for any that look related to today's topic).
4. Read `.harness/backlog.json` / `PROGRESS.md` for which
   problems/requirements exist and their status.
5. If invoked because of new input, read it: `architecture/diagrams/` from
   `/analyse-legacy`, or whatever `/design-frontend` produced.

## The session

1. If `architecture-documentation.md` is still a template (first-ever
   session): have a broad dialogue covering system context, major
   components, data storage approach, how the pieces communicate, and
   deployment shape (self-hosted, per CLAUDE.md). Don't let this become a
   solo lecture -- ask the user's preferences and reasoning, and push back
   where a choice conflicts with stated requirements or the self-hosted /
   local-first constraint.
2. If revisiting: state plainly what changed since the last session (new
   requirements, legacy findings, frontend needs) and what it implies.
   Confirm with the user before amending anything.
3. For every decision point that has real alternatives (framework, storage
   engine, module boundaries, auth approach, etc.), don't just assert a
   choice -- lay out 2-3 realistic options with tradeoffs, get the user's
   call, and write it up as an ADR. Trivial/obvious choices don't need an
   ADR (e.g. "use a .gitignore").
4. Cross-check against `requirements/*.md`: does the architecture actually
   support every `requirements_ready` requirement's acceptance criteria?
   Flag any gap to the user rather than silently leaving it.

## Writing the ADR

Follow the template in `architecture/ADRs/README.md`. Number sequentially
(`adr-0001`, never reused). Link `related_requirements` by id. If a new
ADR reverses an old one, set the old one's `status: superseded` and
`superseded_by`, and the new one's `supersedes` -- never delete or
silently rewrite a past ADR.

## Updating architecture-documentation.md

This file should always describe *current* state, coherently, as if
written fresh today -- not a changelog. After any session that changes
the picture, rewrite the relevant section outright rather than appending.
Keep an up-to-date table mapping each ADR id to a one-line summary so a
reader can find the rationale for anything in the current-state doc.

For any requirement whose acceptance criteria are now architecturally
covered, update that requirement's file: bump `status` to
`architecture_ready` and `updated` date.

## Before ending the session (clean-campsite checklist)

1. `python3 .harness/rebuild_index.py`.
2. Commit new/updated files.
3. Append to `.harness/SESSION_LOG.md`: what was decided, which ADRs were
   added/superseded, which requirements moved to `architecture_ready`, and
   an explicit resume line for anything left open (e.g. "still need to
   decide the auth model for multi-user -- flagged as an open architectural
   question in architecture-documentation.md").
