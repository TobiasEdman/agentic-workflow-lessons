#!/usr/bin/env bash
#
# PreToolUse hook: prompt to add Co-Authored-By trailer when a git commit
# message is missing one.
#
# Enforces global rule §7 from ~/.claude/CLAUDE.md.
#
# Research backing: ../../docs/lessons/multi_user_multi_agent.md §C5 — commit
# attribution is the unsolved git-layer governance problem. Community
# consensus is "signed commits + Co-authored-by: trailers keep git blame
# honest" until native tooling lands.
#
# How it works:
#   Claude Code fires this hook as PreToolUse on the Bash tool. We read
#   the JSON payload from stdin, look at the command, and if it's a
#   `git commit -m "..."` that does NOT already include a Co-Authored-By
#   line, we emit `permissionDecision: "ask"` so the user sees a UI prompt
#   they can approve (ship as-is) or deny (regenerate the commit with the
#   trailer appended).
#
#   If the command is anything else, or already has the trailer, we exit 0
#   with no output — the command proceeds unchanged.
#
# Posture history:
#   v1 emitted a non-blocking `additionalContext` reminder. Trailer escapes
#   were ~13% under that posture. v2 (current) returns `permissionDecision:
#   "ask"`, which surfaces a UI confirmation. Same posture as
#   active-jobs-guard.sh.
#
# Safety:
#   - Never blocks unconditionally — only emits "ask" so user can confirm.
#   - Never modifies commits that already have Co-Authored-By.
#   - Never touches non-commit Bash commands.
#   - Operates only on -m "..." / -m '...' / heredoc forms Claude uses.
#   - Hook-failures (python missing, malformed payload) → exit 0 silently
#     to never block a commit due to hook bugs.
#
# Testing:
#   echo '{"tool_name":"Bash","tool_input":{"command":"git commit -m \"feat: x\""}}' | bash ~/.claude/hooks/co-authored-by.sh
#   → emits permissionDecision=ask
#
#   echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}' | bash ~/.claude/hooks/co-authored-by.sh
#   → exits 0 silently
set -euo pipefail

# Read the JSON payload from stdin
payload="$(cat)"

# Extract tool_name + command using python (stdlib — more robust than jq in hooks)
read -r tool_name command <<<"$(python3 -c '
import json, sys
data = json.loads(sys.stdin.read() or "{}")
tn = data.get("tool_name", "")
cmd = data.get("tool_input", {}).get("command", "")
# Print on one line, tab-separated, for read -r
print(tn + " " + cmd.replace("\n", " ").replace("\t", " "))
' <<<"$payload" 2>/dev/null || echo "UNKNOWN")"

# Only care about Bash tool
if [[ "$tool_name" != "Bash" ]]; then
    exit 0
fi

# Only care about git commit commands
if [[ "$command" != *"git commit"* ]]; then
    exit 0
fi

# Skip if Co-Authored-By already present (any case / spelling variant)
if echo "$command" | grep -qiE "co-authored-by"; then
    exit 0
fi

# Skip amend-with-no-edit and similar where we can't inject safely
if echo "$command" | grep -qE -- "--no-edit|--amend.*--no-edit"; then
    exit 0
fi

# Skip commits that don't use -m / heredoc (rare; let them through)
if ! echo "$command" | grep -qE -- "-m "; then
    exit 0
fi

# At this point we have a `git commit -m ...` without Co-Authored-By.
# Surface a UI prompt the user must approve. Approve = ship the commit
# without trailer (rare legitimate case: user pre-composed the message).
# Deny = Claude rewrites the commit with the trailer.
#
# We don't try to rewrite the command in-place — heredoc + shell-quoting
# edge cases are too risky for a fail-open hook.
cat <<'JSON'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "ask",
    "permissionDecisionReason": "This commit is missing the Co-Authored-By trailer required by ~/.claude/CLAUDE.md §7.\n\nApprove to ship as-is (e.g. user pre-composed the message). Deny to regenerate the commit with `Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>` appended."
  }
}
JSON
exit 0
