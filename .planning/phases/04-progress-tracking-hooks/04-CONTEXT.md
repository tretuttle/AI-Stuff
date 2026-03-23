# Phase 4: Progress Tracking Hooks - Context

**Gathered:** 2026-03-22
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure phase — no discuss needed)

<domain>
## Phase Boundary

Deliver SubagentStart and SubagentStop hooks that report which persona is starting or finishing during a review. Hook scripts must work correctly on Windows using inline bash commands (no script file references).

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion — pure infrastructure phase. Use ROADMAP phase goal, success criteria, and codebase conventions to guide decisions.

Key constraints from CLAUDE.md and pitfalls research:
- Use `hooks/hooks.json` for plugin-level hooks (agent-level hooks are silently ignored — Pitfall 2)
- Use inline bash commands, NOT script file references (Windows compatibility — Pitfall 4)
- Always add `"async": true` to SessionStart hooks
- Use command-type hooks (zero LLM cost, deterministic)
- Matchers must use exact agent names from agents/*.md frontmatter (case-sensitive — Pitfall 12)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Hooks System
- `research/08-hooks-guide.md` — Hooks patterns, event types, matchers
- `research/hooks-reference.md` — Complete hooks reference with event schemas, SubagentStart/SubagentStop input format

### Pitfalls
- `.planning/research/PITFALLS.md` — Pitfall 2 (plugin agents ignore hooks), Pitfall 4 (Windows hook scripts), Pitfall 12 (matcher case sensitivity)

### Plugin System
- `research/02-plugins-reference.md` — Plugin hook configuration via hooks/hooks.json

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `agents/*.md` — 14 persona agents with frontmatter names (matchers need these exact names)
- `.claude-plugin/plugin.json` — Plugin manifest (hooks.json location)
- `skills/review/reference.md` — Persona roster with agent names

### Integration Points
- `hooks/hooks.json` — Must be created at plugin root (not inside .claude-plugin/)
- SubagentStart/SubagentStop events fire when persona agents are spawned/complete during /persona:review

</code_context>

<specifics>
## Specific Ideas

No specific requirements — infrastructure phase. Refer to ROADMAP phase description and success criteria.

</specifics>

<deferred>
## Deferred Ideas

None — infrastructure phase.

</deferred>

---

*Phase: 04-progress-tracking-hooks*
*Context gathered: 2026-03-22*
