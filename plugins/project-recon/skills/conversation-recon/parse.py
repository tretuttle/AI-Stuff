#!/usr/bin/env python3
"""Walk a Claude Code slug dir, parse jsonl, emit session summaries as JSON."""
from __future__ import annotations
import json, sys, re, pathlib, collections, os

NOISE_TYPES = {"queue-operation", "progress"}
PATH_RE = re.compile(r"(?:/home/tt|/mnt/windows/Users/trent)(?:/[\w.\-]+)+")

SYSTEM_ROOTS = {
    "/", "/home", "/home/tt", "/tmp", "/root", "/etc", "/usr", "/var",
    "/mnt", "/mnt/windows", "/mnt/windows/Users", "/mnt/windows/Users/trent",
}
GENERIC_HOME_SUBDIRS = {
    "Downloads", "Documents", "Desktop", "Pictures", "Videos", "Music",
    "Public", "Templates", "Games", "Work",
}
PROJECT_MARKERS = (
    ".git", "package.json", "CLAUDE.md", "Cargo.toml", "pyproject.toml",
    "go.mod", "pubspec.yaml", "Gemfile", "composer.json", ".claude-plugin",
)


def is_project_dir(cwd):
    """True if cwd looks like a real project root (not home/system dir)."""
    if not cwd:
        return False
    if cwd.rstrip("/") in SYSTEM_ROOTS:
        return False
    if not os.path.isdir(cwd):
        return False
    p = pathlib.Path(cwd)
    for marker in PROJECT_MARKERS:
        if (p / marker).exists():
            return True
    # Direct subdir of /home/tt that isn't a generic user dir → treat as project
    if p.parent == pathlib.Path("/home/tt") and p.name not in GENERIC_HOME_SUBDIRS:
        return True
    return False


def walk_slug(slug_dir: pathlib.Path):
    records = []
    for jsonl in sorted(slug_dir.glob("*.jsonl")):
        for line in jsonl.read_text(errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("type") in NOISE_TYPES:
                continue
            r["_file"] = jsonl.name
            records.append(r)
    return records


def group_by_session(records):
    sessions = collections.defaultdict(list)
    for r in records:
        sid = r.get("sessionId")
        if sid:
            sessions[sid].append(r)
    return sessions


def resolve_cwd(records):
    for r in records:
        cwd = r.get("cwd")
        if cwd:
            return cwd
    return None


def text_of(content, include_tool_results=True):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for b in content:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "text":
                parts.append(b.get("text", ""))
            elif b.get("type") == "tool_result" and include_tool_results:
                tc = b.get("content")
                if isinstance(tc, str):
                    parts.append(tc)
                elif isinstance(tc, list):
                    parts.extend(x.get("text", "") for x in tc if isinstance(x, dict))
        return "\n".join(parts)
    return ""


def is_tool_result_only(content) -> bool:
    """User messages that are ONLY tool results aren't real user input."""
    if isinstance(content, str):
        return False
    if not isinstance(content, list):
        return False
    types = {b.get("type") for b in content if isinstance(b, dict)}
    return bool(types) and types.issubset({"tool_result"})


INJECTED_MARKERS = (
    "<command-name>",
    "<command-message>",
    "<command-args>",
    "<local-command-",
    "<system-reminder>",
    "Base directory for this skill:",
)


def _is_injected(txt: str) -> bool:
    """Detect slash-command/skill injections that appear as user messages."""
    head = txt[:500]
    if any(m in head for m in INJECTED_MARKERS):
        return True
    first = txt.lstrip().split("\n", 1)[0].strip()
    # Skill/command bodies commonly open with "## Context" or a heading
    if first == "## Context":
        return True
    # Recon-style context block fingerprint
    if "- Current directory:" in head and "- Directory contents:" in head:
        return True
    return False


COMMAND_NAME_RE = re.compile(r"<command-name>([^<]+)</command-name>")


def _extract_command_name(txt: str):
    m = COMMAND_NAME_RE.search(txt)
    return m.group(1).strip() if m else None


def first_user_msg(session_records):
    """Prefer real user text; fall back to slash-command name if the session
    was started via a command injection and no organic text follows."""
    fallback = None
    for r in session_records:
        if r.get("type") != "user":
            continue
        if r.get("isSidechain"):
            continue
        msg = r.get("message") or {}
        content = msg.get("content")
        if is_tool_result_only(content):
            continue
        txt = text_of(content, include_tool_results=False).strip()
        if not txt:
            continue
        if txt.startswith("<") and txt.endswith(">"):
            continue
        if "tool_use_id" in txt[:80]:
            continue
        if _is_injected(txt):
            if fallback is None:
                cmd = _extract_command_name(txt)
                if cmd:
                    fallback = f"/{cmd}"
            continue
        return txt
    return fallback


def slugify(s: str, maxlen=60) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:maxlen] or "untitled"


