#!/usr/bin/env bash
#
# PreToolUse hook: guard Edit/Write against files belonging to currently
# running jobs.
#
# Enforces global rule §3 from ~/.claude/CLAUDE.md:
#   "Code that is executing — on a remote cluster, inside a running server,
#   inside an active training job, inside a live fetch — is read-only."
#
# Source justification: see ../../docs/lessons/pitfalls.md §5 and §13 —
# advisory rules drift; hooks don't. In one rollout, trailer-compliance
# jumped from 35% (text rule) to 87% (hook) within half a day.
#
# How it works:
#   Claude Code fires this hook as PreToolUse on Edit and Write. We read
#   the JSON payload from stdin, look at tool_input.file_path, and check
#   whether it matches any glob in any sentinel under ~/.claude/active-jobs/.
#   On match: emit permissionDecision="ask" with a reason naming the
#   matching slug + note + glob; the Claude Code UI surfaces a confirmation
#   prompt to the user. The user's approval functions as the explicit
#   imperative §3 prescribes.
#
# Sentinel format (~/.claude/active-jobs/<slug>.json):
#   {
#     "slug": "fetch-2026-spring",
#     "note": "Live S3 sync running on the remote cluster; do not edit",
#     "paths": ["~/Developer/myrepo/src/fetch/**", "~/Developer/myrepo/run.sh"],
#     "expires_at": "2026-05-15T18:00:00Z"  // optional ISO-8601; omit for no expiry
#   }
#
# Safety / posture:
#   - Fail-open: any parse error → exit 0 silently. A hook bug must never
#     block legitimate work. Same posture as co-authored-by.sh.
#   - Only fires on Edit | Write tools. Bash, Read, Grep, Glob etc. always pass.
#   - Expired locks are ignored (so users don't end up with permanent stale blocks).
#   - Idempotent on repeated calls; no side effects.
#
# Test fixtures:
#   echo '{"tool_name":"Edit","tool_input":{"file_path":"/tmp/x.py"}}' | bash ~/.claude/hooks/active-jobs-guard.sh
#     → no output if no lock matches
#     → JSON {permissionDecision:"ask", ...} if a lock matches /tmp/x.py
#
#   echo '{"tool_name":"Bash","tool_input":{"command":"ls"}}' | bash ~/.claude/hooks/active-jobs-guard.sh
#     → no output (Bash is not guarded by this hook)
set -euo pipefail

payload="$(cat)"

python3 - "$payload" <<'PY' || true
import fnmatch
import glob
import json
import os
import sys
from datetime import datetime, timezone

LOCKS_DIR = os.path.expanduser("~/.claude/active-jobs")

def main(payload_str: str) -> int:
    try:
        data = json.loads(payload_str or "{}")
    except json.JSONDecodeError:
        return 0  # fail-open

    tool_name = data.get("tool_name", "")
    if tool_name not in ("Edit", "Write"):
        return 0

    tool_input = data.get("tool_input", {}) or {}
    target = tool_input.get("file_path") or ""
    if not target:
        return 0

    # Always work with the absolute, ~-expanded path
    target_abs = os.path.abspath(os.path.expanduser(target))

    if not os.path.isdir(LOCKS_DIR):
        return 0

    matches = []
    now = datetime.now(timezone.utc)

    for lock_path in sorted(glob.glob(os.path.join(LOCKS_DIR, "*.json"))):
        try:
            with open(lock_path, encoding="utf-8") as fh:
                lock = json.load(fh)
        except (OSError, json.JSONDecodeError):
            continue  # malformed — skip

        # Honor optional expiry
        expires_at = lock.get("expires_at")
        if expires_at:
            try:
                # Accept "Z" suffix and offset forms
                ts = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if ts <= now:
                    continue
            except ValueError:
                pass  # bad timestamp — treat as no expiry

        slug = str(lock.get("slug") or os.path.splitext(os.path.basename(lock_path))[0])
        note = str(lock.get("note") or "")
        paths = lock.get("paths") or []
        if not isinstance(paths, list):
            continue

        for raw_glob in paths:
            if not isinstance(raw_glob, str) or not raw_glob:
                continue
            expanded = os.path.expanduser(raw_glob)
            # Two matchers — fnmatch (covers ** with our normalized form) and a
            # naive prefix check that catches "dir/" style entries.
            if fnmatch.fnmatch(target_abs, expanded):
                matches.append((slug, note, expanded))
                break
            # Support "**" recursion explicitly: fnmatch treats * non-greedy on /,
            # so for "dir/**" we additionally test prefix.
            if "**" in expanded:
                prefix = expanded.split("**", 1)[0].rstrip("/")
                if prefix and target_abs.startswith(prefix + os.sep):
                    matches.append((slug, note, expanded))
                    break

    if not matches:
        return 0

    slug, note, matched_glob = matches[0]
    reason_lines = [
        f"{target_abs} matches active job '{slug}' via glob '{matched_glob}'.",
    ]
    if note:
        reason_lines.append(f"Note: {note}")
    reason_lines += [
        "",
        "Per ~/.claude/CLAUDE.md §3, running code is read-only until you confirm an explicit imperative.",
        "Approve to proceed; deny to leave the running code untouched.",
        f"To clear the lock: rm ~/.claude/active-jobs/{slug}.json",
    ]

    out = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": "\n".join(reason_lines),
        }
    }
    json.dump(out, sys.stdout)
    sys.stdout.write("\n")
    return 0


sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else ""))
PY
