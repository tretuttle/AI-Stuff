"""Unit tests for aggregator. Uses a temp $HOME to avoid touching real data."""
from __future__ import annotations
import pathlib
import textwrap

import pytest

from recon_wrapper import aggregator
from recon_wrapper.config import Config


@pytest.fixture
def tmp_home(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    # Config reads paths from HOME lazily via pathlib.Path.home()
    (tmp_path / ".claude" / "conversations").mkdir(parents=True)
    return tmp_path


@pytest.fixture
def cfg(tmp_home):
    cfg = Config()
    # Override paths to sit under tmp_home
    object.__setattr__(cfg, "claude_dir", tmp_home / ".claude")
    object.__setattr__(cfg, "projects_dir", tmp_home / ".claude" / "projects")
    object.__setattr__(cfg, "conversations_dir", tmp_home / ".claude" / "conversations")
    object.__setattr__(cfg, "conversation_index", tmp_home / ".claude" / "conversation-index.md")
    return cfg


def write_index(cfg: Config, rows: list[dict]) -> None:
    lines = [
        "# Conversation Index", "", "**Schema:** 1", "**Updated:** 2026-04-12", "",
        "## Projects", "",
        "| Slug | Cwd | Status | Sessions | Last activity | Identity |",
        "|------|-----|--------|---------:|---------------|----------|",
    ]
    for r in rows:
        lines.append(
            f"| {r['slug']} | {r.get('cwd','—')} | {r['status']} "
            f"| {r.get('sessions', 0)} | {r.get('last', '—')} | — |"
        )
    cfg.conversation_index.write_text("\n".join(lines))


def test_read_index_empty(cfg):
    assert aggregator.read_index(cfg) == []


def test_list_projects_basic(cfg):
    write_index(cfg, [
        {"slug": "-home-tt-foo", "cwd": "/home/tt/foo", "status": "current",
         "sessions": 4, "last": "2026-04-01"},
        {"slug": "-home-tt", "cwd": "/home/tt", "status": "homedir",
         "sessions": 25, "last": "2026-04-10"},
    ])
    rows = aggregator.list_projects(cfg)
    assert len(rows) == 2
    assert rows[0]["slug"] == "-home-tt-foo"
    assert rows[0]["status"] == "current"
    assert rows[0]["sessions"] == 4
    assert rows[1]["status"] == "homedir"


def test_get_project_returns_none_when_missing(cfg):
    write_index(cfg, [])
    assert aggregator.get_project(cfg, "-does-not-exist") is None


def test_build_graph_shape(cfg, tmp_path):
    # Two projects, one mentions the other
    write_index(cfg, [
        {"slug": "-home-tt-a", "cwd": str(tmp_path / "a"), "status": "current",
         "sessions": 1, "last": "2026-04-01"},
        {"slug": "-home-tt-b", "cwd": str(tmp_path / "b"), "status": "current",
         "sessions": 1, "last": "2026-04-01"},
    ])
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()

    conv = textwrap.dedent(f"""\
        # Conversation Identity

        **Schema:** 1
        **Slug:** -home-tt-a
        **Cwd:** {tmp_path}/a
        **Status:** current
        **Sessions:** 1
        **Span:** 2026-04-01 → 2026-04-01
        **Determined:** 2026-04-01

        ## Sessions

        | Date | Title | File | Msgs | Tools | Resumed-from |
        |------|-------|------|-----:|------:|--------------|
        | 2026-04-01 | hello | abc123 | 5 | 2 | — |

        ## Cross-references

        | Path | Sessions | Mentions | Coupling |
        |------|---------:|---------:|----------|
        | {tmp_path}/b | 1 | 3 | soft |
    """)
    (cfg.conversations_dir / "-home-tt-a.md").write_text(conv)
    (cfg.conversations_dir / "-home-tt-b.md").write_text(
        "# Conversation Identity\n**Schema:** 1\n**Slug:** -home-tt-b\n"
    )
    graph = aggregator.build_graph(cfg)
    assert len(graph["nodes"]) == 2
    # Edge should resolve target path → slug
    mention_edges = [e for e in graph["edges"] if e["kind"] == "mention"]
    assert len(mention_edges) == 1
    assert mention_edges[0]["source"] == "-home-tt-a"
    assert mention_edges[0]["target"] == "-home-tt-b"
    assert mention_edges[0]["weight"] == 3
