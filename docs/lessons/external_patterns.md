# External Patterns — Synthesis of Four Lenses

How the broader agentic-workflow community works, read through four parallel lenses: **Anthropic official**, **practitioner write-ups**, **academic research**, and **enterprise / team adoption**. This document is the synthesis — convergences across sources carry the most weight; productive disagreements are flagged; adoption actions are ranked.

Raw returns per lens are in [`external_patterns_raw/`](external_patterns_raw/): [`anthropic.md`](external_patterns_raw/anthropic.md), [`practitioners.md`](external_patterns_raw/practitioners.md), [`academic.md`](external_patterns_raw/academic.md), [`enterprise.md`](external_patterns_raw/enterprise.md).

> Note on methodology: subagents in this environment are denied WebFetch/WebSearch permissions, so research was conducted from the main session using 12 direct web fetches + 4 searches across 2026-04-24. Every quote is traceable to a URL in the raw files.

---

## What every lens converged on

Five findings where Anthropic docs, practitioner blogs, academic papers, and enterprise case studies independently agreed. These are the strongest signals.

### C1 — The model is only half the system; the harness is the other half

- **Anthropic:** *"Claude's context window fills up fast, and performance degrades as it fills."* (Best Practices)
- **Practitioner (Osmani):** *"A decent model with a great harness beats a great model with a bad harness."*
- **Academic (Context-Folding):** active-context-management outperforms ReAct baselines with a **10× smaller** context window.
- **Enterprise (Shopify):** centralized LLM proxy is the *platform layer*; tool choice is per-engineer. The platform is the harness.

**Implication for us:** our continuity layer (`~/.claude/CLAUDE.md` + skills + checkpoints) is the right category of investment. Skills and hooks have more leverage than prompting finesse.

### C2 — Verification is the single highest-leverage move

- **Anthropic:** *"Include tests, screenshots, or expected outputs so Claude can check itself. This is the single highest-leverage thing you can do."*
- **Practitioner (Osmani):** quality checks are a *"learning signal"* — failed tests become teaching moments.
- **Academic (C-compiler post):** *"It's important that the task verifier is nearly perfect, otherwise Claude will solve the wrong problem."*
- **Enterprise (Stripe/Wiz):** the 20× speedup on large migrations depends on regression tests catching breakage per-file.

**Implication for us:** our 31-session retrospective emphasizes openers and corrections; verification is the missing leg of the stool. Every session should end with a verification artifact (test, screenshot, linter pass) — and CLAUDE.md should demand one.

### C3 — Context management is the bottleneck, not context length

- **Anthropic:** *"Quality tends to fall when context reaches approximately 50% full."* (via Simon Willison summary)
- **Practitioner:** PLAN → WORK → REVIEW → COMPOUND as explicit refresh cycle.
- **Academic (AgentFold, Context-Folding, ACON, COMPASS):** dozens of 2025 papers treat context management as *the* agent-scaling problem. One source claimed *"65% of enterprise AI failures attributed to context drift or memory loss during multi-step reasoning rather than raw context exhaustion."* Directionally echoed across papers.
- **Enterprise (Anthropic C-compiler):** 16 agents succeed by *each having its own clean context*. File locks coordinate without shared context.

**Implication for us:** our checkpoint protocol is the right direction but too coarse. The research pushes toward **two-scale folding** (granular + deep) and **proactive summarization at turn boundaries**, not end-of-session.

### C4 — Separate exploration, planning, and implementation

- **Anthropic:** Plan Mode (`Explore → Plan → Implement → Commit`). *"Letting Claude jump straight to coding can produce code that solves the wrong problem."*
- **Practitioner (Osmani):** brainstorm → `spec.md` → *"let's implement Step 1 from the plan."*
- **Academic:** chain-of-thought + plan-then-execute consistently outperform react-at-each-step in long-horizon benchmarks.
- **Enterprise (Anthropic security):** *"design doc → tests → code"* replaced *"design doc → janky code → give up on tests."*

