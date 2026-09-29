# Session Log

Append-only. Every skill/agent that finishes a unit of work adds an entry
here before the session ends, per the clean-campsite checklist in CLAUDE.md.

Newest entries go at the top. Format:

```
## <date> -- <skill/agent name>
- Did: <what happened>
- Touched: <item ids / files>
- Resume here: <exact next step, specific enough to act on cold>
```

---

## 2026-09-29 -- harness change: working memory
- Did: Added working memory. `knowledge/kn-NNNN-*.md` holds typed, confirmed entries (term, rule, convention, constraint, fact). `knowledge/README.md` has the schema. `rebuild_index.py` now validates entries (`--check`) and generates `knowledge/INDEX.md` + `.harness/knowledge.json`, with the ADRs included. New skills: `/remember` (write, supersede, retract, draft proposed ADRs) and `/recall` (read with citations). Dialogue skills now run a capture step. Launchers paste binding knowledge into agent prompts. The boot-up ritual reads the index.
- Touched: CLAUDE.md, .harness/rebuild_index.py, knowledge/, .claude/skills/{remember,recall,define-problem,requirements,architecture-session,design-frontend,generate-tests,implement,verify}
- Resume here: memory is empty. Run `/define-problem` to fill domain-vision.md and define prob-001. Its capture step writes the first `kn-` entries.

