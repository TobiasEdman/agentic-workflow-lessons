#!/usr/bin/env bash
#
# PreToolUse hook: surface a UI prompt when a `git commit` lacks evidence
# of verification.
#
# Per ~/.claude/CLAUDE.md §6 ("Verify work before declaring done"). The
# rule is policy across all sessions; this hook is mechanical enforcement.
#
# How it works:
#   Claude Code fires this hook as PreToolUse on the Bash tool. We read
#   the JSON payload from stdin. If the command is a `git commit ...`
#   that does NOT include a `Verified-by: …` trailer, we return
#   `permissionDecision: "ask"`, surfacing a UI prompt the user/agent
#   must approve. Approve = ship without trailer (rare legitimate case);
#   deny = regenerate the commit with a verify trailer.
#
# Trailer convention (§6 made mechanical):
#   Verified-by: pytest tests/ — 78 passed
#   Verified-by: smoke — PYTHONPATH=src python -c "import x" → 0
#   Verified-by: trivial — typo fix, no test needed
#   Verified-by: cannot-verify — env-dependent; user to verify before close
#
#   The hook does not parse what's after the colon. It only checks the
#   trailer is present and non-empty. The point is to force the question
#   to be asked — what's after the colon is the writer's claim, audit
#   trail for `git log --grep`.
#
# Safety:
#   - Never blocks; always returns `ask` (user/agent can override).
#   - Never modifies the command in place (heredoc shell-quoting is risky).
#   - Skips amend/no-edit commits where we can't inject safely.
#   - Skips non-Bash tools and non-commit Bash commands.
#
# Companion hook:
#   ~/.claude/hooks/co-authored-by.sh — checks for §7 attribution trailer.
#   Both hooks fire on the same git commit; if both trailers are missing,
#   the user sees two sequential prompts. After a few commits the trailers
#   become reflex; prompts go away.
#
# Testing:
#   echo '{"tool_name":"Bash","tool_input":{"command":"git commit -m \"x\""}}' \
#     | bash ~/.claude/hooks/verify-artefakt.sh
#   → emits permissionDecision=ask
#
#   echo '{"tool_name":"Bash","tool_input":{"command":"git commit -m \"x\n\nVerified-by: pytest\""}}' \
#     | bash ~/.claude/hooks/verify-artefakt.sh
#   → exits 0 silently
set -euo pipefail

# Read the JSON payload from stdin
payload="$(cat)"

# Extract tool_name + command using python (stdlib — robust against
# embedded quotes/heredocs that would trip jq).
read -r tool_name command <<<"$(python3 -c '
import json, sys
data = json.loads(sys.stdin.read() or "{}")
tn = data.get("tool_name", "")
cmd = data.get("tool_input", {}).get("command", "")
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

# Skip if Verified-by already present (any case variant, value must start with
# alphanumeric — excludes empty trailers `Verified-by: "` where the next char
# is just a closing shell quote).
if echo "$command" | grep -qiE "verified-by:[[:space:]]*[[:alnum:]]"; then
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

# Skip merge/revert commits — these inherit verification from their parents,
# same logic as co-authored-by.sh / co-authored-by-dual.sh.
if echo "$command" | grep -qE -- "(--merge|-m \"Merge |-m 'Merge |Revert \\\")"; then
    exit 0
fi

# At this point we have a `git commit -m ...` without Verified-by.
# Surface the prompt. Approve = ship as-is; deny = Claude rewrites with trailer.
cat <<'JSON'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "ask",
    "permissionDecisionReason": "This commit is missing the Verified-by trailer required by ~/.claude/CLAUDE.md §6.\n\nApprove to ship as-is (e.g. cannot verify in this environment, user to verify out-of-band). Deny to regenerate the commit with a `Verified-by: <how>` trailer.\n\nExamples:\n  Verified-by: pytest tests/ — 78 passed\n  Verified-by: smoke — PYTHONPATH=src python -c \"import x\" → 0\n  Verified-by: trivial — typo fix, no test needed\n  Verified-by: cannot-verify — env-dependent; user to verify before close"
  }
}
JSON
exit 0
