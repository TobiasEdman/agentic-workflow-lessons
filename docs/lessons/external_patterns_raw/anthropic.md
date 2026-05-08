# Anthropic Official — Agentic Workflow Guidance

Compiled from direct WebFetch returns of:
- https://code.claude.com/docs/en/best-practices
- https://code.claude.com/docs/en/memory
- https://code.claude.com/docs/en/sub-agents
- https://code.claude.com/docs/en/hooks
- https://www.anthropic.com/engineering/built-multi-agent-research-system
- https://www.anthropic.com/engineering/building-c-compiler
- https://claude.com/blog/how-anthropic-teams-use-claude-code

---

## Patterns Anthropic emphasizes

### 1. Verification is the single highest-leverage move
> "Include tests, screenshots, or expected outputs so Claude can check itself. This is the single highest-leverage thing you can do." — Best Practices

Rewrite prompts to include test cases. For UI, paste screenshots and ask Claude to compare. For bugs, ask it to reproduce first, then fix. *This is stated in the Best Practices guide as the most important single move.*

### 2. Explore → Plan → Implement → Commit (Plan Mode)
Four-phase workflow. Plan Mode keeps Claude read-only during exploration/planning. Press `Ctrl+G` to edit the plan directly before execution. Skip planning only when the diff fits in one sentence.

### 3. "Give Claude a way to verify its work"
Tests, linters, shell commands, screenshots. Without verification, the human is the only feedback loop and every mistake requires human attention. `Claude in Chrome` extension handles UI iteration automatically.

### 4. CLAUDE.md conventions
Short (< 200 lines), specific, prunable. Loads into every session and consumes context — bloat reduces adherence. Four placement scopes:

| Scope | Path | Purpose |
|---|---|---|
| Managed policy | `/Library/Application Support/ClaudeCode/CLAUDE.md` | Org-wide, cannot be excluded |
| Project instructions | `./CLAUDE.md` or `./.claude/CLAUDE.md` | Team-shared, committed to git |
| User | `~/.claude/CLAUDE.md` | Personal, all projects |
| Local | `./CLAUDE.local.md` | Personal per-project, gitignored |

Quote: *"For each line, ask: Would removing this cause Claude to make mistakes? If not, cut it. Bloated CLAUDE.md files cause Claude to ignore your actual instructions!"*

Imports via `@path/to/file.md` — max depth 5. `CLAUDE.md` is appended to by `CLAUDE.local.md` at the same level.

### 5. Skills vs. Rules vs. Hooks
Sharp distinction:

- **CLAUDE.md / rules** — advisory context, always loaded, may be ignored
- **Skills** — on-demand workflows (`.claude/skills/<name>/SKILL.md`). Load only when Claude decides they're relevant or user invokes `/name`
- **Hooks** — deterministic shell/HTTP/MCP scripts at lifecycle events. **Cannot be bypassed.** Use for "actions that must happen every time with zero exceptions."
- **Subagents** (`.claude/agents/`) — isolated context + scoped tools, delegated to

Quote: *"Skills extend what Claude can do while hooks constrain how Claude does it."*

### 6. Path-scoped rules `.claude/rules/<topic>.md`
Frontmatter `paths: ["src/api/**/*.ts"]` means rule only loads when Claude reads matching files. Keeps context lean in large repos. Can be symlinked across projects for shared conventions.

### 7. Auto memory (v2.1.59+)
Claude writes its own notes to `~/.claude/projects/<project>/memory/MEMORY.md`. First 200 lines / 25 KB loaded every session. Topic files (`debugging.md`, `patterns.md`) loaded on demand. Toggle with `/memory` or `autoMemoryEnabled`.

Quote: *"CLAUDE.md files are you writing them; auto memory is Claude writing them."*

### 8. Context management discipline
- `/clear` between unrelated tasks
- `/compact <instructions>` for targeted summarization
- `Esc + Esc` or `/rewind` — restore checkpoint
- `/btw` — side questions that don't enter context
- Subagent delegation for investigation: *"one of the most powerful tools available. When Claude researches a codebase it reads lots of files, all of which consume your context."*

### 9. Hooks for deterministic enforcement
Events: `SessionStart`, `SessionEnd`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `Stop`, `FileChanged`, `InstructionsLoaded`. Handler types: command (shell), HTTP endpoint, MCP tool, prompt, spawned agent. Exit code 2 = blocking error.

Example hook for blocking `rm *` in Bash tool given in docs.

### 10. Interview-driven spec
> "Interview me in detail using the AskUserQuestion tool. Ask about technical implementation, UI/UX, edge cases, concerns, and tradeoffs. Don't ask obvious questions, dig into the hard parts I might not have considered. Keep interviewing until we've covered everything, then write a complete spec to SPEC.md."

Fresh session executes the spec.

### 11. Non-interactive mode for automation
`claude -p "prompt"` with `--output-format json | stream-json`. Used in CI, pre-commit hooks, fan-out scripts. `--allowedTools` scopes permissions in unattended runs.

### 12. Fan-out across files
For large migrations: generate task list → bash loop calling `claude -p` per file → test on 2–3 → scale. Pattern used by Stripe for a 10k-line Scala-to-Java migration in 4 days.

### 13. Writer / Reviewer parallel sessions
One Claude writes, a second Claude reviews with fresh context (no bias toward code it just wrote). Same pattern works for tests-first: Claude A writes failing tests, Claude B writes code to pass them.

