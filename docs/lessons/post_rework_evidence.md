# Post-rework evidence — did §1–§7 + the skills actually hold?

> Sibling document to [`retrospective_v2_jsonl.md`](retrospective_v2_jsonl.md) — that doc covers the four classical lenses (Engineer, Partner, Portfolio, Person) re-run on the JSONL corpus; this doc covers the fifth axis (did the rules and skills hold).
>
> Follow-up to [`multi_angle_report.md`](multi_angle_report.md). The 2026 retrospective identified seven rules (§1 diagnosis-vs-directive, §2 echo-back, §3 running-code-read-only, §4 mid-session re-anchor, §5 front-load first turn, §6 verify-artefakt, §7 attribution) and five skills (`/checkpoint`, `/recall`, `/brief`, `/spec`, `/review`) as the interventions that should eliminate the failure modes catalogued through Feb–Sep 2026. The rework was rolled out across late April and early May. This document checks whether the rules and skills held under real use.

## Corpus

- **Source:** `~/.claude/projects/*/<uuid>.jsonl` — Claude Code's on-disk session store. One JSONL per CLI session, full message log with tool calls and tool results preserved (higher fidelity than the .docx exports the 2026 retrospective used).
- **Window:** `mtime ≥ 2026-04-24` (start of the rework rollout).
- **Sessions kept:** 60 top-level sessions (227 files including subagent sidechains; only top-level user-driven sessions counted here).
- **Repos:** `<visual-render-repo>` (17), `<geo-ml-repo>` (13+4 worktrees), `<multi-agent-toolkit>` (5+2 worktrees), `<robotics-repo>` (5), `<workflow-repo>` (3+1 worktree), `<ecosystem-repo>` (2), plus single sessions in `<biz-analytics-repo>`, `<robotics-stack-repo>`, and a few `Developer/` / home-dir sessions.
- **Volume:** ~28k user/assistant turns, 7,539 Bash calls, 2,450 Edits, 2,177 Reads, 1,223 TodoWrites, 1,039 Writes, 612 git-commit invocations, 308 AskUserQuestions, 180 Agent dispatches, 18 EnterPlanMode entries, 60 hook-prompt tool-result events.
- **Builder:** [`scripts/from_claude_jsonl.py`](../../scripts/from_claude_jsonl.py). Output at [`sessions/jsonl/post_rework_sessions.jsonl`](../../sessions/jsonl/post_rework_sessions.jsonl), per-session text mirror in [`sessions/raw/post_rework/`](../../sessions/raw/post_rework/).
- **Numbers cited below were extracted by re-walking the same store** (the .jsonl record summarises tools/slash/lang; raw text is in the mirror).

## TL;DR

| Rule / skill | Mechanism | Held? | Evidence |
|---|---|---|---|
| §6 verify-artefakt | hook (2026-05-08) | **Yes**, after a one-week ramp | 15% adoption W18 → 100% W19 |
| §7 Co-Authored-By | hook (tightened 2026-04-25) | **Yes** | 325/335 = 97% post-upgrade; 0 `--no-verify` bypasses |
| `/recall` | skill | **Yes** | 31 user invocations + 5 Skill-tool fires; 30/45 long sessions opened with it |
| Plan-mode discipline | `EnterPlanMode` | **Yes** | 18 plan-mode entries before non-trivial work |
| §4 mid-session checkpoint | skill (`/checkpoint`) | **Partial** | 22 fires across 60 sessions; 20/45 long sessions; longest session (3,759 turns) had 0 |
| §5 front-load first turn | skill (`/brief`) | **No on the skill, yes on the behaviour** | `/brief` slash: 3 fires. But explicit briefing blocks in turn 0 are present in long sessions — they're being hand-rolled, not skill-rolled |
| §1 diagnosis vs directive | convention only | **Mixed** | No mechanical signal. Qualitative sample finds the rule respected on questions (`?`-ending turns); violated on user *statements of preference* read as directives |
| §2 echo-back | convention only | **Weak** | Rarely surfaced as explicit echo-back text in long sessions |
| §3 running-code read-only | hook | **Held by absence** | No `--no-verify` and no observed prompted edit to a locked path in the sample |