def count_tools(session_records):
    counts = collections.Counter()
    msg_count = 0
    sidechain_count = 0
    for r in session_records:
        t = r.get("type")
        if t in ("user", "assistant"):
            if r.get("isSidechain"):
                sidechain_count += 1
            else:
                msg_count += 1
        if t == "assistant":
            content = (r.get("message") or {}).get("content")
            if isinstance(content, list):
                for b in content:
                    if isinstance(b, dict) and b.get("type") == "tool_use":
                        counts[b.get("name", "?")] += 1
    return msg_count, sidechain_count, dict(counts)


def session_date(session_records):
    for r in session_records:
        ts = r.get("timestamp")
        if ts:
            return ts[:10]
    return None


def detect_resume(session_records, all_sessions):
    for r in session_records:
        if r.get("isSidechain"):
            continue
        pu = r.get("parentUuid")
        if not pu:
            return None
        for sid, recs in all_sessions.items():
            if sid == r.get("sessionId"):
                continue
            if any(x.get("uuid") == pu for x in recs):
                return sid
        return None
    return None


def extract_path_mentions(session_records, self_cwd):
    hits = collections.Counter()
    for r in session_records:
        if r.get("type") not in ("user", "assistant"):
            continue
        txt = text_of((r.get("message") or {}).get("content"))
        for m in PATH_RE.findall(txt):
            m = m.rstrip(".,;:)\"'")
            if self_cwd and (m == self_cwd or m.startswith(self_cwd + "/")):
                continue
            hits[m] += 1
    return hits


def summarize_session(sid, recs, all_sessions, self_cwd):
    msg_count, sidechain_count, tool_counts = count_tools(recs)
    fum = first_user_msg(recs)
    return {
        "id": sid,
        "file": recs[0].get("_file") if recs else None,
        "date": session_date(recs),
        "title": slugify(fum) if fum else "untitled",
        "first_user_msg": (fum[:300] if fum else None),
        "msg_count": msg_count,
        "sidechain_msg_count": sidechain_count,
        "tool_counts": tool_counts,
        "resumed_from": detect_resume(recs, all_sessions),
        "path_mentions": extract_path_mentions(recs, self_cwd).most_common(),
    }


def summarize_slug(slug_dir: pathlib.Path):
    records = walk_slug(slug_dir)
    sessions = group_by_session(records)
    cwd = resolve_cwd(records)
    summaries = [summarize_session(sid, recs, sessions, cwd) for sid, recs in sessions.items()]
    summaries.sort(key=lambda s: (s["date"] or "0"))

    agg = collections.Counter()
    sessions_mentioning = collections.defaultdict(int)
    for s in summaries:
        for path, n in s["path_mentions"]:
            agg[path] += n
            sessions_mentioning[path] += 1

    agg_out = [
        {"path": p, "total_mentions": n, "sessions": sessions_mentioning[p], "exists": os.path.exists(p)}
        for p, n in agg.most_common()
    ]

    dates = [s["date"] for s in summaries if s["date"]]
    project_like = is_project_dir(cwd)
    cwd_exists = bool(cwd) and os.path.isdir(cwd)
    if not cwd_exists:
        status = "orphaned"
    elif not summaries:
        status = "empty"
    elif not project_like:
        status = "homedir"
    else:
        status = "current"
    return {
        "slug": slug_dir.name,
        "cwd": cwd,
        "cwd_exists": cwd_exists,
        "project_like": project_like,
        "status": status,
        "session_count": len(summaries),
        "span": {"first": min(dates), "last": max(dates)} if dates else None,
        "sessions": summaries,
        "path_mentions": agg_out,
    }


def main():
    if len(sys.argv) < 2:
        print("usage: parse.py <slug-dir>", file=sys.stderr)
        sys.exit(2)
    slug_dir = pathlib.Path(sys.argv[1])
    if not slug_dir.is_dir():
        print(json.dumps({"slug": slug_dir.name, "session_count": 0, "error": "not a directory"}))
        sys.exit(0)
    result = summarize_slug(slug_dir)
    json.dump(result, sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
