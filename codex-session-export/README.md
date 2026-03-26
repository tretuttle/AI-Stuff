<!-- PROJECT SHIELDS -->
<div align="center">

<img src="../assets/works-on-my-machine.svg" alt="Works on My Machine" height="28" />
&nbsp;&nbsp;
<img src="../assets/designed-in-ms-paint.svg" alt="Designed in MS Paint" height="28" />

</div>

<div align="center">

# codex-session-export

**Saved session discovery and transcript export for Codex CLI**

Lists saved Codex sessions, shows session IDs with friendly labels, and exports any session to `.jsonl` and readable `.txt` without touching the original resumable session.

</div>

---

## What It Does

- Finds saved Codex CLI sessions from `~/.codex/sessions`
- Surfaces the session UUID for each saved chat
- Derives a friendly label for each session from the best available source
- Exports a selected session to raw `.jsonl` and/or readable `.txt`
- Leaves the original session file untouched so `codex resume <SESSION_ID>` still works

---

## Install With Codex

Clone this repo if you have not already:

```bash
gh repo clone tretuttle/AI-Stuff ~/AI-Stuff
```

Install by copying the skill into your Codex skills directory:

```bash
mkdir -p ~/.codex/skills
cp -R ~/AI-Stuff/codex-session-export ~/.codex/skills/
```

Or install as a symlink so updates in the repo are reflected immediately:

```bash
mkdir -p ~/.codex/skills
ln -s ~/AI-Stuff/codex-session-export ~/.codex/skills/codex-session-export
```

If you already have a local copy of the skill in `~/.codex/skills`, replace it first or sync the files manually.

---

## Use In Codex

Ask Codex to use the skill directly:

```text
$codex-session-export list my saved Codex sessions
```

Examples:

```text
$codex-session-export show my recent session IDs with friendly names
$codex-session-export export session 019cd2d5-5a4a-7fc3-86dc-a2039c5307b3 to Downloads
$codex-session-export export the latest Codex transcript as txt only
```

You can also run the helper script directly:

```bash
python3 ~/.codex/skills/codex-session-export/scripts/codex_session_export.py list
python3 ~/.codex/skills/codex-session-export/scripts/codex_session_export.py export --session latest
python3 ~/.codex/skills/codex-session-export/scripts/codex_session_export.py export --session 019cd2d5-5a4a-7fc3-86dc-a2039c5307b3 --formats txt
```

---

## Friendly Labels

The skill tries these sources in order:

1. explicit title-like metadata if Codex stores one
2. the earliest prompt for that session from `~/.codex/history.jsonl`
3. the first real user message in the session JSONL
4. the session filename as a fallback

That makes the labels a practical approximation of what you likely saw in `/resume`, even when Codex does not expose a formal saved title.

---

## Output

By default, exports go to `~/Downloads`:

- `codex-transcript-<SESSION_ID>.jsonl`
- `codex-transcript-<SESSION_ID>.txt`

The saved session under `~/.codex/sessions/...` is not modified.

---

## Files

- `SKILL.md`: Skill instructions for Codex
- `agents/openai.yaml`: UI metadata for discovery
- `scripts/codex_session_export.py`: Session listing and export helper

