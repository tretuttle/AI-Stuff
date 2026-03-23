# Phase 2: Orchestration Skill - Context

**Gathered:** 2026-03-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver a `/persona:review` skill that dispatches persona agents in parallel against targeted files or changes, collects structured output via file-based handoff, and presents a summary. Includes persona selection (--only flag) and Gilfoyle mode (--gilfoyle flag). This phase does NOT include synthesis/deduplication (Phase 3), progress hooks (Phase 4), or memory (Phase 5).

</domain>

<decisions>
## Implementation Decisions

### Persona Selection
- **D-01:** User controls exactly who runs. Three modes:
  1. **All (default):** No flags — all 14 personas run
  2. **Subset:** `--only ThePrimeagen,DHH,Gilfoyle` — comma-separated persona names
  3. **Single:** `--only "Rich Harris"` — one persona
- **D-02:** The `--only` flag is core to the orchestration skill (pulled forward from Phase 6 SELC-01). Persona selection is a fundamental input, not an enhancement.
- **D-03:** No smart auto-selection of personas. The user knows who they want to hear from.

### Review Target Input
- **D-04:** `$ARGUMENTS` accepts: file path, directory, or glob pattern. Empty defaults to staged diff (`git diff --staged`).
- **D-05:** Examples:
  - `/persona:review src/auth.ts` — single file, all personas
  - `/persona:review packages/convex/ --only "Matt Pocock,Theo Browne"` — directory, specific personas
  - `/persona:review` — staged changes, all personas

### Output Collection
- **D-06:** File-based output. Each persona writes structured JSON to `persona-reviews/{persona-name}.json`.
- **D-07:** Synthesis step (Phase 3) reads files and presents ranked summary. In-context returns are NOT used — avoids context exhaustion with 14 personas (Pitfall 5).
- **D-08:** The `persona-reviews/` directory is created per-review and lives at the project root (or a configurable location). Files are overwritten each review cycle.

### Skill UX
- **D-09:** Skill name: `/persona:review` (not `/persona:orchestrate`).
- **D-10:** Confirmation before dispatch showing:
  - Who's running (persona names)
  - What's being reviewed (files/diff target)
- **D-11:** Per-persona completion messages during execution (e.g., "ThePrimeagen complete", "DHH complete").
- **D-12:** Ranked severity summary after all personas complete.

### Gilfoyle Mode
- **D-13:** Every persona gets a `--gilfoyle` flag. When active, the persona's strongest known opinions on web dev are cranked to maximum — but applied within the project's existing architecture.
- **D-14:** Base constraint (ALWAYS active, not just Gilfoyle mode): Personas MUST read the project's stack from CLAUDE.md / package.json / the codebase itself and treat those choices as non-negotiable foundational decisions. They can critique how the stack is being used, but cannot recommend ripping out or replacing core technology choices.
- **D-15:** Gilfoyle mode adds: "Drop all diplomacy and hold nothing back." The persona is brutal about bad patterns, missed opportunities, wrong abstractions, anti-patterns — but within the project's existing architecture.
- **D-16:** Gilfoyle mode summary: "Roast the implementation, not the architecture."

### Orchestration Constraints (from Phase 1 / Pitfalls)
- **D-17:** Skill MUST NOT use `context: fork`. The orchestrator runs in the main conversation context so it can spawn persona subagents in parallel (Pitfall 1: subagents cannot spawn subagents).
- **D-18:** Skill must contain explicit Agent/Task dispatch instructions for each persona. Do not rely on Claude auto-delegating to subagents (Pitfall 3).

### Claude's Discretion
- How to parse `$ARGUMENTS` to distinguish file paths from flags (--only, --gilfoyle)
- Whether to use the Agent tool or Task tool for dispatching persona subagents
- How to structure the JSON output schema for persona-reviews files
- How to generate the post-review severity summary (simple count vs. detailed breakdown)
- Whether persona-reviews/ directory should be gitignored

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Plugin System
- `research/01-create-plugins.md` — How to create Claude Code plugins (manifest, directory structure)
- `research/02-plugins-reference.md` — Plugin reference (supported fields, agent constraints)

### Skills System
- `research/03-skills.md` — Skills frontmatter, string substitutions ($ARGUMENTS), dynamic context injection, context: fork behavior

### Subagent System
- `research/04-subagents.md` — Subagent definitions, frontmatter fields, spawning via Agent/Task tools

### Pitfalls
- `.planning/research/PITFALLS.md` — Critical constraints:
  - Pitfall 1: Subagents cannot spawn subagents (orchestrator must run in main context)
  - Pitfall 3: Main agent does not auto-delegate (skill must explicitly spawn)
  - Pitfall 5: Context window exhaustion with multi-persona output (mitigated by file-based output)
  - Pitfall 9: Parallel subagent file conflicts (each persona writes to its own file)

### Phase 1 Context
- `.planning/phases/01-plugin-foundation-and-persona-agents/01-CONTEXT.md` — Persona roster, output structure, tool restrictions

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `.claude-plugin/plugin.json` — Valid plugin manifest (name: "persona", version: "0.1.0")
- `agents/` — 14 persona agent `.md` files with frontmatter (name, description, tools, disallowedTools, memory, model, maxTurns)
- `research/03-skills.md` — Complete skills reference with frontmatter, $ARGUMENTS, dynamic context injection

### Established Patterns
- Agent frontmatter uses: `tools: Read, Glob, Grep, Bash` and `disallowedTools: Write, Edit, NotebookEdit`
- All agents set `memory: project`, `model: inherit`, `maxTurns: 10`
- Agent names are kebab-case (e.g., `theprimeagen`, `dhh`, `chris-coyier`)

### Integration Points
- `skills/orchestrate/SKILL.md` — Needs to be created (no skills directory exists yet)
- SKILL.md will reference agents by name for dispatch
- `persona-reviews/` directory will be created at project root for file-based output

### Known Gaps
- No skills directory exists — must create `skills/review/SKILL.md` (or `skills/orchestrate/SKILL.md`)
- Persona agent prompts need the Gilfoyle mode constraint (D-14 base constraint + D-15 Gilfoyle activation)
- Persona agents currently produce markdown output — need to also support JSON output for file-based collection (D-06)

</code_context>

<specifics>
## Specific Ideas

- The skill name is `/persona:review` — maps to `skills/review/SKILL.md` in the plugin directory structure
- Gilfoyle mode constraint should be in every persona's system prompt: "Roast the implementation, not the architecture"
- With 14 personas, the confirmation step before dispatch is essential UX — users need to know what they're about to trigger
- The --only flag pulls SELC-01 forward from Phase 6 into Phase 2. Phase 6 roadmap should be updated to reflect this.

</specifics>

<deferred>
## Deferred Ideas

- **Phase 6 update:** SELC-01 (--only flag) is now implemented in Phase 2. Phase 6 scope needs adjustment.
- **Gilfoyle mode as default:** User may want to make Gilfoyle mode the default for specific personas or projects — deferred to Phase 5/6 as a configuration option.

</deferred>

---

*Phase: 02-orchestration-skill*
*Context gathered: 2026-03-22*
