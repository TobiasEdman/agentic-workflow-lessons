---
name: team-loop
description: Orchestrate the named-role multi-agent cascade — Product Owner writes user stories, Developer + Architect run a parallel gap+arch analysis, Frontend Builder iterates UI. Pauses for user approval between phases. Use when a product needs structured planning and the inputs (research / simulations / friction catalogues) already exist. NOT for one-off tasks or pure exploration.
---

# /team-loop

Implements the named-role multi-agent pattern observed in the `rise-pax-lime-gui` build session (2026-05-12, see `multi-agentic/docs/case-studies/2026-05_rise-pax-lime-gui.md`). The pattern: PO defines what to build → Architect + Developer plan how → Frontend Builder executes. Each phase is an `Agent` dispatch against a named persona in `~/.claude/agents/`. The user approves between phases.

## Why this skill exists

The rise-pax case study showed that named-role parallel agents work — but **only when the dispatches are composed in the right sequence**. Composing the sequence by hand each time is the friction `/team-loop` removes.

## When to invoke

- User says `/team-loop`, `/team-loop <user-story-source>`, or `/team-loop --from=<dir>`.
- The product has discovery material that needs to become user stories (research outputs, simulations, friction catalogues, perspective reports), AND
- The codebase exists in a state where Developer can gap-analyse against it, AND
- The user wants the whole PO → Dev+Arch → Frontend cascade, not just one piece.

**Do NOT invoke when:**
- The work is a single-story tweak — just dispatch the relevant agent directly.
- The product is pre-discovery — run discovery first (use `/spec` or parallel exploratory agents).
- The user wants only review, not build — use `/review` instead.

## What to do — phased orchestration

### Phase 0 — Confirm inputs

Before any dispatch, confirm:

1. **What's the user-story source?** Concrete pointers to discovery material (e.g. `docs/feature-spec/`, `docs/simulation/run_1/`, friction catalogues).
2. **What's the codebase root?** The repo the work targets.
3. **What's the phase boundary?** Are we doing Phase 2? Sprint 1? A specific story set?
4. **Where does output land?** Default: `docs/product/` in the target repo.

If any are missing, use `AskUserQuestion` once to confirm. Don't dispatch agents without these.

### Phase 1 — Product Owner

Dispatch:

```
Agent(
  subagent_type="product-owner",
  description="Write user stories from <source>",
  prompt="""
  Read the discovery material at <pointers>.
  Product context: <one-sentence description from user>.
  Current phase: <name>.
  Write the user-story catalogue to <output-path>.
  """
)
```

**Pause.** Show the user the resulting story catalogue. Ask: *"Stories look right? Approve to dispatch Architect + Developer, or refine stories first?"*

If the user wants refinement: re-dispatch PO with their feedback. Do **not** proceed to Phase 2 until approved.

### Phase 2 — Architect + Developer (parallel)

Dispatch both in the **same** assistant turn (parallel `Agent` calls):

```
Agent(
  subagent_type="architect",
  description="Architecture analysis against user stories",
  prompt="""
  Read stories at <stories-path>.
  Read existing code at <code-root>.
  Read API references at <api-refs>.
  Write structural analysis to <arch-output-path>.
  """
)

Agent(
  subagent_type="developer",
  description="Developer gap analysis against user stories",
  prompt="""
  Read stories at <stories-path>.
  Read Architect output at <arch-output-path> if it exists (will be ready in parallel).
  Read existing code at <code-root>.
  Write per-story gap analysis + sprint plan to <dev-output-path>.
  """
)
```

**Pause.** Show the user:
- Architect's verdict + open decisions
- Developer's sprint plan
- Inconsistencies between the two (if any)

Ask: *"Architecture decisions approved? Sprint plan looks right? Approve to dispatch Frontend Builder for Sprint 1, or address decisions first?"*

The Architect's "open decisions" list is the user's input gate. Don't auto-resolve.

### Phase 3 — Frontend Builder

Once the user has ratified the architectural decisions:

```
Agent(
  subagent_type="frontend-builder",
  description="Build Sprint <N> end-to-end",
  prompt="""
  Read stories at <stories-path>.
  Read Developer gap analysis at <dev-output-path>.
  Read Architect output at <arch-output-path>.
  Architectural-decision defaults the user has ratified: <list>.
  Build Sprint <N> (stories <list>).
  Verify each story in browser preview.
  Report at end with what shipped, what's blocked.
  """
)
```

**Do not pause** during Phase 3 — the Frontend Builder is the executor; it should run to completion and report. The user reads the report and decides what's next.

### Phase 3.5 — UX critique (optional but recommended)

If the Frontend Builder shipped UI changes, dispatch the UX critic before declaring the sprint done:

```
Agent(
  subagent_type="ux-critic",
  description="UX-critique of Sprint <N> shipped UI",
  prompt="""
  Read frontend components at <code-root>/frontend/.
  Read user stories at <stories-path>.
  Read locked architectural decisions at <arch-output-path>.
  Read Frontend Builder report at <builder-report-path>.
  Produce a UX-fitness critique against Nielsen + WCAG + the user personas.
  Severity scale: Block / High / Medium / Low. Cite file:line for every finding.
  """
)
```

The UX critic is read-only — surfaces findings, doesn't fix. The user then decides whether to address Top-3 fixes inline, defer, or ignore.

This phase is **complementary** to `/review --lens=savant` (which is code-quality). UX critic asks *"does this serve users?"*; savant asks *"is this code good?"*. Run both for a complete review.

### Phase 4 — Hand off

After the Frontend Builder report (and optional UX-critic report):

- Surface the **"Open items / handoff notes"** section verbatim
- Surface the UX-critic Top-3 fixes if Phase 3.5 ran
- Recommend `/checkpoint` (this is a milestone)
- Recommend `/review --lens=savant` over the diff if any non-trivial commit landed (per §6 verify-before-done)

## Approval discipline

This skill **only progresses on explicit user approval** between phases. Implicit cues ("ok", "yes") count; ambiguous responses ("looks fine") trigger a confirmation question.

The pause points are non-negotiable. The whole skill collapses to "dispatch four agents in sequence" if approvals are skipped — and that's exactly the failure mode of the unstructured version.

## What to NOT do

- Don't dispatch all four agents up front. The cascade exists because each phase depends on the previous one's output.
- Don't fabricate Architect / Developer inputs. If the previous phase didn't produce them, stop.
- Don't run `frontend-builder` without ratified architectural decisions. The Architect's "open decisions" list is a gate.
- Don't substitute `general-purpose` Agent dispatches for named-role personas. The roles are the whole point.
- Don't continue past a user "stop" or "wait" mid-phase. Approval is not implied.

## Provenance

Born from the `rise-pax-lime-gui` session (2026-05-12). Each role corresponds to a `~/.claude/agents/<name>.md` file extracted from that session. Case study: `~/Developer/multi-agentic/docs/case-studies/2026-05_rise-pax-lime-gui.md`. Companion skills: `/spec` (for pre-discovery phase), `/checkpoint` (after each phase pause), `/review` (after Frontend Builder reports).

## Variants

- `/team-loop --review-only` — dispatch BC + domain-reviewer in parallel against a proposed plan, without building anything. Useful for stakeholder simulation before committing to a sprint.
- `/team-loop --from=<dir>` — pre-populate the user-story source from a specific docs directory.
- `/team-loop --skip-architect` — when architecture is already ratified, skip Phase 2 architect dispatch (Developer still runs).
