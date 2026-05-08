# Practitioner Write-ups — Agentic Coding Workflows

Compiled from WebFetch returns of:
- https://addyosmani.com/blog/agent-harness-engineering/
- https://addyo.substack.com/p/my-llm-coding-workflow-going-into
- https://simonwillison.net/2025/Apr/19/claude-code-best-practices/
- https://addyosmani.com/blog/self-improving-agents/

Plus search-surfaced references to:
- https://addyosmani.com/blog/code-agent-orchestra/
- https://addyosmani.com/blog/claude-code-agent-teams/
- https://addyo.substack.com/p/the-80-problem-in-agentic-coding
- https://druce.ai/2026/02/claude-code
- https://alexop.dev/posts/understanding-claude-code-full-stack/

---

## Addy Osmani — Agent Harness Engineering

> "The model is only half the system."
> "A decent model with a great harness beats a great model with a bad harness."

### 5 takeaways

1. **Treat failures as permanent signals.** *"Every line in a good AGENTS.md should be traceable back to a specific thing that went wrong."* Every agent mistake becomes an engineering constraint encoded into system prompts, hooks, or tool configurations. Don't retry — encode.

2. **The "skill issue" reframe.** *"It's not a model problem. It's a configuration problem."* (HumanLayer). Most failures are harness failures, not model failures.

3. **Filesystem + bash are the foundation.** Git gives durable state; shell access enables tool-on-the-fly.

4. **Hooks enforce silently. Success quiet, failures verbose.** Intercept mistakes before they compound.

5. **AGENTS.md / CLAUDE.md is highest-leverage.** Keep under 60 lines. Every line traceable to a real failure. Loads in every prompt and competes for attention.

### The ratchet principle
*"Each constraint is earned through failure, then systematically enforced."* Speculative rules don't survive; failure-derived rules do.

### Harnesses converge
*"Leading coding agents (Claude Code, Cursor, Aider, Cline) look more like each other than their underlying models do."* Best practices converge around context management, tool design, execution loops — not raw model capability.

---

## Addy Osmani — My LLM Coding Workflow Going Into 2026

### 7 concrete practices

1. **Planning before code** — iterative spec brainstorming until requirements are solid. Compile into `spec.md` with requirements, architecture, data models, test strategy. *"Waterfall in 15 minutes."*
2. **Break work into small chunks** — *"let's implement Step 1 from the plan"*, test, then Step 2. Prevents *"jumbled mess."*
3. **Extensive context upfront** — code, docs, constraints, preferred approaches. Tools: `gitingest`, `repo2txt` to bundle codebases into text for the LLM. Also explicitly state *"what not to focus on if something is out of scope (to save tokens)."*
4. **Multi-model strategy** — *"If one model gets stuck or gives mediocre outputs, try another."* Practices "model musical chairs." Gravitates toward Gemini but stays flexible.
5. **Rigorous human oversight** — treat AI output like a *"junior developer"* — read every snippet, run tests, exercise features manually. Secondary AI sessions review the first.
6. **Granular version control** — commit after each small task succeeds. Commits as *"save points in a game."* Git branches / worktrees isolate parallel experiments.
7. **Behavioral customization via `CLAUDE.md`** — style preferences, patterns, constraints. Reduces manual tweaking afterward.

> Core mindset: *"The LLM is an assistant, not an autonomously reliable coder."*

---

## Addy Osmani — Self-Improving Coding Agents

### 5 techniques

1. **Persistent knowledge files** — *"agents update AGENTS.md — discovered patterns are documented for future iterations."*
2. **Multi-channel memory persistence** — 4 channels: git history, progress logs, task-state files, AGENTS.md. *"Each improvement should make future improvements easier."*
3. **Real-time feedback correction** — *"Record this in AGENTS.md, then continue."* Corrections encoded in real-time.
4. **Quality assurance as a learning signal** — tests, type checks, linting. Failed tests become teaching moments: *"the loop knows the task isn't really done and can prompt the agent to fix the code."*
5. **Periodic refocusing to combat drift** — *"periodic fresh starts to combat drift and tunnel vision."* Re-scan codebase, update task list, maintain alignment.

---

## Simon Willison — "Claude Code: Best practices for agentic coding" (2025-04-19)

- Highlights Anthropic's extended-thinking keyword system.
- Investigated by deobfuscating the Claude Code JS package:
  - `think` → 4,000 tokens
  - `think hard` / `think harder` → 10,000 tokens
  - `ultrathink` → 31,999 tokens
- Treats it as an interesting architectural detail, not a prescriptive best practice.
- Context quality discussion: *"Quality tends to fall when context reaches approximately 50% full."*
- Emphasizes giving Claude the right context at the right time and clearing it between tasks.

---

## Other practitioner threads (from searches)

- **PLAN → WORK → REVIEW → COMPOUND** workflow: *Plan + Review = 80% of effort; Work + Compound = 20%.* Bottleneck is *"knowing what to build and verifying it was built correctly."*
- **Conditional context loading:** *"instead of dumping everything in CLAUDE.md, hooks let you load context only when working in specific directories."*
- **Skills vs hooks framing:** *"skills extend what Claude can do while hooks constrain how Claude does it."*
- **Addy Osmani on swarms/agent teams:** experimental Claude Code feature — lead agent + 3 teammates + shared task list with dependency tracking, peer-to-peer messaging, file locking.
- **Armin Ronacher:** runs Claude Code with `--dangerously-skip-permissions` — *"unlocks a huge amount of productivity"* (for use when trusted, paired with sandbox isolation).

---

## What's new vs. our corpus

**New to us:**
- The "ratchet principle" — explicit encoding of every failure
- Multi-channel memory (git + logs + task state + AGENTS.md) as deliberate persistence strategy
- "Model musical chairs" — trying the same prompt across providers
- `gitingest` / `repo2txt` tooling for bundling codebases as context
- Writer + Reviewer session pattern (also in Anthropic docs, reinforced here)
- Extended-thinking keyword tiers (think → ultrathink → 4k/10k/31,999 tokens)
- PLAN → WORK → REVIEW → COMPOUND as a phase model
- Conditional context loading via hooks
- `--dangerously-skip-permissions` + sandbox as a productivity unlock pair

**Confirming:**
- Plan before code — ubiquitous
- CLAUDE.md short + specific — universal
- Commit-as-save-point — matches our commit-as-quality-gate
- Treat AI like a junior dev — matches our "running code is read-only" rule

**Nuanced or contrary:**
- Our corpus favors a single high-density opener; practitioners favor brainstorming-then-`spec.md`. Both converge on "don't start coding cold."
- Osmani: *"commit after each small task succeeds."* We've treated commits as quality gates *at the end* of long sessions — bundling unrelated changes. The smaller-commit practice is better.
