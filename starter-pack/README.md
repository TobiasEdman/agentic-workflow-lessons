# Starter Pack — Conventions, Skills, Hooks, Agents

A drop-in `~/.claude/` configuration distilled from the lessons in [`../docs/lessons/`](../docs/lessons/). One CLAUDE.md template, six user-invocable skills, four enforcement hooks, eight named-role agent personas, and three analysis scripts. Together they implement the nine conventions from the 2026 retrospective + May 2026 follow-up.

If the [lessons](../docs/lessons/) are *what was learned*, this pack is *how to apply it from day one*.

## Contents

```
starter-pack/
├── CLAUDE.md.template        — global conventions (nine rules: §1–§9)
├── skills/
│   ├── checkpoint/SKILL.md   — mid-session state snapshot
│   ├── brief/SKILL.md        — turn 0 briefing-prompt opener
│   ├── spec/SKILL.md         — interview-driven SPEC.md handoff
│   ├── review/SKILL.md       — fresh-context reviewer subagent
│   ├── recall/SKILL.md       — cross-session checkpoint retrieval (+ implicit-resume)
│   └── team-loop/SKILL.md    — named-role multi-agent cascade orchestrator
├── hooks/
│   ├── active-jobs-guard.sh  — block edits to files belonging to running jobs (rule §3)
│   ├── co-authored-by.sh     — prompt for the agent commit trailer (rule §7)
│   ├── verify-artefakt.sh    — prompt for Verified-by: commit trailer (rule §6)
│   └── cadence-reminder.sh   — surface /checkpoint suggestion at turn-count thresholds (rule §4)
├── agents/
│   ├── product-owner.md       — discovery → user stories
│   ├── architect.md           — stories → structural-fitness analysis
│   ├── developer.md           — per-story gap analysis + sprint plan
│   ├── frontend-builder.md    — build next UI iteration with verification
│   ├── ux-critic.md           — Nielsen + WCAG + interactive task-flow walkthrough
│   ├── business-controller.md — financial-control reviewer simulation
│   ├── domain-reviewer.md     — parameterised domain-expert reviewer
│   └── savant-reviewer.md     — uncompromising code-quality review
└── scripts/                  — continuous-analysis layer (optional)
    ├── from_claude_jsonl.py   — walk ~/.claude/projects/ and build a JSONL corpus
    ├── detect_patterns.py     — 17 rules across 5 categories (continuity / quality / efficiency / praxis / tooling)
    └── daily_drift.py         — daily drift report; intended for scheduled invocation
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

# 4. Named-role agents (for /team-loop and ad-hoc Agent dispatches)
mkdir -p ~/.claude/agents
cp starter-pack/agents/*.md ~/.claude/agents/

# 5. (Optional) Continuous-analysis scripts — put wherever convenient
#    The scripts read ~/.claude/projects/<encoded-cwd>/*.jsonl directly
#    and write analysis/ output relative to wherever you run them from
cp -R starter-pack/scripts ~/Developer/your-analysis-repo/scripts
```

Then register the hooks in `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": "bash $HOME/.claude/hooks/active-jobs-guard.sh" }
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "bash $HOME/.claude/hooks/co-authored-by.sh" },
          { "type": "command", "command": "bash $HOME/.claude/hooks/verify-artefakt.sh" },
          { "type": "command", "command": "bash $HOME/.claude/hooks/cadence-reminder.sh" }
        ]
      }
    ]
  }
}
```

Restart your Claude Code session. Type `/checkpoint` (or any other skill) to confirm they loaded.

## How the pieces compose

The nine conventions in CLAUDE.md prevent the failure modes; the skills make following them cheap; the hooks make breaking them inconvenient. They reinforce each other:

| Convention | Skill that supports it | Hook that enforces it |
|---|---|---|
| §1 Diagnosis vs. directive | — | — (model-side discipline) |
| §2 Echo-back discipline | `/checkpoint` records active rules + plans + sources | — |
| §3 Running code is read-only | — | `active-jobs-guard.sh` |
| §4 Mid-session re-anchor | `/checkpoint`, `/recall` | `cadence-reminder.sh` |
| §5 Front-load the first turn | `/brief`, `/spec` | — |
| §6 Verify work before declaring done | — | `verify-artefakt.sh` |
| §7 Attribute agent commits | — | `co-authored-by.sh` |
| §8 Async hand-off | — | — (uses scheduled-tasks tooling) |
| §9 Artifact minimalism | — | — (model-side discipline) |

The unhooked text rules (§1, §5, §8, §9) are the ones where automatic enforcement would be too brittle — they require model-side judgement. The pack relies on the CLAUDE.md text to carry them.