**Implication for us:** our briefing-opener captures this for session openers. We don't apply it at the *task* level within a session. Long sessions need a plan-refresh every ~50 turns.

### C5 — Failures become permanent constraints, not retries

- **Anthropic:** *"For each CLAUDE.md line, ask: Would removing this cause Claude to make mistakes? If not, cut it."*
- **Practitioner (Osmani):** *"Every line in a good AGENTS.md should be traceable back to a specific thing that went wrong."* The **ratchet principle.**
- **Academic:** self-improving agent research shows that explicit learning stores ("agents update AGENTS.md") beat in-context adaptation.
- **Enterprise:** hook-based deterministic enforcement beats advisory rules at team scale.

**Implication for us:** our `~/.claude/CLAUDE.md` rules are correctly derived from observed failures (the 2026 retrospective). Each rule should cite the session where the failure happened — this matches the ratchet principle exactly.

---

## What's genuinely new to us

Twelve patterns documented in external sources that our corpus did not surface.

| # | Pattern | Source | What it is |
|---|---|---|---|
| 1 | **Auto memory** (`~/.claude/projects/<project>/memory/`) | Anthropic | Claude writes its own notes between sessions; first 200 lines loaded each session |
| 2 | **Path-scoped rules** `.claude/rules/<topic>.md` with `paths:` frontmatter | Anthropic | Rules that only load when Claude reads matching files |
| 3 | **Extended thinking budgets** via keywords (`think` → `ultrathink` = 4k → 32k tokens) | Willison reverse-engineering | Claude Code-specific keyword → token budget mapping |
| 4 | **`--permission-mode auto`** with classifier | Anthropic | Model reviews each command, blocks risky ones, lets routine work through |
| 5 | **`/rewind` + Esc+Esc** checkpoint-restore | Anthropic | Restore conversation, code, or both to any prior turn |
| 6 | **`/btw`** side questions outside context | Anthropic | Questions that don't pollute the main conversation |
| 7 | **File-based locking for multi-agent** (`current_tasks/` dir) | Anthropic C-compiler post | 16 agents coordinate via filesystem, no orchestrator |
| 8 | **Centralized LLM proxy** (Shopify pattern) | Shopify / Bessemer | One platform layer routing all tools/providers |
| 9 | **Writer / Reviewer parallel sessions** | Anthropic + practitioners | Second agent with fresh context reviews first agent's output |
| 10 | **Interview-driven spec** via `AskUserQuestion` | Anthropic | Claude interviews user → writes SPEC.md → fresh session executes |
| 11 | **Fan-out across files** via `claude -p` bash loop | Anthropic | Non-interactive mode with `--allowedTools` for batch migrations |
| 12 | **Two-scale folding** (granular + deep) | AgentFold paper | Context compression at two levels of abstraction |

---

## Productive disagreements

### Briefing openers — our heavy style vs. Anthropic's conditional advice

We advocate 500–800 word briefing openers. Anthropic says:

> "Plan Mode is useful, but also adds overhead. For tasks where the scope is clear and the fix is small (like fixing a typo, adding a log line, or renaming a variable) ask Claude to do it directly. If you could describe the diff in one sentence, skip the plan."

**Reconciliation:** our position holds for non-trivial work (the kind that dominates our corpus) but we should amend `what_worked.md` to acknowledge the one-sentence-diff exception. Updated rule: *front-load turn 0 only when the task touches > 2 files or takes > 3 tool calls.*

### Commits — our "end-of-session checkpoint" vs. practitioner's "save point per task"

Our `can-you-make-sure-everything-is-committed` pattern bundles many changes into one session-spanning commit. Osmani recommends *"commit after each small task succeeds... treating commits as save points in a game."*

**Reconciliation:** the small-commit practice is better. Bundling obscures which change addressed which instruction. Update `pitfalls.md §10` to explicitly recommend the per-task pattern.

