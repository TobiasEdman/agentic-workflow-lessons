# Misunderstandings — where Claude and the user diverged, and proposed ways-of-working

> Research output. Mines the post-rework JSONL corpus for moments where the user explicitly corrected, stopped, or had to ask Claude to redo work — and groups them into recurring divergence patterns. Each pattern has a proposed way-of-working (WoW) to avoid recurrence.

## Method

Scanned user turns in 73 post-2026-04 sessions (skipping system tags and very long briefing turns) for seven categories of pushback signal: explicit STOP, explicit correction, scope pushback, "you misunderstood", redo-it, wrong-file, premature-action. ~200 raw matches; the explicit-STOP category is mostly framework noise (the Stop-hook telemetry that fires every time a Write happens during a preview server run). The real signal is in the other six categories — about **25 distinct misunderstanding moments** across 11 sessions.

## The six divergence patterns

### Pattern 1 — "Sluta ändra, jag frågade bara"

**Diagnosis-read-as-directive.** The user asks a question or makes a structural observation; Claude treats it as an instruction to act.

**Quote of record:**
> *"sluta ändra i fetchkoden för att jag ställer frågor!!! fortsätt hämta bara"*
> — `<geo-ml-repo> <session-X>`, <geo-ml-repo> LULC training session

Three exclamation marks, profanity-adjacent. This is the most expensive class of misunderstanding by far, and it's the one §1 in `CLAUDE.md` was written to prevent. It still happens.

**Sub-form:** Claude treats a question as a *plan-of-action* and starts editing the code referenced in the question. The user asked "is this the bug?" — Claude heard "fix this bug".

**Proposed WoW:**
- **WoW-1a (in CLAUDE.md, already added 2026-05-12):** When the user's turn lacks an imperative verb (`fix`, `change`, `edit`, etc.), prefix the response with: *"Reading this as a question/diagnosis/preference, not an instruction to act. Should I investigate, or change it?"*
- **WoW-1b (new):** **Especially for running code.** Add to §3: when the user asks a question about code that is currently executing (live fetch, training job, server process), the default is *answer the question*, never *edit the code*. The hook `active-jobs-guard.sh` covers locked paths but not the broader class.
- **WoW-1c (verbal):** If a user message ends with `?` and contains code paths or function names, the default response is *explanation*, not *modification*. Only act if the next user turn is an imperative.

### Pattern 2 — "Vi skulle ju köra X, gör om"

**Plan-context lost mid-session.** The user established a plan (e.g. "test small bbox first, then scale up", "produce sjökort in large bbox + laga-skifte in small bbox"). Many turns later Claude executes against the *wrong half* of the plan.

**Quotes of record:**
> *"Vi skall ju köra utan vägar, hus och LPIS, de lägger vi på i efterhand, gör om och addera till lagaskiftesbeskrivningen"*
> — `<visual-render-repo> <session-X>`

> *"Vi skulle köra sjökort i den stora och laga skifte i den lilla bbox:en. Gör om och gör rätt"*
> — `<visual-render-repo> <session-X>`

These are session-internal **plan violations** — the user's plan was correct, Claude's memory of which half of it was active drifted.

**Proposed WoW:**
- **WoW-2a:** When a user states a multi-part plan with *"first X, then Y"* / *"X i Z och Y i W"* structure, the assistant should restate the plan back in a numbered list as part of its first action turn. Echo-back §2, but specifically for *plan structure*.
- **WoW-2b:** When the assistant is about to perform a major action (run a pipeline, render an output, run a script with parameters), it should self-check: *"Plan said X in context A, Y in context B. I'm about to do …, which is context …"* — one line of explicit self-orientation before the tool call. Cheap; covers the case.
- **WoW-2c:** For multi-context sessions (<visual-render-repo> is the obvious case — large/small bbox, sjökort/laga-skifte, with/without LPIS), recommend `/checkpoint` halfway through to persist the plan. The cadence hook now mechanically prompts this past turn 50; this is the *content* the cadence anchor should preserve.

