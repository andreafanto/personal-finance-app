#!/usr/bin/env bash
# UserPromptSubmit hook: cheap, deterministic scan of the user's message for
# signals that it contains knowledge worth saving to working memory
# (knowledge/). It never writes memory and never blocks. It only injects a
# short note so Claude judges the message and, if it is real knowledge, asks
# the user in one line whether to save it. The trigger list lives in
# .claude/skills/remember/SKILL.md ("When to save").
set -euo pipefail

input="$(cat)"
prompt="$(jq -r '.prompt // ""' <<<"$input")"
cwd="$(jq -r '.cwd // ""' <<<"$input")"
[[ -n "$prompt" ]] || exit 0

lc="$(tr '[:upper:]' '[:lower:]' <<<"$prompt")"
signals=()
has() { grep -Eq "$1" <<<"$lc"; }

has '(^|[.!?][[:space:]]+)(no|nope|wrong|not quite|not really|actually)[,.! ]|that.?s (not|wrong|incorrect)|you (got|have)[^.]* wrong|i (said|meant)|not [a-z ]{1,30},? but |rather than|instead of' \
  && signals+=("correction: the user may be correcting an assumption or a statement")
has "by [a-z \"']{1,30} i mean|[a-z]+ means |is (called|defined as)|we call |stands for|i call |what i mean by" \
  && signals+=("definition: the user may be defining a term")
has "\b(always|never|must|must not|mustn.?t|cannot|can.?t ever|only if|only when|not allowed|is required)\b" \
  && signals+=("rule: the user may be stating a domain rule or invariant")
has "\b(i prefer|we prefer|from now on|going forward|in the future,? |use [a-z]+ instead|name it|call it|should be named|format(ted)? as|style)\b" \
  && signals+=("convention: the user may be setting a style/naming/format convention")
has "out of scope|not (in|for) (the )?mvp|post-mvp|we don.?t need|won.?t support|not supported" \
  && signals+=("constraint: the user may be drawing a scope or design limit")
has "\b(let.?s go with|we.?ll use|we will use|i.?ve decided|decided to|go with option)\b" \
  && signals+=("decision: the user may be choosing between alternatives (ADR-shaped)")
has "\b(i have|we have|my (partner|wife|husband|family|household|bank|salary)|i usually|i currently|in my case)\b" \
  && signals+=("fact: the user may be sharing context about their situation")

# Quoted terms that the glossary does not know yet.
root="$(git -C "${cwd:-.}" rev-parse --show-toplevel 2>/dev/null || echo "${cwd:-.}")"
index="$root/knowledge/INDEX.md"
new_terms=()
while IFS= read -r term; do
  [[ -z "$term" ]] && continue
  if [[ ! -f "$index" ]] || ! grep -Fqi -- "$term" "$index"; then
    new_terms+=("$term")
  fi
done < <(grep -Eo "[\"“'][A-Za-z][A-Za-z -]{1,28}[\"”']" <<<"$prompt" | tr -d "\"“”'" | sort -u | head -5)
((${#new_terms[@]})) && signals+=("new term(s) not in the glossary: $(IFS=', '; echo "${new_terms[*]}")")

((${#signals[@]})) || exit 0

note="Memory check (automatic, heuristic -- may be a false positive). Possible signals in this message:"
for s in "${signals[@]}"; do note+=$'\n'"- $s"; done
note+=$'\n'"Judge it against knowledge/INDEX.md. Act only if the user stated or confirmed durable project knowledge that is not already recorded, or that contradicts an active entry. If so, finish the task first, then end your reply with ONE line: \"Save to memory? [kind] <summary> -- yes / edit / later / no\". Batch several into one prompt. On \"yes\" run /remember explicit mode. On \"later\" append to .harness/memory-pending.md. If nothing qualifies, say nothing about memory."

jq -n --arg c "$note" '{hookSpecificOutput: {hookEventName: "UserPromptSubmit", additionalContext: $c}}'
