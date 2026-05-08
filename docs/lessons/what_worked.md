# What Worked — patterns that produced output

Drawn from the sessions where a tangible artifact shipped (repo created, dashboard rendered, data fetched, report written). Cross-referenced against `analysis/per_session.csv` — "working" sessions skew toward higher tool counts and lower correction density.

## The session-starter briefing

The single most reliable pattern. Visible in its clearest form in `here.txt` (image-processing lab cross-raster alignment investigation):

> "I need help debugging a pixel-level alignment problem between three georeferenced rasters […] I need a **rigorous ground-up plan** before any code is written.
>
> Project location: /Users/<user>/Developer/<image-processing-lab-repo>
>
> Key files:
> - scripts/serve_viewer.py — the viewer HTTP server (has a big LESSON LEARNED comment around line 48)
> - scripts/viewer.html — the client
> - data/&lt;provider&gt;/&lt;aoi&gt;/…
>
> Python env: /Users/<user>/Developer/<analysis-pipeline-repo>/.venv/bin/python (has rasterio 1.4.3, geopandas, fiona, …)
>
> […]
>
> ### What I already tried (and why it's suspect)
> - Reprojecting the TSX from rotated EPSG:4326 → axis-aligned north-up EPSG:4326 using rasterio.warp.reproject(…)"

What made this work:

1. **Absolute paths** for project root, venv, key files.
2. **Enumeration of everything tried** — so Claude doesn't propose what's already been ruled out.
3. **Explicit framing of what's wanted** — *plan before code*, not *solve this now*.
4. **Candid uncertainty** — "and why it's suspect" flags that each attempted fix is suspect. Claude can then challenge each one.

That session produced a structured alignment plan instead of tool-flailing. Replicate this shape.

## "fortsätt där vi slutade" with a state snapshot

The best continuation prompts pair the command with a written state summary, so Claude doesn't have to reconstruct it:

> "I would like you to cintune where we stopped:
>
> Vad som fungerar:
> - 563 EO-satelliter med parametrisk generering
> - 17 S2 + 68 S1 scener hämtade från CDSE
> - YOLO-detektion (51 fartyg)
> - Dashboard med Feb 1-start, ⏭-knappar, escape timeline
> - analysis-pipeline refaktorerad (crs parameter, optional nodata)
>
> Vad som behöver göras ordentligt:
> - Dynamisk tile overlay — globe.scene().add(mesh) med separat THREE-import
> - Konsol-injektionen bevisade att det fungerar — behöver bara implementeras korrekt som ren type=\"module\" kod utan syntaxfel och med korrekt livscykel"
> — `hi.txt`, turn 1

Two lists: *what works* and *what needs doing properly*. Claude can skip rediscovery.

## Naming a file, not a feature

Prompts that reference a concrete file or line range consistently land. From `can-we-restart-with-this-info`:

> "Fix: torch.zeros_like → torch.ones_like in losses.py. NMD pixels default to weight=1.0."

That single sentence contains: the bug, the fix, the file, and the invariant. Claude's next turn committed it. Compare with "the loss looks wrong" which in earlier sessions required 6–8 turns of diagnosis.

## STOP, stated literally

From `can-you-make-sure-everything-is-committed` (three times) and `session-context`. The word `STOP` on its own line halts Claude's in-flight action reliably. No other correction form is as fast.

## Delegation to the Agent tool

Multiple `Ran agent` lines appear in sessions where Claude had to explore unfamiliar code. `long-engine-session-A` uses 14 agent delegations. These bypass Claude's tendency to read too many files in the main context and keep the primary conversation focused on decisions. When the session's primary goal is decisions, push the research to agents.

## Committing as a checkpoint

`can-you-make-sure-everything-is-committed` is titled literally that — it's a dedicated *commit-everything* session. Looking at the transcript: the act of preparing commits surfaces latent bugs ("harvest_mask max=0 överallt", "LPIS-problemet"). The commit workflow is a quality gate, not just a persistence step.

## Running dev servers through `.claude/launch.json`

Sessions where a preview tool was pre-registered in launch.json had no "how do I restart the server?" churn. Sessions that ran servers via ad-hoc `Bash` had multiple restarts and port conflicts. Pre-declaring servers in launch.json was worth the 30 seconds.

## Swedish for small, English for large

