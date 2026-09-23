---
name: design-frontend
description: Dialogue-driven session to design the frontend/UI approach (screens, navigation, key interactions) for a requirement or the app as a whole. Output feeds into /architecture-session. Use when the user wants to design or discuss frontend/UI structure before or alongside architecture decisions.
---

# Design Frontend

Goal: work out the frontend shape -- screens, navigation, key interactions,
state ownership between client and server -- through dialogue, in enough
detail that `/architecture-session` can make informed decisions about how
the frontend and backend fit together.

This is not a visual design tool -- no pixel-level mockups. It's about
structure: what screens/views exist, what data each needs, how they
connect, and what that implies architecturally (e.g. does this need
real-time updates, optimistic UI, a particular API shape).

## Boot-up

1. Read `CLAUDE.md`, `domain-vision.md`.
2. Read `requirements/*.md` with `status: requirements_ready` or later --
   frontend design should be grounded in actual requirements, not
   invented from scratch.
3. Read `architecture/architecture-documentation.md` for any existing
   frontend-relevant decisions.

## The dialogue

1. Ask which requirement(s) or area this session is about (or "the whole
   app" for a first pass).
2. For each: what screens/views does the user picture, what does each
   need to show, what actions can happen there, what triggers navigation
   between them.
3. Probe for structural implications: does anything need to update live?
   Does anything need offline behavior? Are there shared components across
   screens that imply a design system decision?
4. Push back gently on anything that implies backend capability the
   requirements/architecture don't yet support -- flag it for
   `/architecture-session` rather than silently assuming it'll work.

## Output

Write findings to `architecture/diagrams/frontend-<topic>.md` (a simple
markdown description of screens/flow is fine; use an actual diagram --
e.g. a Mermaid flowchart in a fenced code block -- only where it clarifies
navigation/state flow better than prose).

## Before ending the session

1. Tell the user explicitly: "This should feed into `/architecture-session`
   next" -- this skill doesn't update architecture-documentation.md itself.
2. Commit new/updated files.
3. Append a resume line to `.harness/SESSION_LOG.md`.
