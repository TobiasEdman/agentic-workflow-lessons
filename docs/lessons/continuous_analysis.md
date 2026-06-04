# Continuous analysis — how the workflow learns from itself

> Built 2026-05-12 in response to the question *"can you build a structure that continuously analyzes and learns from our sessions?"*. Passive by design: writes alerts, never acts. The agentic part is when you (the user) read them and decide what to do.

## What it is

A four-piece system that turns the JSONL session store into a self-monitoring loop:

| Piece | What it does | When it runs |
|---|---|---|
| **`scripts/detect_patterns.py`** | Walks `~/.claude/projects/*.jsonl`, applies 13 deterministic rules across four categories, emits findings | On every checkpoint write + every daily drift run |
| **`scripts/daily_drift.py`** | Snapshots corpus state, diffs against yesterday's snapshot, emits a per-day report. Invokes `detect_patterns.py` at the end | Once a day via scheduled-tasks |
| **`~/.claude/hooks/checkpoint-pattern-scan.sh`** | PostToolUse on Write to `~/.claude/checkpoints/`. Re-runs `detect_patterns.py` in the background | Every time `/checkpoint` writes a snapshot |
| **`mcp__scheduled-tasks` task `daily-drift-agentic-workflow`** | Fires `daily_drift.py` at 07:27 AM local, daily | Cron-driven |

## What it produces

```
agentic_workflow/
├── analysis/
│   ├── daily/<YYYY-MM-DD>.md      ← read this first thing in the morning
│   ├── corpus/<YYYY-MM-DD>.json   ← machine-readable snapshots, kept as history
│   └── patterns/
│       ├── _summary.md            ← human summary of all rule hits, grouped by category
│       └── <rule-name>.jsonl      ← one line per finding, machine-readable
```

The daily report concatenates volume drift + repo-set diff + skill diff + the pattern summary. It is the one file to read.

## The 13 rules, by category

### Continuity (5 rules)

| Rule | Detects | Severity |
|---|---|---|
| `long-session-no-checkpoint` | Session has ≥250 user turns but no `/checkpoint` invocation | warning |
| `hook-bypass` | `git commit/push/am/rebase/merge` with `--no-verify` within 100 chars on the same line | blocker |
| `preference-as-directive` | User says *"X should be Y"* (without imperative verb), assistant does Edit/Write without AskUserQuestion | warning |
| `branch-drift` | Session changes `gitBranch` ≥3 times — drifting across topics | info |
| `recall-underuse` | Repo has ≥5 sessions but 0 used `/recall` in the opener (first 10 events) | info |

### Quality (3 rules)

| Rule | Detects | Severity |
|---|---|---|
| `missing-verified-by` | Commit after 2026-05-08 missing `Verified-by:` trailer | warning |
| `missing-coauthor` | Commit after 2026-04-25 missing `Co-Authored-By:` trailer | warning |
| `giant-commit` | Commit body >50 lines — bundled, not per-task atomic | info |

### Efficiency (3 rules)

| Rule | Detects | Severity |
|---|---|---|
| `file-re-read` | Same file Read ≥4× in one session — working-memory loss | info |
| `bash-loop-struggle` | ≥15 consecutive Bash calls with no Read/Edit/Grep — thrashing | info |
| `tool-call-explosion` | >200 tool calls per commit (over ≥3 commits) — unfocused work | info |

### Praxis (3 rules)

| Rule | Detects | Severity |
|---|---|---|
| `commit-without-test` | No `pytest`/`vitest`/`jest`/etc in 20 tool calls before commit, no trivial/cannot-verify opt-out in trailer | info |
| `edit-without-read` | Edit on a file the session never Read first — risk of stale assumptions | warning |
| `main-branch-commits` | ≥3 commits made while `gitBranch` is `main`/`master` | info |

Severity is informational, not a UI gate. All findings are passive.

## How to use it

**Daily flow:**

