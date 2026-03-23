# Roadmap: Persona

## Overview

Persona is a Claude Code plugin that orchestrates multi-persona code reviews. The build progresses from defining the expert personas themselves, through the orchestration and synthesis pipeline that connects them, to lifecycle hooks, persistent memory, and final packaging. Each phase delivers a testable increment: individual personas, then dispatch, then unified output, then progress UX, then learning, then marketplace readiness.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Plugin Foundation and Persona Agents** - Valid plugin manifest and 3+ distinct persona agents with structured output contracts
- [ ] **Phase 2: Orchestration Skill** - Working /persona:review skill that dispatches all personas in parallel with file targeting
- [ ] **Phase 3: Synthesis and Confidence Scoring** - Unified review output with deduplication, attribution, severity ranking, and confidence filtering
- [ ] **Phase 4: Progress Tracking Hooks** - SubagentStart/Stop hooks that report persona review progress on Windows
- [ ] **Phase 5: Persona Memory** - Persistent per-persona project insights that improve feedback over time
- [ ] **Phase 6: Selective Invocation and Packaging** - Persona selection by name, template persona, documentation, and marketplace readiness

## Phase Details

### Phase 1: Plugin Foundation and Persona Agents
**Goal**: Users have a valid plugin with 14 real developer persona agents (ThePrimeagen, DHH, Chris Coyier, Dan Abramov, Evan You, Kent C. Dodds, Lee Robinson, Matt Mullenweg, Matt Pocock, Rich Harris, Scott Tolinski, Tanner Linsley, Theo Browne, Wes Bos) that can each independently review code through distinct philosophical lenses
**Depends on**: Nothing (first phase)
**Requirements**: PERS-01, PERS-02, PERS-03, PERS-04, PERS-05, PLUG-01
**Success Criteria** (what must be TRUE):
  1. Plugin has a valid plugin.json manifest with name, version, description, and author fields
  2. At least 3 persona agents exist, each with a unique name and distinct review philosophy (e.g., security-adversarial, architecture-structural, readability-empathetic)
  3. Each persona produces structured findings with severity, file, explanation, and recommendation fields
  4. Persona agents can only read code (Glob, Grep, Read, non-destructive Bash) -- they cannot edit files
  5. Persona agents reference and respect CLAUDE.md project conventions in their reviews
**Plans:** 3 plans
Plans:
- [x] 01-01-PLAN.md — Standardize 4 existing agents (ThePrimeagen, DHH, Dan Abramov, Matt Pocock) and verify plugin.json
- [x] 01-02-PLAN.md — Write complete personas for Chris Coyier, Evan You, Kent C. Dodds, Lee Robinson, Matt Mullenweg
- [x] 01-03-PLAN.md — Write complete personas for Rich Harris, Scott Tolinski, Tanner Linsley, Theo Browne, Wes Bos

### Phase 2: Orchestration Skill
**Goal**: Users can invoke /persona:review to dispatch all persona agents in parallel against targeted files or changes, with persona selection and Gilfoyle mode
**Depends on**: Phase 1
**Requirements**: ORCH-01, ORCH-02, ORCH-03, ORCH-04, ORCH-05
**Success Criteria** (what must be TRUE):
  1. User can run `/persona:review` (or equivalent skill name) to trigger a multi-persona review
  2. All persona agents are dispatched in parallel from the main agent context (not sequentially, not from a forked context)
  3. User can target specific files or staged changes via skill arguments (e.g., `/persona:review src/auth.ts` or `/persona:review --staged`)
  4. Structured output from all persona agents is collected back into the main agent context for downstream processing
**Plans:** 2 plans
Plans:
- [x] 02-01-PLAN.md — Create /persona:review skill (SKILL.md + reference.md) with argument parsing, parallel dispatch, and file-based output collection
- [x] 02-02-PLAN.md — Update all 14 persona agents with project-stack constraint, Gilfoyle mode, and JSON output support

### Phase 3: Synthesis and Confidence Scoring
**Goal**: Users receive a single unified review that merges, deduplicates, and ranks findings from all personas with confidence-based filtering
**Depends on**: Phase 2
**Requirements**: SYNT-01, SYNT-02, SYNT-03, SYNT-04, SYNT-05, CONF-01, CONF-02
**Success Criteria** (what must be TRUE):
  1. User can invoke synthesis (via /persona:parse-output or as part of the orchestration flow) to get a unified review from all persona outputs
  2. Duplicate findings flagged by multiple personas appear once, attributed to all originating personas
  3. Findings are ranked by severity (critical / warning / suggestion) and each carries a confidence score (0-100)
  4. Cross-persona disagreements are surfaced explicitly rather than silently resolved
  5. User can filter findings below a configurable confidence threshold
**Plans:** 2 plans
Plans:
- [x] 03-01-PLAN.md — Write Synthesis Protocol in reference.md and create standalone /persona:parse-output skill
- [x] 03-02-PLAN.md — Integrate synthesis into /persona:review orchestration flow with sample test data and verification

### Phase 4: Progress Tracking Hooks
**Goal**: Users see real-time feedback about which personas are running and which have completed during a review
**Depends on**: Phase 2
**Requirements**: PROG-01, PROG-02
**Success Criteria** (what must be TRUE):
  1. SubagentStart and SubagentStop hooks fire and report which persona is starting or finishing
  2. Hook scripts work correctly on Windows (inline bash commands, no script file references that fail silently)
**Plans:** 1 plan
Plans:
- [x] 04-01-PLAN.md — Create hooks/hooks.json with SubagentStart/Stop progress hooks and register in plugin.json

### Phase 5: Persona Memory
**Goal**: Persona agents accumulate project-specific insights so their reviews become more relevant over repeated sessions
**Depends on**: Phase 1
**Requirements**: MEMO-01, MEMO-02
**Success Criteria** (what must be TRUE):
  1. Each persona agent uses `memory: project` scope to persist review insights between sessions
  2. After multiple review sessions, persona feedback demonstrably references project-specific patterns or conventions learned from prior reviews
**Plans:** 1 plan
Plans:
- [x] 05-01-PLAN.md — Create MEMORY.md template and add memory curation instructions to all 14 persona agents

### Phase 6: Selective Invocation and Packaging
**Goal**: Users can run specific personas by name, create custom personas from a template, and install the plugin from the marketplace
**Depends on**: Phase 2, Phase 3
**Requirements**: SELC-01, SELC-02, PLUG-02, PLUG-03, PLUG-04
**Success Criteria** (what must be TRUE):
  1. User can invoke specific personas by name (e.g., `/persona:review --only security,architect`) and only those personas run
  2. When no persona selection is specified, all persona agents run (default behavior)
  3. Plugin is installable via `/plugin install persona@ai-stuff` from the tretuttle/AI-Stuff marketplace
  4. A template persona `.md` file exists for users who want to create custom personas
  5. Plugin README documents usage, persona descriptions, and the custom persona contract
**Plans:** 2 plans
Plans:
- [x] 06-01-PLAN.md — Template persona, marketplace-ready plugin.json, and marketplace.json
- [x] 06-02-PLAN.md — README documentation with usage, personas, and custom persona contract

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Plugin Foundation and Persona Agents | 0/3 | Planning complete | - |
| 2. Orchestration Skill | 0/2 | Planning complete | - |
| 3. Synthesis and Confidence Scoring | 0/2 | Planning complete | - |
| 4. Progress Tracking Hooks | 0/1 | Planning complete | - |
| 5. Persona Memory | 0/1 | Planning complete | - |
| 6. Selective Invocation and Packaging | 0/2 | Planning complete | - |
