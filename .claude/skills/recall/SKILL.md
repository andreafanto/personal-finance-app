---
name: recall
description: Answers questions from the harness's working memory -- glossary terms, domain rules, conventions/style guide, constraints, facts (knowledge/) and architectural decisions (architecture/ADRs/) -- with citations to entry ids, and flags gaps or contradictions. Use when the user says "/recall", "what do we know about X", "what did we decide about X", "what's our convention for X", "what does <term> mean here", or before drafting anything that should respect prior decisions.
---

# Recall

Goal: give an answer grounded **only** in what the project has recorded,
and cite every claim so it can be traced. Say plainly what is not
recorded. Do not fill gaps from general knowledge without labeling them.

## Steps

1. Run `python3 .harness/rebuild_index.py` so the index is current, then
   read `knowledge/INDEX.md`.
2. Find the candidate entries for the topic:
   - match on titles, summaries, and `#tags` in the index
   - `grep -ril --exclude-dir=wiki "<keyword>" knowledge/ architecture/ADRs/` for words that
     are only in entry bodies. Try synonyms. For example, "rollover" can
     also be "carry over" or "carry forward".
   - use `.harness/knowledge.json` for structured filters (by kind, tag,
     status, source) when the question calls for them
   - follow `related` links one step out
   - for "what did we learn recently / this week / on <date>", read
     `knowledge/wiki/README.md` and the matching day pages
3. Read the **full file** of every candidate. The summary alone is not
   enough to answer from, because the qualifications are in Why and
   How to apply.
4. Answer:
   - state what is recorded, citing ids inline, e.g. "Amounts are
     integer cents (kn-0007), because of rounding bugs in float math."
   - separate **binding** knowledge (active entries, accepted ADRs) from
     **non-binding** (proposed ADRs). Mention superseded or retracted
     entries only when they explain why something is no longer true, and
     label them.
   - if two active entries conflict, say so and name both ids. Do not
     pick one.
   - if nothing is recorded, say "nothing recorded about X". If you add
     general advice, label it as not project knowledge.
5. If the conversation produces an answer to a gap or a resolution of a
   conflict, offer `/remember` to record it. Do not write memory from
   this skill.

## Called by other skills or before delegating to an agent

Worker agents (test-generator, implementer, verifier, and so on) have no
memory of their own. When a launcher skill builds an agent prompt, it
runs steps 1-3 for the requirement's topic and tags. It then pastes the
**full text** of the relevant active entries and accepted ADRs into the
prompt, under a `## Project knowledge (binding)` heading. Paths alone
are not enough, because the agent may not open them.

This skill is read-only. It never changes any file other than the
generated indexes.
