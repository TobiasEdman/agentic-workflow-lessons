---
name: spec
description: Interview the user about a non-trivial feature or task, writing the answers into a SPEC.md file. Then instruct the user to start a fresh session that executes the spec. Use when the user says "/spec", or when they describe a feature that will touch multiple files, require architectural decisions, or has ambiguous requirements. Do NOT use for one-line fixes or tasks with clear scope.
---

# /spec

Implements Anthropic's interview-driven spec pattern. Converts an ambiguous task description into a written specification, then hands off to a fresh session for execution.

## Why this skill exists

Non-trivial features fail when Claude starts implementing before requirements are clear. The briefing-opener pattern works for sessions where the user already has clarity. This skill works for sessions where the user has a goal but hasn't yet thought through the edge cases.

Source: Anthropic Best Practices §Communicate effectively — *"For larger features, have Claude interview you first. Start with a minimal prompt and ask Claude to interview you using the AskUserQuestion tool. Claude asks about things you might not have considered yet, including technical implementation, UI/UX, edge cases, and tradeoffs."*

## When to invoke

- User says `/spec` or `/spec <brief description>`.
- User describes a feature that:
  - Will touch more than 2 files, OR
  - Involves an architectural decision (new dependency, new service, new data flow), OR
  - Has unclear edge cases or failure modes, OR
  - Could reasonably be built three different ways.
- Do NOT invoke for: typos, one-line fixes, renaming a variable, adding a log line, obvious bug fixes.

## What to do

### Step 1 — Frame the interview

Open with:

> I'll interview you to build a SPEC.md. I'll ask about technical implementation, UX, edge cases, and tradeoffs — dig into the hard parts, skip the obvious. Once we've covered everything I'll write the spec and you can start a fresh session to execute it.

### Step 2 — Interview using `AskUserQuestion`

Use the `AskUserQuestion` tool, one focused batch at a time. Topics to cover (not all mandatory — judge by task):

1. **Scope & non-goals.** What's in scope for this iteration? What's explicitly OUT of scope?
2. **Data & state.** What data is read, written, mutated? Where does it live now?
3. **Interface.** CLI, API, UI? What does the user (human or machine) call, and what do they get back?
4. **Dependencies.** What existing code must not break? What new deps are acceptable? What are off-limits?
5. **Failure modes.** What happens on: bad input, network failure, concurrent access, partial completion?
6. **Verification.** How will we know it works? Tests, screenshots, manual check?
7. **Constraints.** Hard limits (latency, memory, cost, concurrency), soft preferences (language, style).
8. **Tradeoffs.** If there are two reasonable approaches, which does the user prefer and why?

Batch 2–4 questions per `AskUserQuestion` call. Don't ask more than 4 batches total unless the user asks for more depth. If a question is obvious from context, skip it.

### Step 3 — Write `SPEC.md`

Save to `./SPEC.md` in the current working directory. Template:

```markdown
# SPEC — <task headline>

**Created:** <ISO date>
**Target repo:** <cwd>
**Status:** draft, pending fresh-session execution

## Context

<2-3 sentences on why this work is happening and what triggered it>

## In scope

- <bullet>
- <bullet>

## Out of scope

- <bullet — what we explicitly will NOT do>

## Interface

<CLI / API / UI / other — concrete signatures>

## Data & state

<What gets read / written / migrated — cite specific paths>

## Dependencies

- New deps (if any): <list with version constraints>
- Must not break: <list>
- Off-limits: <list>

## Failure modes & verification

| Scenario | Expected behavior | Verification method |
|----------|-------------------|---------------------|
| <bad input> | <...> | <test / assertion> |
| <network failure> | <...> | <...> |

## Constraints

- <Hard limits>
- <Soft preferences>

## Tradeoffs accepted

<Any place where the user chose A over B, with one-line rationale>

## Execution hints

- Files likely to change: <best guess>
- Tests to add: <best guess>
- Rollback strategy: <how to undo if it goes wrong>

## Open questions

<Anything the user deferred or left ambiguous — flagged so the executing session knows to ask>
```

### Step 4 — Hand off

After writing SPEC.md, output a single block the user can paste into a fresh session:

```
Open a new Claude Code session in this repo and paste:

  Read SPEC.md and execute it. Ask before doing anything that isn't explicitly in scope.
  Use /brief if you need to flesh out any section further.
```

Then end the current session's spec-writing phase. Do NOT start implementation in the same session — the point is a fresh context.

## Quick mode

If invoked as `/spec --quick`, skip the interview. Write a SPEC.md skeleton with placeholders the user fills in manually. Useful when the user has the answers ready and just wants the structure.

## What NOT to do

- Don't interrogate. Batch questions 2-4 at a time, not 10.
- Don't ask obvious questions (*"What programming language?"* when the repo is clearly Python).
- Don't write SPEC.md before confirming coverage with the user. Always end the interview phase explicitly: *"I have enough. Writing the spec now."*
- Don't start implementation. The whole point is the handoff.
- Don't skip the "open questions" section — if something is ambiguous after the interview, name it. The executing session needs to know.

## Rationale

From [`../../docs/lessons/external_patterns.md`](../../docs/lessons/external_patterns.md) Tier 1: the interview-driven spec is one of four patterns documented in Anthropic's best practices that compounds especially well with `/checkpoint` (to recover context across the handoff) and `/brief` (to flesh out individual execution steps).
