#!/usr/bin/env python3
"""
Pattern detection over the post-rework JSONL corpus.

Runs five deterministic rules against ``~/.claude/projects/*/<uuid>.jsonl``,
emits findings to ``analysis/patterns/<rule>.jsonl`` (one finding per line)
plus a human-readable summary at ``analysis/patterns/_summary.md``.

The rules encode the known failure modes from
``docs/lessons/post_rework_evidence.md``. No LLM calls, no agents — fast,
deterministic, cheap.

Usage::

    python3 scripts/detect_patterns.py              # all rules, full corpus
    python3 scripts/detect_patterns.py --since 2026-05-01
    python3 scripts/detect_patterns.py --rule long-session-no-checkpoint
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional

PROJECTS_DIR = Path.home() / ".claude" / "projects"
OUT_DIR = Path("analysis/patterns")

PREFERENCE_PATTERNS = [
    r"\b(?:should|borde)\s+(?:be|vara)\s+",
    r"\bthe right (?:thing|way) (?:is|would be)\s+",
    r"\bthey should be\s+\w+",
    r"\bdet rätta är\s+",
    r"\bdet borde vara\s+",
]
PREFERENCE_RE = re.compile("|".join(PREFERENCE_PATTERNS), re.IGNORECASE)

IMPERATIVE_VERBS = {
    "fix", "change", "edit", "replace", "restart", "run", "write",
    "add", "remove", "delete", "create", "build", "make", "do",
    "kör", "fixa", "ändra", "skapa", "skriv", "ta bort", "lägg till",
}
IMPERATIVE_RE = re.compile(
    r"\b(" + "|".join(re.escape(v) for v in IMPERATIVE_VERBS) + r")\b",
    re.IGNORECASE,
)


def parse_ts(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def iter_top_level_sessions() -> Iterator[Path]:
    """Yield top-level session JSONL files, skipping subagent sidechains."""
    for p in PROJECTS_DIR.glob("*/*.jsonl"):
        if "subagents" in p.parts:
            continue
        yield p


def is_scheduled_task_session(events: list[dict]) -> bool:
    """Detect sessions auto-spawned by mcp__scheduled-tasks.

    These open with a system-prompt-style user message starting with
    ``<scheduled-task name=...>``. They have very different shape from
    human-driven sessions (short, automated, no commits) and pollute
    discipline metrics. Filter them out before pattern analysis.
    """
    for e in events:
        if not isinstance(e, dict) or e.get("type") != "user":
            continue
        msg = e.get("message", {})
        if not isinstance(msg, dict):
            continue
        c = msg.get("content")
        if isinstance(c, str) and c.lstrip().startswith("<scheduled-task"):
            return True
        # First real user message decides — don't keep scanning
        if isinstance(c, str) and c.strip():
            return False
        if isinstance(c, list):
            return False
    return False


def load_events(path: Path) -> list[dict]:
    events: list[dict] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    except OSError:
        pass
    return events


def session_meta(events: list[dict], path: Path) -> dict:
    cwd = None
    branches = []
    for e in events:
        if not isinstance(e, dict):
            continue
        if cwd is None:
            cwd = e.get("cwd")
        b = e.get("gitBranch")
        if b and (not branches or branches[-1] != b):
            branches.append(b)
    repo = "?"
    if cwd:
        parts = Path(cwd).parts
        if "Developer" in parts:
            i = parts.index("Developer")
            if len(parts) > i + 1:
                repo = parts[i + 1]
    return {
        "session_id": path.stem,
        "path": str(path),
        "cwd": cwd,
        "repo": repo,
        "branch_changes": len(branches) - 1 if branches else 0,
        "mtime": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Rule 1: long session without /checkpoint
# ---------------------------------------------------------------------------

CADENCE_HOOK_LANDED = datetime(2026, 5, 12, tzinfo=timezone.utc)


def rule_long_session_no_checkpoint(events: list[dict], meta: dict) -> list[dict]:
    """Long session without checkpointing — counts both Skill(checkpoint)
    AND Write to ~/.claude/checkpoints/. Suppresses for pre-hook sessions
    (cadence-reminder.sh landed 2026-05-12; sessions that started earlier
    can't have had it fire).
    """
    user_turns = 0
    saw_checkpoint = False
    session_start_ts: Optional[datetime] = None

    for e in events:
        if not isinstance(e, dict):
            continue
        # Capture session start
        if session_start_ts is None:
            ts = parse_ts(e.get("timestamp"))
            if ts:
                session_start_ts = ts
        if e.get("type") == "user":
            msg = e.get("message", {})
            if isinstance(msg, dict) and msg.get("role") == "user":
                user_turns += 1
                c = msg.get("content")
                if isinstance(c, str) and "/checkpoint" in c.lower():
                    saw_checkpoint = True
        if e.get("type") == "assistant":
            msg = e.get("message", {})
            if isinstance(msg, dict):
                c = msg.get("content")
                if isinstance(c, list):
                    for blk in c:
                        if not isinstance(blk, dict) or blk.get("type") != "tool_use":
                            continue
                        name = blk.get("name")
                        inp = blk.get("input", {}) or {}
                        # Skill-based checkpoint
                        if name == "Skill" and inp.get("skill") == "checkpoint":
                            saw_checkpoint = True
                        # Write-based checkpoint (milestone-mode pattern)
                        elif name == "Write":
                            fp = inp.get("file_path", "") or ""
                            if "/.claude/checkpoints/" in fp and fp.endswith(".md"):
                                saw_checkpoint = True

    if user_turns < 250 or saw_checkpoint:
        return []

    # Suppress for pre-hook sessions — the cadence hook couldn't have fired
    pre_hook = session_start_ts is not None and session_start_ts < CADENCE_HOOK_LANDED
    if pre_hook:
        return [{
            "rule": "long-session-no-checkpoint",
            "severity": "info",  # not a violation — outside hook reach
            "session": meta,
            "user_turns": user_turns,
            "pre_hook": True,
            "note": (
                f"{user_turns} user turns, no checkpoint event. Session started "
                f"{session_start_ts.date().isoformat()} — before cadence-reminder hook "
                f"landed 2026-05-12. Outside hook reach; not a §4 violation."
            ),
        }]

    return [{
        "rule": "long-session-no-checkpoint",
        "severity": "warning",
        "session": meta,
        "user_turns": user_turns,
        "pre_hook": False,
        "note": f"{user_turns} user turns, no checkpoint event (Skill or Write). §4 cadence violated.",
    }]


# ---------------------------------------------------------------------------
# Rule 2: hook bypass attempts (--no-verify)
# ---------------------------------------------------------------------------

def rule_git_precommit_bypass(events: list[dict], meta: dict) -> list[dict]:
    """git --no-verify bypasses git's own pre-commit / commit-msg hooks (lint,
    type-check, project conventions). It does NOT bypass Claude's PreToolUse
    hooks — those fire before the bash command runs and are unaffected.

    Originally misnamed ``hook-bypass`` with blocker severity. Reclassified to
    info: it's a real signal worth knowing about (project-level guard skipped)
    but it doesn't violate any §1-§9 rule.
    """
    findings = []
    for e in events:
        if not isinstance(e, dict) or e.get("type") != "assistant":
            continue
        msg = e.get("message", {})
        if not isinstance(msg, dict):
            continue
        c = msg.get("content")
        if not isinstance(c, list):
            continue
        for blk in c:
            if not isinstance(blk, dict) or blk.get("type") != "tool_use":
                continue
            if blk.get("name") != "Bash":
                continue
            cmd = (blk.get("input", {}) or {}).get("command", "") or ""
            if re.search(
                r"\bgit\s+(?:commit|push|am|rebase|merge)\b[^\n;|]{0,100}--no-verify",
                cmd,
            ):
                findings.append({
                    "rule": "git-precommit-bypass",
                    "severity": "info",
                    "session": meta,
                    "ts": e.get("timestamp"),
                    "command_preview": cmd[:160],
                    "note": "git --no-verify — bypasses project-level pre-commit hooks (lint/type/test). Claude's PreToolUse hooks are unaffected (they fire before bash runs).",
                })
    return findings


# ---------------------------------------------------------------------------
# Rule 3: §1 misfire candidates (preference-as-directive)
# ---------------------------------------------------------------------------

def rule_preference_as_directive(events: list[dict], meta: dict) -> list[dict]:
    findings = []
    prev_user_text: Optional[str] = None
    prev_user_ts: Optional[str] = None
    for e in events:
        if not isinstance(e, dict):
            continue
        msg = e.get("message", {})
        if not isinstance(msg, dict):
            continue
        if e.get("type") == "user":
            c = msg.get("content")
            if isinstance(c, str) and not c.startswith("<command-"):
                prev_user_text = c
                prev_user_ts = e.get("timestamp")
            elif isinstance(c, list):
                # Tool results — not user prose
                prev_user_text = None
            else:
                prev_user_text = None
        elif e.get("type") == "assistant" and prev_user_text is not None:
            if not PREFERENCE_RE.search(prev_user_text):
                prev_user_text = None
                continue
            if IMPERATIVE_RE.search(prev_user_text):
                # Has an explicit imperative — not a pure preference
                prev_user_text = None
                continue
            c = msg.get("content")
            if not isinstance(c, list):
                prev_user_text = None
                continue
            had_ask = False
            had_edit = False
            for blk in c:
                if not isinstance(blk, dict) or blk.get("type") != "tool_use":
                    continue
                name = blk.get("name", "")
                if name == "AskUserQuestion":
                    had_ask = True
                if name in ("Edit", "Write"):
                    had_edit = True
            if had_edit and not had_ask:
                findings.append({
                    "rule": "preference-as-directive",
                    "severity": "warning",
                    "session": meta,
                    "user_ts": prev_user_ts,
                    "user_excerpt": prev_user_text[:200],
                    "note": "Preference statement followed by Edit/Write without AskUserQuestion intervening. §1 candidate misfire.",
                })
            prev_user_text = None
    return findings


# ---------------------------------------------------------------------------
# Rule 4: drift — multiple branch changes without explicit pivot
# ---------------------------------------------------------------------------

def rule_branch_drift(events: list[dict], meta: dict) -> list[dict]:
    if meta["branch_changes"] >= 3:
        return [{
            "rule": "branch-drift",
            "severity": "info",
            "session": meta,
            "branch_changes": meta["branch_changes"],
            "note": f"Session changed gitBranch {meta['branch_changes']} times — potential drift across topics.",
        }]
    return []


# ---------------------------------------------------------------------------
# Rule 5: repo with >=5 sessions and 0 /recall in turn-0
# ---------------------------------------------------------------------------

def rule_skill_underuse_recall(sessions_meta: list[dict]) -> list[dict]:
    """Cross-session rule — runs once at the end, not per-session."""
    by_repo: dict[str, dict] = {}
    for s in sessions_meta:
        r = s["repo"]
        d = by_repo.setdefault(r, {"sessions": 0, "with_recall": 0})
        d["sessions"] += 1
        if s.get("had_recall_in_first_10_events"):
            d["with_recall"] += 1
    findings = []
    for repo, stats in by_repo.items():
        if stats["sessions"] >= 5 and stats["with_recall"] == 0:
            findings.append({
                "rule": "recall-underuse",
                "severity": "info",
                "repo": repo,
                "sessions": stats["sessions"],
                "note": f"Repo '{repo}' has {stats['sessions']} sessions but 0 used /recall in opener. §5 / continuity gap.",
            })
    return findings


def had_recall_early(events: list[dict]) -> bool:
    seen = 0
    for e in events:
        if not isinstance(e, dict):
            continue
        if e.get("type") not in ("user", "assistant"):
            continue
        seen += 1
        msg = e.get("message", {})
        if not isinstance(msg, dict):
            continue
        c = msg.get("content")
        if isinstance(c, str) and "/recall" in c.lower():
            return True
        if isinstance(c, list):
            for blk in c:
                if isinstance(blk, dict) and blk.get("type") == "tool_use":
                    if blk.get("name") == "Skill" and (blk.get("input", {}) or {}).get("skill") == "recall":
                        return True
        if seen >= 10:
            break
    return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Quality rules
# ---------------------------------------------------------------------------

VERIFY_HOOK_LANDED = datetime(2026, 5, 8, tzinfo=timezone.utc)
COAUTHOR_HOOK_TIGHTENED = datetime(2026, 4, 25, tzinfo=timezone.utc)


def _iter_commits(events: list[dict]):
    """Yield (timestamp, command) for each git commit invocation."""
    for e in events:
        if not isinstance(e, dict) or e.get("type") != "assistant":
            continue
        msg = e.get("message", {})
        if not isinstance(msg, dict):
            continue
        c = msg.get("content")
        if not isinstance(c, list):
            continue
        ts = parse_ts(e.get("timestamp"))
        for blk in c:
            if not isinstance(blk, dict) or blk.get("type") != "tool_use":
                continue
            if blk.get("name") != "Bash":
                continue
            cmd = (blk.get("input", {}) or {}).get("command", "") or ""
            if re.search(r"\bgit\s+commit\b", cmd) and "--amend" not in cmd:
                yield ts, cmd


def _session_start_ts(events: list[dict]) -> Optional[datetime]:
    """First timestamped event in the session."""
    for e in events:
        if not isinstance(e, dict):
            continue
        ts = parse_ts(e.get("timestamp"))
        if ts:
            return ts
    return None


def rule_missing_verified_by(events: list[dict], meta: dict) -> list[dict]:
    """Commits missing Verified-by: trailer. Distinguishes between:
       - "warning"  — session started after the hook landed, real §6 violation
       - "info/stale-session" — session predates hook; settings.json read at
         session start, so the hook couldn't fire here. Not a discipline gap.
    """
    findings = []
    session_start = _session_start_ts(events)
    stale = session_start is not None and session_start < VERIFY_HOOK_LANDED

    for ts, cmd in _iter_commits(events):
        if ts is None or ts < VERIFY_HOOK_LANDED:
            continue
        if "Verified-by:" not in cmd:
            findings.append({
                "rule": "missing-verified-by",
                "severity": "info" if stale else "warning",
                "session": meta,
                "ts": ts.isoformat(),
                "stale_session_pre_hook": stale,
                "note": (
                    "Commit after 2026-05-08 missing Verified-by:. Session started "
                    "before the hook landed — outside its reach (settings.json read "
                    "at session start)."
                    if stale else
                    "Commit after 2026-05-08 missing Verified-by: trailer. §6 violated."
                ),
            })
    return findings


def rule_missing_coauthor(events: list[dict], meta: dict) -> list[dict]:
    findings = []
    session_start = _session_start_ts(events)
    stale = session_start is not None and session_start < COAUTHOR_HOOK_TIGHTENED

    for ts, cmd in _iter_commits(events):
        if ts is None or ts < COAUTHOR_HOOK_TIGHTENED:
            continue
        if "Co-Authored-By:" not in cmd:
            findings.append({
                "rule": "missing-coauthor",
                "severity": "info" if stale else "warning",
                "session": meta,
                "ts": ts.isoformat(),
                "stale_session_pre_hook": stale,
                "note": (
                    "Commit after 2026-04-25 missing Co-Authored-By:. Session "
                    "started before the hook landed — outside its reach."
                    if stale else
                    "Commit after 2026-04-25 missing Co-Authored-By: trailer. §7 violated."
                ),
            })
    return findings


def rule_giant_commit(events: list[dict], meta: dict) -> list[dict]:
    """Commits that touch >10 files or contain >50 lines of body are bundled, not atomic."""
    findings = []
    for ts, cmd in _iter_commits(events):
        # Heuristic: count lines in the heredoc / -m body
        body = ""
        m = re.search(r'-m\s+"((?:[^"\\]|\\.)*)"', cmd, re.DOTALL)
        if m:
            body = m.group(1)
        else:
            m = re.search(r"<<'EOF'\n(.*?)\nEOF", cmd, re.DOTALL)
            if m:
                body = m.group(1)
        line_count = body.count("\n")
        if line_count > 50:
            findings.append({
                "rule": "giant-commit",
                "severity": "info",
                "session": meta,
                "ts": ts.isoformat() if ts else None,
                "body_lines": line_count,
                "note": f"Commit body has {line_count} lines — likely bundled, not per-task atomic.",
            })
    return findings


# ---------------------------------------------------------------------------
# Efficiency rules
# ---------------------------------------------------------------------------

def rule_file_re_read(events: list[dict], meta: dict) -> list[dict]:
    """Same file Read ≥4 times in one session = inefficient re-reading."""
    counts: Counter = Counter()
    for e in events:
        if not isinstance(e, dict) or e.get("type") != "assistant":
            continue
        msg = e.get("message", {})
        if not isinstance(msg, dict):
            continue
        c = msg.get("content")
        if not isinstance(c, list):
            continue
        for blk in c:
            if not isinstance(blk, dict) or blk.get("type") != "tool_use":
                continue
            if blk.get("name") != "Read":
                continue
            fp = (blk.get("input", {}) or {}).get("file_path", "")
            if fp:
                counts[fp] += 1
    offenders = [(fp, n) for fp, n in counts.items() if n >= 4]
    findings = []
    for fp, n in sorted(offenders, key=lambda x: -x[1])[:5]:
        findings.append({
            "rule": "file-re-read",
            "severity": "info",
            "session": meta,
            "file": fp,
            "read_count": n,
            "note": f"{fp} read {n}× in one session — consider holding it in working memory.",
        })
    return findings


def rule_bash_loop_struggle(events: list[dict], meta: dict) -> list[dict]:
    """≥5 Bash calls in a row with no Read/Edit/Write between them = thrashing."""
    consecutive = 0
    max_streak = 0
    streak_start_ts = None
    max_streak_start = None
    for e in events:
        if not isinstance(e, dict) or e.get("type") != "assistant":
            continue
        msg = e.get("message", {})
        if not isinstance(msg, dict):
            continue
        c = msg.get("content")
        if not isinstance(c, list):
            continue
        for blk in c:
            if not isinstance(blk, dict) or blk.get("type") != "tool_use":
                continue
            name = blk.get("name", "")
            if name == "Bash":
                if consecutive == 0:
                    streak_start_ts = e.get("timestamp")
                consecutive += 1
                if consecutive > max_streak:
                    max_streak = consecutive
                    max_streak_start = streak_start_ts
            elif name in ("Read", "Edit", "Write", "Grep", "Glob", "TodoWrite", "AskUserQuestion"):
                consecutive = 0
    if max_streak >= 15:
        return [{
            "rule": "bash-loop-struggle",
            "severity": "info",
            "session": meta,
            "max_streak": max_streak,
            "streak_start_ts": max_streak_start,
            "note": f"{max_streak} consecutive Bash calls without intervening Read/Edit/Grep — possible thrash loop.",
        }]
    return []


def rule_tool_call_explosion(events: list[dict], meta: dict) -> list[dict]:
    """>100 tool calls per commit ratio = unfocused work."""
    tool_calls = 0
    commits = 0
    for e in events:
        if not isinstance(e, dict) or e.get("type") != "assistant":
            continue
        msg = e.get("message", {})
        if not isinstance(msg, dict):
            continue
        c = msg.get("content")
        if not isinstance(c, list):
            continue
        for blk in c:
            if not isinstance(blk, dict) or blk.get("type") != "tool_use":
                continue
            tool_calls += 1
            if blk.get("name") == "Bash":
                cmd = (blk.get("input", {}) or {}).get("command", "") or ""
                if re.search(r"\bgit\s+commit\b", cmd) and "--amend" not in cmd:
                    commits += 1
    if commits >= 3 and (tool_calls / commits) > 200:
        return [{
            "rule": "tool-call-explosion",
            "severity": "info",
            "session": meta,
            "tool_calls": tool_calls,
            "commits": commits,
            "ratio": round(tool_calls / commits, 1),
            "note": f"{tool_calls} tool calls over {commits} commits = {tool_calls/commits:.0f} calls/commit. High ratio suggests unfocused work.",
        }]
    return []


# ---------------------------------------------------------------------------
# Dev / coding praxis rules
# ---------------------------------------------------------------------------

def rule_commit_without_test(events: list[dict], meta: dict) -> list[dict]:
    """No test command in 20 tool calls before a commit = ship-before-verify."""
    findings = []
    tool_call_log = []  # (kind, ts, blk)
    for e in events:
        if not isinstance(e, dict) or e.get("type") != "assistant":
            continue
        msg = e.get("message", {})
        if not isinstance(msg, dict):
            continue
        c = msg.get("content")
        if not isinstance(c, list):
            continue
        ts = e.get("timestamp")
        for blk in c:
            if not isinstance(blk, dict) or blk.get("type") != "tool_use":
                continue
            name = blk.get("name", "")
            if name != "Bash":
                tool_call_log.append((name, ts, None))
                continue
            cmd = (blk.get("input", {}) or {}).get("command", "") or ""
            tool_call_log.append(("Bash", ts, cmd))
            if not re.search(r"\bgit\s+commit\b", cmd) or "--amend" in cmd:
                continue
            # Look back at last 20 tool calls
            window = tool_call_log[-21:-1]
            test_run = any(
                w[0] == "Bash" and w[2] and re.search(
                    r"\b(?:pytest|vitest|jest|npm test|cargo test|go test|make test|bun test)\b",
                    w[2],
                )
                for w in window
            )
            if not test_run:
                # Allow non-trivial trailer to opt-out (cannot-verify / trivial)
                if not re.search(r"Verified-by:\s*(?:trivial|cannot-verify|smoke)", cmd):
                    findings.append({
                        "rule": "commit-without-test",
                        "severity": "info",
                        "session": meta,
                        "ts": ts,
                        "note": "No pytest/vitest/jest run in 20 tool calls before commit, and no 'trivial/cannot-verify' opt-out in trailer.",
                    })
    return findings


def rule_edit_without_read(events: list[dict], meta: dict) -> list[dict]:
    """Edit on a file path that was never Read in this session."""
    read_paths: set[str] = set()
    findings = []
    for e in events:
        if not isinstance(e, dict) or e.get("type") != "assistant":
            continue
        msg = e.get("message", {})
        if not isinstance(msg, dict):
            continue
        c = msg.get("content")
        if not isinstance(c, list):
            continue
        for blk in c:
            if not isinstance(blk, dict) or blk.get("type") != "tool_use":
                continue
            name = blk.get("name", "")
            inp = blk.get("input", {}) or {}
            fp = inp.get("file_path", "")
            if name == "Read":
                if fp:
                    read_paths.add(fp)
            elif name == "Edit":
                if fp and fp not in read_paths:
                    findings.append({
                        "rule": "edit-without-read",
                        "severity": "warning",
                        "session": meta,
                        "file": fp,
                        "note": "Edit on file that was never Read in this session — risk of stale assumptions.",
                    })
                    # Don't flood: track that we've reported this file
                    read_paths.add(fp)
    return findings[:5]


PLAN_PATTERNS = [
    # "first do X, then do Y" / "first build X, then test Y" — imperatives only
    r"\bfirst\s+(?:do|build|run|fix|make|write|add|test|check)\b.{1,80}\bthen\s+(?:do|build|run|fix|make|write|add|test|check)\b",
    r"\bförst\s+(?:gör|bygg|kör|fix|skriv|testa)\b.{1,80}\bsen\s+(?:gör|bygg|kör|fix|skriv|testa)\b",
    # Explicit "step 1: ..." / "steg 1: ..." pattern
    r"\bstep\s*1[:.]\s.{1,80}\bstep\s*2[:.]\s",
    r"\bsteg\s*1[:.]\s.{1,80}\bsteg\s*2[:.]\s",
    # "i den ena ... i den andra ..." (Swedish parallel-construction pattern)
    r"\bi\s+den\s+(?:ena|stora|första)\b.{1,80}\bi\s+den\s+(?:andra|lilla|senare)\b",
    # Compressed numeric plan references: "kör steg 1+2 nu" / "do steps 1+2"
    # Found in rise-pax session 5846ed79 — original rule missed this form.
    r"\bkör\s+steg\s+\d+[\+\-]\d+",
    r"\bdo\s+step[s]?\s+\d+[\+\-]\d+",
    r"\b(?:kör|do)\s+(?:steg|step[s]?)\s+\d+\s*(?:och|and)\s+\d+\b",
]
PLAN_RE = re.compile("|".join(PLAN_PATTERNS), re.IGNORECASE | re.MULTILINE | re.DOTALL)

# Anti-patterns that look like plans but aren't: system-prompts, doc-listings, policy reviews
PLAN_ANTI_PATTERNS = [
    r"<scheduled-task",  # system prompt for scheduled tasks
    r"<command-name>",   # slash-command invocations
    r"^\*\*Styrkor\b",   # Swedish "Strengths" reviews
    r"^\*\*Strengths\b",
]
PLAN_ANTI_RE = re.compile("|".join(PLAN_ANTI_PATTERNS), re.IGNORECASE | re.MULTILINE)


def rule_plan_without_todowrite(events: list[dict], meta: dict) -> list[dict]:
    """User stated multi-step plan but next 10 tool calls contain no TodoWrite."""
    findings = []
    pending: list[tuple[str, str, int]] = []  # (ts, excerpt, idx_at_detection)
    tool_call_idx = 0
    seen_todowrite_idx = -1
    for e in events:
        if not isinstance(e, dict):
            continue
        msg = e.get("message", {})
        if not isinstance(msg, dict):
            continue
        if e.get("type") == "user":
            c = msg.get("content")
            if isinstance(c, str) and not c.startswith("<command-"):
                if PLAN_RE.search(c) and not PLAN_ANTI_RE.search(c):
                    pending.append((e.get("timestamp", ""), c[:200], tool_call_idx))
        elif e.get("type") == "assistant":
            c = msg.get("content")
            if not isinstance(c, list):
                continue
            for blk in c:
                if not isinstance(blk, dict) or blk.get("type") != "tool_use":
                    continue
                tool_call_idx += 1
                if blk.get("name") == "TodoWrite":
                    seen_todowrite_idx = tool_call_idx
    # Resolve: for each pending plan, did a TodoWrite arrive within 10 tool calls?
    for ts, excerpt, idx_at_detection in pending:
        if seen_todowrite_idx > idx_at_detection and (seen_todowrite_idx - idx_at_detection) <= 10:
            continue  # plan was acknowledged via TodoWrite
        if seen_todowrite_idx > idx_at_detection:
            continue  # TodoWrite eventually came, just not within window — still acceptable
        findings.append({
            "rule": "plan-without-todowrite",
            "severity": "info",
            "session": meta,
            "user_ts": ts,
            "user_excerpt": excerpt.strip(),
            "note": "User stated multi-step plan; no TodoWrite invocation seen after. §2 plan-echo-back via TodoWrite candidate miss.",
        })
    return findings[:5]  # cap per session


def rule_silent_reproject(events: list[dict], meta: dict) -> list[dict]:
    """Write/Edit of code containing rasterio.warp.reproject without nearby assertion.

    Carry-forward from docs/lessons/proj_geo_issues.md: silent reprojection
    without shape/non-nan check is a known geo failure mode.
    """
    findings = []
    for e in events:
        if not isinstance(e, dict) or e.get("type") != "assistant":
            continue
        msg = e.get("message", {})
        if not isinstance(msg, dict):
            continue
        c = msg.get("content")
        if not isinstance(c, list):
            continue
        for blk in c:
            if not isinstance(blk, dict) or blk.get("type") != "tool_use":
                continue
            if blk.get("name") not in ("Write", "Edit"):
                continue
            inp = blk.get("input", {}) or {}
            fp = inp.get("file_path", "") or ""
            # Only Python sources can contain a real rasterio.warp.reproject call.
            # .md / .txt / .json files referencing it are documentation, not code.
            if not fp.endswith(".py"):
                continue
            # Exclude this detector's own source — it contains the literal
            # `warp.reproject(` as a rule body, which would otherwise self-flag.
            if fp.endswith("detect_patterns.py"):
                continue
            body = ""
            if blk.get("name") == "Write":
                body = inp.get("content", "") or ""
            else:
                body = (inp.get("old_string", "") or "") + "\n" + (inp.get("new_string", "") or "")
            # Require an actual *call* (open-paren), not just a string mention.
            # Avoids self-flag where this very rule contains the literal "rasterio.warp.reproject".
            if not re.search(r"\b(?:rasterio\.warp\.reproject|warp\.reproject)\s*\(", body):
                continue
            # Look for nearby assertion / shape check / np.isnan / np.any() / count_nonzero
            if re.search(r"\b(?:assert|np\.isnan|np\.any|count_nonzero|\.shape\s*==|raise\s+\w+Error)", body):
                continue
            findings.append({
                "rule": "silent-reproject",
                "severity": "warning",
                "session": meta,
                "file": inp.get("file_path", ""),
                "note": "rasterio.warp.reproject written without nearby assertion/shape/NaN check. proj_geo_issues.md known failure mode.",
            })
    return findings[:5]


def rule_uncommitted_work_spike(events: list[dict], meta: dict) -> list[dict]:
    """Session with many Write operations spread over hours, with few or no commits.

    Risk window: large amount of work lives only in working-dir; if the session
    crashes or the user moves on, work is lost. When it finally commits it
    becomes a giant-commit. Originally surfaced in rise-pax session 5846ed79
    (107 Writes, 1 commit, 22 h).
    """
    writes = 0
    commits = 0
    first_write_ts: Optional[datetime] = None
    last_write_ts: Optional[datetime] = None

    for e in events:
        if not isinstance(e, dict) or e.get("type") != "assistant":
            continue
        msg = e.get("message", {})
        if not isinstance(msg, dict):
            continue
        c = msg.get("content")
        if not isinstance(c, list):
            continue
        ts = parse_ts(e.get("timestamp"))
        for blk in c:
            if not isinstance(blk, dict) or blk.get("type") != "tool_use":
                continue
            name = blk.get("name", "")
            if name == "Write":
                writes += 1
                if ts:
                    if first_write_ts is None:
                        first_write_ts = ts
                    last_write_ts = ts
            elif name == "Bash":
                cmd = (blk.get("input", {}) or {}).get("command", "") or ""
                if re.search(r"\bgit\s+commit\b", cmd) and "--amend" not in cmd:
                    commits += 1

    if writes < 10:
        return []
    if first_write_ts is None or last_write_ts is None:
        return []
    duration_h = (last_write_ts - first_write_ts).total_seconds() / 3600
    if duration_h < 6:
        return []

    # Trigger: ≥10 writes spread over ≥6 hours with ≤1 commit, OR
    #         ≥30 writes with ≤2 commits regardless of duration
    if (commits <= 1) or (writes >= 30 and commits <= 2):
        return [{
            "rule": "uncommitted-work-spike",
            "severity": "warning",
            "session": meta,
            "writes": writes,
            "commits": commits,
            "duration_hours": round(duration_h, 1),
            "note": (
                f"{writes} Write operations over {duration_h:.1f}h with only "
                f"{commits} commit(s). Risk window: work lives only in working-dir; "
                f"crash recovery or session-end costs the whole spike. Will likely "
                f"land as a giant-commit when it does commit."
            ),
        }]
    return []


def rule_main_branch_commits(events: list[dict], meta: dict) -> list[dict]:
    """Commits made while gitBranch == main / master = unsafe branch hygiene."""
    if not events:
        return []
    main_branch = False
    for e in events:
        b = e.get("gitBranch") if isinstance(e, dict) else None
        if b in ("main", "master"):
            main_branch = True
            break
    if not main_branch:
        return []
    commit_count = sum(1 for _ in _iter_commits(events))
    if commit_count >= 3:
        return [{
            "rule": "main-branch-commits",
            "severity": "info",
            "session": meta,
            "commits": commit_count,
            "note": f"{commit_count} commits on main/master branch in one session — consider feature branches for non-trivial work.",
        }]
    return []


# ---------------------------------------------------------------------------
# /team-loop pattern adoption tracker
# ---------------------------------------------------------------------------

TEAM_LOOP_ROLES = {
    "product-owner",
    "architect",
    "developer",
    "frontend-builder",
    "ux-critic",
    "business-controller",
    "domain-reviewer",
    "savant-reviewer",
}


def rule_team_loop_pattern_without_skill(events: list[dict], meta: dict) -> list[dict]:
    """Session uses ≥3 named-role Agent dispatches but never invoked the
    /team-loop Skill. Not a violation — pattern is operating without the
    orchestrator. Tracks adoption gap between the slash-command and the
    underlying multi-agent pattern.

    Threshold of 3 named-role dispatches separates ad-hoc role-reviews
    from systematic team-loop usage.
    """
    role_dispatches: Counter = Counter()
    saw_team_loop_skill = False

    for e in events:
        if not isinstance(e, dict) or e.get("type") != "assistant":
            continue
        msg = e.get("message", {})
        if not isinstance(msg, dict):
            continue
        c = msg.get("content")
        if not isinstance(c, list):
            continue
        for blk in c:
            if not isinstance(blk, dict) or blk.get("type") != "tool_use":
                continue
            name = blk.get("name", "")
            inp = blk.get("input", {}) or {}
            if name == "Agent":
                role = inp.get("subagent_type", "")
                if role in TEAM_LOOP_ROLES:
                    role_dispatches[role] += 1
            elif name == "Skill" and inp.get("skill") == "team-loop":
                saw_team_loop_skill = True

    total_role_dispatches = sum(role_dispatches.values())
    if total_role_dispatches < 3 or saw_team_loop_skill:
        return []

    return [{
        "rule": "team-loop-pattern-without-skill",
        "severity": "info",
        "session": meta,
        "named_role_dispatches": total_role_dispatches,
        "role_breakdown": dict(role_dispatches),
        "note": (
            f"{total_role_dispatches} named-role Agent dispatches across "
            f"{len(role_dispatches)} role(s) but no /team-loop Skill invocation. "
            f"Pattern is operating without the orchestrator — adoption-tracking "
            f"signal, not a §-rule violation."
        ),
    }]


# ---------------------------------------------------------------------------
# Rule registry
# ---------------------------------------------------------------------------

RULES = {
    # Continuity (existing)
    "long-session-no-checkpoint": rule_long_session_no_checkpoint,
    "git-precommit-bypass": rule_git_precommit_bypass,
    "preference-as-directive": rule_preference_as_directive,
    "branch-drift": rule_branch_drift,
    # Quality
    "missing-verified-by": rule_missing_verified_by,
    "missing-coauthor": rule_missing_coauthor,
    "giant-commit": rule_giant_commit,
    # Efficiency
    "file-re-read": rule_file_re_read,
    "bash-loop-struggle": rule_bash_loop_struggle,
    "tool-call-explosion": rule_tool_call_explosion,
    # Dev/coding praxis
    "commit-without-test": rule_commit_without_test,
    "edit-without-read": rule_edit_without_read,
    "main-branch-commits": rule_main_branch_commits,
    "uncommitted-work-spike": rule_uncommitted_work_spike,
    # Misunderstandings (§2 echo-back of plans; geo failure mode carry-forward)
    "plan-without-todowrite": rule_plan_without_todowrite,
    "silent-reproject": rule_silent_reproject,
    # /team-loop adoption tracking
    "team-loop-pattern-without-skill": rule_team_loop_pattern_without_skill,
}

RULE_CATEGORIES = {
    "continuity": ["long-session-no-checkpoint", "preference-as-directive", "branch-drift", "recall-underuse", "plan-without-todowrite", "team-loop-pattern-without-skill"],
    "tooling": ["git-precommit-bypass"],
    "quality": ["missing-verified-by", "missing-coauthor", "giant-commit"],
    "efficiency": ["file-re-read", "bash-loop-struggle", "tool-call-explosion"],
    "praxis": ["commit-without-test", "edit-without-read", "main-branch-commits", "silent-reproject", "uncommitted-work-spike"],
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", type=str, help="ISO date — only sessions with mtime >= this")
    ap.add_argument("--rule", type=str, choices=list(RULES) + ["recall-underuse"], help="Run only one rule")
    args = ap.parse_args()

    cutoff = None
    if args.since:
        try:
            cutoff = datetime.fromisoformat(args.since).replace(tzinfo=timezone.utc)
        except ValueError:
            print(f"ERROR: invalid --since date: {args.since}", file=sys.stderr)
            return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    findings_by_rule: dict[str, list[dict]] = {r: [] for r in list(RULES) + ["recall-underuse"]}
    sessions_processed = 0
    sessions_filtered_scheduled = 0
    sessions_meta_all: list[dict] = []

    for path in iter_top_level_sessions():
        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        if cutoff and mtime < cutoff:
            continue
        events = load_events(path)
        if not events:
            continue
        # Filter scheduled-task auto-sessions — they pollute discipline metrics
        if is_scheduled_task_session(events):
            sessions_filtered_scheduled += 1
            continue
        meta = session_meta(events, path)
        meta["had_recall_in_first_10_events"] = had_recall_early(events)
        sessions_meta_all.append(meta)
        sessions_processed += 1
        for rule_name, fn in RULES.items():
            if args.rule and rule_name != args.rule:
                continue
            findings_by_rule[rule_name].extend(fn(events, meta))

    if not args.rule or args.rule == "recall-underuse":
        findings_by_rule["recall-underuse"] = rule_skill_underuse_recall(sessions_meta_all)

    # Write per-rule JSONL
    for rule_name, findings in findings_by_rule.items():
        out = OUT_DIR / f"{rule_name}.jsonl"
        with out.open("w", encoding="utf-8") as f:
            for fnd in findings:
                f.write(json.dumps(fnd, ensure_ascii=False) + "\n")

    # Human summary
    summary = OUT_DIR / "_summary.md"
    lines = [f"# Pattern detection — {datetime.now(timezone.utc).isoformat()}", ""]
    lines.append(f"Sessions scanned: **{sessions_processed}**")
    if cutoff:
        lines.append(f"Cutoff: `mtime >= {cutoff.isoformat()}`")
    lines.append("")

    # Category-level totals
    lines.append("## Totals by category")
    lines.append("")
    lines.append("| Category | Findings | Rules with hits |")
    lines.append("|---|---:|---:|")
    for cat, rules in RULE_CATEGORIES.items():
        cat_findings = sum(len(findings_by_rule.get(r, [])) for r in rules)
        cat_with_hits = sum(1 for r in rules if findings_by_rule.get(r))
        lines.append(f"| **{cat}** | {cat_findings} | {cat_with_hits}/{len(rules)} |")
    lines.append("")

    total = sum(len(v) for v in findings_by_rule.values())
    if total == 0:
        lines.append("**No findings.** The corpus is clean against the current rules.")
    else:
        lines.append(f"**{total} findings across {sum(1 for v in findings_by_rule.values() if v)} rules.**")
        lines.append("")
        # Render category-by-category
        for cat, rules in RULE_CATEGORIES.items():
            cat_findings = sum(len(findings_by_rule.get(r, [])) for r in rules)
            if cat_findings == 0:
                continue
            lines.append(f"# {cat.upper()}")
            lines.append("")
            for rule_name in rules:
                findings = findings_by_rule.get(rule_name, [])
                if not findings:
                    continue
                lines.append(f"## `{rule_name}` — {len(findings)} finding(s)")
                lines.append("")
                sev = Counter(f["severity"] for f in findings)
                lines.append("Severity: " + ", ".join(f"{k}={v}" for k, v in sev.items()))
                lines.append("")
                for f in findings[:10]:
                    if "session" in f:
                        s = f["session"]
                        lines.append(f"- **{s['repo']}** / `{s['session_id'][:8]}` — {f['note']}")
                        if "user_excerpt" in f:
                            lines.append(f"  > _{f['user_excerpt'][:150].strip()}_")
                    elif "repo" in f:
                        lines.append(f"- **{f['repo']}** — {f['note']}")
                if len(findings) > 10:
                    lines.append(f"- … {len(findings) - 10} more in `analysis/patterns/{rule_name}.jsonl`")
                lines.append("")
    summary.write_text("\n".join(lines), encoding="utf-8")

    print(f"Scanned {sessions_processed} sessions ({sessions_filtered_scheduled} scheduled-task sessions filtered)")
    for rule_name, findings in findings_by_rule.items():
        marker = "  •" if findings else "  ✓"
        print(f"{marker} {rule_name}: {len(findings)}")
    print(f"Summary: {summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
