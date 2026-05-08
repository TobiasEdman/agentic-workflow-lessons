# Prompting Evolution — how your style changed

Quantitative trends from `analysis/prompting_evolution.csv`, read together with turn-level samples from 31 sessions (Feb–Sep 2026).

## Summary

Three shifts, in order of impact:

1. **Format shift (Feb → Mar 2026).** You moved from `claude.ai` web (conversational, Swedish-heavy, 20–80 word prompts) to Claude Code CLI (imperative, often English, 15–25 word prompts). Tool use exploded — from 0–2 per session to hundreds.
2. **Language shift.** Web sessions are mostly Swedish (5 of 13 pure `sv`, 1 pure `en`). CLI sessions tilt English or mixed (11 `en`, 5 `mixed`, 2 `sv` of 18). Technical terminology pulls you toward English when the tools are English.
3. **Correction density rose with session length.** Short sessions (<5k words): 0–1 corrections. Medium (5–30k): 2–5. Large (>50k): 12–22. Not because you're more frustrated — because there is more surface area for drift.

---

## Month-by-month

### February 2026 — claude.ai web, discovery mode

Sessions: `utokad-finansiell-analys`, `space_cluster`, `excellenscluster-space[ii…v]`, `biofinans`, `excellenscluster-space`, `ap_1`, `imint-engine`, `ekosystemkartlaggning-rymd`.

- Style: conversational, Swedish-first, longer prompts.
- Mean user turn: **30–40 words** (peak 81 in `excellenscluster-space_iv`).
- Tool use: **0–2 per session**. These were research/analysis chats.
- Correction rate: near-zero. Sessions were scoping exercises, not build-outs.
- Typical opener: *"fortsätt med satcube"*, *"jag vill ansluta til lgithub och analysera ett repo"*.

Pattern: you were mapping the problem space. Claude was generating options; you were choosing.

### March 2026 — the pivot to Claude Code

Sessions: `can-we-restart-with-this-info`, `can-you-read-excellencekluster`, `here`, `du-kan-fortstta-har-ok`, `lets-work-with-the-space-cluster-application`, `go-tothe`, `hi`.

- Style: **imperative**. "go to the LEO repo in developer" (`hi`, turn 0). "fortsätt" / "continue where we stopped" became the standard opener.
- Mean user turn dropped to **16–22 words**. But `max_user_turn_words` jumped — 151 in `here`, 163 in `can-we-restart-with-this-info`. You started writing *long briefing preambles* at session start, then issuing short imperatives.
- This is the first cluster with heavy tool use: `du-kan-fortstta-har-ok` hit **657 tool calls in a single session**.
- Correction rate appeared: 3–14 per session.
- Key pattern: **session-starter megaprompts**. `Here.txt` begins with a 790-word briefing (a viewer cross-raster alignment investigation) that lists files, env path, what you tried, and why each suspect is suspect. That kind of prompt is what led to the most productive sessions.

### May–September 2026 — the long-running engine sessions

Sessions: `long-engine-session-A` (130k words), `can-you-find-the-fetch` (52k), `session-context` (69k), `can-you-make-sure-everything-is-committed` (28k).

- These are the highest-cost, highest-drift sessions. Each represents days of work compressed into one transcript.
- You switched from framing ("here's the situation, plan it") to **in-flight ops**: "status?", "restart the fetch", "why didn't it update the dashboard?".
- Correction rate per session is 12–22 — but *correction rate per thousand user turns* is similar to shorter sessions. This is session-length drift, not you being harder to work with.

---

## Concrete before/after pairs

### Opener style

**Before (Feb, claude.ai web):**
> "I want to biúild an imint engine based on the AI pipe line, can you help me with that?"
> — `imint-engine`, turn 0

Claude's response (turn 1): 415 words asking 4 clarifying questions before proposing a structure.

**After (Mar, Claude Code):**
> "HI, can you go to the LEO repo in developer?"
> — `hi`, turn 0

Claude's response: immediate `Ran` tool call → cd → listing. No clarifying question.

**Takeaway:** Web gave you back a discussion. CLI gave you back an action. The tradeoff is that CLI rarely pauses to say *"I should check first if X"*.

### Continuation prompts

Your most effective opener across the corpus is the **briefing-then-imperative pattern**:

> "I need help debugging a **pixel-level alignment problem** between three georeferenced rasters […] I need a **rigorous ground-up plan** before any code is written."
> — `here`, turn 0 (790 words)

That session produced the cleanest structured planning of any in the corpus. Contrast with:

> "can we look atthe imint engine repo"
> — `can-we-look-atthe-imint-engine-repo`, turn 0 (6 words)

which drifted into tool-flailing before cohering 20+ turns later.

**Takeaway:** when the task is larger than a single tool call, **invest in the first turn**. A 500-word briefing at turn 0 costs less than 10 mis-steered turns later.

### Correction style

**Early (Feb):** *(no corrections found in any Feb session)*

**Mid (Mar–Apr):** polite redirects.
> "not in chrome, just the file"
> — reconstructed from `long-engine-session-A:250`

**Late (May–Sep):** imperative stop-words.
> "STOP"
> "sluta ändra i fetchkoden för att jag ställer frågor!!! fortsätt hämta bara"

**Takeaway:** by September, your corrections had become sharper and faster — because you'd learned that the sharp, verbatim-rule form is the one that works (see `instruction_adherence.md`).

---

## Metrics at a glance

From `analysis/per_session.csv` (sorted by date):

| Period | Median prompt length | Tool calls / session | Corrections / session |
|--------|----------------------|----------------------|-----------------------|
| Feb (web)  | 27 w | 0 | 0 |
| Mar (CLI)  | 20 w | 77 | 3 |
| May–Sep (CLI, long) | 22 w | 500+ | 12–22 |

The prompt-length median is **stable**; what changed is what surrounds each prompt (a growing volume of tool calls and session-spanning context).

---

## What to carry forward

Things that clearly worked for you:
- **The briefing-then-imperative opener** at session start.
- **Verbatim rules** stated once, reinforced with `STOP` when violated.
- **Moving to Claude Code** when the work became build-oriented rather than discussion-oriented.

Things to consider adjusting:
- Tag diagnosis vs. directive. Both forms "the bug is X" and "fix X" exist in your corpus, and Claude reads the first as the second too often.
- In very long sessions, restate the session's top-level goal every ~50 turns. The `long-engine-session-A` session drifted specifically because there was no mid-session re-anchor.
