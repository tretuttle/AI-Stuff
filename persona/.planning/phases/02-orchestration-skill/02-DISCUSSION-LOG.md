# Phase 2: Orchestration Skill - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-22
**Phase:** 02-orchestration-skill
**Areas discussed:** Persona selection, Review target input, Output collection, Skill UX, Gilfoyle mode

---

## Persona Selection

| Option | Description | Selected |
|--------|-------------|----------|
| Smart auto-selection | Auto-select relevant personas based on file type/language | |
| User-controlled with --only | User specifies exactly who runs via --only flag | ✓ |
| Always run all | No selection mechanism, all personas every time | |

**User's choice:** User-controlled with --only flag, three modes: all (default), subset, single
**Notes:** --only flag pulled forward from Phase 6 (SELC-01) into Phase 2. "The user knows who they want to hear from." No smart auto-selection — persona selection is a fundamental input, not an enhancement.

---

## Review Target Input

| Option | Description | Selected |
|--------|-------------|----------|
| File path / directory / glob | $ARGUMENTS accepts paths and globs | ✓ |
| --staged flag | Explicit flag for staged diff | |
| Empty = staged diff | No arguments defaults to staged changes | ✓ |

**User's choice:** $ARGUMENTS accepts file path, directory, or glob. Empty defaults to staged diff.
**Notes:** Examples provided: `/persona:review src/auth.ts`, `/persona:review packages/convex/ --only "Matt Pocock,Theo Browne"`, `/persona:review` (staged).

---

## Output Collection

| Option | Description | Selected |
|--------|-------------|----------|
| In-context return | Persona output flows back through agent return values | |
| File-based JSON | Each persona writes to persona-reviews/{name}.json | ✓ |
| File-based markdown | Each persona writes to persona-reviews/{name}.md | |

**User's choice:** File-based JSON to persona-reviews/{persona-name}.json
**Notes:** Synthesis step (Phase 3) reads files and presents ranked summary. Avoids context exhaustion with 14 personas.

---

## Skill UX

| Option | Description | Selected |
|--------|-------------|----------|
| /persona:orchestrate | Original skill name from CLAUDE.md | |
| /persona:review | Shorter, more intuitive name | ✓ |

**User's choice:** /persona:review with confirmation before dispatch, per-persona completion messages, and ranked severity summary after.
**Notes:** Confirmation shows who's running and what's being reviewed. Per-persona progress during execution.

---

## Gilfoyle Mode (user-initiated addition)

**User's choice:** Every persona gets a --gilfoyle flag. Two layers:
1. Base constraint (always active): Respect project architecture, critique implementation not technology choices
2. Gilfoyle activation: Drop all diplomacy, maximum opinion intensity

**Notes:** "Roast the implementation, not the architecture." Personas must read project stack from CLAUDE.md / package.json / codebase and treat those as non-negotiable. Gilfoyle mode adds instruction to hold nothing back. This was user-initiated scope — not a gray area from analysis.

---

## Claude's Discretion

- $ARGUMENTS parsing strategy (file paths vs flags)
- Agent vs Task tool for dispatch
- JSON output schema for persona-reviews
- Post-review summary format
- Whether persona-reviews/ should be gitignored

## Deferred Ideas

- Phase 6 roadmap update needed (SELC-01 pulled to Phase 2)
- Gilfoyle mode as configurable default (Phase 5/6)
