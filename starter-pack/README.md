# Starter Pack — Conventions, Skills, Hooks

A drop-in `~/.claude/` configuration distilled from the lessons in [`../docs/lessons/`](../docs/lessons/). One CLAUDE.md template, five user-invocable skills, and two enforcement hooks. Together they implement the seven conventions from the 2026 retrospective.

If the [lessons](../docs/lessons/) are *what was learned*, this pack is *how to apply it from day one*.

## Contents

```
starter-pack/
├── CLAUDE.md.template        — global conventions (the seven rules)
├── skills/
│   ├── checkpoint/SKILL.md   — mid-session state snapshot
│   ├── brief/SKILL.md        — turn 0 briefing-prompt opener
│   ├── spec/SKILL.md         — interview-driven SPEC.md handoff
│   ├── review/SKILL.md       — fresh-context reviewer subagent
│   └── recall/SKILL.md       — cross-session checkpoint retrieval
└── hooks/
    ├── active-jobs-guard.sh  — block edits to files belonging to running jobs (rule §3)
    └── co-authored-by.sh     — prompt for the agent commit trailer (rule §7)
```

## Install

```bash
# 1. Conventions (review the template first; then copy to ~/.claude/CLAUDE.md)
cp starter-pack/CLAUDE.md.template ~/.claude/CLAUDE.md

# 2. Skills (each becomes a /<name> slash-command)
mkdir -p ~/.claude/skills
cp -R starter-pack/skills/* ~/.claude/skills/

# 3. Hooks
mkdir -p ~/.claude/hooks
cp starter-pack/hooks/*.sh ~/.claude/hooks/
chmod +x ~/.claude/hooks/*.sh
```

Then register the hooks in `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": "bash ~/.claude/hooks/active-jobs-guard.sh" }
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "bash ~/.claude/hooks/co-authored-by.sh" }
        ]
      }
    ]
  }
}
```

Restart your Claude Code session. Type `/checkpoint` (or any of the other skills) to confirm they loaded.

## How the pieces compose

The seven conventions in CLAUDE.md prevent the failure modes; the skills make following them cheap; the hooks make breaking them inconvenient. They reinforce each other:

| Convention | Skill that supports it | Hook that enforces it |
|---|---|---|
| §1 Diagnosis vs. directive | — | — (model-side discipline) |
| §2 Echo-back discipline | `/checkpoint` records active rules | — |
| §3 Running code is read-only | — | `active-jobs-guard.sh` |
| §4 Mid-session re-anchor | `/checkpoint`, `/recall` | — |
| §5 Front-load the first turn | `/brief`, `/spec` | — |
| §6 Verify work before declaring done | — | — (model-side discipline) |
| §7 Attribute agent commits | — | `co-authored-by.sh` |

The two unhooked text rules (§1, §6) are the ones where automatic enforcement would be too brittle — both require model-side judgement. The pack relies on the CLAUDE.md text to carry them.

## Customize, don't fork

- **CLAUDE.md.template** — read it; remove rules that don't apply to your work; add project-specific ones. The seven listed are a *starting point*, not a sacred set.
- **Skills** — the SKILL.md files are markdown and self-explanatory. Edit prompts, add flags, change templates as your style evolves.
- **Hooks** — both are fail-open shell scripts. They emit `permissionDecision: "ask"` rather than blocking outright, so a hook bug never costs you work. Read them before installing — you should understand what's intercepting your `git commit` and `Edit`.

## What's intentionally not in here

- **Output-vs-process commit guard.** A third hook from the original setup blocked commits that staged binary outputs without versioning the producing process. The concept is universal and worth implementing in any codebase that ships generated artifacts (PNGs, models, datasets), but the original was tightly coupled to one repo's directory layout. Build your own from the active-jobs-guard.sh as a template.
- **Project-specific subagents.** Things like `savant-reviewer`, `security-reviewer`, `schema-guardian` belong at the *repo* level (`<repo>/.claude/agents/`), not at the global `~/.claude/` level. The pack's `/review` skill supports lens variants for those when you build them.
- **Checkpoint RAG layer.** `/recall --query` requires a local index over `~/.claude/checkpoints/`. The pack's recall skill works in file-listing mode without one; the semantic-search mode is something you bolt on (LlamaIndex, Vespa, simple embedding search — pick what fits your stack).

## Versioning

This pack is a snapshot — the source `~/.claude/` it was carved from continues to evolve. If you find a divergence between this pack and your installed copy useful, that's a signal something has shipped that's worth contributing back. Open an issue on the lessons repo.
