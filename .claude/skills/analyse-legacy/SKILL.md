---
name: analyse-legacy
description: Analyses and describes an existing/legacy codebase or system the new app needs to interact with or replace, producing diagrams and a written description that feeds into /architecture-session. Use when there's existing code, data, or a system to understand before making architecture decisions.
---

# Analyse Legacy System

Goal: produce an accurate, honest description of an existing system --
what it does, how it's structured, what's salvageable, what's a trap --
so `/architecture-session` can make decisions grounded in reality instead
of assumptions.

Not relevant if there is no legacy system to analyse (a from-scratch
project can skip this entirely).

## Process

1. Ask the user what the legacy system is and where it lives (a path in
   this repo, another repo, a description of a system with no code
   access, a data export format, etc.). Don't assume -- this varies a lot.
2. If code is accessible: read it broadly first (structure, entry points,
   data model) before drilling into any one part. Prefer a fast, thorough
   read-only exploration over guessing from filenames.
3. If code is not accessible: interview the user the way `/define-problem`
   does -- ask concrete questions rather than accepting vague summaries
   ("what does it do when X happens", "where does the data actually live",
   "what's the part everyone's afraid to touch and why").
4. Identify: core responsibilities, data model/storage, integration
   points, known pain points or dead ends, anything that constrains the
   new architecture (data migration needs, formats that must stay
   compatible, behavior users depend on even if undocumented).

## Output

Write to `architecture/diagrams/legacy-<system>.md`: a written description
plus diagrams where they clarify structure or data flow better than prose
(Mermaid in fenced code blocks is fine for component/flow diagrams).
Be concrete and specific -- this document's value is in details a generic
summary would lose.

## Before ending the session

1. Tell the user this should feed into `/architecture-session` next.
2. Commit new/updated files.
3. Append a resume line to `.harness/SESSION_LOG.md` -- if the analysis is
   partial, note exactly what's been covered and what's left.
