---
name: "codex-session-export"
description: "List saved Codex CLI sessions, surface session IDs with friendly resume-style labels, and export any session transcript to JSONL and readable TXT without modifying the original resumable session. Use when the user wants to export a Codex chat, browse saved sessions, recover a session ID, or see likely /resume picker names."
metadata:
  short-description: "List and export Codex CLI sessions safely"
---

# Codex Session Export

Use this skill when the user wants to:

- export a Codex transcript
- find a saved Codex session ID
- browse saved Codex sessions with friendly labels
- export a session to `.jsonl` and/or `.txt`
- preserve resumability while exporting

## Rules

- Never modify files under `~/.codex/sessions/`.
- Export by copying from the saved session file.
- Keep exports separate from the original so `codex resume <SESSION_ID>` still works.
- Prefer the helper script in `scripts/codex_session_export.py` instead of re-deriving paths manually.

## Workflow

1. Run the helper script in `list` mode to discover all saved sessions.
2. If the user did not specify a session, show the list with:
   - session ID
   - started time
   - cwd
   - friendly label
3. If the user gave a full or partial session ID, resolve it with the helper script.
4. Export the selected session with the helper script.
5. Report:
   - source session file
   - export file paths
   - confirmation that the original session was left untouched

## Friendly Labels

The helper script attempts these sources in order:

1. explicit title-like fields if Codex ever stores them in session metadata
2. earliest prompt text from `~/.codex/history.jsonl`
3. first user message found in the session JSONL
4. filename fallback

Treat the label as a best-effort approximation of what `/resume` likely shows unless an explicit stored title is present.

## Commands

List sessions:

```bash
python3 "$HOME/.codex/skills/codex-session-export/scripts/codex_session_export.py" list
```

List sessions as JSON:

```bash
python3 "$HOME/.codex/skills/codex-session-export/scripts/codex_session_export.py" list --json
```

Export a session to both `.jsonl` and `.txt`:

```bash
python3 "$HOME/.codex/skills/codex-session-export/scripts/codex_session_export.py" export --session 019cd2d5-5a4a-7fc3-86dc-a2039c5307b3
```

Export only readable text:

```bash
python3 "$HOME/.codex/skills/codex-session-export/scripts/codex_session_export.py" export --session 019cd2d5-5a4a-7fc3-86dc-a2039c5307b3 --formats txt
```

Choose a different export directory:

```bash
python3 "$HOME/.codex/skills/codex-session-export/scripts/codex_session_export.py" export --session latest --output-dir "$HOME/Downloads"
```

## Behavior Notes

- `latest` resolves to the most recently saved session file.
- Partial session IDs are allowed if they resolve to exactly one match.
- On ambiguity, show the matching sessions and ask the user which one they want.
- Default export directory is `$HOME/Downloads`.
- Default formats are `jsonl,txt`.

