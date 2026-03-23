# Phase 5: Persona Memory - Context

**Gathered:** 2026-03-22
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure phase — memory system setup)

<domain>
## Phase Boundary

Ensure persona agents accumulate project-specific insights via `memory: project` scope so their reviews become more relevant over repeated sessions. Agents already have `memory: project` in frontmatter — this phase adds structured MEMORY.md templates and curation instructions to prevent memory degradation (Pitfall 7).

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion — infrastructure phase with clear requirements. Key constraints:

- `memory: project` is already set in all 14 agent frontmatter (Phase 1)
- Pitfall 7: Memory degrades without structure — add explicit MEMORY.md structure templates with sections for "Active Patterns", "Known Issues", "Style Conventions" with max line counts
- Include curation instructions: "Before adding a new insight, check if it contradicts or supersedes an existing one. Remove the old entry."
- First 200 lines of MEMORY.md are loaded into context — keep entries concise and structured
- Memory scope is `project` (not `user`) — insights are project-specific

</decisions>

<canonical_refs>
## Canonical References

### Subagent Memory
- `research/04-subagents.md` — Memory scopes, MEMORY.md auto-loading, 200-line limit

### Pitfalls
- `.planning/research/PITFALLS.md` — Pitfall 7 (memory degrades into noise over time)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `agents/*.md` — All 14 agents already have `memory: project` in frontmatter
- Memory directories auto-created at `.claude/agent-memory/{agent-name}/`

### Integration Points
- Each persona's system prompt needs memory curation instructions
- MEMORY.md template structure for each persona

</code_context>

<specifics>
## Specific Ideas

No specific requirements — infrastructure phase.

</specifics>

<deferred>
## Deferred Ideas

None.

</deferred>

---

*Phase: 05-persona-memory*
*Context gathered: 2026-03-22*
