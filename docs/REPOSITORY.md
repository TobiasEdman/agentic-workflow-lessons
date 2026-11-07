# Repository role and rules — agentic_workflow_public

`AGENTS.md` and `CLAUDE.md` in this repository are managed by `agentic-task`
(cross-runtime coordination) and must stay byte-identical to its install
manifest. The repository's own role and working rules live here and apply
alongside them.

## Repository role

This public repository publishes sanitized lessons from private session
analysis. It is an evidence and onboarding surface, not the canonical runtime
governance implementation.

The maintained operational controls, skills, templates and Claude/Codex
adapters live in the companion `multi-agentic-public` repository. The legacy
`starter-pack/` remains for compatibility and historical reproducibility; new
installations should use the companion toolkit.

## Working rules

- Never introduce raw session transcripts, customer identifiers, credentials,
  private repository paths, or unredacted examples.
- Preserve claim provenance and distinguish observation, inference, candidate
  control, and graduated control.
- Do not turn a memorable incident directly into a universal rule.
- Verify links, redaction, and Markdown structure before publishing.
- `CLAUDE.md` and `CODEX.md` are thin runtime addenda and may not redefine this
  repository role.

## Read order

1. This file and `AGENTS.md`
2. `README.md`
3. Relevant lesson under `docs/lessons/`
4. `starter-pack/README.md` only when maintaining the compatibility snapshot
