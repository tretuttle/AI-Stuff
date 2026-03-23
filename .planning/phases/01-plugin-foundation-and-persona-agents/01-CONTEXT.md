# Phase 1: Plugin Foundation and Persona Agents - Context

**Gathered:** 2026-03-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver a valid Claude Code plugin with 4 distinct expert persona agents. Each persona independently reviews code through a different philosophical lens and produces structured findings. This phase does NOT include orchestration (Phase 2), synthesis (Phase 3), or hooks (Phase 4) — personas are standalone agents that can be tested individually.

</domain>

<decisions>
## Implementation Decisions

### Persona Roster
- **D-01:** Start with 4 persona agents covering complementary review dimensions:
  1. **Security Hardener** — thinks adversarially, looks for vulnerabilities, injection points, auth gaps, data exposure
  2. **The Architect** — evaluates structural decisions, coupling, abstractions, component boundaries, scalability patterns
  3. **Readability Advocate** — reviews from a "would a new team member understand this?" lens, naming, complexity, documentation gaps
  4. **The Pragmatist** — challenges over-engineering, premature abstraction, unnecessary complexity, focuses on shipping working code

### Review Voice and Tone
- **D-02:** Personas should have strong, memorable character voices — not subtle professional variations. This is the core differentiator. Each persona's feedback should be immediately attributable by voice alone. Think "DHH reviewing your code" not "Reviewer #3".
- **D-03:** Character voice is expressed through: what they notice first, how they frame issues, what they consider important, their tolerance for tradeoffs. NOT through gimmicks, catchphrases, or roleplay.

### Output Structure
- **D-04:** Each persona produces findings in structured markdown format:
  ```
  ## [Persona Name] Review

  ### Finding 1
  - **Severity:** critical | warning | suggestion
  - **Confidence:** [0-100]
  - **File:** [path]
  - **Issue:** [what's wrong]
  - **Recommendation:** [what to do instead]
  - **Reasoning:** [why this matters from this persona's perspective]
  ```
- **D-05:** Each finding MUST include a confidence score (0-100) for downstream filtering in Phase 3.

### Persona Agent Configuration
- **D-06:** All persona agents are read-only: allowed tools are Glob, Grep, Read, and non-destructive Bash. No Edit, Write, or destructive operations.
- **D-07:** Persona agents use `memory: project` scope to accumulate insights (enables Phase 5 learning).
- **D-08:** Persona prompts explicitly instruct agents to read and respect CLAUDE.md project conventions.

### Plugin Manifest
- **D-09:** plugin.json includes name ("persona"), version ("0.1.0"), description, and author. Already scaffolded — verify and update if needed.

### Claude's Discretion
- Agent file naming convention (e.g., `security-hardener.md` vs `the-security-hardener.md`)
- Exact wording of persona system prompts (as long as they embody the character and produce structured output)
- Whether to include a brief "persona bio" section in each agent file for user documentation

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Plugin System
- `research/01-create-plugins.md` — How to create Claude Code plugins (manifest, directory structure)
- `research/02-plugins-reference.md` — Plugin reference (supported fields, agent constraints)

### Subagent System
- `research/04-subagents.md` — Subagent definitions, frontmatter fields, memory scopes, tool restrictions

### Pitfalls
- `.planning/research/PITFALLS.md` — Critical constraints (subagents can't spawn subagents, plugin agents ignore hooks/mcpServers in frontmatter)
- `.planning/research/STACK.md` — Stack conventions for plugin file formats

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `.claude-plugin/plugin.json` — Already scaffolded with name, version, description, author. Needs verification against plugin spec.
- `agents/` — Empty directory ready for persona agent `.md` files
- `research/` — Extensive reference docs on Claude Code plugin system (8+ files)

### Established Patterns
- No existing code patterns (greenfield). Research docs establish the conventions to follow.

### Integration Points
- `agents/` directory is auto-discovered by Claude Code plugin system — any `.md` file placed here becomes available as a subagent
- `plugin.json` must be valid for agents to register

</code_context>

<specifics>
## Specific Ideas

- Persona names should be evocative but professional (e.g., "The Architect" not "Architecture Agent #1")
- The 4 personas are chosen to maximize productive disagreement: Security vs Pragmatist (security cost vs shipping speed), Architect vs Pragmatist (abstraction vs simplicity), Readability Advocate vs Architect (simplicity vs structural correctness)
- Each persona should have a clear "what I ignore" section — things deliberately outside their lens — to prevent overlapping reviews

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-plugin-foundation-and-persona-agents*
*Context gathered: 2026-03-22*
