# Academic Research — Agents, Context, Long-Horizon Coding

Compiled from WebFetch returns and searches of arxiv / ACL / Scale / Epoch AI.

Primary papers fetched:
- https://arxiv.org/abs/2510.24699 — AgentFold
- https://arxiv.org/abs/2510.11967 — Context-Folding

Surfaced by search (titles + abstracts only):
- https://arxiv.org/pdf/2509.25250 — Memory Management and Contextual Consistency for Long-Running Low-Code Agents
- https://arxiv.org/html/2603.29194 — Multi-Layered Memory Architectures for LLM Agents
- https://arxiv.org/pdf/2510.00615 — ACON: Optimizing Context Compression for Long-Horizon LLM Agents
- https://arxiv.org/pdf/2510.08790 — COMPASS: Enhancing Agent Long-Horizon Reasoning with Evolving Context
- https://arxiv.org/html/2512.18470v1 — SWE-EVO: Benchmarking Coding Agents in Long-Horizon Software Evolution
- https://arxiv.org/pdf/2509.16941 — SWE-Bench Pro (Scale AI, accepted Nov 2025)
- https://aclanthology.org/2025.acl-long.189.pdf — Rigorous Evaluation of Coding Agents on SWE-Bench (ACL 2025)

---

## AgentFold — arxiv:2510.24699 (Oct 2025)

### Core thesis
*"ReAct-based agents suffer from context saturation"* while fixed summarization risks losing critical info. Agents need **proactive** context management.

### Technique: folding
> "Context is a dynamic cognitive workspace to be actively sculpted."

Two operations:
- **Granular condensations** — preserve fine-grained details from recent steps
- **Deep consolidations** — abstract multi-step sub-tasks into high-level summaries

Learned via supervised fine-tuning; no RL or continual pretraining.

### Results
- AgentFold-30B-A3B: **36.2% on BrowseComp**, 47.3% on BrowseComp-ZH
- Surpasses DeepSeek-V3.1-671B and OpenAI o1-mini

### Practical implication for us
Mid-session state compression is a research-validated pattern, not just practitioner intuition. Our checkpoint protocol (`~/.claude/checkpoints/`) is the poor-man's version of this — but we could adopt the *two-scale* distinction: some checkpoints preserve detail (granular), some abstract entire sub-tasks (deep).

---

## Context-Folding — arxiv:2510.11967 (Oct 2025)

### Problem
Context length is a fundamental constraint on long-horizon tasks. Accumulating history exhausts the window.

### Technique
Agent branches into a sub-trajectory for a subtask, then **folds** it on completion — collapses intermediate steps, preserves only a concise outcome summary. Trained via **FoldGRPO**, an end-to-end RL framework with process rewards for effective decomposition.

### Results
On Deep Research and SWE benchmarks:
- Performance **matches or exceeds ReAct baselines**
- Active context window **10× smaller**
- Beats summarization-based alternatives

### Practical implication
The sub-agent pattern we already use (parallel Explore agents returning distilled summaries) is essentially **human-directed folding.** Research shows agents can learn to do it themselves. Near-term takeaway: be more aggressive about spawning subagents for anything likely to generate > 20 tool calls.

---

## Broader research consensus (from search abstracts)

- **Context drift kills agents before context limits do.** One source claimed *"nearly 65% of enterprise AI failures in 2025 attributed to context drift or memory loss during multi-step reasoning rather than raw context exhaustion."* (unverified but directionally aligned with multiple arxiv papers)
- **Multi-layered memory architectures** (working / episodic / semantic) control cross-session drift.
- **ACON** and **COMPASS** both propose learned context compression for long-horizon LLM agents.
- **SWE-EVO** and **SWE-Bench Pro** extend agent coding evaluation to long-horizon software evolution — tasks that take humans hours to days. Pass@1 on SWE-Bench Pro remains **below 45%** even for best models, vs. **79.2%** on SWE-bench Verified (Claude Opus 4.5 + Live-SWE-agent, Nov 2025). The gap quantifies how hard long-horizon coding is.

---

## What the research says about our pitfalls

Our documented pitfalls map almost 1:1 to findings in the context-management literature:

| Our pitfall | Research equivalent |
|---|---|
| Long-session drift without re-anchoring | Context saturation / drift (AgentFold, Context-Folding, AMA-Bench) |
| Editing running code while user asks status | Tool-use reliability under context pressure (ACON, COMPASS) |
| Draft residue on "start fresh" | Summarization-loss / failure to consolidate (AgentFold) |
| Tool-preference inertia | Reliability under long-horizon reasoning (several) |

None of this is personal. All of it is the frontier of active research.

---

## Evaluation — what serious teams measure

- **SWE-bench Verified pass@1** — standard for code-agent eval
- **Context window size vs. performance curve** — quality-vs-context
- **Tool call efficiency** — useful calls / total calls
- **Task decomposition depth** — sub-task count vs. success rate
- **Rollback / correction frequency** — how often agents fix their own errors

For our archive: we already have correction count, tool-call totals, session length. We could add *rollback-per-session* (grep for "undo" / "ångra" / `git reset`) as a drift metric.

---

## 3 concrete experiments to try

1. **Two-scale checkpoint.** In long sessions, alternate between *granular* checkpoints (keep file paths, specific rules) and *deep* checkpoints (one-sentence sub-task summary, nothing else). Compare recovery quality after `/clear`.

2. **Proactive folding.** At turn ~50, ask Claude: *"Summarize the last 50 turns as: active goal + outcomes + what I should stop caring about. Then I'll /clear and paste your summary."* Based on AgentFold's approach.

3. **Drift metric on the corpus.** Add a `corrections_per_100_turns` column to `analysis/per_session.csv`. Track this over time vs. session word count to quantify the drift curve in our own data.
