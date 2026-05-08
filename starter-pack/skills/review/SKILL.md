---
name: review
description: Spawn a fresh-context reviewer subagent to critique a recent change without bias toward code the main session just wrote. Use after implementing a non-trivial change, before committing, or on any diff you want a second pair of eyes on. Default scope is the latest commit; can be invoked against a range (HEAD~3..HEAD) or a specific file.
---

# /review

Implements the writer/reviewer pattern documented across all four lenses of the multi-user-multi-agent research sweep. A fresh-context subagent reviews a recent change with no bias toward the code the main session just produced.

## Why this skill exists

From [`../../docs/lessons/multi_user_multi_agent.md`](../../docs/lessons/multi_user_multi_agent.md) §C4:

> Agent-on-agent review is the emerging first-line quality gate. Cloudflare ran 131,246 review-agent runs across 48,095 MRs in one month, averaging 2.7 reviews per MR. Anthropic's Agent Teams docs recommend spawning 3–5 reviewers each with a different lens.

The value is the **fresh context**: a reviewer that didn't author the code catches failure modes the author can't see.

## Invocation

- `/review` — review the latest commit (`HEAD`) against its parent.
- `/review HEAD~3..HEAD` — review a range of commits.
- `/review path/to/file.py` — review a specific file (regardless of git state).
- `/review --staged` — review staged changes (before commit).

## What to do

1. **Determine the target.** Parse the argument:
   - No arg → `git log -1` — name and SHA of the latest commit.
   - Range `A..B` → the diff between those refs.
   - File path → just that file.
   - `--staged` → `git diff --cached`.

2. **Collect context.** Gather:
   - The diff (`git diff <range>` or `git show <sha>`).
   - The CLAUDE.md + any relevant `.claude/rules/*.md` files in the current repo.
   - The project's test command if present (from CLAUDE.md / Makefile / package.json).
   - For file-path mode, read the full file + 1-line context on each imported module.

3. **Dispatch a subagent** using the Agent tool with `subagent_type: "general-purpose"` (or `"Explore"` if the review is read-heavy). Prompt the subagent like this:

   > You are reviewing a change you did NOT author. Your main job is to catch what the author missed.
   >
   > **Change under review:**
   > ```
   > <diff or file contents>
   > ```
   >
   > **Repository conventions (from CLAUDE.md):**
   > `<relevant excerpts — don't paste the whole file, just the rules that apply to this change>`
   >
   > **Review checklist:**
   > - Edge cases: what inputs would break this? Empty, null, unicode, concurrent, very large?
   > - Error handling: are failures caught and handled, or do they bubble up uncaught?
   > - Race conditions / concurrency: any shared state, file writes, or network calls without proper sequencing?
   > - Consistency with existing patterns: does this match how similar code in this repo is written? If not, should it?
   > - Missing tests: what tests are absent that would prove this works?
   > - Security: any input that could be user-controlled and reach a sink (shell, SQL, deserialisation, file path)?
   > - CLAUDE.md rule violations: does this break any repo-level rule?
   > - Readability: would another engineer understand this in a month without you there to explain?
   >
   > **Output format:**
   > Group findings by severity: `BLOCKER` (must fix before commit) / `WARNING` (should fix but not blocking) / `NIT` (style / small improvement) / `PRAISE` (something notably well done).
   >
   > For each finding: file:line + 1-2 sentences + suggested action.
   >
   > End with a one-line verdict: `LGTM` / `LGTM with nits` / `needs changes`.
   >
   > Do not modify any files. This is a read-only review.

4. **Present the review to the user.** Don't auto-apply any suggestions. The main session's job is to implement; this skill's job is to surface the findings.

5. **Ask the user** what to do with each BLOCKER/WARNING: fix, defer, or dismiss with reason. Fixes happen in the main session; the reviewer subagent does not touch code.

## Variants (optional flags)

- `/review --lens=security` — replace the full checklist with security-only focus (injections, auth, secrets, crypto).
- `/review --lens=performance` — focus on hot paths, N+1, memory growth, unbounded loops.
- `/review --lens=tests` — focus on test coverage gaps and flaky-test risks.

These map to the Cloudflare/Anthropic multi-lens pattern (one reviewer per aspect).

## What NOT to do

- Don't modify files — this skill is read-only.
- Don't pass the full CLAUDE.md to the reviewer — excerpts only, or context bloats.
- Don't auto-accept reviewer suggestions. Present them; wait for user decision.
- Don't run the reviewer against huge diffs (>2000 lines) without confirming with the user — cost and quality degrade.
- Don't substitute for a human review on sensitive code (auth, secrets, migrations, infra).

## Rationale

From [`../../docs/lessons/multi_user_multi_agent.md`](../../docs/lessons/multi_user_multi_agent.md) Tier 2 recommendation #4:

> Every PR authored by Person A's agent gets reviewed by a project-scoped reviewer subagent run from Person B's session (or via Claude Code's Code Review action) before human review. Combined with a plan-approval gate for anything touching a directory not owned by the PR author. Keeps verification distributed.

For a solo developer, the second human is replaced by the fresh-context subagent. Same effect: bias-free critique.
