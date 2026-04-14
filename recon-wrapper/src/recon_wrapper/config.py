"""Config + paths. All defaults overridable via env."""
from __future__ import annotations
import os
import secrets
import pathlib
from dataclasses import dataclass, field


HOME = pathlib.Path.home()
CLAUDE_DIR = HOME / ".claude"


@dataclass(frozen=True)
class Config:
    host: str = "127.0.0.1"
    port: int = 7777
    claude_dir: pathlib.Path = CLAUDE_DIR
    projects_dir: pathlib.Path = CLAUDE_DIR / "projects"
    conversations_dir: pathlib.Path = CLAUDE_DIR / "conversations"
    conversation_index: pathlib.Path = CLAUDE_DIR / "conversation-index.md"
    recon_dir: pathlib.Path = CLAUDE_DIR / "recon"
    token_file: pathlib.Path = field(init=False)
    log_file: pathlib.Path = field(init=False)
    windows_projects_dir: pathlib.Path = pathlib.Path("/mnt/windows/Users/trent/.claude/projects")
    claude_bin: str = "claude"

    def __post_init__(self):
        object.__setattr__(self, "token_file", self.recon_dir / "token")
        object.__setattr__(self, "log_file", self.recon_dir / "wrapper.log")

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            host=os.environ.get("RECON_HOST", "127.0.0.1"),
            port=int(os.environ.get("RECON_PORT", "7777")),
            claude_bin=os.environ.get("RECON_CLAUDE_BIN", "claude"),
        )


def ensure_token(cfg: Config) -> str:
    """Create the API token file on first run. Caller is trusted (localhost)."""
    cfg.recon_dir.mkdir(parents=True, exist_ok=True)
    if not cfg.token_file.exists():
        token = secrets.token_urlsafe(32)
        cfg.token_file.write_text(token + "\n")
        cfg.token_file.chmod(0o600)
        return token
    return cfg.token_file.read_text().strip()


def slug_to_cwd(slug: str) -> str:
    """Decode slug back to cwd path. `-home-tt-x` → `/home/tt/x`."""
    if not slug.startswith("-"):
        return slug
    return "/" + slug[1:].replace("-", "/", 1000)  # naive; real cwd comes from jsonl
