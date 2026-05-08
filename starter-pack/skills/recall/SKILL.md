---
name: recall
description: Retrieve past Claude session context from ~/.claude/checkpoints/. Use when starting a fresh session in a repo and you want to know what was being worked on previously, what the active goal was, what files are off-limits, or what user-stated rules were carried. Also useful when you can't remember the state of a long-running effort across sessions.
---

# /recall

Cross-session continuity retrieval. Looks up checkpoint snapshots written by the `/checkpoint` skill across any repo, surfaces the most relevant ones, and gives the current session a clean opener instead of starting cold.

## Why this skill exists

From [`../../docs/lessons/multi_user_multi_agent.md`](../../docs/lessons/multi_user_multi_agent.md) §C1 + §C2:

> Git is the coordination substrate; coordination > model. Memory matters more than swapping LLM backbones (37% of multi-agent failures = inter-agent misalignment, per AgentGit / Croto research).

`/checkpoint` writes the state. `/recall` reads it back. Together they close the cross-session continuity loop.

## Invocation

- `/recall` — show the most recent checkpoint(s) from the current repo (cwd basename).
- `/recall <repo>` — show recent checkpoints from a specific repo.
- `/recall --all` — list recent checkpoints across all repos.
- `/recall --query "<question>"` — semantic search across all checkpoints (requires a RAG layer indexed over `~/.claude/checkpoints/`; configure as below).
- `/recall --since 2026-04-20` — checkpoints written on or after that date.

## What to do

### Step 1 — pick the lookup mode

| User input | Action |
|---|---|
| no args | infer current repo from `basename $(pwd)`; list latest 3 checkpoints from `~/.claude/checkpoints/<repo>/` |
| repo name | list latest 3 checkpoints from `~/.claude/checkpoints/<repo>/` |
| `--all` | list latest 5 checkpoints across all repos, sorted by ISO date in filename |
| `--query "<q>"` | shell out to your configured RAG tool against the checkpoints index; parse top-3 hits |
| `--since DATE` | filter the file listing by date prefix in filename |

### Step 2 — read the actual checkpoint file(s)

Use the Read tool on the matching `.md` file(s). Each is short (< 30 lines).

### Step 3 — synthesize for the user

Present a single concise opener block:

```
## Recall — <repo>

Most recent checkpoint: <filename>  (<ISO date>, turn <N>)

**Last active goal:** <one sentence from checkpoint>

**Active rules to carry forward:**
- <rule 1>
- <rule 2>

**Files that were off-limits last time:**
- <list>

**Next steps that were planned:**
1. <step>
2. <step>
3. <step>

**Was blocked on:** <text>
```

If `--query` was used, lead with the hit summary, then the standard block.

### Step 4 — offer the natural next move

End with one line: *"Resume from here? Or run `/brief` to start a new task?"*

Don't auto-load context into the next turn — the user decides what to carry forward.

## Configuration

Default checkpoint root: `$HOME/.claude/checkpoints/`. Override via env var `CLAUDE_CHECKPOINTS_DIR` if you've moved it.

For `--query` semantic search, you need a RAG tool indexed against the checkpoints directory. The original setup used a local vector index over `~/.claude/checkpoints/`; any equivalent (LlamaIndex, simple embedding-based search, etc.) works. Without one, the file-listing modes still function.

## Pre-requisites

- `/checkpoint` skill installed and used (otherwise nothing to recall).
- For `--query` mode: a local RAG/index against the checkpoints directory.

## What NOT to do

- Don't paraphrase or "improve" the recalled checkpoint — present it verbatim. The point is to surface what the previous session committed to, not to reinterpret it.
- Don't auto-accept the recalled state. The user might be intentionally pivoting; ask before resuming.
- Don't query if the user just wants the latest file — file listing is faster + cheaper than vector search.
- Don't recall checkpoints from repos the user isn't currently in unless they explicitly ask.

## Rationale

True cross-session retrieval lets a new Claude session ask *"what was I doing in repo X last week?"* and get back the previous session's active goal, off-limits files, and planned next steps. This skill is the user-facing wrapper around that capability.
