# Retrospective v2 — Four Lenses on the Post-Rework Window

> Successor to [`multi_angle_report.md`](multi_angle_report.md). Same methodology — four independent Explore agents, no agent sees the others' output, convergences carry the most weight — but with two source upgrades:
>
> 1. **Higher-fidelity corpus.** 60 post-rework sessions extracted directly from Claude Code's on-disk JSONL store (`~/.claude/projects/<encoded-cwd>/<uuid>.jsonl`). Tool calls, slash commands, timestamps, repos, and language preserved. Replaces the heuristic-split `.docx` exports the v1 report used.
> 2. **A predecessor to compare against.** The v1 report's findings (briefing opener, <geo-ml-repo>-as-spine, drift in long sessions, persistent-memory unlock, structural bilingualism) are now hypotheses to test. Each lens was instructed to extend or contradict, not to re-summarise.
>
> A fifth axis — *did the §1–§7 rules and the new skills actually hold?* — has its own document at [`post_rework_evidence.md`](post_rework_evidence.md). This report covers the other four: Engineer, Partner, Portfolio, Person.
>
> Methodology: each agent received the corpus index (`/tmp/corpus_index.md`), the JSONL records, the per-session text mirrors at [`sessions/raw/post_rework/`](../../sessions/raw/post_rework/), and the specific parts of v1 their lens succeeds. They were told not to read each other's output and not to read `post_rework_evidence.md` (continuity lens would bias them). Full lens returns are in the agent dispatch turn.

---

## The four lenses, briefly

| Lens | Successor finding-vector | Core question |
|------|--------------------------|---------------|
| **Engineer v2** | What does the code, commits, and tool-use pattern say about engineering practice in the rework window? |
| **Partner v2** | How does the user collaborate with Claude *now*? What changed since v1? |
| **Portfolio v2** | What is the portfolio doing, and where has the strategic centre of gravity moved? |
| **Person v2** | Who is the human now? Voice, growth, tolerance, satisfaction signals. |

---

## 1. Convergences — what all four lenses agreed on

### 1.1 The front-loaded turn-0 is no longer a habit; it is the *protocol*

In v1, the briefing-prompt opener was named as *"the load-bearing move of the year."* In v2, every lens treats it as the operational default — and the data shows it's now mechanical, not effortful.

- **Engineer**: `Edit:Read` ratio holds at 1.5:1 across all session lengths — "no chaos editing," changes are always read-before-written.
- **Partner**: <geo-ml-repo> `<session-X>` (3,759 turns) opens with a **790-word context dump** — schema-v5 state, "Check if it completed: `kubectl logs…`", explicit pointer to a missing checkpoint. The opener is now diagnostic, not just informational.
- **Person**: Quoted user turns include short minimal-context directives like *"Follow proposed commit order and start the S1 fetch"* — six words that only parse because the front-loading happened in turn 0.
- **Portfolio**: implicitly relied on by the velocity claims — 126 <geo-ml-repo> commits in 13 days, 100 <visual-render-repo> commits in 2.5 weeks, no per-task re-explanation cycles.

**Convergent implication:** the discipline from v1 §1.1 didn't just hold — it tightened. The user is now able to compress directives because context is fully resolved in turn 0.

### 1.2 The Swedish/English split sharpened — language is now the diagnosis/build switch

v1 §1.5 read bilingualism as a *tell*: shift to Swedish = something wrong. v2 finds the same pattern operating in a more consistent, more functional form.

- **Partner**: *"Swedish utterances are diagnostic and English are directive."* When the user shifts to Swedish (*"sluta ändra i fetchkoden"*, *"kanske vi ska X?"*, *"vilken av 1–4?"*) it signals hold-before-acting. When English dominates, it's imperative with clear execution scope.
- **Person**: `<session-X>` shows a session-internal switch — Swedish for diagnosing a clipped Claude message (*"ditt meddelande 'For the big' klipptes av, vad menade du?"*) → English once the problem is understood (*"kör igång"*). The bilingual boundary is *the boundary between diagnosis and build*.
- **Engineer** + **Portfolio** did not address language directly, but neither contradicted.

