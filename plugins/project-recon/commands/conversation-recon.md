---
description: Parse Claude Code session history for this project (or all projects), extract the story, write conversation identity files
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
---

## Context

- Current directory: !`pwd`
- Mode arg: $ARGUMENTS
- Existing identity: !`cat .conversation-identity.md 2>/dev/null | head -30 || echo "No conversation-identity file yet"`
- Matching slug dir: !`bash -c 'slug=$(pwd | sed "s|/|-|g"); ls "/home/tt/.claude/projects/${slug}" 2>/dev/null | head -20 || echo "none"'`
- Central index: !`head -20 ~/.claude/conversation-index.md 2>/dev/null || echo "No central index yet"`
- Parser path: ${CLAUDE_PLUGIN_ROOT}/skills/conversation-recon/parse.py

## Mode Selection

Read $ARGUMENTS:
- `sweep` → run across every slug in `~/.claude/projects/`
- empty or `single` or a path → one project (current dir, or the path given)

## Step 0: Check Existing Identity (single mode only)

Read the existing identity above:
- Contains `**Schema:** 1` AND `**Determined:**` date within 7 days → report contents, stop.
- Exists but different schema or older → continue, will overwrite.
- No identity → continue.

## Step 1: Resolve Slug ↔ Cwd

**Single mode:**
1. Resolve target cwd (argument path, else `pwd`). Canonicalize with `realpath`.
2. Compute slug: replace every `/` with `-` (leading `-` included). Example `/home/tt/bleakBench` → `-home-tt-bleakBench`.
3. Check `~/.claude/projects/{slug}/` exists.
4. If dir missing → report "no session history for this project" and stop.
5. If dir exists but no `*.jsonl` → report "empty slug dir", still record in central index, stop before writing identity.

**Sweep mode:**
1. List all entries in `~/.claude/projects/`.
2. For each slug, decode slug → cwd (replace leading `-` with `/`, replace remaining `-` with `/`).
3. Check if cwd exists on disk. Classify: `current` (exists), `orphaned` (gone), `empty` (cwd exists but 0 jsonl).

## Step 2: Parse

Invoke the parser (stdlib only, no deps):

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/conversation-recon/parse.py "/home/tt/.claude/projects/{slug}"
```

Parser emits JSON on stdout:
```json
{
  "slug": "-home-tt-bleakBench",
  "cwd": "/home/tt/bleakBench",
  "session_count": 4,
  "span": {"first": "YYYY-MM-DD", "last": "YYYY-MM-DD"},
  "sessions": [
    {
      "id": "...", "file": "...jsonl", "date": "YYYY-MM-DD",
      "title": "first-user-msg-slugified", "first_user_msg": "...",
      "msg_count": 42, "tool_counts": {"Bash": 5, "Read": 8},
      "resumed_from": null,
      "path_mentions": [["/home/tt/ParkPal", 3]]
    }
  ],
  "path_mentions": [{"path":"/home/tt/ParkPal","total_mentions":3,"sessions":2,"exists":true}]
}
```

If `session_count == 0` → skip to central index update only.

## Step 3: Render Identity

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/conversation-recon/parse.py "/home/tt/.claude/projects/{slug}" \
  | python3 ${CLAUDE_PLUGIN_ROOT}/skills/conversation-recon/render.py identity > "{cwd}/.conversation-identity.md"
```

Expected shape:
```markdown
# Conversation Identity

**Schema:** 1
**Slug:** -home-tt-bleakBench
**Cwd:** /home/tt/bleakBench
**Sessions:** 4
**Span:** 2026-03-30 → 2026-04-03
**Determined:** YYYY-MM-DD

## Sessions

| Date | Title | File | Msgs | Tools | Resumed-from |
|------|-------|------|-----:|------:|--------------|
| 2026-03-31 | say-just-the-word-hello | d22ef050 | 2 | 0 | — |

## Cross-references

| Path | Sessions | Mentions | Coupling |
|------|---------:|---------:|----------|
| /home/tt/ParkPal | 2 | 3 | soft |
```

Coupling rule for cross-references:
- `hard` — path equals this project's cwd (self-reference, skipped by parser)
- `soft` — path appears in text, exists on disk
- `intent` — path mentioned but not on disk

## Step 4: Update Central Index

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/conversation-recon/render.py index-update \
  --slug "{slug}" --cwd "{cwd}" --status "{current|orphaned|empty}" \
  --sessions {N} --last "{YYYY-MM-DD}" --identity "{cwd}/.conversation-identity.md"
```

Renderer sorts alphabetically by slug and preserves entries for slugs not touched this run.

Index shape (`~/.claude/conversation-index.md`):
```markdown
# Conversation Index

**Schema:** 1
**Updated:** YYYY-MM-DD

## Projects

| Slug | Cwd | Status | Sessions | Last activity | Identity |
|------|-----|--------|---------:|---------------|----------|
| -home-tt-bleakBench | /home/tt/bleakBench | current | 4 | 2026-04-03 | [link](/home/tt/bleakBench/.conversation-identity.md) |
| -home-tt-old-thing | /home/tt/old-thing | orphaned | 12 | 2026-01-15 | — |
```

## Step 5: Report

Single mode: print session count, span, file paths written.

Sweep mode: summary table — total slugs, current/orphaned/empty counts, total sessions, path to central index. Do NOT dump per-project details.

---

## RULES

**BANNED WORDS:** Never use: stale, cleanup, clean up, deprecated, obsolete, outdated, dead, unused, should be deleted, should be removed. Factual state only: `orphaned` (cwd gone), `empty` (no jsonl), `current` (active).

**NEVER recommend deletion.** Report. User decides.

**NO LLM SUMMARIZATION YET.** Titles = first user message, that's it. Deep summaries are a future `conversation-scout` agent.

**IDEMPOTENT.** Re-run = identical output. Sort sessions by date, mentions by count desc, index by slug asc.

**ORPHAN HANDLING:** If cwd is gone, do NOT write an identity file. Record in central index only with `orphaned` status.

**SIDECHAIN MSGS:** Excluded from titles, counted separately.

**EMPTY SLUG DIRS:** Central index `empty`, no identity file.

**CROSS-PROJECT LINKAGE:** Path mentions become `soft`/`intent` hints. `/project-recon:recon` may consult `.conversation-identity.md` for candidates (separate integration).
