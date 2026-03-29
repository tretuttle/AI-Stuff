---
description: Identify this project, find what it belongs to, and write identity files
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, Agent
---

## Context

- Current directory: !`pwd`
- Directory contents: !`ls -la`
- Git info: !`git log --oneline -5 2>/dev/null || echo "Not a git repo"` / !`git remote -v 2>/dev/null || echo "No remotes"`
- Existing identity: !`cat .project-identity.md 2>/dev/null || echo "No identity file yet"`
- Reference files: !`find . -maxdepth 3 -name "reference.md" 2>/dev/null | head -20`
- Project-todo: !`ls project-todo/ 2>/dev/null || echo "No project-todo"`

## Step 0: Check Existing Identity

Check the existing identity above:
- If it contains `**Schema:** 2` → report its contents and stop. Already current.
- If it exists but has no `**Schema:**` line, or schema is not `2` → delete it and continue.
- If no identity file → continue.

## Step 1: Identify This Project

From the context above, determine what this project IS in 2-3 sentences. Not every project is a git repo or has a package.json — describe what you see. This becomes the "origin summary" for scouts.

## Step 1b: Read Declared Relationships

If reference.md files were found above, read each one. Paths mentioned in them are AUTOMATIC scout candidates with reason "declared in reference.md".

If project-todo/ exists, read all reference.md files inside it:
```bash
for f in project-todo/*/reference.md project-todo/*/*/reference.md; do [ -f "$f" ] && echo "=== $f ===" && cat "$f" && echo; done 2>/dev/null
```

## Step 2: Extract Keywords

Pull out 3-5 distinctive search terms from Step 1:
- Directory name, package name, git remote repo name (if applicable)
- Unique filenames, topic-specific words, unusual subdirectory names
- Do NOT use generic terms (react, typescript, utils, src, images, docs)

## Step 3: Sweep Both SSDs

For each keyword, search OUTSIDE the current directory:

```bash
# Name match
find /home/tt -maxdepth 3 -type d -iname "*{keyword}*" 2>/dev/null | grep -v '/\.' | grep -v node_modules | grep -v AppData | grep -v __pycache__ | grep -v "$(pwd)"
find /mnt/windows/Users/trent -maxdepth 3 -type d -iname "*{keyword}*" 2>/dev/null | grep -v '/\.' | grep -v node_modules | grep -v AppData

# Deep reference.md search — find other projects that mention THIS project
rg -l "{project-name}" /home/tt --max-depth 6 -g 'reference.md' 2>/dev/null | grep -v '/\.' | grep -v "$(pwd)" | head -15

# Content match
rg -l "{distinctive-term}" /home/tt --max-depth 4 -g '*.{json,md,toml,yml}' 2>/dev/null | grep -v '/\.' | grep -v "$(pwd)" | head -15

# Git remote match (only if this is a git repo)
find /home/tt -maxdepth 4 -name config -path "*/.git/*" -exec grep -l "{remote-fragment}" {} \; 2>/dev/null | grep -v "$(pwd)"

# Windows Claude history (READ ONLY — count sessions, never dispatch scouts here)
ls -d /mnt/windows/Users/trent/.claude/projects/C--Users-trent*{name}* 2>/dev/null
```

When a reference.md mentions this project, trace back to the PROJECT ROOT (nearest parent with `.git/`, `package.json`, `CLAUDE.md`, or direct child of `/home/tt/`).

Merge candidates from Step 1b and Step 3. Deduplicate. Filter out:
- The current directory
- Dotfile directories (`.claude/`, `.config/`, `.local/`, `.git/`, etc.)
- AppData-equivalents (`AppData/`, `scoop/`, `__pycache__/`)
- `node_modules/`, `dist/`, `build/`
- System dirs (Desktop, Documents — unless Documents/GitHub)

Max 8 candidates. Rank by name similarity if more.

## Step 4: Dispatch Scouts

**For EACH candidate, launch a project-recon:project-scout agent using the Agent tool.** Launch them in parallel (multiple Agent tool calls in one message).

Each scout needs:
1. The candidate path
2. The origin summary from Step 1
3. The origin path (this directory)
4. Why it was flagged (keyword match or "declared in reference.md")

**Every candidate gets a scout. No exceptions.** Not for mirrors, not for obvious cases.

Wait for all scouts to report back.

## Step 5: Write Identity

Based on scout reports, write `.project-identity.md` in the current directory:

```markdown
# Project Identity

**Schema:** 2
**Name:** {project name}
**Path:** {absolute path}
**What it is:** {2-3 sentence description}
**Determined:** {YYYY-MM-DD}

## Locations

| SSD | Path | Status |
|-----|------|--------|
| Arch | {path or "not found"} | {current | not present} |
| Windows | {path or "not found"} | {current | not present} |
| Claude History | {.claude/projects path or "none"} | {N sessions, latest YYYY-MM-DD} |

## Relationships

| Path | Relationship | Coupling | Notes |
|------|-------------|----------|-------|
| /path/to/parent | child-of | hard | Extracted from this monolith |
| /path/to/tool | feeds-into | soft | Planned rendering engine per reference.md |
| /path/to/ref | reference-material | intent | Design inspiration for the overhaul |
| /path/to/copy | mirror | hard | Same remote, same HEAD |
| /path/to/old | historical | soft | Earlier iteration, diverged at commit abc123 |
| /path/to/try | experiment | soft | Tested Next.js migration, not adopted |
```

**Format rules:**
- No single "Role" field. The Relationships table IS the identity.
- Coupling: `hard` (code/git link), `soft` (declared/planned), `intent` (makes sense to connect)
- A project can have MULTIPLE relationships at different strengths
- Zero relationships = standalone (leave table empty with a note)
- Locations always has all three rows
- If appending to existing, preserve existing rows

## Step 6: Report

Tell the user what this project is, its relationships, and where identity files were written.

---

## RULES

**BANNED WORDS:** Never use: stale, cleanup, clean up, deprecated, obsolete, outdated, dead, unused, should be deleted, should be removed. Describe state factually instead.

**NEVER recommend cleanup or deletion.** Report relationships. User decides.

**NO CHAINING:** Candidates come from your sweep and reference.md declarations only. Never follow references inside `.project-identity.md` files.

**NO DOTFILES/APPDATA:** Never dispatch scouts to dotfile or AppData directories.

**RELATIONSHIP TYPES:** child-of, parent-of, uses, used-by, feeds-into, fed-by, mirror, fork, orphaned-branch, historical, experiment, reference-material, unrelated.

**THINK CREATIVELY:** If a candidate isn't linked by code but would obviously be useful to this project — if connecting them makes practical sense — that's an `intent` coupling. Report it.