Short coordination prompts in Swedish land as well as English. Long briefings land better in English — partly because the tools' output (stack traces, rasterio warnings, kubectl output) is English, so switching languages inside one turn creates friction. Session `here.txt` is entirely English and is one of the densest productive sessions in the corpus.

## Pre-committing to a tool choice

When you pre-stated a tool (e.g., "use the preview tool, not Chrome DevTools"), subsequent turns in the same session stayed on that tool — *if and only if* Claude acknowledged the preference. When Claude silently skipped the acknowledgment, the preference drifted (see `instruction_adherence.md` case 3). Ask Claude to echo tool preferences.

## The "3 subagents, parallel read" pattern

`can-you-read-excellencekluster` shows multiple places where 3–4 Agent calls were dispatched in parallel to different aspects of the same analysis (Karolinska, KTH, Lund, Uppsala, etc.). This is the cleanest use of concurrency in the corpus and produced a consistent, comparable output across institutions. When a task has independent parallel lanes, naming them in the prompt ("run four subagents, one per university") works.

---

## Meta-pattern

Across all of the above, the common property is **front-loading**: the first turn carries as much of the weight as possible. File paths, env details, prior attempts, preferred tools, non-goals, explicit stop-words — all stated before the first tool call. Sessions that front-load spend their tool budget on the actual problem. Sessions that don't spend it rediscovering context.

---

## External reinforcements (2026-04 literature sweep)

Cross-validation of the above patterns, plus additions from Anthropic docs, practitioner blogs, academic papers, and enterprise case studies. Full synthesis in [`external_patterns.md`](external_patterns.md); raw sources in [`external_patterns_raw/`](external_patterns_raw/).

### Confirmed by the broader community

- **Briefing opener = plan-then-execute.** Anthropic's Best Practices names *"Explore → Plan → Implement → Commit"* as the core workflow. Osmani's 2026 workflow uses a *spec.md* step before code. Our `here.txt` pattern is a compressed version of the same.
- **Parallel subagents.** Anthropic's "multi-agent research system" post reports parallel tool calls cut research time by **up to 90%**. Matches our Excellence Cluster session's 4-agent university research.
- **Small commits as save points.** Osmani: *"commits as save points in a game."* Our commit-as-quality-gate works, but the **per-task commit** variant is better — see pitfalls update.

### Net-new additions to this file's playbook

- **Verification is the highest-leverage move.** Anthropic Best Practices: *"Include tests, screenshots, or expected outputs so Claude can check itself. This is the single highest-leverage thing you can do."* We have this implicitly in some sessions; make it explicit in every CLAUDE.md.
- **Interview-driven spec.** For non-trivial features: *"Interview me using AskUserQuestion. Ask about implementation, UI/UX, edge cases, concerns, tradeoffs. Keep interviewing until we've covered everything, then write SPEC.md."* Fresh session executes. Adopting as `/spec` skill.
- **Auto memory.** Claude writes its own notes between sessions to `~/.claude/projects/<project>/memory/MEMORY.md`. First 200 lines load each session. Complements CLAUDE.md without manual curation.
- **Writer / Reviewer parallel sessions.** A second fresh-context Claude reviews the first's output. Bias-free; catches what the author missed. Anthropic docs recommend this directly.
- **Extended-thinking keywords.** Keywords `think`, `think hard`, `ultrathink` trigger 4k / 10k / 32k-token thinking budgets inside Claude Code (Simon Willison, reverse-engineered). Useful for ambiguous planning turns.
- **`/rewind` + `Esc+Esc`.** Native checkpoint-restore, finer-grained than STOP. Keep STOP as the blunt fallback.

### Team / enterprise reinforcements

- **Stripe — 1,370 engineers, 10k-line Scala→Java migration in 4 days** (est. 10 engineer-weeks). **Wiz — 50k-line Python→Go in ~20 hours** (est. 2–3 months). **Ramp — 80% reduction in incident investigation time.**
- **Anthropic Security:** *"design doc → tests → code"* replaced *"design doc → janky code → give up on tests."* Test-driven development guided by Claude.
- **Anthropic C-compiler experiment:** 16 agents coordinated via file-based locking (`current_tasks/` dir). No orchestrator. The principle — *design the environment, not the work* — applies solo too.

Together, these confirm front-loading as the load-bearing pattern and add verification + interview-driven spec as co-equal practices.
