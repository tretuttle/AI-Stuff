#!/usr/bin/env python3
import argparse
import json
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional


HOME = Path.home()
CODEX_DIR = HOME / ".codex"
SESSIONS_DIR = CODEX_DIR / "sessions"
HISTORY_FILE = CODEX_DIR / "history.jsonl"


@dataclass
class SessionRecord:
    session_id: str
    session_file: Path
    started_at: str
    cwd: str
    friendly_name: str
    source_for_name: str


def iter_session_files() -> Iterable[Path]:
    if not SESSIONS_DIR.exists():
        return []
    return sorted(SESSIONS_DIR.glob("*/*/*/rollout-*.jsonl"))


def parse_jsonl_line(line: str) -> Optional[dict]:
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return None


def first_jsonl_objects(path: Path, limit: int = 60) -> list[dict]:
    objects: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for idx, line in enumerate(handle):
            if idx >= limit:
                break
            obj = parse_jsonl_line(line)
            if obj is not None:
                objects.append(obj)
    return objects


def find_explicit_title(meta_payload: dict) -> Optional[str]:
    candidates = [
        meta_payload.get("thread_name"),
        meta_payload.get("title"),
        meta_payload.get("summary"),
        meta_payload.get("display_name"),
        meta_payload.get("name"),
    ]
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return None


def load_history_first_prompts() -> dict[str, str]:
    prompts: dict[str, str] = {}
    if not HISTORY_FILE.exists():
        return prompts
    with HISTORY_FILE.open("r", encoding="utf-8") as handle:
        for line in handle:
            obj = parse_jsonl_line(line)
            if not obj:
                continue
            session_id = obj.get("session_id")
            text = obj.get("text")
            if session_id and isinstance(text, str) and text.strip() and session_id not in prompts:
                prompts[session_id] = normalize_label(text)
    return prompts


def normalize_label(text: str, limit: int = 96) -> str:
    one_line = " ".join(text.split())
    if len(one_line) <= limit:
        return one_line
    return one_line[: limit - 3].rstrip() + "..."