**Convergent implication:** v1's framing was right but understated the predictability. The switch is now reliable enough to use as a signal for Claude — when the user shifts to Swedish mid-session, the right default response is *answer in Swedish, don't act in code.*

### 1.3 The skills exist, but use is wildly uneven

v1 predicted the rework would close the persistent-memory gap. v2 finds the skills are working — but only some of them.

- **Partner**: *"`/recall` is in use everywhere (31 user fires + 5 Skill fires). The `/brief` skill is almost never invoked (3 fires). No `/spec` invocations. No `/review` invocations."*
- **Engineer**: *"`/checkpoint /recall /brief /spec` toolchain is used but not over-relied-upon — deliberate, not reflex."* But the longest session (3,759 turns) had zero `/checkpoint` mid-session.
- **Portfolio**: *"<rag-service> (renamed from <rag-service>) now indexes `claude-checkpoints` (56 chunks) and `<workflow-repo>-sessions` (177 chunks). Cross-session memory works."*
- **Person**: *"the preference for `/brief` over cold starts is implicit"* — i.e. the *behaviour* is in place, the *skill invocation* is not.

**Convergent implication:** `/recall` is the unambiguous winner. `/brief` is unused because the user front-loads manually, faster than a skill-driven interview. `/spec`, `/checkpoint`, `/review` are underused at the cadence the rework predicted. The skill layer is half-adopted; the behaviour layer is mostly there. *Carry-forward to the next intervention round:* don't add more skills, make the under-used ones more discoverable or auto-suggested.

### 1.4 The portfolio is now three coherent strategies, not one spine

v1 §1.2 collapsed the 13-repo portfolio into one product: *<geo-ml-repo> → <rag-service> → <chatbot-service>* as the spine, *<ecosystem-repo>* as the data foundation. v2 contradicts this — gently.

- **Portfolio**: identifies *three* simultaneous strategies, all progressing:
  1. **Deepen <geo-ml-repo>** — pivot from accuracy-metric chasing to measurement-physics fundamentals (parallax, band-timing, atmospheric correction).
  2. **Productize <visual-render-repo>** — 17 post-rework sessions, 100 commits in 2.5 weeks. Aesthetic/rendering as a delivery surface; the only repo showing complete feature lifecycle (design → wave-by-wave implementation → shipping).
  3. **Architect <multi-agent-toolkit>** — closing the gap between Claude Code's single-session discipline and multi-vendor, multi-agent workflows.
- **Engineer** confirms by tool volume: `<visual-render-repo>` second only to `<geo-ml-repo>` in session count (17 vs 13).
- **Person**: the satisfaction signals are spread across all three strategies — *"PMTiles-pipelinen fungerar"* (<visual-render-repo>), *"yes please"* on the K8s watcher (<geo-ml-repo>), no quoted moments specifically from <multi-agent-toolkit> but the work is continuous.
- **Partner** doesn't address portfolio shape directly.

**Convergent implication:** v1's "you've been building one thing the whole time" was a partial truth. The truer post-rework framing is *you've been building one **mode** the whole time* (briefing-led, atomic-commit, structured-handoff) — and that mode now powers three distinct products. The portfolio is wider than v1 said.

### 1.5 Long sessions still drift after ~turn 200–300

v1 §1.3 said *"the discipline you have at session start is not the discipline you have at session hour 4."* The rework introduced `/checkpoint` to bound this. v2 finds the rule held *partially*.

