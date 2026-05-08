# Enterprise / Team Adoption

Compiled from searches and WebFetch of:
- https://claude.com/blog/how-anthropic-teams-use-claude-code
- https://www.anthropic.com/engineering/building-c-compiler
- https://www.bvp.com/atlas/inside-shopifys-ai-first-engineering-playbook (search-surfaced)
- https://www.anthropic.com/research/how-ai-is-transforming-work-at-anthropic (search-surfaced)
- https://www.zenml.io/llmops-database/building-production-ai-agents-lessons-from-claude-code-and-enterprise-deployments (search-surfaced)

---

## Headline data

| Team / Company | Pattern | Impact |
|---|---|---|
| **Stripe** | Full rollout | 1,370 engineers. 10k-line Scala→Java migration in **4 days** (est. 10 engineer-weeks) |
| **Wiz** | Large migration | 50k-line Python→Go in **~20 hours** of active dev (est. 2–3 months manual) |
| **Ramp** | Incident investigation | Time cut by **80%** |
| **Shopify** | Multi-tool, centralized proxy | **20% productivity gain** across engineering (Farhan Thawar estimate) |
| **Anthropic Security** | Stack trace debugging | 10–15 min → 3–5 min (**3× faster**) |
| **Anthropic Inference** | Non-ML devs researching ML | 1 hr → 10–20 min (**80% research-time reduction**) |
| **Anthropic C-compiler experiment** | 16 parallel agents | 2 weeks, 2k sessions, $20k, 100k-line compiler building Linux 6.9 |

---

## Shopify — the AI-first playbook

### Stack strategy: don't standardize on one tool
Shopify engineers use *"Cursor, Claude Code, GitHub Copilot, OpenAI Codex, and experimental tools from Gemini"* in parallel.

### Infrastructure: centralize the LLM proxy
*"Every request from tools like Claude Code or Copilot flows through the proxy before reaching models from providers like OpenAI, Anthropic, or Google."*

### Why
- Single point for governance (auth, spend limits, audit)
- Tool choice stays at the individual engineer level
- Model provider choice stays at the platform layer
- Enables telemetry across tools

### Productivity: 20%
Farhan Thawar (VP & Head of Engineering). Not 10×; not marginal. Realistic team-scale number.

---

## Stripe — at-scale rollout

1,370 engineers. Mixed experience levels. Single migration (Scala→Java, 10k lines) completed in **4 days** by one team that estimated it as 10 engineer-weeks. This is a ~20× speedup on a migration, consistent with Wiz's 50k-line Python→Go in 20 hours vs. 2–3 months.

**Pattern inferred:** large cross-cutting migrations are where agent tooling shines, because the work is *parallelizable* (one file at a time), *repetitive* (same translation task over and over), and *verifiable* (tests catch regressions). This matches the Anthropic multi-agent post's framing of where multi-agent is economical: breadth-first parallelizable tasks.

---

## Anthropic internal — department-by-department

Full list in `anthropic.md`. Highlights relevant to team patterns:

- **Product Engineering:** Claude Code is *"first stop"* for any programming task.
- **Security:** test-driven development *guided by Claude* — *"design doc → janky code → give up on tests"* became *"design doc → tests → code"*.
- **Product Design:** Figma plugin — 100 ad variations in seconds.
- **Legal + Growth Marketing:** *non-engineering* teams building tools. Phone trees. CSV ad generators. This is the deepest sign of team penetration.

---

## Anthropic multi-agent C-compiler — team-scale pattern

The most concrete team-scale pattern in the corpus:

- **File-based locking** for multi-agent coordination. `current_tasks/` directory; agents write a lock file before picking up a task. No orchestrator.
- **Shared git repo** — each agent in its own Docker container pushes back upstream.
- **Natural specialization** — some agents own docs, some own quality, some own core features.
- **Human designs the environment, not the work:** *"I spent most effort designing the environment around Claude — the tests, the environment, the feedback — so that it could orient itself without me."*

---

## Governance patterns (synthesized from multiple sources)

### Shared CLAUDE.md
- Project CLAUDE.md checked into git.
- `~/.claude/CLAUDE.md` per engineer for personal preferences.
- Managed policy CLAUDE.md for org-wide rules (cannot be excluded by users).

### Permission modes
- `auto` mode with classifier for routine work.
- Allowlists for frequent safe tools.
- `--dangerously-skip-permissions` only inside a sandbox.
- Managed settings can enforce `allowManagedHooksOnly` to prevent user hooks from overriding org hooks.

### Skills as a registry
- `awesome-agent-skills`, `awesome-claude-skills`, `hesreallyhim/awesome-claude-code` are curated community lists.
- Anthropic, Google Labs, Vercel, Stripe, Cloudflare, Netlify, and others ship official skills.
- Pattern: skills become the *package manager* of agentic workflows.

### Hooks for attribution and permissions
- `PostToolUse` hooks that auto-attribute commits (`Co-Authored-By: Claude`).
- `PreToolUse` hooks that block writes to migration/infra paths.
- `SessionStart` hooks that inject recent context (e.g., last commit message).
- `UserPromptSubmit` hooks that expand shorthand aliases into full prompts.

### Plugins bundle all of the above
`/plugin` browses marketplace; plugins bundle skills + hooks + subagents + MCP into an installable unit. Team-authored plugins become the team's agentic standard.

### Cost and rate limiting
- Centralized LLM proxy (Shopify model) → per-team / per-user quotas.
- Token economy awareness: ~4× for single-agent, ~15× for multi-agent. Multi-agent only for valuable tasks.
- Non-interactive `claude -p` with `--allowedTools` for CI cost control.

---

## What breaks at team scale (and how teams mitigate)

| Break | Mitigation |
|---|---|
| One engineer's CLAUDE.md works; a new joiner's doesn't | Shared project `CLAUDE.md` + `/init` for new repos + skills |
| Conventions drift per engineer | Hooks (deterministic) vs. CLAUDE.md (advisory) |
| Inconsistent tool selection | Centralized proxy + managed settings |
| PR flood from agents | Writer/Reviewer pattern with second fresh-context agent |
| Attribution unclear | `Co-Authored-By: Claude` hook |
| Long sessions = high cost + low quality | Checkpoints + `/clear` + non-interactive fan-out for repetitive work |
| Security — secrets leaking into context | Hooks blocking file reads on `.env*` + managed policy |

---

## 3 team-practices we could adopt even as a solo dev

1. **A "team of one" CLAUDE.md repo.** Version-controlled global CLAUDE.md, skills, hooks. Symlinked into `~/.claude/`. Makes the config portable across machines and allows retroactive discovery of what worked when.

2. **Commit attribution hook.** `PostToolUse` on `git commit` appends `Co-Authored-By: Claude Opus 4.6`. Already standard practice at Anthropic; helps analytic retrospectives like our repo distinguish Claude-authored vs. human-authored changes.

3. **Skills library as our own "registry."** Adopt the community convention (`.claude/skills/<topic>/SKILL.md`), mirror `checkpoint` and `brief` there (already done), add a `review-diff` skill that runs our repo's own "diagnosis-vs-directive" and "running-code-read-only" checks against a pending change before commit. Makes the retrospective rules actually enforceable.
