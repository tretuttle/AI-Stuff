"""Reads identity + index markdown files. Emits structured JSON.

Single responsibility: translate what the skills already wrote into API shapes
defined in models.py. Zero discovery, zero re-parsing of jsonl.
"""
from __future__ import annotations
import pathlib
import re
from typing import Iterable

from .config import Config
from . import models as m


# ----- markdown helpers -----

_FRONTMATTER_RE = re.compile(r"^\s*\*\*([\w ]+):\*\*\s*(.+?)\s*$")


def _parse_frontmatter(text: str) -> dict:
    """Parse the `**Key:** value` header block at the top of identity files."""
    meta: dict = {}
    for line in text.splitlines():
        if line.startswith("#") or line.startswith("##"):
            continue
        if not line.strip():
            if meta:
                break
            continue
        match = _FRONTMATTER_RE.match(line)
        if match:
            meta[match.group(1).strip().lower()] = match.group(2).strip()
    return meta


def _parse_table(text: str, section_heading: str) -> list[dict]:
    """Pull rows out of a named `## Section` markdown table."""
    lines = text.splitlines()
    in_section = False
    header: list[str] | None = None
    rows: list[dict] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("##"):
            in_section = stripped.lstrip("# ").lower().startswith(section_heading.lower())
            header = None
            continue
        if not in_section:
            continue
        if not stripped.startswith("|"):
            if header:
                break
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if header is None:
            header = [c.lower().replace(" ", "_") for c in cells]
            continue
        if all(c.startswith("-") or c.startswith(":") for c in cells if c):
            continue
        rows.append(dict(zip(header, cells)))
    return rows


# ----- project identity (.project-identity.md) -----

def read_project_identity(path: pathlib.Path) -> dict:
    if not path.is_file():
        return {}
    text = path.read_text(errors="replace")
    meta = _parse_frontmatter(text)
    relationships = _parse_table(text, "Relationships")
    return {"meta": meta, "relationships": relationships}


# ----- conversation identity (.conversation-identity.md OR ~/.claude/conversations/{slug}.md) -----

def read_conversation_identity(path: pathlib.Path) -> dict:
    if not path.is_file():
        return {}
    text = path.read_text(errors="replace")
    meta = _parse_frontmatter(text)
    sessions = _parse_table(text, "Sessions")
    cross_refs = _parse_table(text, "Cross-references")
    return {"meta": meta, "sessions": sessions, "cross_refs": cross_refs}


# ----- central index -----

def read_index(cfg: Config) -> list[dict]:
    if not cfg.conversation_index.is_file():
        return []
    text = cfg.conversation_index.read_text(errors="replace")
    return _parse_table(text, "Projects")


# ----- context file probes (cheap stat calls) -----

_SKILL_GLOBS = ("SKILL.md", "skills/*/SKILL.md", ".claude/skills/*/SKILL.md")


def read_context_files(cwd: str | None) -> m.ContextFiles:
    result: m.ContextFiles = {
        "claude_md": False,
        "agent_md": False,
        "project_identity": False,
        "conversation_identity": False,
        "git": False,
        "skills": [],
        "reference_md_count": 0,
    }
    if not cwd:
        return result
    p = pathlib.Path(cwd)
    if not p.is_dir():
        return result
    result["claude_md"] = (p / "CLAUDE.md").exists()
    result["agent_md"] = (p / "AGENT.md").exists() or (p / "AGENTS.md").exists()
    result["project_identity"] = (p / ".project-identity.md").exists()
    result["conversation_identity"] = (p / ".conversation-identity.md").exists()
    result["git"] = (p / ".git").exists()
    skills: list[str] = []
    for pattern in _SKILL_GLOBS:
        for hit in p.glob(pattern):
            skills.append(str(hit.relative_to(p)))
    result["skills"] = sorted(set(skills))
    result["reference_md_count"] = len(list(p.rglob("reference.md")))
    return result


# ----- aggregation entrypoints -----

