# Concurrent sessions diagnosis — git-layer conflicts from parallel Claude sessions

> Investigation following user observation 2026-06-10: *"jag har haft ett antal samtidiga sessioner och det har inte hanterats väl"*. Root cause traced to two failure modes — stacked-PR rebase conflicts within one session, and shared working-tree races across simultaneously-active sessions. Five interventions landed in response.

## Observed evidence

### Cluster 1 — <biz-analytics-repo>, 2026-05-26 to 2026-05-31

| Time | Session | Concrete signal |
|---|---|---|
| 05-26 12:04 | `<session-X>` | `Merge conflict in frontend/src/components/<component-A>.jsx` + `<component-B>.jsx` during PR #12 rebase against main (after #9 + #11 merged) |
| 05-27 07:02 | `<session-X>` | `git checkout main && git reset --hard origin/main` followed by branch switch — manual conflict resolution |
| 05-28 12:50-13:04 | `<session-X>` | Multiple `git reset --hard` attempts + `git push --force-with-lease origin main` (one rejected by Claude's auto-mode classifier as discarding authorised work) |
| 05-31 11:39 | `<session-X>` | `Auto-merging <doc-file> CONFLICT (content)` |

**Concurrent-session timeline:** by 2026-05-28 12:00 UTC, **4 sessions** had active JSONL writes against the `<biz-analytics-repo>` family (`<session-X>`, `<session-X>`, `<session-X>`, `<session-X>`).

### Cluster 2 — <geo-ml-repo>, 2026-06-08

3 sessions simultaneously active in `~/Developer/<geo-ml-repo>`, **all on branch `<feature-branch>`**:

| Session | Window |
|---|---|
| `<session-X>` | 2026-06-01 → 2026-06-08 (had created the branch) |
| `<session-X>` | 2026-06-08 12:01 → 06-09 11:41 (8 push events) |
| `<session-X>` | 2026-06-08 13:12 → 06-08 17:40 |

Smoking gun — user turn in `<session-X>` at 2026-06-08 17:34:

> *"first i want to fix Heads-up from the dev-env session — you're on `<feature-branch>`, and so was I. I just migrated the local Python toolchain off 3.9.6."*

The user manually wrote a heads-up between two sessions because no mechanical layer detected the collision.

### Detector validation

The new cross-session rules (added 2026-06-10) found 38 `same-branch-multi-session` events and 52 `concurrent-sessions-same-cwd` events across the corpus since 2026-04-24. <geo-ml-repo> `<session-X>` correctly shows three pairs:

- `<session-X> ⇆ <session-X>` on `<feature-branch>` — overlap 8.5h
- `<session-X> ⇆ <session-X>` on `<feature-branch>` — overlap 4.5h
- `<session-X> ⇆ <session-X>` on `<feature-branch>` — overlap 0.2h

## Two failure modes

### Mode 1 — Stacked-PR rebase conflicts (intra-session)

Not actually a parallel-session problem. One session opens three PRs against overlapping code. As earlier PRs merge, later PRs need to rebase against the new main. Conflicts surface at rebase time.

**Fix:** sequence PR merges so each one is non-conflicting before the next is created. Or use a merge queue. The PR #9 → #11 → #12 case in <biz-gui-repo> would have been prevented by either.

**This mode is out of scope for §10** — §10 addresses session-level concurrency, not PR-level conflict ordering. Documented here for completeness.

### Mode 2 — Shared working tree + same branch (cross-session)

Two or more Claude Code sessions open in the same `cwd` (`~/Developer/<repo>/`), all checking out the same branch, both editing files. Git's index is shared via `<repo>/.git/`. Symptoms:

- One session pulls origin/main; the other has uncommitted changes that didn't get stashed → merge state confusion
- Both edit the same file → second `Write` silently overwrites the first
- Both attempt `git push origin <branch>` → second push rejected with non-fast-forward
- User resolves manually with `git reset --hard` (potentially destructive) and `git push --force-with-lease`

**This is what §10 addresses.**

## Five interventions

All landed 2026-06-10 in response to this diagnosis.

### 1. SessionStart hook — `~/.claude/hooks/concurrent-session-warn.sh`

Scans `~/.claude/active-sessions/*.cadence` at every new session start. State files include `cwd` (extension shipped same day to `cadence-reminder.sh`). If matches with recent mtime are found:

- **Match < 1h ago:** `permissionDecision: "ask"` — surfaces UI prompt with worktree options
- **Match 1h–24h ago:** `additionalContext` block warning the model; non-blocking

Posture matches the other PreToolUse hooks — fail-open, never blocks, ask-mode is the strongest signal.

### 2. `/worktree` skill — `~/.claude/skills/worktree/SKILL.md`

User-invocable handle for the worktree pattern. Wraps `git worktree add ../<repo>-wt-<branch-slug>` with:

- Confirms not already in a worktree (no nesting)
- Handles uncommitted changes (asks: commit / stash / move / abort)
- Logs creation to `~/.claude/active-sessions/worktrees.log`
- Prints next-step instructions (user opens Claude in new dir)

Does NOT auto-cd into the worktree — Claude Code is bound to its launch cwd.

### 3. §10 in `~/.claude/CLAUDE.md`

> **One session per branch per cwd.** If another Claude Code session is already active in the same working directory, don't share the working tree. Use `git worktree add`, verify the other is idle, or finish it first. Same branch + same tree + two concurrent sessions = rebase conflicts, force-pushes, `git reset --hard`. Cost is asymmetric — preventing the collision is one `git worktree add`; resolving it after the fact is manual conflict-marker editing on two parallel commit histories.

Cites both <geo-ml-repo> `<session-X>` and <biz-gui-repo> 2026-05-28 as source incidents.

### 4. Two detector rules in `scripts/detect_patterns.py`

- **`concurrent-sessions-same-cwd`** — pairs of sessions whose time windows overlap in same cwd ≥ 5 min. Severity: info (pre-§10) / warning (post-§10).
- **`same-branch-multi-session`** — adds the branch-intersection check. Same cwd + shared meaningful (non-main) branches + overlap. Sharper signal; severity: warning (post-§10), info (pre-§10, for visibility).

Both surface in `analysis/patterns/_summary.md` and the daily drift report. 52 + 38 historical findings across the corpus.

### 5. `.agents/tasks/` bootstrap across active repos

The <multi-agent-toolkit>-public toolkit's file-lock protocol gives mechanical "this work is claimed" tickets. Bootstrap script (`/tmp/bootstrap_agents.sh`) installed `.agents/{README.md, schema.json, tasks/.gitkeep}` in **17 previously-bare repos** in `~/Developer/`. 8 already had it (<multi-agent-toolkit>, <biz-gui-repo>, robotics-stack, etc.). 2 skipped as stale. Total: **25 repos with `.agents/`** as of 2026-06-10.

The CLI is installed at `~/.local/bin/agentic-task` via `uv tool install --from ~/Developer/<multi-agent-toolkit> <multi-agent-toolkit>`. Usage:

```bash
AGENT_ID=te-claude AGENT_RUNTIME=claude agentic-task claim <repo-path>
agentic-task list <repo-path>
agentic-task complete <repo-path> <task-id>
```

Coordination via git push collisions — no central server.

## What's still not solved

- **Auto-compact shadow sessions.** When Claude Code hits context limits and spawns a continuation JSONL, the new JSONL is technically a new session by `session_id` but it's the same logical workstream. The detector treats them as concurrent same-cwd sessions, which produces false positives for compacted long-runners. Possible filter: detect "this session is being continued from a previous conversation" markers in user turns. Not implemented yet.
- **Stacked-PR rebase conflicts** (Mode 1 above). The merge-queue spec in `<multi-agent-toolkit>-public/docs/merge-queue.md` addresses this but isn't installed in any consuming repo.
- **Concurrent sessions across machines.** All the detection so far is local to one user's `~/.claude/`. Multi-machine coordination (e.g. one session on laptop + one on a dev VM) is unhandled.

## Carry-forward

- Run the detector after a week to measure whether `same-branch-multi-session` findings drop. Hypothesis: they will, because the SessionStart hook will surface collisions and the user (or Claude) will spin up worktrees instead.
- The five interventions are the minimum mechanical layer. The behavioural layer — user actually *responding* to the hook prompts by creating worktrees — is what determines whether the rate drops. Track per-repo `git worktree list` growth as a positive signal.
- `agentic-task` CLI usage is currently zero in any repo. Adoption is a follow-up — for now the infrastructure exists; the discipline to call it on real work hasn't been established yet.

---

*Diagnosed + interventions landed 2026-06-10. Method: scan `~/.claude/projects/*/<uuid>.jsonl` for git-conflict signals, group by cwd + time window, identify concurrent pairs, validate via timeline overlap. Code: `scripts/detect_patterns.py` rules `concurrent-sessions-same-cwd` + `same-branch-multi-session`.*
