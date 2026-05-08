# Academic Research — Multi-User + Multi-Agent Collaborative Software Development (2024–2026)

Source: the academic-lens research agent from the 2026-04-24 dispatch. Five arxiv abstracts were fetched and verified via WebFetch.

---

## 1. Key Research Findings

### Finding 1 — Git-native state management dramatically improves multi-agent coding reliability
**AgentGit** (Nov 2025) brings commit/revert/branch to LangGraph agent workflows, reducing redundant computation and token usage while enabling safe parallel trajectory exploration.

**Implication:** treat agent state like code — make it branchable and revertible before letting agents touch production repos.

### Finding 2 — Shared context is better modeled as a version graph than a chat log
**Git Context Controller** (Aug 2025) elevates agent memory to a persistent workspace with COMMIT / BRANCH / MERGE / CONTEXT operations, reaching >80% on SWE-Bench Verified and beating long-context baselines by 13% relative.

**Implication:** replace ever-growing prompts with checkpointed, navigable context stores.

### Finding 3 — Decentralized Git-based coordination scales without a central orchestrator
**EvoGit** (Jun 2025) uses a shared Git phylogenetic graph as the only coordination substrate. Agents asynchronously read/write branches; conflicts are handled through lineage rather than messaging.

**Implication:** branch-per-agent with repo-level coordination is a viable alternative to message-passing orchestration.

### Finding 4 — Multi-user memory needs explicit, asymmetric, time-evolving access control
**Collaborative Memory** (May 2025) introduces private/shared tiers with bipartite user-agent-resource graphs and auditable read/write policies.

**Implication:** in any multi-human setting, "who can see what an agent remembered" must be a first-class design decision, not an afterthought.

### Finding 5 — Cross-team orchestration beats single-team exploration
**Croto** (ACL 2025 Findings) has multiple LLM teams concurrently propose solutions and exchange insights, yielding measurable software-quality gains over ChatDev-style single-team setups.

**Implication:** parallel "red team / blue team" agent squads outperform one big team.

### Finding 6 — Benchmarks are finally catching up to realistic long-horizon, human-verified tasks
**SWE-Bench Pro** (Sep 2025, updated Nov 2025) includes 1,865 problems with a three-stage human-in-the-loop pipeline (env construction, issue augmentation, test verification). Top models stay below 45%.

**Implication:** multi-hour, multi-file tasks remain largely unsolved even by frontier agents.

### Finding 7 — Most multi-agent failures are coordination failures, not model failures
Trace analyses across frameworks show 40–80% failure rates with ~37% attributable to inter-agent misalignment; *"has memory vs. no memory"* matters more than swapping LLM backbones.

**Implication:** invest in coordination protocols before upgrading the model.

---

## 2. Open Problems Researchers Acknowledge

- **Conflict resolution between concurrent agent edits** is handled implicitly (lineage) rather than explicitly; semantic merge conflicts in code are unsolved.
- **Multi-human + multi-agent access control** is formalized (Collaborative Memory) but lacks standardized evaluation.
- **Error recovery / collaborative debugging across branches** is flagged as open in AgentGit.
- **Scalability of shared context** beyond ~1K agents (MacNet/ChatDev) still degrades in practice.
- No mature benchmark combines multiple humans AND multiple agents on the same repo — SWE-Bench Pro uses humans only for verification, not concurrent contribution.

---

## 3. Evaluation Metrics Used

- Task resolution / pass@1 on SWE-Bench Verified & Pro
- Token cost and runtime per resolved task (AgentGit)
- Inter-agent misalignment rate from trace analysis
- Software-quality scores (completeness, executability) in ChatDev/Croto
- Auditability and access-policy adherence (Collaborative Memory)
- Trajectory diversity / branches explored per solved task

---

## 4. Three Experiments a Practitioner Team Could Run

1. **Branch-per-agent vs. shared-branch A/B.** Give N agents the same issue; in arm A each gets its own branch with merge-at-end, in arm B all commit to a shared branch. Measure merge-conflict rate, wall-clock to green CI, and reviewer-rejected PRs.
2. **Checkpointed context vs. rolling prompt.** Replace conversation history with a GCC-style commit/branch context store. Compare SWE-Bench Verified-lite success rate, token spend, and recovery time after a bad step.
3. **Access-controlled shared memory.** Introduce private/shared memory tiers across two human reviewers + three agents on a real repo. Measure leakage incidents, duplicate work, and reviewer trust (survey) vs. an open-memory baseline.

---

## 5. Citations

- AgentGit: https://arxiv.org/abs/2511.00628
- Git Context Controller: https://arxiv.org/abs/2508.00031
- EvoGit: https://arxiv.org/abs/2506.02049
- Collaborative Memory: https://arxiv.org/abs/2505.18279
- Cross-Team Orchestration (Croto, ACL 2025 Findings): https://arxiv.org/abs/2406.08979
- SWE-Bench Pro: https://arxiv.org/abs/2509.16941
- Self-Evolving MAC Networks (EvoMAC): https://arxiv.org/abs/2410.16946
- LLM-Based MAS for SE — Survey (TOSEM 2025): https://arxiv.org/abs/2404.04834

Five abstracts were WebFetch-verified (AgentGit, GCC, EvoGit, Collaborative Memory, Croto).