- **Engineer**: structured checkpointing is "embedded" via `TodoWrite` (1,223 calls), `EnterPlanMode` (18 entries), and explicit mid-session re-anchors in the longer sessions. But not in *all* long sessions.
- **Partner**: *"Session `<session-X>` (2,819 turns) starts tight … by turn 500+ there are 18 `TaskStop` and 31 `TaskOutput` calls. No mid-session checkpoint visible to recover intent at turn 1,500. The 1,759-turn `<session-X>` session has 28 `AskUserQuestion` calls — if it had clear rules every 50 turns, Claude wouldn't need to ask 28 times."*
- **Portfolio** does not address.
- **Person**: tolerance for long sessions has *stabilised* — the user doesn't vent, but neither do they actively bound the session length.

**Convergent implication:** v1's diagnosis stands. The mechanical rules (§6, §7) hold under context pressure. The cadence rule (§4) does not. This is the headline residual problem.

---

## 2. Divergences — where the lenses disagreed productively

### 2.1 "The §1 rule held" (Engineer) vs. "the §1 rule is still violated" (Partner, Person)

Engineer reads `<geo-ml-repo>__31941feb`'s explicit *"Läser detta som en fråga … inte en instruktion att börja bygga något"* as evidence that diagnosis-vs-directive is internalised. Partner reads the corpus differently: *"corrections happen in-flight and are mostly implicit … there's no 'STOP, you're wrong' moment."* Person quotes the *"Should weight decay not be 0.35?"* exchange in `<session-X>` — where Claude proposed 0.05 immediately after writing that 0.35 is the right end of the range for multi-class crop segmentation. The user caught the inconsistency; Claude did not self-catch.

**How to read it:** both are right. The §1 prefix *("Reading this as a diagnosis…")* fires occasionally in Swedish but rarely in English, and almost never on user *statements of preference* (the most common ambiguous form). The rule is held on questions ending in `?`; it is violated on *"X should be Y"* statements. Cost is asymmetric: questions are obviously questions; preferences are easy to misread as instructions.

### 2.2 "Engineering practice is now senior" (Engineer) vs. "productization is still research-grade" (Portfolio, Engineer-self)

v1 §2.1 said engineering = senior, productization = research-project. v2's Engineer notes that *atomic writes, briefing-first, per-task commits, structured checkpointing* are now operationalised — i.e. the *engineering* side moved further upmarket. But the same lens flags five productionisation gaps (schema versioning, observability, CI/CD gating, visual-regression, job-spec versioning). Portfolio reinforces this from above (GPU scarcity, no automated band-timing check, no schema-migration mechanism).

**How to read it:** engineering practice now exceeds the bar of the codebase it is building. The discipline is no longer the bottleneck. Infrastructure is.

### 2.3 "<geo-ml-repo> is the centre" (Engineer) vs. "<visual-render-repo> is the new delivery centre" (Portfolio)

Engineer reads tool volume and infers <geo-ml-repo> as the heaviest gravity well. Portfolio reads commit cadence + feature lifecycle and sees <visual-render-repo> as the only repo showing *end-to-end delivery* post-rework — design spec → waves → render infra → interactive shipping. Both are looking at the same data and weighting *velocity* vs *completion* differently.

**How to read it:** <geo-ml-repo> is where the deep work happens. <visual-render-repo> is where the *shipped work* happens. The user's portfolio has both — the research engine and the delivery surface — for the first time in the corpus.

---

## 3. New patterns surfaced post-rework (not in v1)

1. **Scheduled-task automation.** Engineer: *"`CronCreate` watchers for K8s job completion auto-delete when done. Session `<session-X>` uses `mcp__scheduled-tasks__*` instead of manual `kubectl wait` loops."* This is the user delegating to a *time-based supervisor*, not just an in-session subagent.

2. **Browser-preview MCP as primary inspection tool.** Engineer + Portfolio: 544 `preview_*` calls, 340 Chrome-DevTools calls. The user pushed Claude toward the preview MCP as a session-wide rule (*"use the preview tool, not Chrome DevTools"*) — registered echo-back, held throughout.

3. **<visual-render-repo> + aesthetic delivery as a new strategic axis.** Portfolio: not on the v1 map at all. 17 sessions, 100 commits, the only end-to-end-shipping repo post-rework. The aesthetic/rendering work is no longer a side demo.

