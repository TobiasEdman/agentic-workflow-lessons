# Agentic Workflow — Lessons & Starter Pack

Two artifacts from a 2026 retrospective on long-running Claude Code sessions:

1. **[Lessons](docs/lessons/)** — observations distilled from ~31 sessions across a private R&D portfolio (Feb–Sep 2026). The *what was learned*.
2. **[Starter pack](starter-pack/)** — a drop-in `~/.claude/` configuration (CLAUDE.md template + 5 skills + 2 hooks) that operationalizes the lessons. The *how to apply it from day one*.

The original sessions, raw transcripts, and per-repo strategy notes stay private; this repo carries only the portable workflow patterns and the operational scaffolding to run them.

## What's in here

```
docs/lessons/                       — the observational layer
├── workflow_patterns.md            — high-level patterns that recurred across sessions
├── what_worked.md                  — practices that consistently produced good outcomes
├── pitfalls.md                     — failure modes and how they presented
├── instruction_adherence.md        — how Claude follows (and breaks) rules across long sessions
├── prompting_evolution.md          — how the user's prompting style changed Feb→Sep 2026
├── multi_user_multi_agent.md       — patterns for multi-user, multi-agent setups
├── external_patterns.md            — synthesis of external research and practitioner reports
├── external_patterns_raw/          — per-source notes feeding external_patterns.md
└── multi_user_multi_agent_raw/     — per-source notes feeding multi_user_multi_agent.md

starter-pack/                       — the operational layer
├── README.md                       — install instructions and design notes
├── CLAUDE.md.template              — the seven conventions, ready to copy to ~/.claude/CLAUDE.md
├── skills/                         — /checkpoint, /brief, /spec, /review, /recall
└── hooks/                          — active-jobs-guard.sh, co-authored-by.sh
```

## How to read it

Two paths in:

- **If you want to understand what was learned**, start with [`docs/lessons/workflow_patterns.md`](docs/lessons/workflow_patterns.md) and follow your interest. The `*_raw/` directories are the underlying notes if you want to trace a claim.
- **If you want to apply it**, go to [`starter-pack/README.md`](starter-pack/README.md). It explains the install, what each piece does, and how to customize. Read the [CLAUDE.md template](starter-pack/CLAUDE.md.template) before copying — the seven rules are a starting point, not a sacred set.

The lessons assume you're using Claude Code (or a comparable agentic coding harness) on real engineering work, not toy tasks. They are biased toward sessions in the 50–1,300 turn range, mixed-language projects (Swedish/English), and codebases that touch ML training, geospatial data, and orbital simulation.

## What's been redacted

Concrete examples in the source material reference internal projects, funding sources, and specific work artifacts. Those references have been replaced with generic descriptors (e.g. "the analysis-pipeline repo" instead of project names) so the *patterns* stay legible without leaking the *portfolio*. Where a paragraph was entirely about a specific repo and didn't generalize, it was removed.

If a lesson reads as ungrounded or hand-wavy in places, that's usually where a concrete example used to be. The pattern still holds — the example is just gone.

## Provenance

Source: a private retrospective archive (`agentic_workflow`, private repo) that ingests Claude Code session transcripts, parses them into structured JSONL, and produces analytical reports. The **scripts** that do the parsing/analysis are not in this public mirror — they're tightly coupled to the private archive's data layout. The lessons published here are the durable output of that pipeline.

## License

- Prose (`docs/` and `starter-pack/*.md`): [CC BY 4.0](./LICENSE)
- Code (`starter-pack/skills/*/SKILL.md` prompts, `starter-pack/hooks/*.sh`): [CC BY 4.0](./LICENSE) — same terms; reuse and adapt freely

If you cite or build on this work, a link back is appreciated but not required.

## Not in scope

This repo is not a tutorial, a framework, or a reusable library. It is observational — *here is what happened over seven months of agentic coding*. Take what's useful, discard what isn't, and write your own retrospective.
