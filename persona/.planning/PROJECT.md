# Persona

## What This Is

A Claude Code plugin that orchestrates multi-persona code reviews. It dispatches code to multiple AI subagents — each with a distinct expert identity, philosophy, and priorities — collects their feedback in parallel, and synthesizes a unified review. Personas accumulate project-specific insights via memory, so feedback sharpens over time.

## Core Value

Diverse expert perspectives on code that a single reviewer would miss — each persona has its own philosophy, priorities, and blind spots.

## Requirements

### Validated

- ✓ Define expert persona agents with distinct identities and review styles — v1.0 (14 real developer personas)
- ✓ Orchestrate parallel multi-persona code reviews via a skill — v1.0 (/persona:review with --only, --gilfoyle)
- ✓ Parse and synthesize persona feedback into a unified review — v1.0 (Synthesis Protocol with dedup, confidence boosting, disagreements)
- ✓ Track review progress via hooks (SubagentStart/Stop) — v1.0 (inline bash hooks, Windows-compatible)
- ✓ Persist persona insights via project memory so feedback improves over time — v1.0 (memory: project + curation)
- ✓ Package as a Claude Code plugin installable from the tretuttle/AI-Stuff marketplace — v1.0

### Active

(Fresh for v2 — see /gsd:new-milestone)

### Out of Scope

- Custom persona creation UI — users can add `.md` agent files directly
- Real-time streaming of persona feedback — reviews complete then present results
- Non-code review use cases — focused on code review only for v1

## Context

Shipped v1.0 with 3,204 lines across 24 files (markdown + JSON).
- **14 persona agents:** ThePrimeagen, DHH, Chris Coyier, Dan Abramov, Evan You, Kent C. Dodds, Lee Robinson, Matt Mullenweg, Matt Pocock, Rich Harris, Scott Tolinski, Tanner Linsley, Theo Browne, Wes Bos
- **2 skills:** `/persona:review` (orchestration) and `/persona:parse-output` (standalone synthesis)
- **Hooks:** SubagentStart/SubagentStop for progress tracking
- **Memory:** project-scoped with structured curation templates
- **Distribution:** `/plugin install persona@ai-stuff` from tretuttle/AI-Stuff marketplace

## Constraints

- **Plugin format**: Must conform to Claude Code plugin conventions (plugin.json, agents/, skills/, hooks/)
- **Subagent system**: Persona agents must be `.md` subagent definitions that Claude Code can dispatch
- **No external deps**: Plugin should work with just Claude Code — no npm packages or external services
- **Marketplace compatible**: Must be installable via `/plugin install persona@ai-stuff`

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Use subagents for personas | Claude Code's native agent system — no custom infra needed | ✓ Good — 14 agents work reliably |
| Parallel dispatch | Reviews from multiple personas simultaneously for speed | ✓ Good — Task tool dispatches all in parallel |
| Memory for learning | `memory: project` lets personas accumulate insights | ✓ Good — structured curation prevents degradation |
| 14 real developer personas | Real voices (ThePrimeagen, DHH, etc.) vs generic archetypes | ✓ Good — distinctive, immediately attributable |
| File-based JSON output | Avoids context exhaustion with 14 personas | ✓ Good — persona-reviews/*.json cleanly separates concerns |
| Gilfoyle mode | "Roast the implementation, not the architecture" | ✓ Good — respects project stack choices |
| Shared Synthesis Protocol | Single source in reference.md for both skills | ✓ Good — prevents instruction drift |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-23 after v1.0 milestone*
