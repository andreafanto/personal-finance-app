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

## 2026-09-30 -- harness change: /planning-session skill
- Did: Added `/planning-session`, an interactive skill that models milestones, tasks, and docs. It first rebuilds the domain from memory as a cited brief the user corrects, then asks one question at a time and challenges the answers. It has a personal-finance challenge bank (transfers vs credit cards, entry friction, data scoping, money sign, category merge, rollover, backups) and a domain dependency chain. New item types `ms-`/`task-`/`doc-` (schema in `planning/README.md`) are indexed by `rebuild_index.py`, which validates their status and links and adds a milestone roll-up to PROGRESS.md.
- Touched: .claude/skills/planning-session/SKILL.md, planning/README.md, .harness/rebuild_index.py, CLAUDE.md
- Resume here: memory and domain-vision.md are still empty, so run /define-problem first. After that, run /planning-session in milestone mode to plan the first MVP milestone.

## 2026-09-29 -- harness change: automatic memory detection + commit check + daily wiki
- Did: Replaced the MR gate. `memory-signal.sh` (UserPromptSubmit) flags memory triggers in each user message, such as a new term, a correction, a rule, a convention, a scope line, a fact, or a decision. Claude then offers a one-line "Save to memory?". `memory-gate.sh` (PreToolUse) now blocks the first `git commit` of non-memory changes until Claude has run the memory check and `--mark`. "Later" items go to `.harness/memory-pending.md`. `/remember` has a 14-item "When to save" trigger table. `rebuild_index.py` generates the daily wiki `knowledge/wiki/YYYY-MM-DD.md` plus README. Dialogue skills no longer write candidate notes.
- Touched: .claude/hooks/{memory-signal.sh,memory-gate.sh}, .claude/settings.json, .claude/skills/{remember,recall,define-problem,requirements,architecture-session,design-frontend}, .harness/rebuild_index.py, .harness/memory-pending.md, knowledge/README.md, knowledge/wiki/, CLAUDE.md, .gitignore, memory-system.svg
- Resume here: run /define-problem for prob-001. Watch that "Save to memory?" prompts appear when you define terms or correct Claude, and that the clean-campsite commit runs the memory check once.

## 2026-09-29 -- harness change: memory saved on MR, not session end
- Did: Memory capture is now triggered by opening an MR/PR. `.claude/hooks/memory-gate.sh` (PreToolUse, `.claude/settings.json`) denies MR/PR creation until `.harness/.memory-captured` (gitignored) equals HEAD. `/remember` gained an MR mode: it reviews the branch diff, the session-log `Knowledge candidates:` lines, and the conversation, then commits, writes the marker, and retries the MR with a `## Working memory` section. Dialogue skills no longer capture at session end; they only note candidates.
- Touched: .claude/hooks/memory-gate.sh, .claude/settings.json, .gitignore, CLAUDE.md, knowledge/README.md, .claude/skills/{remember,define-problem,requirements,architecture-session,design-frontend}, memory-system.svg
- Resume here: the first real MR will exercise the gate end to end. Run /define-problem to start prob-001 on a feature branch; when its MR is opened, the gate should send you to /remember MR mode.

## 2026-09-29 -- harness change: working memory
- Did: Added working memory. `knowledge/kn-NNNN-*.md` holds typed, confirmed entries (term, rule, convention, constraint, fact). `knowledge/README.md` has the schema. `rebuild_index.py` now validates entries (`--check`) and generates `knowledge/INDEX.md` + `.harness/knowledge.json`, with the ADRs included. New skills: `/remember` (write, supersede, retract, draft proposed ADRs) and `/recall` (read with citations). Dialogue skills now run a capture step. Launchers paste binding knowledge into agent prompts. The boot-up ritual reads the index.
- Touched: CLAUDE.md, .harness/rebuild_index.py, knowledge/, .claude/skills/{remember,recall,define-problem,requirements,architecture-session,design-frontend,generate-tests,implement,verify}
- Resume here: memory is empty. Run `/define-problem` to fill domain-vision.md and define prob-001. Its capture step writes the first `kn-` entries.

