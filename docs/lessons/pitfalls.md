# Pitfalls — the anti-patterns we kept repeating

Recurring failure modes observed across the 31 sessions. Each has concrete evidence. These are ordered by cost (how much tool-flailing or rework they caused).

## 1. Diagnosis read as directive

See `instruction_adherence.md` cases 1 and 6 for the detailed cases. Short version: when you write *"the bug is X"* or *"I think Y is confused"*, Claude starts fixing it. Sometimes you want it fixed; sometimes you were thinking out loud.

**Cost:** multiple STOPs in `session-context` and `can-you-make-sure-everything-is-committed`, and several wasted edits to fetch code.

**Fix:** prefix diagnoses with `Q:` or `Observation:`. Use bare imperatives only when you mean them.

## 2. Long sessions without re-anchoring

`long-engine-session-A` is 130,510 words and drifts through at least four distinct sub-topics: label schema, dashboard updates, tmp-file rename atomicity, API overload. By turn ~400 the session has lost its initial anchor. **Cause:** no mid-session recap.

**Cost:** 22 corrections in that one session, many of them undoing work that addressed the wrong sub-topic.

**Fix:** every ~50 turns in long sessions, restate the current top-level goal. If Claude is tracking todos, ask it to echo the active todo.

## 3. Dashboards not updating — and Claude "fixing" the wrong layer

From `long-engine-session-A:534`:

> User: "I do not get the updates in the dashboard"

Claude's response investigated the sync loop, file mtime, HTTP 200 — all correct diagnostics. But when no bug was found in those layers, Claude started modifying the dashboard refresh interval, then the server side, then the pod restart logic. The actual fix was upstream (loss function weighting — unrelated to dashboard display).

**Cost:** ~20 turns on symptom-fixing before returning to root cause.

**Fix:** when a failure is "X doesn't show up", check end-to-end first. If the data pipeline produced no data, no display fix will help.

## 4. Chrome DevTools vs. Preview tool drift

`long-engine-session-A:250`:

> User correction "not in chrome, just the file"

After the user explicitly stated a preferred tool at session start, Claude reverted to Chrome DevTools within ~10 turns. Every such reversion required a re-correction.

**Cost:** at least 3 tool-switching corrections in that session.

**Fix:** ask Claude to confirm tool preferences at session start and restate them after any tool-call cluster.

## 5. Editing code while the user is asking status

`session-context:298`:

> User: "fuck! gör aldrig om något som tar min tid i onödan, notera det. fråga alltid innan du gör idioti"

This came after Claude had silently modified fetch code that was running in production on the cluster. The session contains similar patterns elsewhere ("sluta ändra i fetchkoden för att jag ställer frågor!!!").

**Cost:** real production risk — the fetch was running against a Kubernetes cluster and code edits were not rolled back before restart.

**Fix:** a strict rule that *running* code is read-only unless the user issues an explicit verb like `fix`, `change`, `edit`, `replace`.

## 6. Over-eager scope expansion

`can-you-make-sure-everything-is-committed:362`–`368`:

> User: "I do not beleive in the oljeväxter, I think that is a NMD class thats been cnfused"

User wanted an investigation. Claude started proposing class-remapping patches. The user followed with "STOP".

**Cost:** one STOP + ~15 turns of backtracking.

**Fix:** separate *exploration* from *mutation*. Claude's default should be: investigate → report → wait for go-ahead → mutate. The leap from "I think X is wrong" directly to "here's the fix" skips the go-ahead step.

## 7. Keeping old drafts in context when writing a "fresh" version

`can-you-read-excellencekluster:956`:

> User: "OK lets use the results from v5 and write a fully new repport. Exclude the part on Darpa […] Do not write it to prove Space West right or wrong, just write taking the findings and the relevant comments that were built into v5 into account and use them to argue for a Space Excellence Cluster in an objective way."

When the user says "write a new report", Claude typically re-uses the old draft as scaffolding. That makes excluded sections creep back in and shifts the voice toward the original framing.

**Cost:** in that session, at least two revisions before the DARPA thread was removed cleanly.

**Fix:** for "write a new X", start from structured findings (bullets, tables), not the old prose. Treat the previous draft as one source among many, not the default template.

## 8. "Claude" appearing in user turns (parser-level, not behavioral)

The CLI-format parser in this repo over-splits turns. Don't trust turn_idx role labels for CLI sessions when doing qualitative work — read the text. This isn't Claude's pitfall, but it's the pitfall you'll hit when reading this repo's metrics.

**Fix:** for CLI sessions, use raw text + action counts, not role-stratified stats.

## 9. Silence on architectural tradeoffs