1. Morning, before starting work: `cat analysis/daily/$(date +%F).md` — or just `cat analysis/daily/*.md | tail -100`.
2. If a finding looks wrong, drill in via `analysis/patterns/<rule>.jsonl`. Each finding has session UUID + repo so you can `Read` the source.
3. If a finding is a false positive: tighten the rule in `scripts/detect_patterns.py`. The rules are deterministic Python; no LLM in the loop.

**On demand:**

- `python3 scripts/detect_patterns.py --since 2026-04-24` — full corpus scan
- `python3 scripts/detect_patterns.py --rule preference-as-directive` — one rule
- `python3 scripts/daily_drift.py` — same as cron but run now

**Adding a rule:**

Each rule is one function `rule_<name>(events, meta) -> list[dict]`. Register in `RULES` and add to `RULE_CATEGORIES`. The detector handles output formatting automatically.

## Why this shape (and not others)

The other shapes I considered before building this:

- **Periodic four-lens re-run (Explore agents).** Useful quarterly, not daily. At ~30 new sessions/month, the trends don't shift fast enough to justify the agent cost.
- **SessionEnd hook summaries.** SessionEnd doesn't reliably fire (sessions don't always close cleanly), and per-session summaries duplicate what `/checkpoint` already produces. Better to invest in `/checkpoint` than to add a second persistence channel.
- **Auto-acting alerts.** Tightest loop but highest annoyance risk. Patterns are noisy in absolute terms (the corpus has 758 findings); auto-prompting on each would be intolerable. Passive is the right default; if a class of finding consistently warrants action, *then* upgrade it to a hook.

## What the first run already showed (2026-05-12)

Initial scan, 64 sessions, post-rework window:

| Category | Findings | Top signal |
|---|---:|---|
| Continuity | 8 | 8 long sessions with no `/checkpoint` — the cadence hook (shipped same day) targets this |
| Quality | 38 | 24 commits missing `Verified-by:` (mostly between 2026-05-08 ramp-up and W19 100% adoption — historical) |
| Efficiency | 91 | 76 file-re-read findings — sessions Reading the same file 4–8 times |
| Praxis | **472** | The single largest signal: commits without an explicit test run in the preceding 20 tool calls |

**The praxis number is the headline insight.** 472 commits-without-test (out of 612 total commits, ~77%) is a real gap between *trailer hygiene* (97% `Co-Authored-By:`, ramping to 100% `Verified-by:`) and *actual verification* (test run before commit, only ~23%).

This is exactly what the continuous analyzer is for: surfacing the difference between **process compliance** (trailers present) and **substance** (tests actually run). The §6 hook ensured the trailer; the continuous loop reveals the trailer is sometimes the *only* thing happening.

**Carry-forward for the next intervention round:** either tighten `Verified-by:` semantically (require the trailer to name a command that actually appears in the preceding 20 tool calls) or accept that "Verified-by: trivial" is a legitimate exit and the 472 figure is overstated.

## Files

- [`scripts/detect_patterns.py`](../../scripts/detect_patterns.py) — rule engine
- [`scripts/daily_drift.py`](../../scripts/daily_drift.py) — daily drift + pattern invocation
- [`~/.claude/hooks/checkpoint-pattern-scan.sh`](file:///Users/tobiasedman/.claude/hooks/checkpoint-pattern-scan.sh) — PostToolUse hook
- Scheduled task: `daily-drift-agentic-workflow` at 07:27 AM local (7-day auto-expiry — re-create as needed)

## Maintenance

- **The scheduled task expires after 7 days.** When it does, ask for re-creation or migrate to `launchd` for permanence.
- **The `analysis/corpus/<date>.json` snapshots accumulate.** Prune monthly if disk pressure ever matters; currently each is ~20 KB.
- **The rules will need tuning.** First few weeks of false-positive rate will tell you which thresholds are too tight (e.g. `file-re-read` at 4 might want to be 6 for visual-design-heavy work).
- **The categories are the unit of trend.** When a category total moves sharply over a week, that's where intervention focus should land.