def looks_like_scaffolding(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return True
    prefixes = (
        "# AGENTS.md instructions for ",
        "<environment_context>",
        "<INSTRUCTIONS>",
    )
    return stripped.startswith(prefixes)


def extract_first_user_message(path: Path) -> Optional[str]:
    for obj in first_jsonl_objects(path, limit=160):
        if obj.get("type") == "event_msg":
            payload = obj.get("payload") or {}
            if payload.get("type") == "user_message":
                message = payload.get("message")
                if isinstance(message, str) and message.strip() and not looks_like_scaffolding(message):
                    return normalize_label(message)

        if obj.get("type") != "response_item":
            continue
        payload = obj.get("payload") or {}
        if payload.get("type") != "message" or payload.get("role") != "user":
            continue
        content = payload.get("content") or []
        texts = []
        for item in content:
            text = item.get("text")
            if isinstance(text, str) and text.strip():
                texts.append(text.strip())
        for text in reversed(texts):
            if not looks_like_scaffolding(text):
                return normalize_label(text)
    return None


def load_session_record(path: Path, history_prompts: dict[str, str]) -> SessionRecord:
    objects = first_jsonl_objects(path, limit=20)
    meta = {}
    for obj in objects:
        if obj.get("type") == "session_meta":
            meta = obj.get("payload") or {}
            break

    session_id = meta.get("id")
    if not session_id:
        session_id = path.stem.rsplit("-", 1)[-1]

    started_at = meta.get("timestamp") or ""
    cwd = meta.get("cwd") or ""

    explicit_title = find_explicit_title(meta)
    if explicit_title:
        friendly_name = normalize_label(explicit_title)
        source_for_name = "session_meta"
    elif session_id in history_prompts:
        friendly_name = history_prompts[session_id]
        source_for_name = "history"
    else:
        first_user = extract_first_user_message(path)
        if first_user:
            friendly_name = first_user
            source_for_name = "session_user_message"
        else:
            friendly_name = path.stem
            source_for_name = "filename"

    return SessionRecord(
        session_id=session_id,
        session_file=path,
        started_at=started_at,
        cwd=cwd,
        friendly_name=friendly_name,
        source_for_name=source_for_name,
    )


def load_sessions() -> list[SessionRecord]:
    history_prompts = load_history_first_prompts()
    sessions = [load_session_record(path, history_prompts) for path in iter_session_files()]
    sessions.sort(key=lambda s: (s.started_at, str(s.session_file)), reverse=True)
    return sessions


def resolve_session(sessions: list[SessionRecord], query: str) -> SessionRecord:
    query = query.strip()
    if query == "latest":
        if not sessions:
            raise SystemExit("No saved Codex sessions were found.")
        return sessions[0]

    query_path = Path(query).expanduser()
    if query_path.exists():
        for session in sessions:
            if session.session_file == query_path.resolve():
                return session
        raise SystemExit(f"Session file exists but is not under {SESSIONS_DIR}: {query_path}")

    exact = [s for s in sessions if s.session_id == query]
    if len(exact) == 1:
        return exact[0]

    partial = [s for s in sessions if s.session_id.startswith(query)]
    if len(partial) == 1:
        return partial[0]
    if len(partial) > 1:
        lines = ["Session query is ambiguous. Matching sessions:"]
        for session in partial:
            lines.append(f"- {session.session_id} | {session.started_at} | {session.friendly_name}")
        raise SystemExit("\n".join(lines))

    raise SystemExit(f"No saved Codex session matched: {query}")


def render_txt(session: SessionRecord, destination: Path) -> None:
    lines: list[str] = [
        "SESSION META",
        f"id: {session.session_id}",
        f"cwd: {session.cwd}",
        f"started: {session.started_at}",
        f"source: {session.session_file}",
        f"friendly_name: {session.friendly_name}",
        "",
    ]

    with session.session_file.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            obj = parse_jsonl_line(raw_line)
            if not obj or obj.get("type") != "response_item":
                continue
            payload = obj.get("payload") or {}
            if payload.get("type") != "message":
                continue
            role = str(payload.get("role") or "assistant").upper()
            timestamp = obj.get("timestamp")
            content = payload.get("content") or []
            texts = []
            for item in content:
                text = item.get("text")
                if isinstance(text, str) and text.strip():
                    texts.append(text.strip())
            if not texts:
                continue
            if timestamp:
                lines.append(f"[{timestamp}] {role}")
            else:
                lines.append(role)
            lines.append("\n".join(texts))
            lines.append("")

    destination.write_text("\n".join(lines), encoding="utf-8")


def cmd_list(args: argparse.Namespace) -> int:
    sessions = load_sessions()
    if args.json:
        payload = [
            {
                "session_id": s.session_id,
                "started_at": s.started_at,
                "cwd": s.cwd,
                "friendly_name": s.friendly_name,
                "friendly_name_source": s.source_for_name,
                "session_file": str(s.session_file),
            }
            for s in sessions
        ]
        json.dump(payload, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    if not sessions:
        print("No saved Codex sessions were found.")
        return 0

    for session in sessions:
        print(f"{session.session_id}")
        print(f"  started: {session.started_at or 'unknown'}")
        print(f"  cwd: {session.cwd or 'unknown'}")
        print(f"  name: {session.friendly_name}")
        print(f"  name_source: {session.source_for_name}")
        print(f"  file: {session.session_file}")
        print()
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    sessions = load_sessions()
    session = resolve_session(sessions, args.session)
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    formats = {part.strip().lower() for part in args.formats.split(",") if part.strip()}
    if not formats:
        raise SystemExit("No export formats were requested.")

    exported: dict[str, str] = {}

    if "jsonl" in formats:
        jsonl_path = output_dir / f"codex-transcript-{session.session_id}.jsonl"
        shutil.copy2(session.session_file, jsonl_path)
        exported["jsonl"] = str(jsonl_path)

    if "txt" in formats:
        txt_path = output_dir / f"codex-transcript-{session.session_id}.txt"
        render_txt(session, txt_path)
        exported["txt"] = str(txt_path)

    result = {
        "session_id": session.session_id,
        "friendly_name": session.friendly_name,
        "friendly_name_source": session.source_for_name,
        "source_session_file": str(session.session_file),
        "original_session_untouched": True,
        "exports": exported,
    }

    if args.json:
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        print(f"session_id: {session.session_id}")
        print(f"friendly_name: {session.friendly_name}")
        print(f"friendly_name_source: {session.source_for_name}")
        print(f"source_session_file: {session.session_file}")
        print("original_session_untouched: true")
        for name, path in exported.items():
            print(f"{name}: {path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="List and export saved Codex CLI sessions without modifying originals."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List saved Codex sessions")
    list_parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    list_parser.set_defaults(func=cmd_list)

    export_parser = subparsers.add_parser("export", help="Export one saved Codex session")
    export_parser.add_argument(
        "--session",
        required=True,
        help="Session ID, session ID prefix, full session file path, or 'latest'",
    )
    export_parser.add_argument(
        "--formats",
        default="jsonl,txt",
        help="Comma-separated export formats. Supported: jsonl,txt",
    )
    export_parser.add_argument(
        "--output-dir",
        default=str(HOME / "Downloads"),
        help="Directory to write exports into",
    )
    export_parser.add_argument("--json", action="store_true", help="Emit JSON result")
    export_parser.set_defaults(func=cmd_export)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
