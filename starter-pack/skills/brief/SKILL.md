---
name: brief
description: Expand a one-line task description into a full briefing-opener prompt for non-trivial work. Fills in project location, Python env, key files, prior attempts, non-goals, tool preferences, and the explicit ask. Interactive by default — asks for missing fields one at a time. Use when the user wants to open a session properly for something non-trivial, or says "/brief".
---

# /brief

Expand a one-line task description into a full briefing prompt following the template proven effective in the 2026 retrospective.

## Invocation

- `/brief <one-line task>` — interactive. Asks for missing fields.
- `/brief --quick <one-line task>` — one-shot. Emits the template with placeholders the user fills in.
- `/brief` with no argument — ask the user for the task headline first.

## Template shape

```markdown
# <Task headline — one sentence>

**Project location:** <absolute path>
**Python env:** <absolute path to .venv bin/python, or "n/a">

## Key files
- <path> — <what to know about it>
- <path> — <what to know about it>

## What I already tried (and why it's suspect)
- <attempt> — <why it didn't fully work>
- <attempt> — <why it didn't fully work>

## Non-goals
- <what NOT to do this session, e.g. "no dive-in — plan before code">

## Tool preferences (please echo these back)
- <e.g. "use the preview tool, not Chrome">
- <e.g. "don't auto-commit; stage and show me the diff">

## Ask
<the actual imperative — what you want done>
```

## Interactive behavior (default)

For each section, do this:

1. **Task headline:** if provided as the skill argument, use it. Otherwise ask.
2. **Project location:** auto-fill from `pwd`. Confirm with the user.
3. **Python env:** try `ls .venv/bin/python` or check `$VIRTUAL_ENV`. If nothing is found, ask. If not applicable (non-Python project), auto-fill `n/a`.
4. **Key files:** ask the user to list them. If the user says "you tell me", run a quick `ls` on the repo root and list candidates you see as important (CLAUDE.md, main entry points, config), and ask for confirmation.
5. **What I already tried:** ask the user. This is the highest-value section — push for specifics. "None yet" is a valid answer if the task is fresh.
6. **Non-goals:** ask. Default suggestion: `"no dive-in — plan before code"` for planning-heavy tasks, `"no new dependencies without asking"` for build tasks.
7. **Tool preferences:** ask. Suggest common ones (preview tool vs. Chrome, don't auto-commit, etc.).
8. **Ask:** the actual imperative. Push for verb-first phrasing.

After all fields are filled, emit the complete briefing as a single markdown block the user can copy/edit before pasting into a new session.

## Quick mode (`--quick`)

Emit the template with the task headline filled in and all other fields as placeholders. Do not ask questions. Let the user fill in the blanks.

## Formatting rules

- Always emit the final briefing as a single markdown block inside a fenced code-block-of-markdown so the user can copy it cleanly.
- Don't add sections beyond the template. Don't editorialize.
- Use absolute paths, not relative, in `Project location` and `Python env`.

## Rationale

From [`../../docs/lessons/what_worked.md`](../../docs/lessons/what_worked.md) and the four-lens retrospective: the briefing-opener is the load-bearing move of the year. All four analytical lenses independently named it as what converts exploration into shipping. This skill makes the proven shape one keystroke away.
