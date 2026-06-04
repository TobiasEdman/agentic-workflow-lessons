# omni-rag — the cross-session memory contract

> What `/recall`, `/checkpoint`, and any non-Claude agent runtime can rely on. Single source of truth: this file. Updated when the contract changes, not when the implementation does.

## What omni-rag is

A multi-repo RAG index over `~/.claude/checkpoints/` (and `~/Developer/agentic_workflow/sessions/`). Renamed from `des-agent` 2026-04-25. Source at `~/Developer/omni-rag/`. CLI entrypoint: `omni-rag` (registered via `pyproject.toml`); module entry: `python3 -m cli.main`.

The role it plays in the architecture: **cross-session memory layer**. `/checkpoint` writes. `/recall` reads (file listing first, semantic search second). omni-rag is the *semantic* layer of read.

## What `/recall` actually depends on

The `/recall` skill is engineered to degrade gracefully. Its dependency chain, from cheapest to most expensive:

| Mode | Backend | Required for | Failure mode |
|---|---|---|---|
| `recall` (no args) | `ls -t ~/.claude/checkpoints/<repo>/` | most opener-recall calls (67% of long sessions per [`post_rework_evidence.md`](post_rework_evidence.md)) | filesystem unavailable → /recall returns "no checkpoints" gracefully |
| `recall <repo>` | same | same | same |
| `recall --all` | same, glob across repos | cross-repo discovery | same |
| `recall --since DATE` | same, filename prefix filter | date-bounded lookup | same |
| `recall --query "<q>"` | `omni-rag query --repo claude-checkpoints` | semantic search across content, not just filenames | falls back to filename glob if omni-rag returns nothing or fails |

**The bottom four modes do not require omni-rag at all.** Only `--query` needs the semantic backend. This is by design — the file-listing path is the fast common case, and a missing/broken omni-rag does not break `/recall` for routine use.

## omni-rag's promised surface

Pinned commitments (changing any of these is a contract break):

1. **Command:** `omni-rag query "<question>" --repo claude-checkpoints --top-k <N> --no-llm`
2. **Output format on success:** a list of `top-k` hits, each containing at minimum:
   - `score` (float)
   - `source_path` — relative to `~/.claude/checkpoints/`
   - `content_excerpt` — first ~400 chars of the matched chunk
3. **Output format on failure:** non-zero exit with stderr message. **Never** prints a half-formed hit list.
4. **Index naming:** the `claude-checkpoints` repo is the canonical name for the checkpoint index. Other indices (`agentic-workflow-sessions`) are siblings, not substitutes.

Anything not on this list (chunk schema, embedding model, scoring algorithm, Qdrant collection name, etc.) is implementation detail and may change without breaking the contract.

## Environment dependencies (current state, 2026-05-12)

omni-rag's *full* functionality requires:

- **Qdrant** — vector store. Run via `docker-compose up -d` from `~/Developer/omni-rag/`. Without it: `--query` mode fails; file-listing modes unaffected.
- **Ollama** — local embedding model + LLM. Models needed: `nomic-embed-text:v1.5` (embeddings), `llama3.1:8b` (optional, only when `--no-llm` not passed).
- **Python package `qdrant_client`** — must be importable from whichever Python invokes `omni-rag`. Currently missing on the system Python (Python 3.9 at `/Applications/Xcode.app/...`). Fix: `pip install qdrant_client` in the omni-rag venv, or install into the system Python.

**Today's observed state:** Ollama up with both models; Qdrant unavailable due to missing `qdrant_client` package; `--query` mode therefore broken. File-listing modes work.

This is the kind of degradation the contract is designed to absorb — `/recall` still works for the 67% of long sessions that don't need semantic search, and it surfaces a clear "semantic search unavailable" rather than failing silently.

## What to do if omni-rag is down

In order of escalation:

1. **Confirm it matters.** Most `/recall` calls don't need semantic search. If you can answer the user by listing recent checkpoints, do that.
2. **Read the checkpoint files directly.** `ls -t ~/.claude/checkpoints/<repo>/ | head -3` then `Read` the top one. This is what `/recall` already does in its default mode.
3. **Verify Qdrant + Ollama.** `cd ~/Developer/omni-rag && python3 -m cli.main status` shows both. If Qdrant says "module not found", install `qdrant_client`. If Ollama is empty, `ollama pull nomic-embed-text:v1.5`.
4. **Re-ingest if state looks stale.** `omni-rag ingest --repo claude-checkpoints` rebuilds the index from `~/.claude/checkpoints/`. Idempotent.
5. **Last resort: skip omni-rag entirely.** `/recall` still works without it.

## Bus-factor note

omni-rag is single-author, no SLA, no API versioning. If it disappears, the file-listing fallback in `/recall` keeps the system functional. The semantic layer is an enhancement, not a requirement.

The post-rework retrospective ([`retrospective_v2_jsonl.md`](retrospective_v2_jsonl.md) §4 surviving open problems) flagged this. The contract above is the response: define the surface narrowly so any replacement (Codex's MCP, a different vector store, a homegrown grep over checkpoints) can satisfy it without rewriting `/recall`.

## Cross-vendor consideration

Per `~/Developer/omni-rag/docs/cross-vendor-continuity.md`, omni-rag is intended to be queryable from non-Claude runtimes (Codex CLI, Mistral wrappers). The contract above is the spec for that interface. The verification *"can I query omni-rag from a Codex session?"* is gated on Codex actually shipping a runtime — currently out of scope.

When that happens: the test is whether a non-Claude agent can run `omni-rag query …` and parse the output without needing any Claude-specific tooling. If yes, the contract holds across vendors.

---

*Updated: 2026-05-12. Edit only when the contract changes; not when the implementation does.*