## Named-role agents — the multi-agent layer

Seven of the eight agent personas (all except `savant-reviewer`) came from observing one production session that ran 11 complete cycles of PO → Architect + Developer → Frontend Builder → UX critic in a single 22-hour stretch. The patterns were extracted to portable persona files and the `/team-loop` skill that orchestrates them.

Dispatch via `Agent(subagent_type="<name>", description="...", prompt="...")`. Or invoke `/team-loop` to run the cascade with user-approval pauses between phases.

Each persona file has:
- A YAML frontmatter (name, description, tools, model)
- A mandatory workflow the persona must follow
- Rules the persona must respect (e.g. "Architect doesn't propose rewrites without evidence")
- Output format requirements
- A "what this subagent will NOT do" section

Customize the personas for your domain — the workflow shapes are universal but the language can match your stakeholders.

## Continuous-analysis layer (scripts/)

Optional but recommended once you have ~30 sessions of history. The three scripts form a passive analysis loop:

1. `from_claude_jsonl.py` walks `~/.claude/projects/` and builds a structured corpus.
2. `detect_patterns.py` runs 17 rules against the corpus, emitting findings to `analysis/patterns/`.
3. `daily_drift.py` compares today's snapshot to yesterday's, emits `analysis/daily/<date>.md`.

Schedule `daily_drift.py` via Claude Code's `mcp__scheduled-tasks` to fire daily — the script writes to disk, never acts. You read the alerts and decide whether to intervene.

The rule categories: **continuity** (drift, missing checkpoint, echo-back gaps), **quality** (trailers, commit size), **efficiency** (re-reads, Bash loops, tool-call explosion), **praxis** (commit-without-test, edit-without-read, main-branch commits), **tooling** (git pre-commit bypass attempts). See `detect_patterns.py` for the full registry.

## Customize, don't fork

- **CLAUDE.md.template** — read it; remove rules that don't apply to your work; add project-specific ones. The nine listed are a *starting point*, not a sacred set.
- **Skills** — the SKILL.md files are markdown and self-explanatory. Edit prompts, add flags, change templates as your style evolves.
- **Hooks** — all four are fail-open shell scripts. They emit `permissionDecision: "ask"` rather than blocking outright, so a hook bug never costs you work. Read them before installing — you should understand what's intercepting your `git commit`, `Edit`, and `Bash`.
- **Agents** — the personas were extracted from one domain (research-administration workflows) but generalize. Replace stakeholder language in `business-controller.md` and `domain-reviewer.md` to match your domain.

## What's intentionally not in here

- **Project-specific subagents.** Things like `security-reviewer`, `schema-guardian` belong at the *repo* level (`<repo>/.claude/agents/`), not at the global `~/.claude/` level.
- **Checkpoint RAG layer.** `/recall --query` would require a local vector index over `~/.claude/checkpoints/`. The skill works in file-listing mode without one; semantic-search mode is something you bolt on (LlamaIndex, Vespa, simple embedding search — pick what fits your stack). See [`../docs/lessons/omni_rag_contract.md`](../docs/lessons/omni_rag_contract.md) for the contract such a layer should satisfy.
- **Output-vs-process commit guard.** A fifth hook from the original setup blocked commits that staged binary outputs without versioning the producing process. The concept is universal and worth implementing in any codebase that ships generated artifacts (PNGs, models, datasets), but the original was tightly coupled to one repo's directory layout. Build your own from `active-jobs-guard.sh` as a template.

## Anti-patterns to avoid

After deploying the pack, watch out for these failure modes (all observed in real corpora):

- **Wildcard `git commit` patterns in project-level allow-lists.** Patterns like `Bash(git commit:*)` in `.claude/settings.local.json` silence the §6 + §7 enforcement hooks at the UI layer. Don't add them. If you accidentally clicked "Always allow" on a commit prompt, edit the settings file to remove the pattern.
- **Long sessions without checkpoint.** The cadence-reminder hook fires at 50/100/250/500/1000 turns; if you find yourself dismissing it repeatedly, the session is probably drifting and a fresh-session restart will be cheaper than continuing.
- **Generic `general-purpose` agents when named roles exist.** If you're dispatching for "review the architecture", use `subagent_type: "architect"` not `general-purpose`. The persona constraints catch failure modes the generic prompt misses.

## Versioning

This pack is a snapshot — the source `~/.claude/` it was carved from continues to evolve. If you find a divergence between this pack and your installed copy useful, that's a signal something has shipped that's worth contributing back. Open an issue on the lessons repo.
