# Agentic Workflow — Session evidence and lessons

Two artifacts from a 2026 retrospective on long-running agentic coding
sessions, updated with follow-up analyses:

1. **[Lessons](docs/lessons/)** — observations distilled from ~31 archived sessions (Feb–Sep 2026) + 60 post-rework sessions (Apr–May 2026). The *what was learned* and *what changed after we did something about it*.
2. **[Starter-pack compatibility snapshot](starter-pack/)** — the historical
   Claude-oriented operational pack used during the original intervention.

The original sessions, raw transcripts, and per-repo strategy notes stay private; this repo carries only the portable workflow patterns and the operational scaffolding to run them.

## Companion repo

The maintained operational governance now lives in
[**`multi-agentic-public`**](https://github.com/TobiasEdman/multi-agentic-public):
vendor-neutral policy and skills with `AGENTS.md` as primary, plus thin
`CLAUDE.md` and `CODEX.md` runtime addenda.

For new installations, use `multi-agentic-public`. Use this repository to
understand the evidence and why each graduated control exists.

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

starter-pack/                       — historical compatibility snapshot
├── README.md                       — archived install notes and design context
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
- **If you want to apply it today**, use
  [`multi-agentic-public`](https://github.com/TobiasEdman/multi-agentic-public).
  The local [`starter-pack/`](starter-pack/) is retained only for historical
  compatibility and provenance.

The lessons assume you're using Claude Code (or a comparable agentic coding harness) on real engineering work, not toy tasks. They are biased toward sessions in the 50–1,300 turn range, mixed-language projects (Swedish/English), and codebases that touch ML training, geospatial data, and orbital simulation.

## What's been redacted

Concrete examples in the source material reference internal projects, funding sources, and specific work artifacts. Those references have been replaced with generic descriptors (e.g. "the analysis-pipeline repo" instead of project names) so the *patterns* stay legible without leaking the *portfolio*. Where a paragraph was entirely about a specific repo and didn't generalize, it was removed.

If a lesson reads as ungrounded or hand-wavy in places, that's usually where a concrete example used to be. The pattern still holds — the example is just gone.

## Provenance

Source: a private retrospective archive that ingests Claude and Codex session
transcripts, normalizes them into structured events, and produces analytical
reports. The historical Claude-only analysis scripts remain in
[`starter-pack/scripts/`](starter-pack/scripts/) for reproducibility. The
maintained multi-runtime pipeline is private; the post-rework lessons published
here are its sanitized, durable output.

## Maintaining this repository

The repository's role and working rules (redaction, provenance, read order)
are in [`docs/REPOSITORY.md`](docs/REPOSITORY.md). `AGENTS.md` and `CLAUDE.md`
are managed by `agentic-task` and carry only the coordination rules.

## License

- Prose (`docs/` and `starter-pack/*.md`): [CC BY 4.0](./LICENSE)
- Code (`starter-pack/skills/*/SKILL.md` prompts, `starter-pack/hooks/*.sh`): [CC BY 4.0](./LICENSE) — same terms; reuse and adapt freely

If you cite or build on this work, a link back is appreciated but not required.

## Not in scope

This repo is not a tutorial, a framework, or a reusable library. It is observational — *here is what happened over seven months of agentic coding*. Take what's useful, discard what isn't, and write your own retrospective.