When given a choice ("do we use ensemble voting or a single model?"), Claude sometimes presents one option as foregone. `session-context:554` shows a case where the user proposed ensemble voting and Claude endorsed it without discussing whether a single stronger model might be cheaper to maintain. The session later pivoted again.

**Cost:** pivots inside the same session. Each pivot re-anchors the implementation.

**Fix:** for any architectural choice, require at least one sentence on the *counter-option* and the breakpoint at which that option wins.

## 10. "I'll just commit everything" as a shortcut

`can-you-make-sure-everything-is-committed` is titled after this pattern. It works as a checkpoint, but it also bundles unrelated changes into single commits — which later makes the instruction-adherence analysis harder (you can't tell which change addressed which instruction).

**Cost:** analytical, not operational — but worth noting.

**Fix:** commit by instruction satisfied, not by "everything since the last commit".

---

## Meta-pattern

The through-line in pitfalls 1, 5, 6, 7: **Claude collapses the distance between a user's observation and the user's intent**. A good internal rule would be: "If I can't quote a verb from the user's last turn, I'm about to hallucinate one."

---

## External corroboration + new pitfalls from the literature sweep (2026-04)

Cross-referenced against Anthropic docs, practitioner blogs, and academic research. Full synthesis in [`external_patterns.md`](external_patterns.md).

### Confirming what we found

- **Long-session drift (§2)** is the *single most active research area* in 2025 LLM-agent work. AgentFold (arxiv:2510.24699) and Context-Folding (arxiv:2510.11967) both show that **active context management** beats passive accumulation, with Context-Folding matching ReAct performance using a **10× smaller active context**. One survey claimed "65% of enterprise AI failures attributed to context drift during multi-step reasoning rather than raw context exhaustion."
- **Running-code edits (§5)** is recognized as a safety failure in enterprise deployments. Anthropic's managed-settings system allows organizations to block tools entirely on specific paths — precisely to prevent this.
- **Over-eager scope expansion (§6)** maps to the academic finding that coding agents perform dramatically worse on **SWE-Bench Pro** (long-horizon, multi-file tasks) than on **SWE-bench Verified** (focused single-fix tasks): **below 45% vs. 79.2%**. Agents are good at scoped problems; they get worse as scope grows. Our empirical observation matches.

### Amended pitfall — §10 updated

Our §10 noted that "commit everything" sessions bundle unrelated changes, an analytical cost. Addy Osmani's 2026 workflow reframes this more strongly:

> "I commit after each small task succeeds — commits as save points in a game."

**Revised guidance:** prefer per-task commits. The `can-you-make-sure-everything-is-committed` megasession was productive but left an illegible git history. Replace with: small commits during the session, a tidy-up PR at the end if needed.

### New pitfalls to add to the list

#### 11. Over-investing in planning for trivial work

Anthropic explicitly pushes back on always-plan-first:

> "For tasks where the scope is clear and the fix is small (like fixing a typo, adding a log line, or renaming a variable) ask Claude to do it directly. If you could describe the diff in one sentence, skip the plan."

**Our risk:** we've internalized "always brief heavily before starting." This wastes turns on work that doesn't need it.

**Fix:** apply the front-loaded briefing pattern only to tasks touching >2 files OR requiring >3 tool calls. For one-sentence-diff work, a one-sentence prompt is correct.

#### 12. Bloated CLAUDE.md causes rule abandonment

Anthropic Best Practices:

> "Bloated CLAUDE.md files cause Claude to ignore your actual instructions! For each line, ask: Would removing this cause Claude to make mistakes? If not, cut it."

**Our risk:** our global `~/.claude/CLAUDE.md` (installed as part of the continuity rollout) has 5 rules + explanations. Under 200 lines, so fine for now. But each new rule we add from research has a cost.

**Fix:** encode each new rule only after it's traced to a real failure (the "ratchet principle"). When adding, also prune: what rule has this displaced or made redundant? Use path-scoped rules (`.claude/rules/<topic>.md`) for anything that isn't needed in every session.

#### 13. Advisory rules vs. deterministic hooks — misplaced trust

Practitioner consensus:

> "Skills extend what Claude can do while hooks constrain how Claude does it. Unlike CLAUDE.md instructions which are advisory, hooks are deterministic and guarantee the action happens."

**Our risk:** we documented our retrospective rules as CLAUDE.md text. Text rules are ignored under long-session drift (see §2). For rules where violation is high-cost — e.g. "running code is read-only" — a CLAUDE.md rule is insufficient.

**Fix:** in the next continuity-layer iteration, convert the highest-cost rules to `PreToolUse` hooks. Start with: block `Edit` / `Write` on paths marked as "active job config" via a sentinel file. Keep CLAUDE.md for advisory guidance only.