### STOP — our blunt interrupt vs. Anthropic's `Esc` + `/rewind`

Our sessions used `STOP` literally because it was fast. Anthropic offers native primitives: `Esc` interrupts with context preserved; `/rewind` restores a checkpoint. Both are more surgical than typing STOP.

**Reconciliation:** keep STOP as the fallback (it works and travels across UIs) but adopt `Esc` + `/rewind` as the default when available. Update `instruction_adherence.md §What works`.

---

## Net new ideas to adopt

Ranked by leverage-vs-effort. Each cites the source that surfaced it.

### Tier 1 — Adopt this week (low effort, direct continuity-layer improvement)

1. **Enable auto memory** per Anthropic docs. Create `~/.claude/projects/.../memory/MEMORY.md` for each active repo. *(Source: Anthropic docs §memory)*
2. **Add `verify_work` as a CLAUDE.md rule.** Every non-trivial change must include a verification artifact: test, screenshot, linter pass, or expected-output comparison. *(Source: Anthropic Best Practices §1)*
3. **Mid-session fold prompt.** Add a snippet to the `/checkpoint` skill: *"If we've been going >50 turns, summarize the last 50 turns as: active goal + outcomes + what I should stop caring about. I'll paste this after /clear."* *(Source: AgentFold paper)*
4. **Interview-driven `/spec` skill.** A new skill that runs the *"interview me using AskUserQuestion → write SPEC.md → tell me to start a fresh session"* flow for any non-trivial feature. *(Source: Anthropic Best Practices §Communicate effectively)*

### Tier 2 — Adopt this month (requires minor config work)

5. **Per-task commits as the default.** Update `~/.claude/CLAUDE.md` to prefer per-task commits; flag the "commit everything" pattern as an anti-pattern. *(Source: Addy Osmani workflow)*
6. **Commit-attribution hook.** `PostToolUse` on `git commit` that appends `Co-Authored-By: Claude Opus 4.6`. Anthropic-internal standard. *(Source: enterprise lens)*
7. **Writer/Reviewer skill.** A skill that, given a recent change, spawns a fresh subagent to review it with no bias toward the code. Maps directly to the parallel-session pattern from Anthropic docs. *(Source: Anthropic Best Practices §Run multiple Claude sessions)*
8. **Path-scoped rules for active repos.** Convert repo-specific rules from CLAUDE.md into `.claude/rules/<topic>.md` with `paths:` frontmatter. Keeps global CLAUDE.md small. *(Source: Anthropic docs §rules)*

### Tier 3 — Worth trying, larger commitment

9. **`/permission-mode auto` during unattended runs.** Combined with sandbox. Test on a low-risk repo first. *(Source: Anthropic Best Practices §permissions)*
10. **Fan-out migration template.** A `make migrate SRC=... PATTERN=...` Makefile target using `claude -p` with `--allowedTools`. Aimed at a future analysis-pipeline → shared-contracts extraction. *(Source: Anthropic + Stripe case study)*
11. **Drift metric in `analysis/`.** Add `corrections_per_100_turns` column to `per_session.csv`; plot over time. Quantifies the context-drift problem in our own data. *(Source: academic lens)*
12. **Managed-settings template.** A template `settings.json` with `allowManagedHooksOnly: true`, path denylists for secrets, and default permission allowlists. Even as a solo dev, makes the config reviewable. *(Source: Anthropic docs §settings)*

### Tier 4 — Selective / situational

13. **Centralized LLM proxy.** Overkill solo; invaluable at team scale. Revisit if/when we're > 1 engineer. *(Shopify)*
14. **File-based multi-agent locks.** The C-compiler pattern. Only worth it for genuinely parallelizable long-horizon work (e.g., a repo-wide migration). *(Anthropic C-compiler)*
15. **Multi-model musical chairs.** Copy prompts across Claude + Gemini + GPT. Worth it when one model is stuck, not as a default. *(Osmani)*

