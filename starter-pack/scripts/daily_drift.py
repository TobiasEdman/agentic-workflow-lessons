#!/usr/bin/env python3
"""
Daily drift detector.

Compares today's corpus state against the most recent prior snapshot and
emits a human-readable alert to ``analysis/daily/<YYYY-MM-DD>.md`` plus a
machine-readable JSON snapshot. Designed for scheduled (cron / mcp__
scheduled-tasks) invocation — passive, never acts.

Three things are tracked:

1. **Volume drift** — sessions, tool calls, commits, AskUserQuestion total,
   /recall + /checkpoint counts. A jump or drop in any of these is signal.
2. **Active-repo set** — repos that appeared or disappeared since last run.
3. **Pattern findings** — runs ``detect_patterns.py`` and surfaces any
   *new* findings (sessions / repos that weren't flagged yesterday).

Snapshots live at ``analysis/corpus/<date>.jsonl``. The most recent one
is the baseline. If no prior snapshot exists, the first run just writes
the baseline and emits an empty alert.

Usage::

    python3 scripts/daily_drift.py
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

PROJECTS_DIR = Path.home() / ".claude" / "projects"
CORPUS_DIR = Path("analysis/corpus")
DAILY_DIR = Path("analysis/daily")
PATTERNS_DIR = Path("analysis/patterns")
SCRIPTS_DIR = Path("scripts")

TODAY = datetime.now(timezone.utc).date()


def iter_top_level_sessions():
    for p in PROJECTS_DIR.glob("*/*.jsonl"):
        if "subagents" in p.parts:
            continue
        yield p


def snapshot_corpus() -> dict:
    """Walk JSONL and produce today's metrics snapshot."""
    totals = Counter()
    repos = Counter()
    skills = Counter()
    slash = Counter()
    sessions_seen = 0
    per_session = []

    for path in iter_top_level_sessions():
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        sessions_seen += 1
        cwd = None
        user_turns = 0
        tool_calls = 0
        commits = 0
        asks = 0
        for raw in lines:
            try:
                e = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if not isinstance(e, dict):
                continue
            if cwd is None:
                cwd = e.get("cwd")
            etype = e.get("type")
            if etype not in ("user", "assistant"):
                continue
            msg = e.get("message", {})
            if not isinstance(msg, dict):
                continue
            c = msg.get("content")
            if etype == "user":
                if isinstance(c, str) and msg.get("role") == "user":
                    user_turns += 1
                    for m in re.finditer(r"<command-name>(/[a-z][\w-]*)</command-name>", c):
                        slash[m.group(1)] += 1
            if isinstance(c, list):
                for blk in c:
                    if not isinstance(blk, dict):
                        continue
                    if blk.get("type") != "tool_use":
                        continue
                    tool_calls += 1
                    name = blk.get("name", "")
                    inp = blk.get("input", {}) or {}
                    if name == "Bash":
                        cmd = inp.get("command", "") or ""
                        if re.search(r"\bgit\s+commit\b", cmd) and "--amend" not in cmd:
                            commits += 1
                    elif name == "AskUserQuestion":
                        asks += 1
                    elif name == "Skill":
                        sname = inp.get("skill", "")
                        if sname:
                            skills[sname] += 1
        # Per-repo accounting
        repo = "?"
        if cwd:
            parts = Path(cwd).parts
            if "Developer" in parts:
                i = parts.index("Developer")
                if len(parts) > i + 1:
                    repo = parts[i + 1]
        repos[repo] += 1
        totals["user_turns"] += user_turns
        totals["tool_calls"] += tool_calls
        totals["commits"] += commits
        totals["asks"] += asks
        per_session.append({
            "session_id": path.stem,
            "repo": repo,
            "user_turns": user_turns,
            "tool_calls": tool_calls,
        })

    return {
        "date": TODAY.isoformat(),
        "ts": datetime.now(timezone.utc).isoformat(),
        "sessions": sessions_seen,
        "totals": dict(totals),
        "repos": dict(repos),
        "skills": dict(skills),
        "slash": dict(slash),
    }