4. **<multi-agent-toolkit> as a *multi-vendor* coordination layer.** Portfolio: vendor-neutral spec (AGENTS.md as primary, CLAUDE.md/CODEX.md/MISTRAL.md as addenda). The user is now architecting for a *post-Claude-only* future without abandoning Claude-first runtimes.

5. **Async hand-off as a directive form.** Person: *"yes please"* — three words handing off a multi-day background task. The user trusts Claude as an *async execution layer* now, not just a synchronous pair-programmer. This is the unlock cross-session memory was supposed to enable, and the evidence is in the imperative compression.

---

## 4. Surviving open problems

In rough order of how mechanically they can be addressed:

1. **§4 mid-session cadence is voluntary.** The 3,759-turn <geo-ml-repo> `<session-X>` session had zero `/checkpoint` mid-session. Suggestion: a SessionStart-style banner that fires at turn 50/100/250 reminding to checkpoint — cannot force, can prompt.
2. **Schema versioning across the <geo-ml-repo> → <contracts-repo> → consumer chain.** Engineer + Portfolio agree. Concrete fix: tag dataset artifacts with schema epoch, add a pre-train assertion.
3. **§1 (diagnosis vs directive) still mis-fires on user *preference statements***. Suggestion: an AGENTS.md-level rule requiring an explicit verbal prefix on ambiguous turns.
4. **Visual-regression CI for <visual-render-repo>.** 35 hand-eyeballed screenshots in `<session-X>`. Fix: screenshot-diff threshold in `agent-review.yml`.
5. **<rag-service> is now critical-path** but is single-author, no SLA, no API versioning. Bus-factor 1.
6. **GPU scarcity blocks shipping more than any code or discipline issue does.** Portfolio: *"<visual-render-repo>'s final compositing is offline … 15 nodes occupied, 7 unreachable."* Infrastructure ceiling, not engineering ceiling.

---

## 5. The merged picture

In one paragraph:

> **The discipline that took twelve months to learn now ships at scale.** Briefings are 790-word turn-0 protocols. Commits arrive in atomic per-task batches with mechanically-enforced trailers. Cross-session memory works via `/recall` and the <rag-service>-indexed checkpoint corpus. The user has compressed directives to three words (*"yes please"*) because context no longer evaporates between sessions. The portfolio has expanded from one spine (<geo-ml-repo> → <rag-service> → <chatbot-service>) to three strategies — deepen <geo-ml-repo> on physics, productize <visual-render-repo> on aesthetic delivery, architect <multi-agent-toolkit> for multi-vendor coordination — and all three are progressing in parallel. The ceiling is no longer *operator discipline*. It is **infrastructure** (GPU scarcity, schema versioning, visual-regression CI) and **interpretive rules without hooks** (the §1 preference-as-directive trap, the §4 mid-session cadence gap). The mechanical rework worked. The next intervention round, if there is one, lives one layer up: in how Claude reads ambiguity, and how the runtime nudges the user back to the cadence rule when context starts to drift. Everything else is now just the work.

---

## Methodology notes

- **Corpus:** [`sessions/jsonl/post_rework_sessions.jsonl`](../../sessions/jsonl/post_rework_sessions.jsonl) (60 records). Mirrors at [`sessions/raw/post_rework/`](../../sessions/raw/post_rework/).
- **Index given to agents:** `/tmp/corpus_index.md` (regenerable from the JSONL).
- **Lens prompts:** preserved in the agent-dispatch turn of this session (parent JSONL).
- **Sibling doc:** [`post_rework_evidence.md`](post_rework_evidence.md) for the mechanical-rules (§1–§7) audit.
- **Predecessor:** [`multi_angle_report.md`](multi_angle_report.md) — frozen as the v1 baseline. Read alongside.
- **Rebuild:** `python3 scripts/from_claude_jsonl.py` re-extracts the corpus; agents can be re-dispatched against `/tmp/corpus_index.md`.