def _session_from_row(slug: str, row: dict) -> m.Session:
    tool_total = int(row.get("tools") or 0)
    return {
        "id": row.get("file", ""),                 # short jsonl id
        "slug": slug,
        "file": row.get("file", ""),
        "date": row.get("date") or None,
        "title": row.get("title") or "",
        "msg_count": int(row.get("msgs") or 0),
        "sidechain_msg_count": 0,
        "tool_counts": [{"name": "_total", "count": tool_total}] if tool_total else [],
        "resumed_from": (row.get("resumed-from") or row.get("resumed_from") or None)
            if (row.get("resumed-from") or row.get("resumed_from")) not in ("—", "-", "", None)
            else None,
    }


def _summary_from_index_row(row: dict) -> m.ProjectSummary:
    slug = row.get("slug", "")
    cwd_raw = row.get("cwd", "")
    cwd = None if cwd_raw in ("—", "-", "") else cwd_raw
    status = row.get("status", "orphaned")
    sessions = int(row.get("sessions") or 0)
    last = row.get("last_activity") or None
    if last in ("—", "-", ""):
        last = None
    return {
        "slug": slug,
        "cwd": cwd,
        "status": status,
        "project_like": status == "current",
        "sessions": sessions,
        "last_activity": last,
        "identity_paths": _identity_paths_for(slug, cwd),
    }


def _identity_paths_for(slug: str, cwd: str | None) -> dict:
    from .config import CLAUDE_DIR
    paths = {"central": str(CLAUDE_DIR / "conversations" / f"{slug}.md")}
    if cwd:
        paths["conversation_identity"] = str(pathlib.Path(cwd) / ".conversation-identity.md")
        paths["project_identity"] = str(pathlib.Path(cwd) / ".project-identity.md")
    return paths


def list_projects(cfg: Config) -> list[m.ProjectSummary]:
    return [_summary_from_index_row(r) for r in read_index(cfg)]


def get_project(cfg: Config, slug: str) -> m.ProjectDetail | None:
    summary: m.ProjectSummary | None = None
    for r in read_index(cfg):
        if r.get("slug") == slug:
            summary = _summary_from_index_row(r)
            break
    if summary is None:
        return None

    central = cfg.conversations_dir / f"{slug}.md"
    conv = read_conversation_identity(central)
    cwd = summary["cwd"]
    proj = read_project_identity(pathlib.Path(cwd) / ".project-identity.md") if cwd else {}
    context = read_context_files(cwd)

    sessions_rows = conv.get("sessions", [])
    cross_refs = [
        {
            "path": r.get("path", ""),
            "sessions": int(r.get("sessions") or 0),
            "mentions": int(r.get("mentions") or 0),
            "coupling": r.get("coupling", "soft"),
        }
        for r in conv.get("cross_refs", [])
    ]
    relationships = [
        {
            "path": r.get("path", ""),
            "relationship": r.get("relationship", ""),
            "coupling": r.get("coupling", "soft"),
            "notes": r.get("notes", ""),
        }
        for r in proj.get("relationships", [])
    ]

    detail: m.ProjectDetail = {  # type: ignore[typeddict-item]
        **summary,
        "relationships": relationships,
        "cross_refs": cross_refs,
        "sessions_detail": [_session_from_row(slug, r) for r in sessions_rows],
        "context_files": context,
    }
    return detail


def build_graph(cfg: Config) -> m.Graph:
    """Nodes = projects, edges = relationships + cross-refs (path mentions)."""
    projects = list_projects(cfg)
    slug_by_cwd = {p["cwd"]: p["slug"] for p in projects if p["cwd"]}
    nodes: list[m.GraphNode] = [
        {"slug": p["slug"], "cwd": p["cwd"], "status": p["status"], "sessions": p["sessions"]}
        for p in projects
    ]
    edges: list[m.GraphEdge] = []
    for p in projects:
        detail = get_project(cfg, p["slug"])
        if detail is None:
            continue
        for rel in detail["relationships"]:
            target = slug_by_cwd.get(rel["path"], rel["path"])
            edges.append({
                "source": p["slug"], "target": target,
                "kind": "relationship", "coupling": rel["coupling"], "weight": 1,
            })
        for ref in detail["cross_refs"]:
            target = slug_by_cwd.get(ref["path"], ref["path"])
            edges.append({
                "source": p["slug"], "target": target,
                "kind": "mention", "coupling": ref["coupling"], "weight": ref["mentions"],
            })
    return {"nodes": nodes, "edges": edges}
