# Anthropic Official — Multi-User + Multi-Agent Collaborative Coding

Source: the Anthropic-lens research agent from the 2026-04-24 dispatch. All URLs verified resolved at fetch time.

---

## 1. Concrete Patterns Anthropic Documents

### Pattern 1: Agent Teams with shared task list + mailbox (experimental)
One Claude session acts as lead and spawns peer teammates — each a full independent Claude Code instance — that coordinate via a shared task list and a messaging mailbox rather than reporting back through the lead.

> "Unlike subagents, which run within a single session and can only report back to the main agent, you can also interact with individual teammates directly without going through the lead." (`code.claude.com/docs/en/agent-teams`)

Architecture is explicit: **Team lead + Teammates + Task list + Mailbox**, stored at `~/.claude/teams/{team-name}/config.json` and `~/.claude/tasks/{team-name}/`. Gated behind `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`.

### Pattern 2: File-lock task claiming via git
Task claiming uses filesystem locks to prevent two agents grabbing the same work:

> "Task claiming uses file locking to prevent race conditions when multiple teammates try to claim the same task simultaneously." (`code.claude.com/docs/en/agent-teams`)

The C-compiler post documents the raw primitive outside the agent-team system:

> "Claude takes a 'lock' on a task by writing a text file to current_tasks/ … If two agents try to claim the same task, git's synchronization forces the second agent to pick a different one." (`anthropic.com/engineering/building-c-compiler`)

> "Claude works on the task, then pulls from upstream, merges changes from other agents, pushes its changes, and removes the lock. Merge conflicts are frequent, but Claude is smart enough to figure that out." (same source)

### Pattern 3: Git worktrees for physical isolation between concurrent sessions
Desktop auto-creates a worktree per session so concurrent humans/agents don't stomp each other:

> "For Git repositories, each session gets its own isolated copy of your project using Git worktrees, so changes in one session don't affect other sessions until you commit them." (`code.claude.com/docs/en/desktop`)

### Pattern 4: Repo-committed config as the shared team substrate
Cloud sessions only see what's committed. User-level config does NOT propagate to teammates or cloud runs — `.claude/` in the repo is the multi-user coordination layer:

> "Your user `~/.claude/CLAUDE.md` … Lives on your machine, not in the repo" (not available in cloud). `.claude/settings.json`, `.claude/skills/`, `.claude/agents/`, `.claude/commands/`, and `.mcp.json` **are** available because they're "Part of the clone." (`code.claude.com/docs/en/claude-code-on-the-web`)

### Pattern 5: Plugin marketplaces as the team skill-distribution primitive
Plugins (vs. standalone `.claude/`) exist specifically for sharing across humans:

> "Use plugins when: You want to share functionality with your team or community … You're distributing through a marketplace." (`code.claude.com/docs/en/plugins`)

Plugins are namespaced (`/my-plugin:hello`) to avoid collisions across authors, and versioned so "users only receive updates when you bump this field."

### Pattern 6: Subagent definitions as reusable teammate roles
A single subagent spec (e.g. `security-reviewer`) can be invoked either as a one-shot subagent OR spawned as a long-lived teammate, letting a team author one role library:

> "This lets you define a role once, such as a security-reviewer or test-runner, and reuse it both as a delegated subagent and as an agent team teammate." (`code.claude.com/docs/en/agent-teams`)

### Pattern 7: Orchestrator-worker with clear boundaries (NOT peer chat)
The research-system post documents the dominant pattern for multi-agent — explicit delegation, not free-form peer collaboration:

> "a lead agent coordinates the process while delegating to specialized subagents that operate in parallel" and "Each subagent needs an objective, an output format, guidance on the tools and sources to use, and clear task boundaries" (`anthropic.com/engineering/built-multi-agent-research-system`)

They explicitly note synchronous limits: *"the lead agent can't steer subagents, subagents can't coordinate"* mid-run.

---

## 2. What's Explicitly Scoped Out

- **Real-time collaborative cursors / Google-Docs-style co-editing** — never documented. Sharing is snapshot-based: *"Recipients see the latest state when they open the link, but their view doesn't update in real time."* (`claude-code-on-the-web`)
- **Cross-session peer messaging between humans** — `/teleport` is one-way session hand-off, not live co-presence.
- **Nested/recursive teams** — *"teammates cannot spawn their own teams or teammates. Only the lead can manage the team."* (`agent-teams`)
- **Leadership transfer** — *"the session that creates the team is the lead for its lifetime."*
- **Per-teammate permissions at spawn** — *"all teammates start with the lead's permission mode."*
- **Session resumption for in-process teammates** — `/resume` and `/rewind` don't restore them.
- **Shared secrets store for cloud/team sessions** — *"A dedicated secrets store is not yet available."*

---

## 3. Three Ideas for a 2-3 Human Team

1. **Commit a shared role library** to `.claude/agents/` (e.g. `reviewer.md`, `migration-planner.md`). Any teammate can spawn them as subagents OR agent-team teammates — single source of truth, version-controlled, same config any human picks up.

2. **Adopt the C-compiler file-lock pattern** for overnight/background multi-agent runs: a `current_tasks/` directory of `.txt` lock files, committed/pushed as the sync primitive. Durable, git-native, survives across humans and machines.

3. **Publish an internal plugin marketplace** (git repo) for team-specific skills + hooks. Namespacing (`/acme:deploy`) prevents collisions with personal skills, and `version` in `plugin.json` gates rollouts so one human's skill change doesn't silently rewire everyone's agents.

---

## 4. Citations

- https://code.claude.com/docs/en/agent-teams
- https://code.claude.com/docs/en/claude-code-on-the-web
- https://code.claude.com/docs/en/desktop
- https://code.claude.com/docs/en/plugins
- https://www.anthropic.com/engineering/building-c-compiler
- https://www.anthropic.com/engineering/built-multi-agent-research-system