def load_previous_snapshot() -> dict | None:
    if not CORPUS_DIR.exists():
        return None
    snapshots = sorted(CORPUS_DIR.glob("*.json"))
    # Exclude today's if it already exists (rerun)
    snapshots = [s for s in snapshots if s.stem != TODAY.isoformat()]
    if not snapshots:
        return None
    try:
        return json.loads(snapshots[-1].read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def load_patterns() -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    if not PATTERNS_DIR.exists():
        return out
    for f in PATTERNS_DIR.glob("*.jsonl"):
        out[f.stem] = []
        try:
            for ln in f.read_text(encoding="utf-8").splitlines():
                try:
                    out[f.stem].append(json.loads(ln))
                except json.JSONDecodeError:
                    pass
        except OSError:
            pass
    return out


def diff_alert(today: dict, prev: dict | None) -> list[str]:
    lines = [f"# Daily drift — {TODAY.isoformat()}", ""]
    if prev is None:
        lines.append("**First run.** No prior snapshot to diff against.")
        lines.append("")
        lines.append(f"Baseline: {today['sessions']} sessions, {today['totals'].get('user_turns', 0)} user turns, {today['totals'].get('commits', 0)} commits, {today['totals'].get('asks', 0)} AskUserQuestion calls.")
        return lines

    lines.append(f"Comparing **{TODAY.isoformat()}** against **{prev['date']}**.")
    lines.append("")

    # Volume diff
    lines.append("## Volume")
    lines.append("")
    lines.append("| Metric | Previous | Today | Δ |")
    lines.append("|---|---:|---:|---:|")

    def row(label: str, key: str, source_t=today, source_p=prev):
        prev_v = source_p["totals"].get(key, 0) if "totals" in source_p else source_p.get(key, 0)
        today_v = source_t["totals"].get(key, 0) if "totals" in source_t else source_t.get(key, 0)
        delta = today_v - prev_v
        sign = "+" if delta >= 0 else ""
        lines.append(f"| {label} | {prev_v} | {today_v} | {sign}{delta} |")

    lines.append(f"| Sessions | {prev['sessions']} | {today['sessions']} | {'+' if today['sessions'] >= prev['sessions'] else ''}{today['sessions'] - prev['sessions']} |")
    row("User turns", "user_turns")
    row("Tool calls", "tool_calls")
    row("Commits", "commits")
    row("AskUserQuestion", "asks")
    lines.append("")

    # Repo set diff
    prev_repos = set(prev["repos"])
    today_repos = set(today["repos"])
    new_repos = today_repos - prev_repos
    gone_repos = prev_repos - today_repos
    if new_repos or gone_repos:
        lines.append("## Repo activity")
        lines.append("")
        if new_repos:
            lines.append("**New repos with sessions since last run:** " + ", ".join(f"`{r}`" for r in sorted(new_repos)))
        if gone_repos:
            lines.append("**No longer in corpus:** " + ", ".join(f"`{r}`" for r in sorted(gone_repos)))
        lines.append("")

    # Skill / slash usage diff
    prev_skills = prev.get("skills", {})
    today_skills = today.get("skills", {})
    skill_changes = []
    for k in set(prev_skills) | set(today_skills):
        d = today_skills.get(k, 0) - prev_skills.get(k, 0)
        if d != 0:
            skill_changes.append((k, prev_skills.get(k, 0), today_skills.get(k, 0), d))
    if skill_changes:
        lines.append("## Skill invocations")
        lines.append("")
        lines.append("| Skill | Previous | Today | Δ |")
        lines.append("|---|---:|---:|---:|")
        for k, p_v, t_v, d in sorted(skill_changes, key=lambda x: -abs(x[3])):
            sign = "+" if d >= 0 else ""
            lines.append(f"| `/{k}` | {p_v} | {t_v} | {sign}{d} |")
        lines.append("")

    return lines


def run_pattern_detection() -> str:
    """Run detect_patterns.py and return its summary text."""
    script = SCRIPTS_DIR / "detect_patterns.py"
    if not script.exists():
        return ""
    try:
        subprocess.run(
            [sys.executable, str(script), "--since", "2026-04-24"],
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        return f"\n## Pattern detection FAILED\n\n```\n{exc}\n```\n"
    summary_path = PATTERNS_DIR / "_summary.md"
    if not summary_path.exists():
        return ""
    return "\n---\n\n" + summary_path.read_text(encoding="utf-8")


def main() -> int:
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    DAILY_DIR.mkdir(parents=True, exist_ok=True)

    today = snapshot_corpus()
    prev = load_previous_snapshot()

    lines = diff_alert(today, prev)
    lines.append(run_pattern_detection())

    daily_path = DAILY_DIR / f"{TODAY.isoformat()}.md"
    daily_path.write_text("\n".join(lines), encoding="utf-8")

    snapshot_path = CORPUS_DIR / f"{TODAY.isoformat()}.json"
    snapshot_path.write_text(json.dumps(today, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote {daily_path}")
    print(f"Wrote {snapshot_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
