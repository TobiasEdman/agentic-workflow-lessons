# Instruction Adherence — when Claude's rails bent

This file looks at moments where an instruction (yours, or from Claude's own CLAUDE.md / system prompt) was set aside, and why. Evidence is drawn from 31 archived sessions with 1,922 user turns and ~3,610 assistant turns. Every claim here is linked to a session id + turn index so you can open `sessions/cleaned/<id>.txt` (or `sessions/raw/<id>.txt` until cleaning lands) and read the context yourself.

> Methodology caveat: the CLI-format parser assigns role by alternation and over-counts turns. The quotes below were hand-verified against the source text. Turn indices are from `sessions/jsonl/sessions.jsonl`.

---

## The top 6 drift cases

### 1. Claude edited live fetch code *while the user was asking questions about it*

`session-context:298` and `session-context:324` (digital-earth-sweden cluster, 2026-09-03, ~69k words).

You set the rule *explicitly*:

> "fuck! gör aldrig om något som tar min tid i onödan, notera det. fråga alltid innan du gör idioti" *(session-context, turn 298)*

Then ~30 turns later:

> "sluta ändra i fetchkoden för att jag ställer frågor!!! fortsätt hämta bara" *(session-context, turn 324)*

The preceding user turns (290, 320) were status questions and a conditional suggestion ("öka dynamiskt" — *scale dynamically*). Claude read them as directives and started editing the fetch code instead of observing. **Cause:** ambiguity between *"what if X?"* and *"do X"*. In Swedish technical dialogue the two blur more than in English. **Lesson for Claude:** questions about running code are never permission to change it. Ask explicitly.

### 2. Claude kept modifying classes despite "we work with the 23 class schema everywhere"

`long-engine-session-A:64`, violation around turn 82 (analysis-pipeline cluster, 2026-05..09, 130k words).

Rule:

> "make sure that we work with the 23 class schema everywhere and that we have no confusion between classes" *(turn 64)*

~18 turns later Claude is editing `build_labels.py` with SKS overlays and fallback mappings without stating how each change preserves the 23-class schema. **Cause:** Claude treated the rule as high-level intent rather than a per-edit invariant. **Lesson:** if the user states a global invariant, every subsequent code change should cite it. Make the invariant an explicit pre-commit checklist item in the turn.

### 3. "Not in Chrome, just the file" — Claude used Chrome anyway

`long-engine-session-A:250` documents that the user had to redirect Claude from Chrome DevTools to the preview tool (port 8093). The drift ran for multiple turns before correction. **Cause:** Claude defaults to the tool it used most recently, even when the user has explicitly preferred another workflow earlier in the session. **Lesson:** track tool-of-preference as session state, not turn state.

### 4. The ICEYE/DARPA exclusion

`can-you-read-excellencekluster:946` (space-cluster cluster, 2026-03-01..06, 152k words).

Instruction:

> "OK lets use the results from v5 and write a fully new repport. Exclude the part on Darpa, if Iceye was not funded it's of no importance. Do not write [it] to prove Space West right or wrong, just write taking the findings and the relevant comments that were built into v5 into account and use them to argue for a Space Excellence Cluster in an objective way." *(turn 956)*

Detection in text around turn 968 shows Claude re-introduced peer-review framing that implicitly defended the previous hypothesis. **Cause:** the "objective" framing is harder to follow when prior framing is preserved verbatim in context. **Lesson:** when the user says *"start fresh, drop X"*, that is an instruction to summarize — not to keep the old draft in view while writing a new one.

### 5. "sharper → similar or better results" redirection

`session-context:530` — user redirected Claude from "sharper boundaries" to "similar or better results" across a broader metric suite (mIoU, per-class accuracy, spectral sensitivity). **Cause:** Claude had narrowed the optimization target based on the word *sharper* in an earlier turn. **Lesson:** *sharper* is ambiguous (visual? quantitative?). Confirm the metric before optimizing.

### 6. "STOP" had to be shouted three times in one session

`can-you-make-sure-everything-is-committed` records **three explicit STOPs**:

- turn 374: `STOP` (after Claude kept proposing class-remapping changes while user only said "I don't believe in the oljeväxter")
- turn 422: `STOP` (after Claude was proposing CDSE fallback fixes while the user's turn was a *status report*)
- turn 424: `starta om fetchen och hämta höstram för alla 2018 tiles`

**Cause:** the user's "I think X is confused" or "the bug is Y" reads to Claude as *"fix it"*. But in this session those were **diagnoses shared while the user was still deciding**. **Lesson:** a stated diagnosis is not a directive. Wait for an imperative verb.

---

## What the numbers say

| Signal | Value |
|--------|-------|
| Sessions with at least one correction marker (`no`, `stop`, `nej`, `sluta`, …) | 19 of 31 |
| Total correction markers across the corpus | ~115 |
| Highest in one session | `long-engine-session-A` — 22 corrections over 130k words |
| Candidate rule-violation pairs (automatic detection) | 26 |

See `analysis/instruction_events.csv` for the full machine-detected list. Manual triage of the top 10 shows 6 genuine cases (above) and 4 false positives where the "rule" regex matched inside Claude's own prose.

---

## Patterns behind the drift

Grouping the real drift cases, three causes dominate:

1. **Question mistaken for directive** (cases 1, 3, 6). You ask *"should we X?"* or *"what about X?"* and Claude starts doing X. This happens more in Swedish than English because Swedish imperative and interrogative forms are closer (*"kanske vi ska …?"*).

2. **Tool/defaults inertia** (case 3). Claude keeps using the tool it used last turn even when you've stated a preference. System prompt's "use dedicated tools" rule doesn't override user-stated preferences automatically.

3. **Rule interpreted as high-level intent, not per-edit invariant** (cases 2, 4, 5). A rule stated once ("work with 23 classes", "exclude DARPA", "not sharper — similar or better") should become a precondition Claude cites before each edit in that session. It doesn't.

---

## What works — confirmed reversals

When drift was corrected in-session, what fixed it:

- **Short explicit stop words** (`STOP`, `sluta`, `nej`, `fel`). Near-100% effective on the next turn.
- **Repeating the rule verbatim** (e.g. case 6, turn 424: "starta om fetchen och hämta höstram för alla 2018 tiles" — same imperative form, no diagnosis mixed in). Usually resolves in one turn.
- **Naming the violated rule** ("I said always ask first") is more effective than generic frustration.

What doesn't reliably work:

- Sarcasm or exasperation without a restated rule.
- Emoji or formatting-only signals.

---

## Recommendations (for future sessions)

For you:
- If your turn is a diagnosis or an exploration question, prefix it with `Q:` or `Idea:`. If it's a directive, start with an imperative verb.
- When stating a session-wide rule, ask Claude to echo it back so you can verify it was registered.
- Use a concrete stop word (`STOP`, `sluta`) — it works faster than rephrased frustration.

For Claude (captured as memory):
- Treat any session-stated rule as a precondition to cite before edits, not a one-shot instruction.
- When a user turn contains both a diagnosis and a question mark, do not act — ask.
- Persist "tool/framework preferences stated this session" across turns.