### 14. Auto mode (`--permission-mode auto`)
Classifier model reviews each command. Blocks scope escalation, unknown infrastructure, hostile-content-driven actions. Lets routine work proceed without prompts. For `-p` runs, aborts if classifier repeatedly blocks.

---

## From "How we built our multi-agent research system"

### Scale rules
- 1 agent for fact-finding with 3–10 tool calls
- 2–4 agents for comparisons
- 10+ for complex research with divided responsibilities

### Parallel tool calling cut research time by up to 90%
Two levels: (a) multiple subagents in parallel, (b) each subagent calls 3+ tools in parallel.

### Token economy
- Agent interactions use ~4× chat tokens
- Multi-agent systems use ~15× chat tokens
- Only economical when task value justifies the spend

### Eval with 20 test cases, not hundreds
> "We started with a set of about 20 queries... testing these queries often allowed us to clearly see the impact of changes."

### When multi-agent shines vs. fails
> "Multi-agent systems excel at valuable tasks that involve heavy parallelization, information that exceeds single context windows."

Fails on tight interdependencies — coding tasks where agents need shared context and real-time coordination.

### Extended thinking as controllable scratchpad
Lead agent uses extended thinking to plan strategy. Subagents use interleaved thinking after tool results.

---

## From "Building a C compiler with parallel Claudes"

- 16 Claude Opus 4.6 agents, ~2,000 sessions, 2B input tokens, $20,000, 2 weeks → 100k-line Rust-based C compiler that builds Linux 6.9.
- **File-based locking**: `current_tasks/` directory. Claude takes a lock by writing a file. No orchestrator needed.
- Each agent in its own Docker container cloning a shared repo.
- Specialization emerged naturally (core compilation, docs, quality, specialized sub-tasks).
- **Nicholas Carlini's lessons:**
  1. *"It's important that the task verifier is nearly perfect, otherwise Claude will solve the wrong problem."*
  2. Manage context: avoid dumping thousands of useless bytes into test output; log important info to files.
  3. Design around "time blindness" — agents will happily spend hours on tests. Sample 1% or 10% to make progress.
  4. Structure work for parallelism. For monolithic tasks, use external tools as known-good oracles to enable parallel progress.
- *"I spent most effort designing the environment around Claude — the tests, the environment, the feedback — so that it could orient itself without me."*

---

## From "How Anthropic teams use Claude Code"

Concrete patterns per team:

- **Infrastructure / onboarding:** new data scientists feed entire codebases; Claude reads CLAUDE.md, maps data-pipeline dependencies, replaces the data catalog.
- **Product Engineering:** *"first stop for any programming task."* Files identified before manual context-gathering.
- **Security Engineering:** 10–15 min debugging now 3–5 min (3× speedup) by feeding stack traces for control-flow tracing. Switched to test-driven development guided by Claude.
- **Data Infrastructure:** solved K8s scheduling failure by feeding dashboard screenshots — Claude guided them through Google Cloud UI until IP exhaustion was identified.
- **Product Design:** Figma files → Claude writes features, runs tests, iterates autonomously.
- **Inference (non-ML devs):** 1 hour of Google searches → 10–20 min with Claude explaining model-specific functions. 80% research-time reduction.
- **Growth Marketing (non-eng):** agentic CSV workflow — *"hundreds of new ads in minutes instead of hours."* Figma plugin for 100 ad variations in seconds.
- **Legal (non-eng):** prototype phone-tree for lawyer routing.

**Enterprise customer case studies:**
- **Stripe:** 1,370 engineers, 10k-line Scala-to-Java migration in 4 days (est. 10 engineer-weeks).
- **Ramp:** incident investigation time cut 80%.
- **Wiz:** 50k-line Python→Go migration in ~20 hours of active dev (est. 2–3 months manual).

---

## What's new vs. what our corpus already captured

**New to us:**
- Auto memory (`~/.claude/projects/.../memory/MEMORY.md`) — we have CLAUDE.md-style persistence but haven't leveraged auto memory
- Path-scoped rules `.claude/rules/<topic>.md` with `paths:` frontmatter
- `/btw` for side questions outside context
- `--permission-mode auto` with classifier
- `--append-system-prompt` for scripted enforcement
- `/rewind` + `Esc+Esc` checkpoint-restore semantics
- Interview-driven spec opener (AskUserQuestion-based)
- File-based locking pattern for multi-agent coordination (from C-compiler post)
- Extended thinking budget tiers (think / think hard / think harder / ultrathink → 4k / 10k / 10k / 31,999 tokens per Simon Willison)

**Confirming what we have:**
- Briefing opener → matches Anthropic's "provide specific context", "explore first, then plan"
- STOP / Esc → `Esc` is the canonical interrupt; `/clear` for hard reset after 2+ failed corrections
- Parallel subagents → confirmed + quantified (90% research-time reduction)
- Commit-as-quality-gate → matches Plan → Implement → Commit flow

**Nuanced:**
- We favor heavy briefing openers. Anthropic is more conditional: *"Plan mode is useful but also adds overhead. For tasks where the scope is clear and the fix is small, ask Claude to do it directly."* Worth adopting: skip plan mode for one-sentence-diff tasks.
- Our "diagnosis-read-as-directive" pitfall isn't named by Anthropic — but their "provide specific context" guidance addresses the adjacent failure. Ours is a more specific observation that deserves to stay.