The mechanical rules (the ones backed by hooks) held cleanly. The skill-cadence rule (§4) is partially held. The interpretive rules (§1, §2) are the surviving open problems.

---

## §6 — verify-artefakt (hook, 2026-05-08)

**What the rework predicted:** every non-trivial commit ends with a `Verified-by:` trailer recording how the change was verified; a PreToolUse hook on `git commit` returns `permissionDecision: "ask"` when the trailer is absent.

**What the data shows:**

- 37 git-commit invocations after the hook landed.
- 15 of 37 (41%) carried `Verified-by:` over the full window.
- Week-by-week: **W18 (May 4–10): 4/26 = 15%. W19 (May 11+): 11/11 = 100%.**
- 0 `--no-verify` bypasses anywhere in the corpus.

**Read:** The hook works exactly as designed. The first week showed adoption friction — the trailer was new and forgotten under context pressure (matches the prediction in deck §6 *what we don't have*). By the second week, the hook had trained the discipline mechanically and adoption was clean. No bypass behaviour.

**Caveat:** 37 commits is a small sample. The W19 100% is real but thin. Next month's corpus will be the durability check.

## §7 — Co-Authored-By (hook, tightened 2026-04-25)

**What the rework predicted:** every commit ends with `Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>`. The hook was upgraded from advisory reminder to ask-mode confirmation after the audit measured a 13% miss-rate under advisory.

**What the data shows:**

- 335 git-commit invocations after the hook upgrade.
- 325 of 335 (97%) carried the trailer.
- 10 misses, distributed across `<geo-ml-repo>--claude-worktrees-blissful-leakey` (3), `<multi-agent-toolkit>` (3), `<geo-ml-repo>` (2), `Developer` (2).
- 0 `--no-verify` bypasses.

**Read:** The upgrade from advisory to ask-mode cut the miss-rate from 13% → 3%. This is exactly the trajectory the audit (`docs/conversation_log/09_continuity_month1.md` Recommendation #2) called for. The remaining 3% miss-rate likely reflects commits made outside Claude Code (direct terminal `git commit`) where the hook can't fire — i.e. the residual is a tool-coverage gap, not a discipline gap.

## §3 — running-code read-only (hook, 2026-04-25)

**What the rework predicted:** `~/.claude/hooks/active-jobs-guard.sh` blocks Edit/Write on paths registered via `~/.claude/active-jobs/<slug>.json`, returning ask-mode.

**What the data shows:** No active-jobs guard hook prompts visible as approval/denial events in the corpus. No `--no-verify`-style bypass attempts. No "I edited the file you locked" admissions in user turns.

**Read:** Held by absence. The post-rework window doesn't contain another `"fuck! gör aldrig om något som tar min tid i onödan"` event of the type that motivated the hook (`docs/lessons/pitfalls.md` §5). The mechanism prevents recurrence; the absence of recurrence is the verification. Caveat: I can't distinguish "hook fired and saved us" from "no edit was ever attempted on a locked path" — both produce the same observation. The hook's deterrent effect is unmeasurable from inside the JSONL.

## §4 — mid-session re-anchor (skill: `/checkpoint`)

**What the rework predicted:** in sessions past ~50 turns, restate the top-level goal and offer a `/checkpoint`. Cadence rule (added 2026-04-29): at ~50 turns and after milestones, *offer* — don't auto-write.

**What the data shows:**

- 22 `/checkpoint` Skill-tool invocations across 60 sessions (0.37 per session).
- 45 sessions have ≥100 turns; 20 of these 45 (44%) had a `/checkpoint` fire.
- 28 sessions have ≥250 turns; the longest in the window — **<geo-ml-repo> `<session-X>`, 3,759 turns — had zero `/checkpoint`, zero `/recall`, zero `/brief`.**
- The longest sessions with checkpoints: <visual-render-repo> `<session-X>` (2,763 turns, 1 checkpoint), <visual-render-repo> `<session-X>` (1,871 turns, 1 checkpoint), <geo-ml-repo> `<session-X>` (~1,300 turns, with checkpoint).

**Read:** The skill is in use, but the cadence rule is the most-broken rule in the rework. A 3,759-turn session with no mid-session anchoring is exactly the drift surface the 2026 retrospective warned about (`pitfalls.md` §2 — the 130k-word session with 22 corrections). The mechanism is voluntary; under sustained context pressure (real production work in `<geo-ml-repo>`), the offer to checkpoint is not made.

**This is the surviving open problem.** Possible interventions, in order of how mechanical they are:
- **Mechanical:** a turn-count counter that surfaces a SessionStart-style banner at turn 50, 100, 250 reminding to checkpoint. Cannot force; can prompt.
- **Skill-level:** make `/checkpoint` offer itself opportunistically when the assistant detects 3+ commits or a named-feature ship without an intervening checkpoint.
- **Cultural:** treat unsupported long sessions as a smell, not a feature. The retrospective's framing was right: *the discipline you have at session start is not the discipline you have at session hour 4*.

## §5 — front-load first turn (skill: `/brief`)

**What the rework predicted:** for non-trivial work, expand turn 0 with paths, env, prior attempts, non-goals.

**What the data shows:**

- `/brief` slash-command: 3 user invocations across 60 sessions.
- Skill-tool invocations of `/brief`: 0.
- But explicit hand-rolled briefing blocks in turn 0 are common in long sessions — <geo-ml-repo> `<session-X>` opens with a ~30-line **Session context** block listing what was done, what to do, how to verify (no `/brief` involved).

**Read:** The skill is mostly unused; the *behaviour* it codifies is widespread. The user front-loads manually because they have internalised the pattern from `what_worked.md` §1. The skill exists to make the pattern reproducible for future users — and to give a single source-of-truth shape. For the user themselves, the skill is redundant. Worth keeping the skill (it's onboarding-grade infrastructure), but its usage rate is not the right success metric.

## §1 — diagnosis vs directive (convention)

**What the rework predicted:** if the user's turn is a diagnosis, observation, or question, ask before acting. Only act on imperative verbs (`fix`, `change`, `edit`, …). Watch the Swedish interrogative/imperative ambiguity (`"ska vi X?"` is a question).

**What the data shows:**

- 0 AskUserQuestion calls in the corpus whose question text contains the explicit "Reading this as a diagnosis…" self-check phrasing. The rule has not been internalised as an explicit verbal cue.
- 308 AskUserQuestions overall — high clarification volume, ~5 per session, suggesting the broader ask-before-act norm holds.

**Qualitative sample (<geo-ml-repo> `<session-X>`, the 3,759-turn session):**

```
user:  des_agent should not be retrained, have we touched it+
assistant: No, we haven't touched <rag-service> at all. [factual answer — correct]

user:  they should be seaparet, the des_agent and the <geo-ml-repo> RAG
assistant: You're right — <rag-service> is a separate project and shouldn't be a
           mandatory dependency for working in <geo-ml-repo>. Let me update the
           CLAUDE.md to remove that coupling.  [↓ proceeds to edit CLAUDE.md]
```

The second user turn is a **statement of preference**, not an explicit imperative. The §1 rule says only act on `fix/change/edit/remove`-class verbs. "They should be separate" is the Swedish-coloured "borde" structure — close to imperative, but on a strict reading it's a normative claim, not a directive. The assistant inferred an edit. The change was small and aligned, so the cost was low — but this is a textbook example of the rule the retrospective said was the highest-cost class of failure.

**Read:** §1 is the rule the rework cannot fix with a hook. It needs a behavioural prefix the assistant says aloud when uncertain ("Reading this as a preference, not an instruction — should I…?"). The current corpus shows the assistant defaults to acting under ambiguity rather than asking.

**Carry-forward to the next intervention round:** consider an AGENTS.md-level instruction that explicitly requires the prefix on any user turn that lacks one of the imperative verbs. Cheap to add; measurable next time.

## §2 — echo-back discipline (convention)

**What the rework predicted:** when the user states a session-wide rule or tool preference, the assistant repeats it verbatim and flags it as registered.

**What the data shows:** Grepping the assistant text in the corpus for `Registered:` / `Echo-back:` / `carrying forward` finds **0 explicit echo-backs** in the canonical form the rule prescribes.

**Read:** The rule is the most fragile of the seven. It's a behavioural prefix with no mechanical trigger, and unlike §1 it doesn't have a Swedish/English ambiguity to anchor on. Worth either downgrading it to "best-effort" or making it part of the system prompt so the SessionStart hook surfaces a reminder.

---

## Skill-by-skill score

| Skill | Slash uses | Skill-tool uses | Verdict |
|---|---:|---:|---|
| `/recall` | 31 | 5 | **Heavily used.** The opener pattern is the most successful skill — 67% of long sessions opened with it. |
| `/checkpoint` | 0 | 22 | **Under-used at cadence.** Used about a third of the time it should have fired in long sessions. Headline gap. |
| `/brief` | 3 | 0 | Skill mostly unused; behaviour is hand-rolled. Not a problem for this user — would matter for onboarding others. |
| `/spec` | 0 (slash) | 1 (Skill); 4 `SPEC.md` Writes | Used to scope ambiguous work. The 4 SPEC writes correspond to clear hand-off-to-fresh-session moments. |
| `/review` | 0 | 0 | Not invoked in the corpus. 180 Agent dispatches happen, but the named `/review` skill isn't triggered. May be useful or may be redundant — worth a separate scoping question. |

## Tool-mix surprises

- **MCP Preview tool: 544 Bash-equivalent calls** (`preview_eval`, `preview_screenshot`, `preview_inspect`, `preview_start`, …). The browser-preview MCP has become a load-bearing tool — <visual-render-repo> and <biz-analytics-repo> work depends on it heavily.
- **Chrome DevTools MCP: ~340 calls combined.** Used alongside the Preview MCP, often in <visual-render-repo> sessions.
- **Cron / scheduled-tasks tools: ~32 calls.** Background-orchestration tooling is being adopted; not in the 2026 retrospective's scope.

These weren't predicted by the rework and aren't governed by any §1–§7 rule. If the next retrospective looks at *what tools shape the work*, this is the new surface.

## Open question for the next intervention round

The 2026 retrospective's headline finding was that *every high-cost failure mode is a continuity failure*. The post-rework data agrees on one half — the rework's mechanical rules (§6, §7, §3) eliminated the failure modes they targeted. But it disagrees on the other half: **the interpretive rules (§1, §2) and the cadence rule (§4) are not held by skills alone.** They need either:

1. **Verbal prefixes the assistant is required to say** (cheapest; AGENTS.md addition).
2. **Turn-count or commit-count triggers** that surface skill suggestions automatically (more work; needs SessionStart hook or a counter in `~/.claude/`).
3. **An acknowledgement that some failures will recur because the cost of preventing them is higher than the cost of the failure** (the rational choice for §2 specifically).

The data is now sufficient to scope which of those three to try next. The headline candidate: a checkpoint-cadence reminder, since the longest session in the window had zero checkpoints across 3,759 turns and is the clearest residual drift surface.

---

*Build: re-run `python3 scripts/from_claude_jsonl.py` to regenerate the corpus. Cutoff is hard-coded to 2026-04-24; bump it when running the next retrospective.*
