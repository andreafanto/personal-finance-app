#!/usr/bin/env bash
# PreToolUse commit check for working memory.
#
# Before a `git commit` goes through, Claude must check the changes being
# committed (and the conversation, and .harness/memory-pending.md) for
# knowledge worth saving, and prompt the user if it finds any. The hook denies
# the first commit attempt with instructions. After the check, Claude runs
#   .claude/hooks/memory-gate.sh --mark
# which records a fingerprint of the pending changes in
# .harness/.memory-checked (gitignored). The retry then passes. If the changes
# move again, the fingerprint no longer matches and the check runs again.
#
# Skipped: commits that only touch memory/bookkeeping paths (knowledge/,
# .harness/), and commits with nothing to commit.
set -euo pipefail

fingerprint() { # $1 = repo root
  git -C "$1" diff HEAD --binary 2>/dev/null | git -C "$1" hash-object --stdin
}

if [[ "${1:-}" == "--mark" ]]; then
  root="$(git rev-parse --show-toplevel)"
  fingerprint "$root" > "$root/.harness/.memory-checked"
  echo "memory check recorded for current changes"
  exit 0
fi

input="$(cat)"
[[ "$(jq -r '.tool_name // ""' <<<"$input")" == "Bash" ]] || exit 0
cmd="$(jq -r '.tool_input.command // ""' <<<"$input")"
cwd="$(jq -r '.cwd // ""' <<<"$input")"

# Only a real `git commit` in command position (line start or after ; & | ( ),
# optionally behind the rtk proxy -- not text that mentions it.
grep -Eq '(^|[;&|(])[[:space:]]*(rtk[[:space:]]+)?git([[:space:]]+-C[[:space:]]+[^[:space:]]+)?[[:space:]]+commit\b' <<<"$cmd" || exit 0

root="$(git -C "${cwd:-.}" rev-parse --show-toplevel 2>/dev/null)" || exit 0
git -C "$root" rev-parse --verify -q HEAD >/dev/null || exit 0

# Files this commit will contain: staged, plus tracked changes with -a/--all.
files="$(git -C "$root" diff --cached --name-only)"
if grep -Eq '(^|[[:space:]])(-[a-zA-Z]*a[a-zA-Z]*|--all)([[:space:]]|$)' <<<"$cmd"; then
  files+=$'\n'"$(git -C "$root" diff --name-only)"
fi
files="$(sed '/^$/d' <<<"$files" | sort -u)"
[[ -n "$files" ]] || exit 0
grep -Evq '^(knowledge/|\.harness/)' <<<"$files" || exit 0

marker="$root/.harness/.memory-checked"
if [[ -f "$marker" && "$(tr -d '[:space:]' <"$marker")" == "$(fingerprint "$root")" ]]; then
  exit 0
fi

reason="Memory check before commit (automatic). Before this commit, look for knowledge worth saving in: (1) the staged diff, especially problems/, requirements/, architecture/, domain-vision.md, and conventions the code sets that the user approved; (2) this conversation; (3) open items in .harness/memory-pending.md. Use the triggers in .claude/skills/remember/SKILL.md ('When to save'). If you find candidates, ask the user to confirm them in one prompt (yes / edit / later / no). Write accepted items with /remember and stage them. Move 'later' items to .harness/memory-pending.md. Then run .claude/hooks/memory-gate.sh --mark and retry this exact commit. If nothing qualifies, run --mark and retry without prompting."

jq -n --arg r "$reason" '{
  hookSpecificOutput: {
    hookEventName: "PreToolUse",
    permissionDecision: "deny",
    permissionDecisionReason: $r
  }
}'
