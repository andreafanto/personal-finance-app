#!/usr/bin/env bash
# PreToolUse gate: opening a merge/pull request is the signal to save working
# memory. Blocks MR/PR creation until /remember has run its MR capture for the
# current HEAD, which it records in .harness/.memory-captured (gitignored).
#
# Matches: gh pr create, glab mr create, hub pull-request,
#          git push -o merge_request.create, and MCP create_{pull,merge}_request tools.
set -euo pipefail

input="$(cat)"
tool="$(jq -r '.tool_name // ""' <<<"$input")"
cwd="$(jq -r '.cwd // ""' <<<"$input")"

is_mr=0
if [[ "$tool" == "Bash" ]]; then
  cmd="$(jq -r '.tool_input.command // ""' <<<"$input")"
  # Only match in command position (line start or after ; & | ( ), optionally
  # behind the rtk proxy, so text that merely mentions these commands (echo,
  # grep, heredocs, commit messages) does not trip the gate.
  cmd_start='(^|[;&|(])[[:space:]]*(rtk[[:space:]]+)?'
  mr_cmds='(gh[[:space:]]+pr[[:space:]]+create|glab[[:space:]]+mr[[:space:]]+create|hub[[:space:]]+pull-request|git[[:space:]]+push[^;&|]*merge_request\.create)'
  if grep -Eq "${cmd_start}${mr_cmds}" <<<"$cmd"; then
    is_mr=1
  fi
elif grep -Eiq '(create_?(pull|merge)_?request)' <<<"$tool"; then
  is_mr=1
fi
[[ $is_mr -eq 1 ]] || exit 0

root="$(git -C "${cwd:-.}" rev-parse --show-toplevel 2>/dev/null)" || exit 0
head="$(git -C "$root" rev-parse HEAD 2>/dev/null)" || exit 0
marker="$root/.harness/.memory-captured"

if [[ -f "$marker" && "$(tr -d '[:space:]' <"$marker")" == "$head" ]]; then
  exit 0
fi

reason="Working-memory gate: opening an MR is the signal to save memory. Run /remember in MR mode first -- it reviews this conversation plus the branch's changes (problems/, requirements/, architecture/, domain-vision.md, Knowledge candidates lines in .harness/SESSION_LOG.md), gets the user's confirmation, commits any knowledge/ADR changes, and records HEAD in .harness/.memory-captured. Then retry this exact MR command and list the memory changes in the MR description. (HEAD ${head:0:7} has not been captured.)"

jq -n --arg r "$reason" '{
  hookSpecificOutput: {
    hookEventName: "PreToolUse",
    permissionDecision: "deny",
    permissionDecisionReason: $r
  }
}'
