# Agentic Workflow — Lessons & Starter Pack

Two artifacts from a 2026 retrospective on long-running Claude Code sessions, **updated May 2026** with a follow-up analysis covering the post-rework window:

1. **[Lessons](docs/lessons/)** — observations distilled from ~31 archived sessions (Feb–Sep 2026) + 60 post-rework sessions (Apr–May 2026). The *what was learned* and *what changed after we did something about it*.
2. **[Starter pack](starter-pack/)** — a drop-in `~/.claude/` configuration (CLAUDE.md template with 9 conventions, 6 skills, 4 hooks, 8 named-role agents, 3 analysis scripts) that operationalizes the lessons. The *how to apply it from day one*.

The original sessions, raw transcripts, and per-repo strategy notes stay private; this repo carries only the portable workflow patterns and the operational scaffolding to run them.

## What's in here

```
docs/lessons/                       — the observational layer
├── workflow_patterns.md            — high-level patterns that recurred across sessions
├── what_worked.md                  — practices that consistently produced good outcomes
├── pitfalls.md                     — failure modes and how they presented
├── instruction_adherence.md        — how Claude follows (and breaks) rules
├── prompting_evolution.md          — how the user's prompting style changed Feb→Sep 2026
├── multi_user_multi_agent.md       — patterns for multi-user, multi-agent setups
├── external_patterns.md            — synthesis of external research and practitioner reports
│   (+ *_raw/ directories with per-source notes)
│
│   ─── post-rework follow-up (May 2026) ────────────────────────────
├── post_rework_evidence.md         — did the §1–§7 rules + skills actually hold?
├── retrospective_v2_jsonl.md       — same four-lens method, re-run on the post-rework corpus
├── rework_effects.md               — pre/post quantitative comparison (6.7× sessions, 2.7× repos)
├── misunderstandings.md            — 12 recurring divergence patterns + proposed ways-of-working
├── continuous_analysis.md          — how the workflow learns from itself
└── omni_rag_contract.md            — minimal contract for a cross-session memory layer

starter-pack/                       — the operational layer
├── README.md                       — install instructions and design notes
├── CLAUDE.md.template              — nine conventions (§1–§9), ready to copy to ~/.claude/CLAUDE.md
├── skills/                         — /checkpoint, /brief, /spec, /review, /recall, /team-loop
├── hooks/                          — active-jobs-guard, co-authored-by, verify-artefakt, cadence-reminder
├── agents/                         — 8 named-role personas (PO/Architect/Developer/Frontend-Builder/
│                                     UX-critic/Business-Controller/Domain-Reviewer/Savant-Reviewer)
└── scripts/                        — JSONL extractor + 17-rule pattern detector + daily drift report
```

## How to read it

Two paths in:

- **If you want to understand what was learned**, start with [`docs/lessons/workflow_patterns.md`](docs/lessons/workflow_patterns.md) and follow your interest. The `*_raw/` directories are the underlying notes if you want to trace a claim.
- **If you want to apply it**, go to [`starter-pack/README.md`](starter-pack/README.md). It explains the install, what each piece does, and how to customize. Read the [CLAUDE.md template](starter-pack/CLAUDE.md.template) before copying — the nine rules are a starting point, not a sacred set.

The lessons assume you're using Claude Code (or a comparable agentic coding harness) on real engineering work, not toy tasks. They are biased toward sessions in the 50–1,300 turn range, mixed-language projects (Swedish/English), and codebases that touch ML training, geospatial data, and orbital simulation.

## What's been redacted

Concrete examples in the source material reference internal projects, funding sources, and specific work artifacts. Those references have been replaced with generic descriptors (e.g. "the analysis-pipeline repo" instead of project names) so the *patterns* stay legible without leaking the *portfolio*. Where a paragraph was entirely about a specific repo and didn't generalize, it was removed.

If a lesson reads as ungrounded or hand-wavy in places, that's usually where a concrete example used to be. The pattern still holds — the example is just gone.

## Provenance

Source: a private retrospective archive that ingests Claude Code session transcripts, parses them into structured JSONL, and produces analytical reports. As of May 2026, the **analysis scripts** are now in [`starter-pack/scripts/`](starter-pack/scripts/) — they read `~/.claude/projects/<encoded-cwd>/*.jsonl` directly and don't depend on any private data layout. They run anywhere Claude Code does. The post-rework lessons published here are the durable output of that pipeline.

## License

- Prose (`docs/` and `starter-pack/*.md`): [CC BY 4.0](./LICENSE)
- Code (`starter-pack/skills/*/SKILL.md` prompts, `starter-pack/hooks/*.sh`): [CC BY 4.0](./LICENSE) — same terms; reuse and adapt freely

If you cite or build on this work, a link back is appreciated but not required.

## Not in scope

This repo is not a tutorial, a framework, or a reusable library. It is observational — *here is what happened over seven months of agentic coding*. Take what's useful, discard what isn't, and write your own retrospective.
