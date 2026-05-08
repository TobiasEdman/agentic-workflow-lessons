# Multi-User + Multi-Agent Collaborative Coding — Four-Lens Synthesis

How do multiple humans and multiple agents collaborate on a shared codebase? Four parallel research lenses — **Anthropic official**, **practitioners**, **academic research**, **enterprise adoption** — answer that question with remarkable convergence.

Raw returns per lens in [`multi_user_multi_agent_raw/`](multi_user_multi_agent_raw/): [`anthropic.md`](multi_user_multi_agent_raw/anthropic.md), [`practitioners.md`](multi_user_multi_agent_raw/practitioners.md), [`academic.md`](multi_user_multi_agent_raw/academic.md), [`enterprise.md`](multi_user_multi_agent_raw/enterprise.md).

> Methodology: four subagents ran in parallel on 2026-04-24. Two returned web-access denials initially (we've seen this pattern before in this harness), but all four ultimately produced reports with verified fetches. Claims tied to unfetched URLs are explicitly flagged in each raw report.

---

## The four-way convergence

These patterns appeared in **three or four of the four lenses independently** — the strongest possible evidence that the field has landed on them.

### C1 — Git is the coordination substrate. Not messaging, not shared memory — git.

| Lens | How they said it |
|------|------------------|
| **Anthropic** | File-lock pattern in `current_tasks/` (C-compiler, 16 agents). Git worktree per session. *"Claude takes a 'lock' on a task by writing a text file… git's synchronization forces the second agent to pick a different one."* |
| **Practitioners** | *"Git itself remains the real multi-user substrate: branches, PRs, issues, CI."* Branch-/worktree-per-agent is the **default** isolation primitive. |
| **Academic** | **AgentGit** (Nov 2025), **Git Context Controller** (Aug 2025, >80% SWE-Bench Verified), **EvoGit** (Jun 2025) all formalize git operations (commit/branch/merge) as the coordination protocol. |
| **Enterprise** | **Cloudflare** ran 131,246 review-agent runs across 48,095 MRs in one month — all PR-gated. **Shopify** runs 10 agents in parallel with PRs as the human merge point. |

**The unifying claim:** you don't need a custom multi-agent coordination protocol. You need git worktrees, a lockfile convention, PRs as integration points, and CI as the verification gate. The infrastructure already exists.

### C2 — Coordination > model. Memory matters more than model choice.

| Lens | Evidence |
|------|----------|
| **Academic** | Trace analyses across frameworks show 40–80% failure rates with **~37% attributable to inter-agent misalignment**. *"Has memory vs. no memory matters more than swapping LLM backbones."* |
| **Practitioners** | *"Verification is the constraint, not generation."* LLM-authored `AGENTS.md` hurts success by ~3% and cost by 20% — **human-curated coordination artifacts beat agent-written ones**. |
| **Anthropic** | Agent Teams docs: *"the lead agent can't steer subagents, subagents can't coordinate"* mid-run. Explicit task decomposition with output-format contracts is what works. |
| **Enterprise** | Shopify centralized **LLM proxy** → bulk token buying, per-team quotas, model-agnostic routing. The proxy is the coordination primitive, not the model. |

**The unifying claim:** pick any reasonable frontier model; invest everything else in harness quality. This is a direct confirmation of what Addy Osmani called *"skill issue, not model issue."*

### C3 — Shared-context governance is a first-class problem.

| Lens | Finding |
|------|---------|
| **Academic** | **Collaborative Memory** (May 2025) introduces private/shared memory tiers with bipartite user-agent-resource graphs + auditable read/write policies. *"Who can see what an agent remembered"* must be first-class. |
| **Anthropic** | Cloud sessions only see what's **committed**. User-level `~/.claude/CLAUDE.md` does NOT propagate. Repo-level `.claude/` is the multi-user substrate. **No shared secrets store yet** (flagged by Anthropic as scoped-out). |
| **Practitioners** | *"Directory ownership per person"* as a soft-lock convention. AGENTS.md + per-directory CLAUDE.md files encode invariants. |
| **Enterprise** | Cloudflare's plugin architecture **explicitly isolates secrets** — "GitLab and Cloudflare AI Gateway plugins can't see each other's secrets." |

**The unifying claim:** multi-user agent setups need explicit access control on memory, config, and secrets — and the tooling for this is just barely emerging.

### C4 — Agent-on-agent review is the emerging first-line quality gate.

| Lens | Evidence |
|------|----------|
| **Anthropic** | Subagent definitions (`security-reviewer`, `test-runner`) reusable as one-shot subagents OR long-lived teammates. *"Define a role once… reuse as both."* |
| **Practitioners** | Three-tier review stack: in-process reviewer → local orchestrator → cloud-async PR reviewer. *"Dedicated reviewer agents using read-only access."* |
| **Academic** | **Croto** (ACL 2025): parallel red-team/blue-team agent squads beat single-team exploration on software-quality metrics. |
| **Enterprise** | Cloudflare's 2.7 reviewer runs per MR (multi-lens: security + perf + test-coverage). **Adversarial debate** for bug triage — 5 investigators defending different theories. |

**The unifying claim:** the pattern is *not* one agent, one answer. It's specialized reviewer agents running in parallel, each with a different lens, against the same PR.

### C5 — Attribution at the git layer is the unsolved governance problem.

| Lens | Finding |
|------|---------|
| **Enterprise** | **GitHub Copilot's cloud agent sets author to Copilot on squash-merge, breaking `git blame`** for the requesting human. Community consensus (Apr 2026): signed commits for execution identity, human as `author`, `Co-authored-by:` trailers for the agent. |
| **Anthropic** | Permissions inherit at spawn — *if the lead has --dangerously-skip-permissions, every teammate does too*. Tightening after spawn not supported at spawn-time. |
| **Practitioners** | *"Ultimate accountability still sits with humans"* — but who reviews AI code when everyone uses AI is an open problem. |
| **Academic** | Collaborative Memory formalizes access control but *"lacks standardized evaluation."* |

**The unifying claim:** the tooling for "who did what" is retrofitted onto git via signed commits + trailers. It works, but it's unusual for a well-understood problem to still be in the workaround phase.

---

## Productive disagreements

### Centralization vs. decentralization

- **Anthropic** favors orchestrator-worker. *"A lead agent coordinates… the lead is the lead for its lifetime."*
- **Academic (EvoGit)** shows decentralized git-phylogeny coordination works *without* a central orchestrator.
- **Enterprise (Shopify)** runs BOTH: 10 parallel agents with human merge gatekeeper (centralized) + 45-min sequential critique loops (pipeline).

**Reconciliation:** use orchestrator-worker for bounded tasks with clear decomposition. Use decentralized git-native coordination for longer, exploratory work. Don't mix paradigms inside one task.

### How many teammates?

- **Anthropic:** 3–5 teammates, 5–6 tasks each. *"More teammates means more communication… diminishing returns past ~5."*
- **Anthropic C-compiler:** **16 agents** worked — because each operated on an isolated file-locked task with no inter-agent coordination needed.
- **Shopify:** **10 agents in parallel** works when a human is the merge gatekeeper.

**Reconciliation:** team size is bounded by coordination overhead, not by compute. If tasks are truly independent (branch-per-agent, file-lock), scale out. If agents need to share context, cap at ~5.

### Real-time collaboration

- **Anthropic** is explicit: **no** real-time cursors, no Google-Docs-style co-editing. *"Recipients see the latest state when they open the link, but their view doesn't update in real time."*
- **Practitioners** confirm: PRs are the integration point, not live editing.

**No disagreement here — just confirming the ceiling.** Multi-user agentic coding in 2026 is snapshot-based, not streaming.

---

## What's genuinely new to us (vs. our corpus)

Patterns from this research that we haven't yet captured:

| # | Pattern | Source | What it is |
|---|---------|--------|------------|
| 1 | **`current_tasks/` file-lock directory** | Anthropic C-compiler | Txt-file lockfiles in a committed dir. Git is the sync primitive. |
| 2 | **Agent Teams `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`** | Anthropic v2.1.32 | Lead + teammates + shared task list + mailbox, local under `~/.claude/teams/` |
| 3 | **Plugin marketplace with namespacing + version gating** | Anthropic + Cloudflare | `/acme:deploy` prefixes, `version` in `plugin.json`, opt-in updates |
| 4 | **`.claude/agents/` role library committed to repo** | Anthropic + Enterprise | `security-reviewer.md`, `test-runner.md` as subagent definitions both humans use |
| 5 | **`Co-authored-by: Claude` + signed commits** | Enterprise consensus | Keeps `git blame` honest when agents commit |
| 6 | **Multi-lens reviewer squad** | Cloudflare, Croto | 3-5 reviewer agents per PR, each with a different lens |
| 7 | **Adversarial debate for bug triage** | Anthropic + Shopify | 5 investigators with competing theories |
| 8 | **Plan-gated teammates in read-only mode** | Anthropic | Lead approves plans before teammate gets write access |
| 9 | **Hooks as team policy** (`TaskCompleted` exit 2) | Anthropic | Team-wide quality gates enforced outside the model |
| 10 | **LLM proxy as platform layer** (Shopify, Cloudflare) | Enterprise | Single gateway for bulk tokens + quotas + telemetry |
| 11 | **Git-native agent state libraries** | Academic (AgentGit, GCC, EvoGit) | Branch/commit operations as the primary agent abstraction |
| 12 | **Access-controlled shared memory (private/shared tiers)** | Academic (Collaborative Memory) | Bipartite graphs with auditable read/write policies |

---

## Adoption plan — ranked by leverage, for a 2–3 person team

### Tier 1 — Do this week (low effort, high leverage)

1. **Check `.claude/agents/` role library into active repos.** Start with the analysis-pipeline repo. Define `security-reviewer.md`, `schema-guardian.md` (enforces 23-class invariant), `test-writer.md`. Each has its own `tools:` allowlist and optional `model:` override. Both humans' agents spawn with the same roles.

2. **Enable commit attribution.** Install `PostToolUse` hook that auto-appends `Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>` on `git commit`. Require signed commits. Human stays as `author`, agent goes in trailer.

3. **Add `current_tasks/` convention.** For any multi-agent work (e.g. the shared-contracts extraction from Wave 3), create `current_tasks/` in the repo. Each agent writes a `.txt` lockfile before taking a task. Committed state = coordination state.

### Tier 2 — Do this month (requires harness changes)

4. **Stand up the Writer/Reviewer pattern as a hook.** `PreCommit` hook spawns a fresh-context reviewer subagent (from `.claude/agents/security-reviewer.md` etc.) against the staged diff. Block commit on errors; warn on suggestions.

5. **Multi-lens PR review on the 3 Tier A repos.** Each PR gets automatic runs of: `security-reviewer`, `test-coverage-reviewer`, `schema-guardian`. Posted as PR comments. This is the review-agent repo's natural role — make it Wave 2 of our rollout.

6. **Shared CLAUDE.md audit.** Every Tier A repo's CLAUDE.md gets split: path-scoped rules in `.claude/rules/<topic>.md`, team conventions at root, personal conventions in `CLAUDE.local.md` (gitignored). This was already a Wave 2 item; now it's also the multi-user-readiness step.

### Tier 3 — Do this quarter (architectural)

7. **Try Agent Teams experimental for one bounded task.** Set `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`. Pick a task (e.g. extracting shared contracts). Spawn 3 teammates with the role library. Measure time, token cost, merge conflicts.

8. **Build a `current_tasks/` workflow in `agentic_workflow`.** This repo is the meta-infrastructure — dogfood the file-lock pattern here first. `sessions/cleaned/*.txt` cleaning is a natural first use case (each agent claims one session, writes the cleaned version, removes the lock).

9. **Evaluate the Shopify-style LLM proxy** — skip for a 2-person team. Revisit if we hit 4+ people or if cross-model routing (Claude + Gemini + GPT) becomes necessary.

### Tier 4 — Watch, don't adopt yet

10. **Git-native agent-state libraries (AgentGit, GCC, EvoGit).** Academic research; too new. Revisit Q4 2026 once someone has run one in production.
11. **Collaborative Memory access control.** Same reason. The pattern is right; the tooling isn't mature.
12. **Purpose-built multi-user-multi-agent benchmarks.** None exist yet. SWE-Bench Pro is human-verified but not multi-human-contributing. Don't optimize for a benchmark that doesn't measure your actual workload.

---

## What this means for the existing rollout plan

Reinforced items in the rollout plan:

- **`/review` skill** ← reinforced as the single highest-leverage multi-agent addition
- **review-agent repo as PR check** ← reinforced by Cloudflare's 131k/month review runs
- **Shared-contracts extraction** ← the package structure should include an `agents/` submodule with reusable role definitions
- **New item:** `Co-Authored-By: Claude` PostToolUse hook + signed commit requirement
- **New item:** path-scoped rules migration reframed as multi-user-readiness, not just CLAUDE.md bloat

The rollout plan already contains most of what this research recommends. Three specific additions are needed; they're small.

---

## Honest assessment

**Where this research is strong:**
- Git-as-substrate consensus is solid (4/4 lenses).
- Coordination > model claim has both quantitative (academic: 37% misalignment failures) and qualitative (practitioner: "skill issue") support.
- The specific patterns (task-list + file-lock + worktree + subagent roles + hooks) are all well-documented.

**Where it's weak:**
- Real multi-user-multi-agent case studies are **rare**. Most sources describe single-user-multi-agent, then extend by analogy.
- Attribution + permission models are still immature (signed commits + trailers is a workaround, not a native solution).
- No benchmark measures the actual workload (N humans + M agents on one repo). SWE-Bench Pro is close but not there.
- Practitioner agent explicitly flagged: *"explicit multi-user + multi-agent (as opposed to single-user multi-agent) practice is under-documented."*

**Net:** good enough to act on for a 2–3 person team. Not good enough to write a canonical playbook. The field will be clearer in 6 months.

---

## Citations

Anthropic — [agent-teams](https://code.claude.com/docs/en/agent-teams) · [claude-code-on-the-web](https://code.claude.com/docs/en/claude-code-on-the-web) · [desktop](https://code.claude.com/docs/en/desktop) · [plugins](https://code.claude.com/docs/en/plugins) · [C-compiler](https://www.anthropic.com/engineering/building-c-compiler) · [multi-agent research system](https://www.anthropic.com/engineering/built-multi-agent-research-system)

Practitioners — [Osmani: agent teams](https://addyosmani.com/blog/claude-code-agent-teams/) · [Osmani: orchestra](https://addyosmani.com/blog/code-agent-orchestra/) · [Osmani: future](https://addyosmani.com/blog/future-agentic-coding/)

Academic — [AgentGit](https://arxiv.org/abs/2511.00628) · [Git Context Controller](https://arxiv.org/abs/2508.00031) · [EvoGit](https://arxiv.org/abs/2506.02049) · [Collaborative Memory](https://arxiv.org/abs/2505.18279) · [Croto (ACL 2025)](https://arxiv.org/abs/2406.08979) · [SWE-Bench Pro](https://arxiv.org/abs/2509.16941)

Enterprise — [Cloudflare AI code review](https://blog.cloudflare.com/ai-code-review/) · [Cloudflare internal AI stack](https://blog.cloudflare.com/internal-ai-engineering-stack/) · [Shopify AI-first (Bessemer)](https://www.bvp.com/atlas/inside-shopifys-ai-first-engineering-playbook) · [VS Code multi-agent](https://code.visualstudio.com/blogs/2026/02/05/multi-agent-development) · [GitLab Duo code review](https://docs.gitlab.com/user/duo_agent_platform/flows/foundational_flows/code_review/) · [Vercel Agent PR review](https://vercel.com/docs/agent/pr-review) · [Copilot commit attribution discussion](https://github.com/orgs/community/discussions/184395)
