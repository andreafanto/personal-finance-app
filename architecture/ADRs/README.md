# Architecture Decision Records

One file per decision: `adr-NNNN-short-slug.md`, numbered sequentially,
never renumbered or deleted (superseded decisions get `status: superseded`
and a pointer to the ADR that replaced them, they don't disappear).

## Template

```markdown
---
id: adr-0001
type: adr
title: "Short decision title"
status: proposed
created: YYYY-MM-DD
updated: YYYY-MM-DD
related_requirements: req-001, req-004
supersedes: ""
superseded_by: ""
---

# ADR-0001: Short decision title

## Context

What forces are at play? What problem/requirement triggered this decision?

## Decision

What was decided, stated plainly.

## Alternatives considered

What else was on the table, and why it lost.

## Consequences

What this makes easier, what it makes harder, what it forecloses.
```

`status` values: `proposed | accepted | superseded`.
