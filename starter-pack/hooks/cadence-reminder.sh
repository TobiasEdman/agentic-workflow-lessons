#!/usr/bin/env bash
#
# PreToolUse hook: enforce mid-session re-anchor cadence (§4).
#
# Enforces global rule §4 from ~/.claude/CLAUDE.md:
#   "In sessions past ~50 turns, restate the top-level goal before starting
#   a new sub-topic. Invoke the /checkpoint skill to persist the state."
#
# Source failure: docs/lessons/post_rework_evidence.md §4
#   The longest post-rework session (ImintEngine 61065bbf, 3,759 turns)
#   had ZERO /checkpoint invocations mid-session. Skill-only enforcement
#   of §4 was the most-broken rule across the 60-session corpus —
#   20/45 long sessions (>=100 turns) checkpointed at all.
#
# Source justification: docs/lessons/post_rework_evidence.md §4 final paragraph
#   "Possible interventions: a turn-count counter that surfaces a
#   SessionStart-style banner at turn 50, 100, 250 reminding to checkpoint.
#   Cannot force; can prompt."
#
# How it works:
#   PreToolUse on Bash. On every Bash call we:
#     1. Read session_id + cwd from the JSON payload.
#     2. Locate the live session JSONL at
#        ~/.claude/projects/<encoded-cwd>/<session-id>.jsonl
#     3. Count user-type events (= user turns).
#     4. Read state at ~/.claude/active-sessions/<session-id>.cadence
#        (defaults to {"delivered":[]}).
#     5. If user_turn_count crosses any threshold in {50,100,250,500,1000}
#        that hasn't been delivered for this session yet, emit
#        permissionDecision="ask" with a one-time reminder, then record
#        that threshold as delivered.
#     6. Otherwise: silent.
#
# Posture:
#   - Fail-open: any parse/IO error → exit 0 silently. A hook bug must
#     never block legitimate work. Matches active-jobs-guard.sh /
#     co-authored-by.sh / verify-artefakt.sh conventions.
#   - Subagent sessions (JSONL under .../subagents/) are skipped — they are
#     short-lived by design.
#   - Each threshold fires AT MOST ONCE per session, ever. State persists
#     across restarts since session_id is stable.
#   - The reminder names /checkpoint explicitly but doesn't auto-invoke it
#     — Claude or the user decides. Approve to acknowledge; deny to ignore.
#
# Test fixtures (see also: docs/lessons/post_rework_evidence.md):
#   echo '{"tool_name":"Bash","tool_input":{"command":"ls"},"session_id":"test-99","cwd":"/tmp"}' | bash ~/.claude/hooks/cadence-reminder.sh
#     → silent if no JSONL exists or under threshold
#
#   # With a fake JSONL containing 60 user turns:
#   → emits {permissionDecision:"ask",...} reminding about /checkpoint
#
# Composes with verify-artefakt.sh / co-authored-by.sh: all three fire on
# Bash PreToolUse. If multiple would fire, the user sees sequential prompts.
set -euo pipefail

payload="$(cat)"

python3 - "$payload" <<'PY' || true
import json
import os
import sys
from pathlib import Path
from typing import Optional

THRESHOLDS = [50, 100, 250, 500, 1000]
STATE_DIR = Path.home() / ".claude" / "active-sessions"
PROJECTS_DIR = Path.home() / ".claude" / "projects"


def encode_cwd(cwd: str) -> str:
    """Mirror Claude Code's filesystem encoding of cwd → projects dir name."""
    # Claude Code converts '/' to '-' in cwd paths to form dir names.
    # Example: /Users/tobias/Developer/repo  →  -Users-tobias-Developer-repo
    return cwd.replace("/", "-")


def find_session_jsonl(session_id: str, cwd: str) -> Optional[Path]:
    """Locate the live JSONL for this session under ~/.claude/projects/."""
    if not session_id or not cwd:
        return None
    proj = PROJECTS_DIR / encode_cwd(cwd) / f"{session_id}.jsonl"
    if proj.exists():
        return proj
    # Fall back: scan all project dirs for a matching uuid.jsonl.
    for d in PROJECTS_DIR.iterdir():
        if not d.is_dir():
            continue
        cand = d / f"{session_id}.jsonl"
        if cand.exists():
            return cand
    return None


def is_subagent(p: Path) -> bool:
    return "subagents" in p.parts


def count_user_turns(p: Path) -> int:
    n = 0
    try:
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    evt = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(evt, dict):
                    continue
                if evt.get("type") == "user":
                    msg = evt.get("message", {})
                    if isinstance(msg, dict) and msg.get("role") == "user":
                        n += 1
    except OSError:
        return 0
    return n


def load_state(session_id: str) -> dict:
    f = STATE_DIR / f"{session_id}.cadence"
    if not f.exists():
        return {"delivered": []}
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"delivered": []}


def save_state(session_id: str, state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    f = STATE_DIR / f"{session_id}.cadence"
    try:
        f.write_text(json.dumps(state), encoding="utf-8")
    except OSError:
        pass


def main(payload_str: str) -> int:
    try:
        data = json.loads(payload_str or "{}")
    except json.JSONDecodeError:
        return 0  # fail-open

    session_id = data.get("session_id") or data.get("sessionId") or ""
    cwd = data.get("cwd") or ""
    if not session_id:
        return 0

    jsonl = find_session_jsonl(session_id, cwd)
    if jsonl is None or is_subagent(jsonl):
        return 0

    turn_count = count_user_turns(jsonl)
    if turn_count < THRESHOLDS[0]:
        return 0

    state = load_state(session_id)
    delivered = set(state.get("delivered", []))

    # Find the highest threshold crossed that we haven't delivered for yet.
    crossed = [t for t in THRESHOLDS if turn_count >= t and t not in delivered]
    if not crossed:
        return 0

    threshold = max(crossed)
    delivered.add(threshold)
    state["delivered"] = sorted(delivered)
    save_state(session_id, state)

    reason = (
        f"This session has crossed {threshold} user turns "
        f"(current count: {turn_count}).\n\n"
        f"§4 of ~/.claude/CLAUDE.md prescribes a mid-session re-anchor at "
        f"this cadence: restate the top-level goal and write a `/checkpoint` "
        f"snapshot so a fresh session can recover.\n\n"
        f"Approve to acknowledge — Claude will offer /checkpoint at a "
        f"natural break.\n"
        f"Deny to skip — this threshold won't fire again for this session.\n\n"
        f"Source: docs/lessons/post_rework_evidence.md §4. The 3,759-turn "
        f"ImintEngine 61065bbf session that triggered this hook had zero "
        f"mid-session checkpoints."
    )

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": reason,
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else ""))
PY
