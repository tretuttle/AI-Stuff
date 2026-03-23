# Architecture

## How /persona:review Works

```
/persona:review src/auth.ts --only "ThePrimeagen,DHH" --gilfoyle
  |
  +- Parse arguments (target, --only, --gilfoyle, --min-confidence)
  +- Discover agents (Glob agents/*.md, exclude template.md)
  +- Filter to selected personas
  +- Clear persona-reviews/ (remove stale results)
  +- Show confirmation
  +- Dispatch all in parallel via Task tool
  |    +- theprimeagen reads code, returns JSON
  |    +- dhh reads code, returns JSON
  +- Write JSON to persona-reviews/
  +- Run Synthesis Protocol (dedup, boost, disagree, filter)
  +- Present unified review + save SYNTHESIS.md
```

**Key constraint:** The skill runs in the main conversation context (no `context: fork`) because the main agent must spawn persona subagents, and subagents cannot spawn other subagents.

## How /persona:become Works

```
/persona:become theprimeagen
  |
  +- Resolve name to agents/theprimeagen.md
  +- Read persona file
  +- Extract voice, beliefs, focus
  +- Apply as behavioral overlay (full tool access retained)
  +- Claude responds as ThePrimeagen until reset
```

## Plugin Structure

```
persona/
+-- .claude-plugin/
|   +-- plugin.json              # Manifest (name, version, hooks)
+-- agents/
|   +-- theprimeagen.md          # ThePrimeagen
|   +-- dhh.md                   # DHH
|   +-- chris-coyier.md          # Chris Coyier
|   +-- dan-abramov.md           # Dan Abramov
|   +-- evan-you.md              # Evan You
|   +-- kent-c-dodds.md          # Kent C. Dodds
|   +-- lee-robinson.md          # Lee Robinson
|   +-- matt-mullenweg.md        # Matt Mullenweg
|   +-- matt-pocock.md           # Matt Pocock
|   +-- rich-harris.md           # Rich Harris
|   +-- scott-tolinski.md        # Scott Tolinski
|   +-- tanner-linsley.md        # Tanner Linsley
|   +-- theo-browne.md           # Theo Browne
|   +-- wes-bos.md               # Wes Bos
|   +-- template.md              # Template for custom personas
+-- skills/
|   +-- review/
|   |   +-- SKILL.md             # /persona:review
|   |   +-- reference.md         # Roster, JSON schema, synthesis protocol
|   +-- parse-output/
|   |   +-- SKILL.md             # /persona:parse-output
|   +-- become/
|       +-- SKILL.md             # /persona:become
+-- hooks/
|   +-- hooks.json               # SubagentStart/SubagentStop
+-- docs/
|   +-- PERSONAS.md              # Full persona profiles
|   +-- SYNTHESIS.md             # Synthesis engine details + output format
|   +-- CUSTOM-PERSONAS.md       # Custom persona creation guide
|   +-- ARCHITECTURE.md          # This file
+-- memory/
|   +-- MEMORY-TEMPLATE.md       # Structured memory template
+-- .gitignore                   # Excludes persona-reviews/
+-- README.md                    # Quickstart + overview
```

## Memory System

Each persona uses `memory: project` to accumulate project-specific insights across sessions.

| Section | Budget | Purpose |
|---------|--------|---------|
| Active Patterns | 60 lines | Project conventions and patterns |
| Known Issues | 40 lines | Recurring problems |
| Style Conventions | 40 lines | Project style preferences |
| Resolved Items | 30 lines | Previously flagged, now fixed |
| Session Notes | 20 lines | Recent observations |

Memory is stored in `.claude/agent-memory/{agent-name}/MEMORY.md`. Personas curate their memory — replacing outdated entries rather than appending — to stay within a 190-line budget.

## Progress Tracking

SubagentStart/SubagentStop hooks log review progress:

```
[persona] Starting review: theprimeagen
[persona] Starting review: dhh
[persona] Finished review: theprimeagen
[persona] Finished review: dhh
```

Command-type hooks — zero LLM cost, deterministic execution.

## Project Stack Constraint

Every persona follows one hard rule:

> **Respect the project's technology choices.**

Personas read the project's stack from CLAUDE.md, package.json, and the codebase. Those choices are non-negotiable.

| Can do | Cannot do |
|--------|-----------|
| Critique how the stack is being used | Recommend replacing core technologies |
| Suggest better patterns within chosen tools | Suggest switching frameworks or languages |
| Point out reimplemented library features | Criticize the architecture decision itself |
