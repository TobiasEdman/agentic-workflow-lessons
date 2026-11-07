from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_repository_role_lives_outside_the_managed_files():
    role = (ROOT / "docs" / "REPOSITORY.md").read_text()
    assert "multi-agentic-public" in role
    # AGENTS.md and CLAUDE.md are owned by agentic-task; no repository policy there.
    for managed in ("AGENTS.md", "CLAUDE.md"):
        assert "agentic-task:coordination:start" in (ROOT / managed).read_text()


def test_codex_addendum_is_thin_and_points_to_the_role():
    codex = (ROOT / "CODEX.md").read_text()
    assert "docs/REPOSITORY.md" in codex and "AGENTS.md" in codex
    assert "may not redefine" in codex
    assert len(codex.splitlines()) < 10
