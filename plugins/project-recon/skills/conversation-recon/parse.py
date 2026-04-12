#!/usr/bin/env python3
"""Walk a Claude Code slug dir, parse jsonl, emit session summaries as JSON."""
from __future__ import annotations
import json, sys, re, pathlib, collections, os

NOISE_TYPES = {"queue-operation", "progress"}
PATH_RE = re.compile(r"(?:/home/tt|/mnt/windows/Users/trent)(?:/[\w.\-]+)+")


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


def text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for b in content:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "text":
                parts.append(b.get("text", ""))
            elif b.get("type") == "tool_result":
                tc = b.get("content")
                if isinstance(tc, str):
                    parts.append(tc)
                elif isinstance(tc, list):
                    parts.extend(x.get("text", "") for x in tc if isinstance(x, dict))
        return "\n".join(parts)
    return ""


def first_user_msg(session_records):
    for r in session_records:
        if r.get("type") != "user":
            continue
        if r.get("isSidechain"):
            continue
        msg = r.get("message") or {}
        txt = text_of(msg.get("content")).strip()
        if not txt:
            continue
        if txt.startswith("<") and txt.endswith(">"):
            continue
        if "tool_use_id" in txt[:80]:
            continue
        return txt
    return None


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
    return {
        "slug": slug_dir.name,
        "cwd": cwd,
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