### Pattern 3 — "Nej, jag var nyfiken"

**Asking ≠ asking for action.** The user expresses curiosity about an option or a possibility. Claude treats it as a request to implement.

**Quote of record:**
> *"nej, jag var nyfiken"* (after Claude started building something based on a user query)
> — `<visual-render-repo> <session-X>`

**Proposed WoW:**
- **WoW-3a:** This is the close cousin of Pattern 1, distinct because the user's turn doesn't even hint at a directive — it's pure exploration. When the user asks *"could we X?"* / *"vad händer om vi X?"* / *"is X possible?"*, **always** answer the question first; **only** start building if a follow-up explicitly says so.
- **WoW-3b:** Add to the §1 verbal prefix: distinguish three readings — *question (answer)*, *preference (note it, ask)*, *curiosity (explain, don't build)*.

### Pattern 4 — "Gör om hela analysen baserat på X"

**Re-run with new scope after Claude shipped the wrong scope.** The user asked for analysis based on source A; Claude ran it on source B (the previous default). The user has to explicitly re-instruct with the right source.

**Quote of record:**
> *"Gör om hela analysen baserat på jsonl och utifrån allt arbete som vi har gjort"*
> — `<workflow-repo> <session-X>` (this session)

In this case, the .docx corpus was the *previous* default; JSONL was the new explicit source. Claude had already been told JSONL was better but defaulted to the prior task scope when the user pivoted.

**Proposed WoW:**
- **WoW-4a:** When the user's turn introduces a **source change** (*"based on X instead of Y"*, *"utifrån X"*), the assistant must restate the new source explicitly as part of acknowledging the turn. *"Got it — switching the analysis source from .docx export to JSONL corpus."*
- **WoW-4b:** Source/scope changes should trigger an `AskUserQuestion` if the change has cascading consequences (different output structure, different conclusions). Tighter on the front end saves the redo cost on the back end.

### Pattern 5 — "Gör om pilen, visa den rena pilen utan rotation"

**Claude over-elaborated.** The user wanted a simple, isolated artifact. Claude produced an elaborate composite or applied an effect (rotation, styling, integration) that wasn't asked for.

**Quote of record:**
> *"Vi måste gör om pilen, visa den rena pilen utan rotation"*
> — `<visual-render-repo> <session-X>`

The user wanted a clean reference object. Claude produced a contextual transformation.

**Proposed WoW:**
- **WoW-5a:** For *visual / artifact* asks, the default is **minimal**. Generate the bare artifact in isolation first, then ask if it should be combined / rotated / styled. *"Here's the clean arrow. Should I rotate or composite it into the map next?"*
- **WoW-5b:** This connects to a deeper anti-pattern named in `~/.claude/CLAUDE.md` — *"Don't add features, refactor code, or make 'improvements' beyond what was asked."* The rule exists; the visual-artifact case is where it most often slips.

### Pattern 6 — "Vad har vi kvar enligt plan?"

**The user has to re-orient Claude mid-session.** After Claude finishes a sub-step and proceeds with what it thinks is the next step, the user has to interrupt and ask *"what's left, according to the plan?"* — because Claude's next step doesn't match the plan.

**Quote of record:**
> *"nej, vad jhar vi kvar enligt plan?"*
> — `<robotics-repo> <session-X>`

Note the typo (`jhar` for `har`) — typed in haste because the user is annoyed enough not to proofread.

**Proposed WoW:**
- **WoW-6a:** After completing a sub-step that was part of an explicit multi-step plan, the assistant should **name what's done and what's next from the plan**, not just declare success on the sub-step. *"✅ Step 3 done (sensor research). Plan says next is Step 4 (autopilot evaluation). Should I proceed?"*
- **WoW-6b:** This is a `TodoWrite`-pattern fix. If a TodoWrite todo list exists, refer to it at every completion. If it doesn't, *create one* when the user states a plan.

## Cross-cutting observations

1. **All six patterns share a root cause: ambiguity Claude resolved by acting.** §1 of CLAUDE.md addresses this for diagnosis-vs-directive. The patterns above generalize it: there are *five more flavours* of the same ambiguity, each with its own surface form.

2. **The most expensive instances correlate with long sessions.** `<session-X>` (3,759 turns) generated the strongest pushback (*"sluta ändra i fetchkoden!!!"*). `<session-X>` (2,763 turns) generated four "gör om" moments. Long sessions accumulate plan-state Claude loses track of. The cadence-hook (shipped 2026-05-12) is the start of a mechanical fix; the WoWs above are the verbal half.

3. **Most pushbacks happen in Swedish.** This continues the pattern from `retrospective_v2_jsonl.md` §1.2 — Swedish for diagnosis, English for build. When a Swedish pushback turn arrives, the right response is *also Swedish* and *also diagnostic* (clarify intent before acting), not *English directive* (acknowledge + start doing).

4. **No "you misunderstood" / "wrong file" matches.** The user almost never frames the correction as *Claude's failure*. The frame is always *what should happen next* — *"gör om"*, *"sluta"*, *"vi skulle ju"*. This is generous but also masks the misunderstanding signal: it looks like a new instruction, not a correction. The assistant should learn to *recognise* a redo as a misunderstanding signal, not just execute the redo.

## Summary of proposed WoWs

| # | When | What |
|---|---|---|
| WoW-1a | User turn lacks imperative verb | Prefix response with "Reading this as a question/diagnosis/preference…" |
| WoW-1b | Question about running code | Default to *answer*, never *edit* |
| WoW-1c | User turn ends in `?` and mentions code paths | Default to explanation |
| WoW-2a | User states multi-part plan | Echo back as numbered list in first action turn |
| WoW-2b | Before any major action in a multi-step plan | Self-check: "Plan said X for context A; I'm about to do … in context …" |
| WoW-2c | Multi-context session | Recommend `/checkpoint` halfway to persist the plan |
| WoW-3 | "Could we X?" / "vad händer om X?" | Always answer the question, never start building |
| WoW-4a | Turn introduces source change ("based on X instead of Y") | Restate the new source explicitly |
| WoW-4b | Source change with cascading consequences | Fire `AskUserQuestion` before acting |
| WoW-5a | Visual / artifact ask | Generate bare artifact first, ask about composition next |
| WoW-6a | Completing a sub-step in a stated plan | Name done + next from the plan, ask to proceed |
| WoW-6b | User states a multi-step plan | Create a TodoWrite immediately; refer to it on every completion |

## Carry-forward

These WoWs are convention-layer, not hook-layer — they're behaviours Claude needs to internalize, not mechanical guards. **The cheapest path to adoption** is one short paragraph in `~/.claude/CLAUDE.md` that names the six patterns and points here. Hooks can't enforce these without LLM-side judgement; AGENTS.md paragraphs can.

A new pattern-detector rule is *possible* for WoW-6b: detect sessions where the user states a plan (`"first X, then Y"` structure) and no `TodoWrite` follows within 5 tool calls. Mechanical. Worth adding to `detect_patterns.py` if these recur.

## Files referenced

- Source: `~/.claude/projects/*/<uuid>.jsonl` (post-2026-04)
- Sibling: [`docs/lessons/post_rework_evidence.md`](post_rework_evidence.md) §1 (where preference-as-directive was first measured)
- Sibling: [`docs/lessons/retrospective_v2_jsonl.md`](retrospective_v2_jsonl.md) §2.1 (the Engineer-vs-Partner split on whether §1 holds)
- Related: `~/.claude/CLAUDE.md` §1, §2, §3, §4 — current rules these WoWs would extend
