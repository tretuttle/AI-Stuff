#!/usr/bin/env python3
"""Render conversation identity markdown + maintain central index.

Usage:
  parse.py <slug-dir> | render.py identity > <cwd>/.conversation-identity.md
  render.py index-update --slug X --cwd Y --status Z --sessions N --last DATE --identity PATH
"""
from __future__ import annotations
import json, sys, argparse, pathlib, os
from datetime import date as date_cls

CLAUDE_DIR = pathlib.Path.home() / ".claude"
INDEX_PATH = CLAUDE_DIR / "conversation-index.md"
STORE_DIR = CLAUDE_DIR / "conversations"
INDEX_HEADER = "# Conversation Index"
INDEX_SCHEMA = 1
VALID_STATUSES = ("current", "homedir", "orphaned", "empty")


def render_identity(data: dict) -> str:
    cwd = data.get("cwd") or "(unknown)"
    slug = data.get("slug") or "(unknown)"
    n = data.get("session_count", 0)
    span = data.get("span") or {}
    span_str = f"{span.get('first','?')} → {span.get('last','?')}" if span else "—"
    today = date_cls.today().isoformat()
    status = data.get("status", "current")

    out = []
    out.append("# Conversation Identity\n")
    out.append("**Schema:** 1")
    out.append(f"**Slug:** {slug}")
    out.append(f"**Cwd:** {cwd}")
    out.append(f"**Status:** {status}")
    out.append(f"**Sessions:** {n}")
    out.append(f"**Span:** {span_str}")
    out.append(f"**Determined:** {today}")
    out.append("")
    out.append("## Sessions\n")
    out.append("| Date | Title | File | Msgs | Tools | Resumed-from |")
    out.append("|------|-------|------|-----:|------:|--------------|")
    for s in data.get("sessions", []):
        tool_total = sum(s.get("tool_counts", {}).values())
        resumed = s.get("resumed_from")
        resumed_str = resumed[:8] if resumed else "—"
        file_short = (s.get("file") or "").replace(".jsonl", "")[:8]
        out.append(
            f"| {s.get('date') or '—'} "
            f"| {s.get('title') or '—'} "
            f"| {file_short} "
            f"| {s.get('msg_count', 0)} "
            f"| {tool_total} "
            f"| {resumed_str} |"
        )
    out.append("")
    out.append("## Cross-references\n")
    mentions = data.get("path_mentions", [])
    if not mentions:
        out.append("_No external paths mentioned._")
    else:
        out.append("| Path | Sessions | Mentions | Coupling |")
        out.append("|------|---------:|---------:|----------|")
        for m in mentions:
            coupling = "soft" if m.get("exists") else "intent"
            out.append(
                f"| {m['path']} | {m['sessions']} | {m['total_mentions']} | {coupling} |"
            )
    out.append("")
    return "\n".join(out)


def parse_index(text: str) -> dict:
    rows = {}
    in_table = False
    header_seen = False
    for line in text.splitlines():
        if line.strip().startswith("| Slug "):
            in_table = True
            header_seen = True
            continue
        if header_seen and line.strip().startswith("|---"):
            continue
        if in_table:
            if not line.strip().startswith("|"):
                in_table = False
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 6:
                continue
            slug, cwd, status, sessions, last, identity = cells[:6]
            rows[slug] = {
                "slug": slug, "cwd": cwd, "status": status,
                "sessions": sessions, "last": last, "identity": identity,
            }
    return rows


def write_index(rows: dict):
    today = date_cls.today().isoformat()
    out = [INDEX_HEADER, "", f"**Schema:** {INDEX_SCHEMA}", f"**Updated:** {today}", ""]
    out.append("## Projects\n")
    out.append("| Slug | Cwd | Status | Sessions | Last activity | Identity |")
    out.append("|------|-----|--------|---------:|---------------|----------|")
    for slug in sorted(rows):
        r = rows[slug]
        out.append(
            f"| {r['slug']} | {r['cwd']} | {r['status']} | {r['sessions']} | {r['last']} | {r['identity']} |"
        )
    out.append("")
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text("\n".join(out))


def update_index(args):
    rows = {}
    if INDEX_PATH.exists():
        rows = parse_index(INDEX_PATH.read_text())
    identity_cell = f"[link]({args.identity})" if args.identity and args.identity != "-" else "—"
    rows[args.slug] = {
        "slug": args.slug,
        "cwd": args.cwd,
        "status": args.status,
        "sessions": str(args.sessions),
        "last": args.last or "—",
        "identity": identity_cell,
    }
    write_index(rows)


def write_identity_all(data: dict, mirror: bool) -> dict:
    """Write identity to central store. Mirror to cwd if project-like and mirror=True.
    Return paths written + index entry details."""
    slug = data["slug"]
    cwd = data.get("cwd")
    status = data.get("status", "current")
    n = data.get("session_count", 0)
    span = data.get("span") or {}
    last = span.get("last", "")

    body = render_identity(data)
    STORE_DIR.mkdir(parents=True, exist_ok=True)
    central = STORE_DIR / f"{slug}.md"
    central.write_text(body)

    mirrored = None
    if mirror and status in ("current",) and cwd and os.path.isdir(cwd):
        mirrored = pathlib.Path(cwd) / ".conversation-identity.md"
        mirrored.write_text(body)

    # Update index automatically
    rows = {}
    if INDEX_PATH.exists():
        rows = parse_index(INDEX_PATH.read_text())
    identity_link = f"[central]({central})"
    if mirrored:
        identity_link = f"[central]({central}) · [cwd]({mirrored})"
    rows[slug] = {
        "slug": slug,
        "cwd": cwd or "—",
        "status": status,
        "sessions": str(n),
        "last": last or "—",
        "identity": identity_link,
    }
    write_index(rows)

    return {
        "central": str(central),
        "mirrored": str(mirrored) if mirrored else None,
        "status": status,
        "sessions": n,
    }


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("identity")
    wr = sub.add_parser("write", help="Read parse JSON from stdin; write central + optional cwd mirror + index")
    wr.add_argument("--no-mirror", action="store_true", help="Skip cwd mirror even for project-like dirs")
    iu = sub.add_parser("index-update")
    iu.add_argument("--slug", required=True)
    iu.add_argument("--cwd", required=True)
    iu.add_argument("--status", required=True, choices=list(VALID_STATUSES))
    iu.add_argument("--sessions", type=int, required=True)
    iu.add_argument("--last", default="")
    iu.add_argument("--identity", default="-")
    args = ap.parse_args()

    if args.cmd == "identity":
        data = json.load(sys.stdin)
        sys.stdout.write(render_identity(data))
    elif args.cmd == "write":
        data = json.load(sys.stdin)
        result = write_identity_all(data, mirror=not args.no_mirror)
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")
    elif args.cmd == "index-update":
        update_index(args)


if __name__ == "__main__":
    main()
