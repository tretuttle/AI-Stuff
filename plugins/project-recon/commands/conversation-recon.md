---
description: Parse Claude Code session history for this project (or all projects), extract the story, write conversation identity files
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
---

## Context

- Current directory: !`pwd`
- Mode arg: $ARGUMENTS
- Matching slug dir: !`bash -c 'slug=$(pwd | sed "s|/|-|g"); ls "/home/tt/.claude/projects/${slug}" 2>/dev/null | head -20 || echo "none"'`
- Central index: !`head -20 ~/.claude/conversation-index.md 2>/dev/null || echo "No central index yet"`
- Parser: ${CLAUDE_PLUGIN_ROOT}/skills/conversation-recon/parse.py
- Renderer: ${CLAUDE_PLUGIN_ROOT}/skills/conversation-recon/render.py

## Write locations

- **Central store (always):** `~/.claude/conversations/{slug}.md` — source of truth for every slug.
- **Project mirror (when applicable):** `<cwd>/.conversation-identity.md` — only written for `current`-status slugs (real project dirs). Home-dir, system-dir, orphaned, and empty slugs are NOT mirrored.
- **Central index:** `~/.claude/conversation-index.md` — always updated.

## Status values

Parser auto-computes status:
- `current` — cwd exists AND looks like a project (has `.git`, `package.json`, `CLAUDE.md`, etc., or is a direct subdir of `/home/tt/` that isn't a generic user dir).
- `homedir` — cwd exists but is a bare home or system dir (`/home/tt`, `/tmp`, `/`, etc.). Sessions are still tracked in central store but NOT mirrored to cwd.
- `orphaned` — cwd no longer exists on disk.
- `empty` — slug dir has no `*.jsonl` files.

## Mode Selection

Read $ARGUMENTS:
- `sweep` → run across every slug in `~/.claude/projects/`
- empty or `single` or a path → one project (current dir, or the path given)

## Step 1: Resolve Slug

**Single mode:**
1. Target cwd = argument path (if given, resolved via `realpath`), else `pwd`.
2. Compute slug: replace every `/` with `-`. `/home/tt/bleakBench` → `-home-tt-bleakBench`.
3. If `~/.claude/projects/{slug}/` missing → report "no session history" and stop.

**Sweep mode:**
1. List every entry in `~/.claude/projects/`.
2. For each slug, process in turn (fast — stdlib only).

## Step 2: Parse + Write

For each target slug:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/conversation-recon/parse.py \
    "/home/tt/.claude/projects/{slug}" \
  | python3 ${CLAUDE_PLUGIN_ROOT}/skills/conversation-recon/render.py write
```

The `write` subcommand:
1. Always writes `~/.claude/conversations/{slug}.md`
2. For `current` status AND `cwd` exists: also writes `<cwd>/.conversation-identity.md`
3. Updates `~/.claude/conversation-index.md`
4. Emits JSON result: `{central, mirrored, status, sessions}`

Flag: `--no-mirror` disables the cwd mirror entirely (useful when running against a dir you don't want touched).

## Step 3: Report

**Single mode:** print status, session count, span, and both file paths (central + mirrored).

**Sweep mode:** print summary table — total slugs by status (`current` / `homedir` / `orphaned` / `empty`), total sessions, path to central index. Do NOT dump per-project details.

---

## RULES

**BANNED WORDS:** Never use: stale, cleanup, clean up, deprecated, obsolete, outdated, dead, unused, should be deleted, should be removed. Factual state only: `current` (active project), `homedir` (home or system dir), `orphaned` (cwd gone), `empty` (no jsonl).

**NEVER recommend deletion.** Report. User decides.

**NO LLM SUMMARIZATION YET.** Titles = first user message (or slash-command name if the session started via one). Deep summaries are a future `conversation-scout` agent.

**IDEMPOTENT.** Re-run = identical output. Sort sessions by date, mentions by count desc, index by slug asc.

**HOMEDIR PROTECTION:** Never write `.conversation-identity.md` into `/home/tt/`, `/`, `/tmp`, `/mnt/...`, or any path matching the system-root list in parser. These remain tracked in the central store only.

**SIDECHAIN MSGS:** Excluded from titles, counted separately.

**CROSS-PROJECT LINKAGE:** Path mentions become `soft`/`intent` hints. `/project-recon:recon` may consult central store + cwd identity files for candidates (separate integration).
