<!-- PROJECT SHIELDS -->
<div align="center">

<img src="../../assets/works-on-my-machine.svg" alt="Works on My Machine" height="28" />
&nbsp;&nbsp;
<img src="../../assets/designed-in-ms-paint.svg" alt="Designed in MS Paint" height="28" />

</div>

<div align="center">

# project-recon

**Project reconnaissance and relationship mapping for [Claude Code](https://claude.com/claude-code)**

Scans a project directory, sweeps both SSDs for related projects, determines master/child/util relationships, and writes standardized identity files.

</div>

---

## Why

You have projects scattered across two SSDs (Arch Linux + Windows dual-boot), with duplicates, forks, experiments, and extractions living in different locations. Some are children of monoliths, some are standalone masters, some are stale copies. You need a way to map the relationships without manually tracing every directory.

Run `/recon` from any project directory and let the agents figure it out.

## Features

- **One-command scan** — `/recon` identifies the current project, searches for relatives, and writes identity files
- **Dual-SSD awareness** — searches both `/home/tt/` (Arch) and `/mnt/windows/Users/trent/` (Windows, read-only)
- **Orchestrator + scout architecture** — orchestrator stays in the current dir, dispatches parallel scouts to candidates
- **Standardized identity files** — `.project-identity.md` with a fixed schema: role, locations, relationships
- **No broadcast storms** — scouts never chain. One hop deep. If an identity file already exists, read it and exit.
- **Claude Code history tracking** — finds and counts Windows-side session histories

---

## Getting Started

### Install

```
/plugin marketplace add tretuttle/AI-Stuff
/plugin install project-recon@ai-stuff
```

### Run

```
/recon
```

That's it. From any project directory.

---

## How It Works

```
/recon (from any project dir)
  │
  ▼
recon-orchestrator (stays in current dir)
  │
  ├─ Step 0: If .project-identity.md exists → report and stop
  ├─ Step 1: Scan this directory → "what am I?"
  ├─ Step 2: Extract search keywords
  ├─ Step 3: Sweep outside this dir across both SSDs
  ├─ Step 4: Dispatch project-scout into each candidate dir (parallel)
  │    │
  │    ▼
  │  project-scout (goes to candidate dir)
  │    ├─ Step 0: If .project-identity.md exists → read, report, stop
  │    ├─ Scans the candidate
  │    ├─ Determines relationship from origin's perspective
  │    ├─ Writes .project-identity.md in candidate's root
  │    └─ Reports back to orchestrator
  │
  ├─ Step 5: Writes .project-identity.md in current dir
  └─ Step 6: Reports summary to user
```

## Commands

| Command | Description |
|---------|-------------|
| `/recon` | Full project reconnaissance from the current directory |

## Identity File Format

Every `.project-identity.md` follows this exact schema:

```markdown
# Project Identity

**Name:** project-name
**Path:** /absolute/path
**What it is:** 2-3 sentence description.
**Role:** master | child-of /path/to/parent | util-of /path/to/parent
**Determined:** YYYY-MM-DD

## Locations

| SSD | Path | Status |
|-----|------|--------|
| Arch | /home/tt/... | current/stale/not present |
| Windows | /mnt/windows/... | current/stale/not present |
| Claude History | .claude/projects/... | N sessions, latest date |

## Relationships

| Path | Relationship | Confidence | Notes |
|------|-------------|------------|-------|
| /path/to/... | this is child-of | high | Extracted from monolith |
```

## Relationship Types

| Type | Meaning |
|------|---------|
| `master` | Standalone project, not derived from anything |
| `child-of` | Extracted or derived from a parent project |
| `util-of` | A utility/tool used by another project |
| `duplicate-of` | Same project in a different location |
| `fork-of` | Shared ancestry, diverged direction |
| `experiment-of` | Scratch/experimental version |

---

## Design Decisions

- **Scouts write first, orchestrator writes last** — the scout writes identity in the candidate dir, reports back, then the orchestrator writes identity in the origin dir based on all reports
- **No chaining** — scouts never follow references found in existing identity files. The graph is always one hop deep.
- **Early exit** — if `.project-identity.md` already exists at any level (command, orchestrator, scout), read it and stop. No re-scanning.
- **Merge, never overwrite** — if a scout finds an existing identity file, it appends new relationship rows instead of replacing the file

---

<div align="center">

<a href="https://claude.com/claude-code"><img src="../../assets/open-in-claude-code.svg" alt="Open in Claude Code" height="28" /></a>
&nbsp;&nbsp;
<img src="../../assets/works-on-my-machine.svg" alt="Works on My Machine" height="28" />
&nbsp;&nbsp;
<img src="../../assets/designed-in-ms-paint.svg" alt="Designed in MS Paint" height="28" />

</div>

---

## License

MIT