---

## The updated playbook (integrating external + our own)

**Session start:**
1. `/brief` (ours) — full briefing template
2. Read `MEMORY.md` for the project (new — auto memory)
3. Attach latest checkpoint (ours)
4. *Or* run `/spec` (new) if the task is big and ambiguous, then start a fresh session with the resulting SPEC.md

**During the session:**
5. Explore in Plan Mode if the task needs it (new; skip for one-sentence diffs)
6. Echo stated rules verbatim (ours)
7. `/checkpoint` every ~50 turns (ours — augmented with fold-prompt)
8. Run tests / screenshot / lint after every non-trivial change (new — verification as default)
9. Use `Esc` or `/rewind` when drift appears (new); fall back to `STOP` if needed

**Parallel work:**
10. Delegate research to subagents (ours)
11. For parallel file-level tasks, use `claude -p` fan-out (new)
12. For independent decisions, spawn a second fresh-context reviewer session (new)

**Session end:**
13. Commit per completed task, not end-of-session bundle (new)
14. Write final checkpoint (ours)
15. `PostToolUse` hook auto-attributes Claude commits (new)

**Between sessions:**
16. Auto memory writes `MEMORY.md` for the project (new)
17. If a failure recurred, encode it as a CLAUDE.md rule + cite the source session (ours — ratcheted)

---

## Sources (authoritative)

Direct fetches and confirmed quotes:
- [Anthropic: Best Practices for Claude Code](https://code.claude.com/docs/en/best-practices)
- [Anthropic: Memory](https://code.claude.com/docs/en/memory)
- [Anthropic: Subagents](https://code.claude.com/docs/en/sub-agents)
- [Anthropic: Hooks](https://code.claude.com/docs/en/hooks)
- [How we built our multi-agent research system](https://www.anthropic.com/engineering/built-multi-agent-research-system)
- [Building a C compiler with parallel Claudes](https://www.anthropic.com/engineering/building-c-compiler)
- [How Anthropic teams use Claude Code](https://claude.com/blog/how-anthropic-teams-use-claude-code)
- [Addy Osmani — Agent Harness Engineering](https://addyosmani.com/blog/agent-harness-engineering/)
- [Addy Osmani — My LLM Coding Workflow Going Into 2026](https://addyo.substack.com/p/my-llm-coding-workflow-going-into)
- [Addy Osmani — Self-Improving Coding Agents](https://addyosmani.com/blog/self-improving-agents/)
- [Simon Willison — Claude Code: Best practices for agentic coding](https://simonwillison.net/2025/Apr/19/claude-code-best-practices/)
- [AgentFold (arxiv:2510.24699)](https://arxiv.org/abs/2510.24699)
- [Context-Folding (arxiv:2510.11967)](https://arxiv.org/abs/2510.11967)

Search-surfaced, cited in raw reports:
- [Bessemer / Shopify engineering playbook](https://www.bvp.com/atlas/inside-shopifys-ai-first-engineering-playbook)
- [SWE-bench leaderboards](https://www.swebench.com/)
- [Epoch AI — SWE-bench Verified](https://epoch.ai/benchmarks/swe-bench-verified)
- [Anthropic — How AI is transforming work at Anthropic](https://www.anthropic.com/research/how-ai-is-transforming-work-at-anthropic)

---

## How this doc was produced

4 research lenses, originally scoped to run as 4 parallel Explore agents. Subagents in this environment do not inherit WebFetch/WebSearch permissions, so research was executed from the main session with 12 direct WebFetch calls + 4 WebSearch calls against authoritative sources. Each lens has its raw compiled notes in `external_patterns_raw/<lens>.md`; this file is editorial synthesis.

**Session continuity note:** mid-session checkpoints taken at turn 1 (`continuity-rollout`) and turn 2 (`external-research`) in `~/.claude/checkpoints/agentic_workflow/`. First real use of the checkpoint protocol; it held up.
