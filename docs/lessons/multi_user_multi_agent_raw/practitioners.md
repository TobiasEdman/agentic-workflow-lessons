# Practitioner Write-ups — Multi-User + Multi-Agent Collaborative Coding

Source: the practitioner-lens research agent from the 2026-04-24 dispatch.

> Method caveat from the agent: WebFetch was denied for some sources (Simon Willison's Substack post, HN thread 47313787, claudecode.run, The New Stack article, MindStudio post). Claims tied solely to those URLs are based on search-result summaries only. The agent also flagged and ignored a prompt-injection attempt embedded in one fetched page.

---

## Opening framing

Solo agentic coding is well-covered; team + team coordination is earlier-stage. Most documented practice today is still "one human, N agents." Where 2+ humans each bring their own fleet, practitioners are improvising on top of existing DVCS and task infrastructure.

---

## 1. Concrete patterns practitioners report

1. **Branch-/worktree-per-agent as the default isolation primitive.** Every source converges. Addy Osmani's orchestra piece: *"Git worktrees provide isolation… Each agent receives its own worktree and branch, eliminating merge conflicts during parallel work."* Anthropic points new users to the same pattern under *"Run parallel Claude Code sessions with Git worktrees."*

2. **Shared task list as the synchronization primitive across agents (and, by extension, humans).** Anthropic's Agent Teams docs: a shared task list with pending/in-progress/completed states, dependency tracking, and self-claim. *"Task claiming uses file locking to prevent race conditions."* Osmani generalizes this to `tasks.json` plus git history as "external memory" in the Ralph Loop pattern.

3. **File-scope ownership per agent (soft locks via convention).** Both Osmani pieces and Anthropic's "Avoid file conflicts" section: *"Two teammates editing the same file leads to overwrites. Break the work so each teammate owns a different set of files."* In multi-human setups this extends to **directory ownership per person/fleet**.

4. **Agent-authored PR, reviewed by a different agent persona.** Osmani's orchestra post describes *"dedicated reviewer agents using read-only access"* and a three-tier stack (in-process, local orchestrators, cloud-async) where the cloud tier is *"fire-and-forget delegation, PR generation."* The New Stack and Anthropic's Code Review product add 1-click 👍/👎 feedback on agent comments — humans still adjudicate, but agents do first-pass review.

5. **Competing-hypothesis / adversarial review teams.** Anthropic's agent-teams docs: spawn 3–5 reviewers each with a different lens (security, perf, tests) or adversarial debuggers trying to disprove each other's theories. Maps onto multi-human: each person owns a lens.

6. **Plan-approval gates before implementation.** Anthropic: teammates can be kept in read-only plan mode until the lead approves. Osmani calls this *"Plan approval before implementation"* as a quality gate. Translates to cross-human approval when Person A's agent proposes a change to Person B's area.

7. **Hooks as team policy enforcement.** `TaskCreated` / `TaskCompleted` / `TeammateIdle` hooks (Anthropic docs) let a team encode rules (e.g. tests must pass before completion) that apply to every human's agents.

8. **Hierarchical decomposition (lead → feature leads → specialists).** Osmani: *"Spawn feature leads that spawn their own specialists… 3× deeper decomposition without exploding anyone's context window."* In a 2-3 person team, each human plays "feature lead" for one area.

---

## 2. Friction points practitioners report

- **Who reviews AI code when everyone uses AI?** Osmani: *"Verification is the constraint, not generation."* Agents produce faster than humans audit. The New Stack normalizes *agent reviewers* as a layer, but ultimate accountability still sits with humans.

- **Conflicts between agents from different humans editing the same file.** Osmani: *"workspace isolation (each agent works on its own git branch), but manual integration often falls to humans."* **No mature cross-human-agent merge bot exists yet** in the sources.

- **Context awareness gaps.** Agents on large codebases *"miss constraints outside their view"* — acutely worse when Person B's changes aren't yet on main.

- **Specification quality multiplies.** *"Vague requirements multiply errors across parallel runs."* In a 2-person team, each person's spec sloppiness infects the other's agents.

- **Understanding loss.** *"If you lose understanding of your own system, you have lost the ability to fix it."* Compounding when no single human has read all agent output.

- **Coordination overhead.** Anthropic: *"more teammates means more communication… and potential for conflicts"* — diminishing returns past ~5.

- **Experimental-feature limitations.** Agent Teams today: one team per session, no nested teams, no leadership transfer, fixed lead — so cross-human teams can't natively merge into one super-team.

---

## 3. Tooling

- **Anthropic Agent Teams** (experimental, `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`): shared task list, mailbox messaging, file-locked task claim, hooks, split-pane via tmux/iTerm2. Storage at `~/.claude/teams/` and `~/.claude/tasks/` — local, not multi-user natively.
- **Local orchestrators** (Osmani): Conductor (parallel agents + visual diff review), Vibe Kanban (task board with in-board diffs), OpenClaw/Antfarm (Ralph Loop).
- **Cloud async**: Claude Code Web, Copilot Coding Agent — PRs as the shared surface.
- **Shared memory**: human-curated `AGENTS.md` / `CLAUDE.md`. Osmani notes LLM-authored versions hurt success by ~3% and cost by 20%. **"Beads"** (immutable git-backed decision records) as an alternative to vector RAG.
- **Git itself** remains the real multi-user substrate: branches, PRs, issues, CI. Osmani: orchestrator tools *"produce persistent artifacts… preserved in version control."*
- **MCP servers**: mentioned as the integration layer but sources don't document a canonical multi-user MCP broker yet.
- **Subagent definitions** reusable across humans (project-scoped `.claude/agents/*.md`) give teams a shared library of reviewer/tester roles.

---

## 4. Three concrete adoption ideas for a 2–3 person team

1. **Directory ownership + branch-per-agent + shared `AGENTS.md`.** Each human owns a top-level directory; their agents run in per-task git worktrees. A human-curated `AGENTS.md` at repo root + per-directory `CLAUDE.md` files encode ownership and invariants. Cheapest; no new tools.

2. **Issue tracker as the inter-human task board; Agent Teams as the intra-human coordinator.** GitHub Issues / Linear is the multi-human queue; each human's agent team claims an issue and spawns its own shared task list locally. Agents post progress back to the issue. PRs are the integration point.

3. **Mandatory cross-fleet reviewer agent on every PR.** Every PR authored by Person A's agent gets reviewed by a project-scoped reviewer subagent run from Person B's session (or via Claude Code's Code Review action) before human review. Combined with a plan-approval gate for anything touching a directory not owned by the PR author. Keeps verification distributed.

---

## 5. Citations

- https://addyosmani.com/blog/claude-code-agent-teams/
- https://addyosmani.com/blog/code-agent-orchestra/
- https://addyosmani.com/blog/future-agentic-coding/
- https://code.claude.com/docs/en/agent-teams
- https://news.ycombinator.com/item?id=47313787
- https://thenewstack.io/ai-coding-tool-stack/
- https://simonw.substack.com/p/agentic-engineering-patterns
- https://www.mindstudio.ai/blog/claude-code-agent-teams-parallel-workflows

---

## Notes

> Explicit **multi-user + multi-agent** (as opposed to single-user multi-agent) practice is under-documented in the 2026 sources reachable. Most patterns extend naturally to multi-user via existing DVCS/issue-tracker infrastructure, rather than purpose-built multi-human-multi-agent tooling.
