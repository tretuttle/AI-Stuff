---
name: conversation-recon
description: Use when the user asks about past Claude Code conversations — what they worked on, when they decided X, history of project Y, what they attempted before. Reads .conversation-identity.md files written by /project-recon:conversation-recon. If none exist or are older than 7 days, invoke the command first.
version: 1.0.0
---

# conversation-recon

Claude Code writes every session as jsonl under `~/.claude/projects/{slug}/`. This skill surfaces that history as queryable per-project stories.

## When to activate

- "What did I work on in {project}?"
- "When did I decide {X}?"
- "Find the session where we tried {Y}"
- "How many sessions on {project}?"
- "Which projects did I touch this week?"

## Flow

1. **Check central index first** at `~/.claude/conversation-index.md`.
   - Exists → scan for relevant slug/project.
   - Missing → run `/project-recon:conversation-recon sweep` (heavy — ask user first).

2. **For a specific project**, check `<project-cwd>/.conversation-identity.md`:
   - Present and `**Determined:**` within 7 days → read it, answer from it.
   - Missing or older → run `/project-recon:conversation-recon` in that project first.

3. **Cross-project queries** (e.g. "which projects mention ParkPal"):
   - Grep the central index + all `.conversation-identity.md` cross-reference tables.

## What this skill does NOT do

- No LLM summarization of session bodies (titles only, from first user message).
- No live parsing — always reads materialized identity/index files.
- No writes. Dispatches the command if data is missing.

## Supporting scripts

- `parse.py` — jsonl walker, DAG builder, session summarizer (stdlib only)
- `render.py` — markdown writer (identity file + index update)

Both are invoked by the command, not directly by this skill.
