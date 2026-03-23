---
phase: 02-orchestration-skill
plan: 01
subsystem: orchestration
tags: [skills, subagents, task-tool, json-schema, gilfoyle-mode]

requires:
  - phase: 01-plugin-foundation-and-persona-agents
    provides: "14 persona agent .md files with frontmatter and review prompts"
provides:
  - "/persona:review orchestration skill (skills/review/SKILL.md)"
  - "Persona roster and JSON output schema reference (skills/review/reference.md)"
  - ".gitignore excluding persona-reviews/"
affects: [03-synthesis, 04-hooks, 06-enhancements]

tech-stack:
  added: []
  patterns: ["SKILL.md + reference.md split for skills under 500 lines", "Task tool parallel dispatch for subagent orchestration", "File-based JSON output collection to avoid context exhaustion"]

key-files:
  created:
    - skills/review/SKILL.md
    - skills/review/reference.md
    - .gitignore
  modified: []

key-decisions:
  - "Task tool over Agent tool for fire-and-forget parallel persona dispatch"
  - "Orchestrator writes persona output files (Option B) -- personas stay read-only"
  - "Per-dispatch JSON override -- personas keep markdown format for direct invocation"

patterns-established:
  - "SKILL.md references reference.md for roster/schema details to stay under 500 lines"
  - "Argument parsing via natural language instructions, not shell scripts"

metrics:
  duration: "2min"
  completed: "2026-03-23T01:07:00Z"
---

# Phase 02 Plan 01: Orchestration Skill Summary

/persona:review orchestration skill with parallel Task tool dispatch, argument parsing for --only and --gilfoyle flags, file-based JSON output collection to persona-reviews/, and severity summary

## What Was Built

### skills/review/reference.md
Supporting reference file containing:
- Persona roster table mapping all 14 display names to kebab-case agent names and file paths
- Complete JSON output schema with field reference, severity levels, and a multi-finding example
- Gilfoyle mode block for injection into persona task prompts

### skills/review/SKILL.md
User-invocable `/persona:review` orchestration skill with:
- **Argument parsing**: Extracts review target, `--only` persona filter, and `--gilfoyle` flag from `$ARGUMENTS`
- **Default to staged diff**: When no target provided, uses `git diff --staged`
- **Pre-dispatch confirmation**: Shows personas, target, and Gilfoyle status before proceeding
- **Setup**: Creates `persona-reviews/` directory via `mkdir -p`
- **Parallel dispatch**: Explicit Task tool instructions to dispatch all selected personas simultaneously
- **Anti-self-review guard**: "Do NOT review the code yourself. Do NOT skip delegation."
- **Collection**: Writes each persona's JSON output to `persona-reviews/{agent-name}.json` via Write tool
- **Severity summary**: Ranked listing of critical, warning, and suggestion findings with persona attribution

### .gitignore
Excludes `persona-reviews/` from version control (ephemeral review output).

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | 4155af7 | Create reference.md with persona roster and JSON schema |
| 2 | 9d02804 | Create orchestration skill SKILL.md and .gitignore |

## Deviations from Plan

None -- plan executed exactly as written.

## Known Stubs

None. All files are complete and functional.

## Verification Results

- `name: review` present in SKILL.md frontmatter
- `context: fork` NOT present in SKILL.md (0 matches)
- All 14 agent names present in reference.md
- SKILL.md is 142 lines (under 500 line limit)
- `$ARGUMENTS`, `--only`, `--gilfoyle`, `git diff --staged`, `Task tool`, `persona-reviews/`, `mkdir -p`, `Write tool`, `reference.md` all present in SKILL.md
- `.gitignore` contains `persona-reviews/`

## Self-Check: PASSED

All files exist. All commits verified.
