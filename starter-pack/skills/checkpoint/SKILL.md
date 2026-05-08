---
name: checkpoint
description: Write a mid-session checkpoint snapshot to ~/.claude/checkpoints/<repo>/. Use when ~50 turns have passed in a long session, before a natural break, or when the user asks to checkpoint. Captures active goal, files changed, files off-limits, next 3 steps, blocked-on, and active user-stated rules.
---

# /checkpoint

Emit a structured snapshot of the current session state to `~/.claude/checkpoints/<repo-name>/<YYYY-MM-DD>_<slug>_turn<N>.md`.

## Two modes — same skill, different cadence

The retrospective observed that checkpoints get used in two distinct ways. Both are valid; be explicit which one you're writing.

| Mode | Cadence | Purpose | Slug convention | Written by |
|---|---|---|---|---|
| **drift** | every ~50 turns in long sessions, when topic shifts unannounced, before a natural pause | recover focus when the session has wandered; let a future fresh session resume *intent*, not just files | `drift-<short-context>`, e.g. `drift-fetch-debug` | typically the model when you notice drift, with user confirmation |
| **milestone** | at the completion of a wave, feature, or significant task | mark *project progress* — what shipped, what's next, what's blocking | `<wave-or-task>-complete`, e.g. `wave4-complete`, `oauth-shipped` | typically the user requests it after a clear milestone |

Rule §4 in `~/.claude/CLAUDE.md` prescribes the **drift** cadence specifically (50-turn re-anchor). Milestone checkpoints are a complementary use of the same store. Neither replaces the other.

## When to invoke

- **Drift mode**: every ~50 turns in sessions past 5k words, offer a checkpoint. Do NOT auto-write without user confirmation. Also fires when topic shifts unannounced — see rule §4.
- **Milestone mode**: on user request after a wave / feature / task ships. Argument is the milestone slug.
- Either mode: on user request `/checkpoint` or `/checkpoint <slug>`.
- Before a natural pause (switching sub-topics, ending the day, closing the session).
- Immediately after resolving a significant bug.

## What to do

1. **Determine repo name:** `basename $(pwd)` gives the repo. If the cwd is not inside a repo, ask the user what label to use.
2. **Determine filename:**
   - Date: today's ISO date (`YYYY-MM-DD`).
   - Slug: short kebab-case descriptor. If the user passed one as the skill argument, use it. Otherwise, derive from the active goal (first 3-5 words).
   - Turn: approximate turn index. If you don't have it, use the message count in the current session or drop the `_turnN` suffix.
   - Full path: `~/.claude/checkpoints/<repo>/<YYYY-MM-DD>_<slug>[_turn<N>].md`
3. **Ensure the directory exists:** `mkdir -p ~/.claude/checkpoints/<repo>`.
4. **Fill the template** at `~/.claude/checkpoints/TEMPLATE.md` with the current state:
   - **Active goal:** one sentence. If unclear, ask the user before writing.
   - **Files changed since last checkpoint:** if a previous checkpoint exists for this repo, list files edited since its timestamp. If not, list files edited this session.
   - **Files that must NOT change:** any file the user has declared read-only (e.g. "don't touch the running fetch code"). If none, write `(none declared this session)`.
   - **Next 3 steps:** either from the current TodoWrite state, or ask the user to confirm 3.
   - **Blocked on:** anything external. If nothing, write `nothing`.
   - **Active rules (echo-back):** every session-wide rule the user has stated that should persist. Quote verbatim. If none, write `(none declared this session)`.
   - **Context note:** optional, one line.
5. **Write the file** using the Write tool.
6. **Report:** tell the user the full path written, and the one-sentence active goal you recorded. This lets the user correct any drift between what they think the session is about and what you wrote.

## Formatting rules

- Keep the file under ~25 lines. Brevity is the point.
- Never write secrets, tokens, or credentials into the checkpoint.
- Use relative paths for files in the current repo. Use absolute paths only if cross-repo.
- If a previous checkpoint for this repo exists, link to it at the bottom: `Previous: ~/.claude/checkpoints/<repo>/<earlier-file>.md`.

## What NOT to do

- Don't write a checkpoint without confirming the active goal if it's ambiguous.
- Don't write a checkpoint while a tool call is in flight. Wait for the current action to finish.
- Don't overwrite an existing checkpoint file. Filenames include the turn number specifically to avoid collision.
- Don't rewrite the TEMPLATE.md — always copy its structure into a new file.

## Rationale

Derived from the 2026 retrospective: every high-cost failure mode was a continuity failure. Checkpoints are the minimum viable continuity layer.
