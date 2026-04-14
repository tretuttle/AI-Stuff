"""TypedDict contracts — the frontend-facing API shapes.

Keep these stable. Breaking changes bump DATA_VERSION.
Additive changes are backward compatible.
"""
from __future__ import annotations
from typing import TypedDict, Literal, NotRequired


Status = Literal["current", "homedir", "orphaned", "empty"]
Coupling = Literal["hard", "soft", "intent"]


class ContextFiles(TypedDict):
    """Well-known files present in a project cwd."""
    claude_md: bool
    agent_md: bool
    project_identity: bool
    conversation_identity: bool
    git: bool
    skills: list[str]         # basenames of skill files found
    reference_md_count: int


class Relationship(TypedDict):
    """From .project-identity.md relationships table."""
    path: str
    relationship: str
    coupling: Coupling
    notes: str


class CrossRef(TypedDict):
    """From .conversation-identity.md cross-references (path mentions)."""
    path: str
    sessions: int
    mentions: int
    coupling: Coupling


class ToolCount(TypedDict):
    name: str
    count: int


class Session(TypedDict):
    id: str
    slug: str
    file: str
    date: str | None
    title: str
    first_user_msg: NotRequired[str | None]
    msg_count: int
    sidechain_msg_count: int
    tool_counts: list[ToolCount]
    resumed_from: str | None


class ProjectSummary(TypedDict):
    slug: str
    cwd: str | None
    status: Status
    project_like: bool
    sessions: int
    last_activity: str | None
    span: NotRequired[dict | None]
    identity_paths: dict


class ProjectDetail(ProjectSummary):
    relationships: list[Relationship]
    cross_refs: list[CrossRef]
    sessions_detail: list[Session]
    context_files: ContextFiles


class GraphNode(TypedDict):
    slug: str
    cwd: str | None
    status: Status
    sessions: int


class GraphEdge(TypedDict):
    source: str       # slug
    target: str       # slug OR raw path
    kind: Literal["relationship", "mention"]
    coupling: Coupling
    weight: int


class Graph(TypedDict):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class ActionRequest(TypedDict):
    kind: Literal["recon", "conversation-recon", "prompt"]
    cwd: str
    prompt: NotRequired[str]
    resume_session: NotRequired[str]
    output_format: NotRequired[Literal["text", "json", "stream-json"]]


class ActionState(TypedDict):
    id: str
    kind: str
    cwd: str
    status: Literal["pending", "running", "completed", "failed", "canceled"]
    started_at: str
    ended_at: NotRequired[str]
    exit_code: NotRequired[int]
    stdout_bytes: int
    stderr_bytes: int
    artifacts: list[str]


class SchemaInfo(TypedDict):
    api: str
    data: str
    server_version: str


class Health(TypedDict):
    ok: bool
    claude_bin: str
    claude_available: bool
    claude_version: NotRequired[str]
    data_root: str
    projects_tracked: int
