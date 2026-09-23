---
name: design-frontend
description: Dialogue-driven session to design the frontend/UI approach (screens, navigation, key interactions) for a requirement or the app as a whole, grounded in a Figma design where one exists. Output feeds into /architecture-session. Re-entrant post-implementation to verify the built UI against the Figma design -- /verify refuses to mark a UI requirement done until that verification passes. Use when the user wants to design or discuss frontend/UI structure, or to check implementation against Figma.
---

# Design Frontend

Goal: work out the frontend shape -- screens, navigation, key interactions,
state ownership between client and server -- through dialogue, in enough
detail that `/architecture-session` can make informed decisions about how
the frontend and backend fit together. Later, once implemented, this skill
is re-entered in **verification mode** to confirm the build actually
matches the design it was based on.

This is not a visual design tool -- no pixel-level mockups produced here.
Where a Figma design exists, it *is* the visual source of truth; this
skill's job in the design phase is to translate it into structural
decisions, and in the verification phase to hold implementation
accountable to it.

## Boot-up

1. Read `CLAUDE.md`, `domain-vision.md`.
2. Read `requirements/*.md` with `status: requirements_ready` or later --
   frontend design should be grounded in actual requirements, not
   invented from scratch.
3. Read `architecture/architecture-documentation.md` for any existing
   frontend-relevant decisions.
4. Check `.harness/backlog.json` for any requirement with
   `frontend: yes` and `status: implementing` -- that's a candidate for
   **verification mode** (see below) rather than a fresh design session.
   If the user's request is ambiguous about which mode they want, ask.

## Mode 1: Design dialogue (pre-implementation)

1. Ask which requirement(s) or area this session is about (or "the whole
   app" for a first pass).
2. Ask whether a Figma design already exists for this. If yes, get the
   Figma file/frame link(s) and use the Figma MCP tools
   (`get_design_context`, `get_screenshot`, `get_variable_defs`,
   `get_metadata`) to pull the actual design -- screens, components,
   layout, and design tokens (colors, spacing, typography) -- rather than
   taking the user's verbal description as the source of truth. If no
   Figma design exists yet, run the dialogue from prose as before, and say
   plainly that there's no visual source of truth to verify against later
   (verification mode won't have anything to check).
3. For each screen: what does it show, what actions can happen there,
   what triggers navigation between them. Where a Figma design exists,
   confirm your read of it with the user rather than re-deriving structure
   from scratch -- Figma is authoritative, the dialogue is about closing
   any gaps it doesn't answer (data sources, state ownership, what happens
   on error/empty/loading).
4. Probe for structural implications: does anything need to update live?
   Does anything need offline behavior? Are there shared components across
   screens that imply a design system decision?
5. Push back gently on anything that implies backend capability the
   requirements/architecture don't yet support -- flag it for
   `/architecture-session` rather than silently assuming it'll work.

### Output (design dialogue)

Write findings to `architecture/diagrams/frontend-<topic>.md`, including a
`figma:` frontmatter field with the file/frame link(s) used (or `none` if
no Figma design exists), so verification mode later knows exactly what to
check against:

```markdown
---
figma: https://www.figma.com/design/<file-key>/<name>?node-id=<id>
---

# Frontend design: <topic>
...
```

Also set, on every `requirements/req-NNN-*.md` this session covered,
`frontend: yes` in the frontmatter (default is effectively "no" if the
field is absent) -- this is what tells `/verify` a design-verification
gate applies before that requirement can be marked done.

## Mode 2: Design verification (post-implementation)

Triggered when re-entering this skill for a requirement that has
`frontend: yes` and implemented UI code exists (typically right after
`/implement`, or because `/verify` refused to proceed and pointed back
here).

1. Load the recorded `figma:` reference from
   `architecture/diagrams/frontend-<topic>.md`. If it's `none`, tell the
   user there's nothing to verify against and ask how they want to
   proceed (skip the gate deliberately, or do a retroactive Figma design
   session first) -- don't silently mark it verified.
2. Pull the current, authoritative design from Figma via the MCP tools
   (`get_design_context` for structure/content, `get_screenshot` for the
   visual, `get_variable_defs` for design tokens).
3. Read the actual implemented frontend code (and run the app via the
   `run` skill if available, to see it rendered, rather than judging
   purely from markup).
4. Compare, point by point, and list every mismatch explicitly and
   concretely -- not "looks a bit off," but e.g. "Figma spec has the
   budget progress bar in the warning color at 80% threshold; implemented
   component only changes color at 100%," or "Figma has a cancel action on
   this screen; implementation has none." Also confirm what *does* match,
   don't only report negatives.
5. **If any mismatch is found:**
   - Do not set `design_verified: true`.
   - Write the mismatch list into
     `architecture/diagrams/frontend-<topic>.md` under a
     `## Verification findings (<date>)` section.
   - Set `design_verified: false` in the requirement's frontmatter and
     add a short `## Design verification: BLOCKED` section to
     `requirements/req-NNN-*.md` summarizing why.
   - Tell the user plainly: **this requirement cannot proceed to
     `/verify` until the mismatch is resolved** -- either fix the
     implementation (back to `/implement`) or, if the design itself
     should change, update Figma and re-run this verification. Do not
     soften this into a suggestion.
6. **If everything matches:** set `design_verified: true` and `updated`
   date on the requirement's frontmatter, and tell the user it's clear to
   proceed to `/verify`.

## Before ending the session

1. Tell the user explicitly what's next: "This should feed into
   `/architecture-session`" (design dialogue mode) or "clear to run
   `/verify`" / "back to `/implement`" (verification mode, depending on
   outcome).
2. `python3 .harness/rebuild_index.py`.
3. Commit new/updated files.
4. Append a resume line to `.harness/SESSION_LOG.md`.
