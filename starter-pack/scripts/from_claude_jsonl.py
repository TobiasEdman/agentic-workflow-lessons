#!/usr/bin/env python3
"""
Build a post-rework session corpus from Claude Code's on-disk JSONL store.

Walks ``~/.claude/projects/`` and flattens each session JSONL into:

- ``sessions/jsonl/post_rework_sessions.jsonl`` — one structured record per session
  with tool calls, slash-command invocations, language, repo, mtime, and turn count.
- ``sessions/raw/post_rework/<repo>__<uuid>.txt`` — human-readable mirror.

Filter window: ``mtime >= 2026-04-24`` (start of the continuity rework).

Source format reference (one line = one event):

    {"type":"user","message":{"role":"user","content":"..."},...}
    {"type":"assistant","message":{...,"content":[{"type":"tool_use",...}, ...]},...}
    {"type":"system",...}

Output record schema is documented in ``docs/schema.md`` (post_rework_sessions
addendum to be added when this lands).
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

PROJECTS_DIR = Path.home() / ".claude" / "projects"
OUT_JSONL = Path("sessions/jsonl/post_rework_sessions.jsonl")
RAW_MIRROR_DIR = Path("sessions/raw/post_rework")
CLEANED_MIRROR_DIR = Path("sessions/cleaned/post_rework")
CUTOFF = datetime(2026, 4, 24, tzinfo=timezone.utc)

SLASH_CMD_RE = re.compile(r"<command-name>(/[a-z][\w-]*)</command-name>")

SV_STOP = {
    "och", "att", "jag", "är", "det", "som", "en", "på", "med", "för", "inte",
    "vi", "har", "du", "kan", "till", "men", "om", "den", "så", "nu", "vad",
    "ett", "vill", "ska", "skulle", "när", "där", "hur", "mig", "dig",
}
EN_STOP = {
    "the", "and", "is", "of", "to", "a", "in", "that", "it", "for", "you",
    "with", "this", "on", "are", "be", "have", "not", "or", "can", "we",
    "i", "will", "what", "which", "when", "where", "how",
}


def detect_language(text: str) -> str:
    tokens = re.findall(r"[a-zåäöé]+", text.lower())
    if not tokens:
        return "unknown"
    sv = sum(1 for t in tokens if t in SV_STOP)
    en = sum(1 for t in tokens if t in EN_STOP)
    total = sv + en
    if total < 5:
        return "unknown"
    sv_r = sv / total
    en_r = en / total
    if sv_r > 0.7:
        return "sv"
    if en_r > 0.7:
        return "en"
    return "mixed"


def repo_from_cwd(cwd: str | None) -> str:
    if not cwd:
        return "unknown"
    p = Path(cwd)
    # ~/Developer/<repo>... → <repo>;  ~/Developer/<repo>/.claude/worktrees/<x> → <repo>:<x>
    parts = p.parts
    if "Developer" in parts:
        idx = parts.index("Developer")
        if len(parts) > idx + 1:
            repo = parts[idx + 1]
            if "worktrees" in parts[idx + 2:]:
                wt = parts[parts.index("worktrees") + 1]
                return f"{repo}:wt/{wt}"
            return repo
    return p.name or "unknown"


def parse_ts(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        # Claude Code uses ISO-8601 with Z
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def flatten_content(content) -> tuple[str, list[str], list[dict], list[str]]:
    """Return (text, thinking_snippets, tool_calls, slash_commands)."""
    text_parts: list[str] = []
    thinking: list[str] = []
    tools: list[dict] = []
    slashes: list[str] = []
    if isinstance(content, str):
        text_parts.append(content)
        for m in SLASH_CMD_RE.finditer(content):
            slashes.append(m.group(1))
        return "\n".join(text_parts).strip(), thinking, tools, slashes
    if not isinstance(content, list):
        return "", thinking, tools, slashes
    for blk in content:
        if not isinstance(blk, dict):
            continue
        t = blk.get("type")
        if t == "text":
            txt = blk.get("text", "")
            text_parts.append(txt)
            for m in SLASH_CMD_RE.finditer(txt):
                slashes.append(m.group(1))
        elif t == "thinking":
            thinking.append(blk.get("thinking", "")[:500])
        elif t == "tool_use":
            tools.append({
                "name": blk.get("name", "?"),
                "input_summary": _summarise_tool_input(blk.get("name"), blk.get("input", {})),
            })
        elif t == "tool_result":
            # Skip — recorded against the matching tool_use in turn-flattening
            pass
    return "\n".join(text_parts).strip(), thinking, tools, slashes


def _summarise_tool_input(name: str | None, inp: dict) -> str:
    if not isinstance(inp, dict):
        return ""
    if name == "Bash":
        cmd = (inp.get("command") or "").splitlines()[0][:160]
        return f"$ {cmd}"
    if name in {"Read", "Edit", "Write"}:
        return inp.get("file_path", "")[:160]
    if name in {"Glob", "Grep"}:
        return f"{inp.get('pattern','')[:80]}  ({inp.get('path','')})"
    if name == "TodoWrite":
        todos = inp.get("todos", [])
        return f"{len(todos)} todos"
    if name == "AskUserQuestion":
        qs = inp.get("questions", [])
        if qs:
            return qs[0].get("question", "")[:160]
        return ""
    if name == "Agent":
        return f"[{inp.get('subagent_type','?')}] {inp.get('description','')[:80]}"
    return json.dumps(inp)[:160]


def process_session(path: Path) -> dict | None:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception as exc:
        print(f"  SKIP {path.name}: {exc}", file=sys.stderr)
        return None

    session_id = path.stem
    cwd = None
    git_branch = None
    turns: list[dict] = []
    tool_counter: Counter[str] = Counter()
    slash_counter: Counter[str] = Counter()
    timestamps: list[datetime] = []
    is_sidechain_count = 0
    raw_text_blob: list[str] = []

    for raw in lines:
        try:
            evt = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if not isinstance(evt, dict):
            continue
        etype = evt.get("type")
        if etype in {"queue-operation", "last-prompt", "system"}:
            continue
        if cwd is None:
            cwd = evt.get("cwd")
        if git_branch is None:
            git_branch = evt.get("gitBranch")
        ts = parse_ts(evt.get("timestamp"))
        if ts:
            timestamps.append(ts)
        if evt.get("isSidechain"):
            is_sidechain_count += 1
        msg = evt.get("message", {})
        if not isinstance(msg, dict):
            continue
        role = msg.get("role") or etype
        text, thinking, tools, slashes = flatten_content(msg.get("content"))
        for tc in tools:
            tool_counter[tc["name"]] += 1
        for s in slashes:
            slash_counter[s] += 1
        if not text and not tools and not thinking:
            continue
        turns.append({
            "role": role,
            "text": text,
            "thinking_count": len(thinking),
            "tool_calls": tools,
            "is_sidechain": bool(evt.get("isSidechain")),
            "ts": ts.isoformat() if ts else None,
        })
        if text:
            raw_text_blob.append(f"[{role}] {text}")
        for tc in tools:
            raw_text_blob.append(f"  ⮕ {tc['name']}: {tc['input_summary']}")

    if not turns:
        return None

    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    if mtime < CUTOFF:
        return None

    full_text = "\n\n".join(raw_text_blob)
    record = {
        "session_id": session_id,
        "source_file": str(path).replace(str(Path.home()), "~"),
        "repo": repo_from_cwd(cwd),
        "cwd": cwd,
        "git_branch": git_branch,
        "mtime": mtime.isoformat(),
        "ts_start": min(timestamps).isoformat() if timestamps else None,
        "ts_end": max(timestamps).isoformat() if timestamps else None,
        "duration_s": (max(timestamps) - min(timestamps)).total_seconds() if len(timestamps) >= 2 else None,
        "turn_count": len(turns),
        "tool_call_count": sum(tool_counter.values()),
        "tools_used": dict(tool_counter),
        "slash_commands": dict(slash_counter),
        "sidechain_event_count": is_sidechain_count,
        "language": detect_language(full_text[:20000]),
        "raw_chars": len(full_text),
    }
    return {"record": record, "raw_text": full_text, "turns": turns}


def main() -> int:
    if not PROJECTS_DIR.exists():
        print(f"ERROR: {PROJECTS_DIR} not found", file=sys.stderr)
        return 1

    OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    RAW_MIRROR_DIR.mkdir(parents=True, exist_ok=True)
    CLEANED_MIRROR_DIR.mkdir(parents=True, exist_ok=True)

    files = sorted(PROJECTS_DIR.glob("*/*.jsonl"))
    print(f"Found {len(files)} top-level session JSONL files")

    kept = 0
    skipped_old = 0
    skipped_empty = 0
    with OUT_JSONL.open("w", encoding="utf-8") as out:
        for p in files:
            res = process_session(p)
            if res is None:
                # Distinguish old vs empty
                try:
                    mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
                    if mtime < CUTOFF:
                        skipped_old += 1
                    else:
                        skipped_empty += 1
                except Exception:
                    skipped_empty += 1
                continue
            rec = res["record"]
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            # Mirror text — name as <repo>__<uuid>.txt
            slug = re.sub(r"[^a-zA-Z0-9_.-]", "_", rec["repo"]) + "__" + rec["session_id"][:8]
            (RAW_MIRROR_DIR / f"{slug}.txt").write_text(res["raw_text"], encoding="utf-8")
            # Cleaned = same as raw for now (no redaction needed per scan)
            (CLEANED_MIRROR_DIR / f"{slug}.txt").write_text(res["raw_text"], encoding="utf-8")
            kept += 1
    print(f"Kept:           {kept}")
    print(f"Skipped (old):  {skipped_old}")
    print(f"Skipped (empty):{skipped_empty}")
    print(f"Out:            {OUT_JSONL}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
