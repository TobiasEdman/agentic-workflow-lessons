# Enterprise Lens — Multi-User + Multi-Agent Collaborative Coding

Source: the enterprise-lens research agent from the 2026-04-24 dispatch.

> Method caveat: `claude.com/customers` WebFetch returned only navigation HTML. Pragmatic Engineer + VS Code blog fetches denied; those claims come from search snippets, not full-page reads.

---

## 1. Seven enterprise patterns at scale

1. **Lead-and-teammates orchestration.** One developer runs a *"team lead"* session that spawns 3–5 independent teammate sessions, each with its own context window, coordinating via a shared task list and mailbox. Claude Code formalized this as `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` in v2.1.32 (Feb 2026). Typical sizing: 3–5 teammates, 5–6 tasks each; beyond that, coordination overhead dominates.

2. **Multi-lens parallel review.** Instead of one reviewer, teams spawn specialized reviewer agents (security, performance, test coverage) against the same PR. **Cloudflare ran 131,246 review runs across 48,095 MRs in 5,169 repos in one month**, median 3m39s, averaging 2.7 reviews per MR.

3. **Adversarial debate / competing hypotheses.** For bug triage, teams spawn ~5 investigators each defending a different theory and trying to disprove each other — explicitly countering anchoring bias from single-agent investigation.

4. **Plan-gated teammates.** High-risk refactors force a teammate to stay in read-only plan mode until the lead approves; the lead enforces criteria like *"reject plans that modify the DB schema."*

5. **Parallel execution vs. sequential critique.** Shopify runs two modes: **10 agents in parallel** with a human merge gatekeeper, or **45+ minute sequential critique loops** with multi-model interrogation.

6. **Composable plugin-based review pipelines.** Cloudflare's reviewer is built so plugins register agents, inject prompt sections, and set fine-grained permissions — GitLab and Cloudflare AI Gateway plugins can't see each other's secrets.

7. **Quality gates via hooks.** `TeammateIdle`, `TaskCreated`, and `TaskCompleted` hooks exit with code 2 to force more work or block completion — the team's lint/test/policy layer lives outside the model.

---

## 2. Governance of shared configs, skills, and CLAUDE.md

- **CLAUDE.md is the canonical shared context.** Teammates automatically load `CLAUDE.md`, MCP servers, and skills on spawn but do **NOT** inherit the lead's conversation. Well-structured module boundaries + verification commands radically cut per-teammate exploration cost.
- **Reusable roles via subagent definitions.** Security-reviewer, test-runner, etc. defined once (project / user / plugin / CLI scope) and reused as teammates. Their `tools` allowlist and `model` are honored; their body is appended (not replaced) to the system prompt.
- **Team state lives in `~/.claude/teams/{team-name}/config.json`** and `~/.claude/tasks/{team-name}/` — generated/owned by the harness; hand-editing is overwritten. Deliberately **no project-level team config**.
- **Shopify-style centralized control plane.** A platform team maintains an LLM proxy that does bulk token purchasing, per-team/project usage tracking, spend alerts, model routing across Claude Code + Copilot + others, and exposes 13+ MCP servers (Backstage, GitLab, Jira, Sentry, Prometheus, Google Workspace) in a single monorepo with shared auth.

---

## 3. Security and attribution when agents review agents

- **Permissions inherit at spawn.** Teammates start with the lead's permission mode — if the lead has `--dangerously-skip-permissions`, so does every teammate. You can tighten per-teammate modes later but **not at spawn**.
- **Commit authorship is the load-bearing problem.** GitHub Copilot's cloud agent sets the commit author to Copilot on squash-merge, breaking `git blame` for the requesting human. Community guidance (Apr 2026): use signed commits for execution-identity, set the requesting human as author, capture the agent with `Co-authored-by:` trailers so attribution stays searchable.
- **"Alice's reviewer agent commenting on Bob's implementer agent"** — the emerging norm:
  - (a) reviewer comments are attributed to the **invoking human** with the agent identity in metadata
  - (b) the code remains owned by the human who merged it
  - (c) signed commits prove which agent identity path executed, while policy controls (branch protection, required human review) handle correctness

---

## 4. Proxies, rate limits, observability

- **Shopify's LLM proxy** is the canonical pattern: single gateway for all AI traffic, bulk token buying, per-team quotas, spend alerts, usage analytics, model flexibility.
- **Cloudflare's AI Gateway** is used the same way inside their internal AI Engineering stack.
- **Token cost scales linearly** with teammate count — docs explicitly warn that routine tasks are cheaper on a single session.
- **Observability:** split-pane (tmux / iTerm2) mode gives simultaneous live terminals; in-process mode cycles via Shift+Down; task-list + mailbox are inspectable artifacts on disk.

---

## 5. Three ideas applicable to a 2–3 person team

1. **Check a shared `CLAUDE.md` + `.claude/agents/` (subagent defs) into the repo.** Define `security-reviewer`, `test-writer`, `migration-planner` once; every teammate on every developer's machine spawns with the same role, model, and tool allowlist.

2. **Standardize attribution at the git layer.** Require signed commits, set real human as `author`, auto-inject `Co-authored-by: Claude <...>` trailers. ~30 minutes to wire up; keeps `git blame` honest.

3. **Install one shared hook (`TaskCompleted` or pre-commit)** that runs your lint/test/typecheck and blocks completion on failure. Cheapest way to get "agent reviewing agent" quality without running a second reviewer session.

---

## Sources

- https://code.claude.com/docs/en/agent-teams
- https://blog.cloudflare.com/ai-code-review/
- https://blog.cloudflare.com/internal-ai-engineering-stack/
- https://www.bvp.com/atlas/inside-shopifys-ai-first-engineering-playbook
- https://newsletter.pragmaticengineer.com/p/how-ai-is-changing-software-engineering
- https://code.visualstudio.com/blogs/2026/02/05/multi-agent-development
- https://addyosmani.com/blog/claude-code-agent-teams/
- https://docs.gitlab.com/user/duo_agent_platform/flows/foundational_flows/code_review/
- https://vercel.com/docs/agent/pr-review
- https://expertbeacon.com/signed-commits-in-github-copilot-cloud-agent-what-verification-proves-and-what-it-doesnt/
- https://github.com/orgs/community/discussions/184395
