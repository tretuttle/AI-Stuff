# Phase 2: Orchestration Skill - Research

**Researched:** 2026-03-22
**Domain:** Claude Code plugin skill authoring, subagent dispatch, file-based output collection
**Confidence:** HIGH

## Summary

Phase 2 creates the `/persona:review` skill -- the central orchestration point that dispatches 14 persona agents in parallel, collects their structured JSON output via file-based handoff, and presents a severity summary. The skill runs in the main conversation context (no `context: fork`) so it can spawn subagents directly.

The core technical challenge is argument parsing within a SKILL.md prompt (distinguishing file paths from `--only` and `--gilfoyle` flags), explicit subagent dispatch (Claude does not auto-delegate), and file-based output collection to avoid context window exhaustion with 14 concurrent personas.

**Primary recommendation:** Build the skill as a single SKILL.md file under `skills/review/` that uses `$ARGUMENTS` for input, contains explicit Agent/Task dispatch instructions for each persona, and instructs personas to write JSON findings to `persona-reviews/{persona-name}.json` at the project root.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- D-01: User controls persona selection via three modes: all (default), subset (`--only ThePrimeagen,DHH,Gilfoyle`), single (`--only "Rich Harris"`)
- D-02: `--only` flag is core to Phase 2 (pulled forward from Phase 6 SELC-01)
- D-03: No smart auto-selection. User decides who runs.
- D-04: `$ARGUMENTS` accepts file path, directory, or glob pattern. Empty defaults to staged diff (`git diff --staged`).
- D-05: Usage examples defined (single file, directory + subset, staged changes)
- D-06: File-based output. Each persona writes structured JSON to `persona-reviews/{persona-name}.json`.
- D-07: Synthesis (Phase 3) reads files. In-context returns NOT used to avoid context exhaustion.
- D-08: `persona-reviews/` at project root, overwritten each review cycle.
- D-09: Skill name: `/persona:review` (maps to `skills/review/SKILL.md`)
- D-10: Confirmation before dispatch showing who's running and what's being reviewed.
- D-11: Per-persona completion messages during execution.
- D-12: Ranked severity summary after all personas complete.
- D-13: `--gilfoyle` flag cranks persona opinions to maximum within project architecture.
- D-14: Base constraint (always active): Personas MUST respect project stack choices as non-negotiable.
- D-15: Gilfoyle mode adds "drop all diplomacy and hold nothing back."
- D-16: Gilfoyle mode summary: "Roast the implementation, not the architecture."
- D-17: Skill MUST NOT use `context: fork`. Runs in main context for subagent dispatch.
- D-18: Skill must contain explicit Agent/Task dispatch instructions. No auto-delegation.

### Claude's Discretion
- How to parse `$ARGUMENTS` to distinguish file paths from flags (--only, --gilfoyle)
- Whether to use the Agent tool or Task tool for dispatching persona subagents
- How to structure the JSON output schema for persona-reviews files
- How to generate the post-review severity summary (simple count vs. detailed breakdown)
- Whether persona-reviews/ directory should be gitignored

### Deferred Ideas (OUT OF SCOPE)
- Phase 6 update: SELC-01 (--only flag) is now implemented in Phase 2. Phase 6 scope needs adjustment.
- Gilfoyle mode as default: deferred to Phase 5/6 as a configuration option.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ORCH-01 | User can invoke a multi-persona review via `/persona:orchestrate` skill | SKILL.md at `skills/review/SKILL.md` maps to `/persona:review`. Note: REQUIREMENTS.md says `/persona:orchestrate` but CONTEXT.md D-09 renames to `/persona:review`. |
| ORCH-02 | Orchestration dispatches all persona agents in parallel from the main agent context | Skill omits `context: fork`; includes explicit Agent/Task tool dispatch instructions for all 14 agents |
| ORCH-03 | User can target specific files or staged changes for review via skill arguments | `$ARGUMENTS` substitution in SKILL.md; argument parsing in skill prompt |
| ORCH-04 | Orchestration collects structured output from all persona agents via SubagentStop hook or agent return | File-based collection: personas write JSON to `persona-reviews/{name}.json`; orchestrator reads files after completion |
| ORCH-05 | Orchestration skill does NOT use `context: fork` | Omit `context: fork` from SKILL.md frontmatter entirely |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **No external deps**: Plugin works with just Claude Code -- no npm packages
- **Plugin format**: Must conform to Claude Code plugin conventions
- **Subagent system**: Persona agents must be `.md` subagent definitions
- **Do NOT use `context: fork`** on the orchestrator skill (subagents cannot spawn subagents)
- **Do NOT use `hooks` in agent frontmatter** (not supported for plugin agents)
- **Use `$ARGUMENTS`** for the review target
- **Use `${CLAUDE_PLUGIN_ROOT}`** in all script paths
- **Scripts must be bash** (no npm/node dependencies)
- **Keep SKILL.md under 500 lines** -- move details to supporting files

## Standard Stack

### Core
| Component | Format | Purpose | Why Standard |
|-----------|--------|---------|--------------|
| `skills/review/SKILL.md` | Markdown + YAML frontmatter | User-invocable `/persona:review` command | Claude Code's native skill system for plugin commands |
| `skills/review/reference.md` | Markdown | Persona roster, JSON schema, dispatch instructions | Keeps SKILL.md under 500 lines |
| `persona-reviews/` | Directory at project root | Per-persona JSON output files | File-based handoff avoids context exhaustion (Pitfall 5) |

### Supporting
| Component | Format | Purpose | When to Use |
|-----------|--------|---------|-------------|
| `.gitignore` entry | Text | Exclude `persona-reviews/` from VCS | Always -- review output is ephemeral |
| Agent prompt updates | Markdown edits to `agents/*.md` | Add Gilfoyle mode + JSON file output instructions | Required to support D-06, D-13-D-16 |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| File-based JSON output | In-context return | Context exhaustion with 14 personas (50k+ tokens); file-based is mandatory per D-07 |
| Agent tool (parallel) | Task tool (parallel) | Both support parallel dispatch; Agent tool is more common in docs. Recommend Task tool for fire-and-forget pattern |
| Single SKILL.md | SKILL.md + reference.md split | Split keeps SKILL.md under 500 lines per constraint |

## Architecture Patterns

### Recommended Skill Structure
```
skills/
  review/
    SKILL.md           # Frontmatter + orchestration prompt (< 500 lines)
    reference.md       # Persona roster, JSON schema, detailed instructions
```

### Pattern 1: Argument Parsing in Skill Prompt
**What:** The skill prompt itself instructs Claude how to parse `$ARGUMENTS` into components.
**When to use:** When a skill needs both positional args (file paths) and flags (--only, --gilfoyle).
**Approach:**

The SKILL.md body instructs Claude to parse `$ARGUMENTS` as follows:
1. Split on whitespace
2. Extract `--only <comma-separated-names>` if present
3. Extract `--gilfoyle` if present
4. Everything else is the review target (file path, directory, glob)
5. If no target, default to staged diff

This is natural language instruction, not code. Claude handles the parsing as part of understanding the skill prompt. No shell script needed.

**Example prompt fragment:**
```markdown
## Arguments

Parse `$ARGUMENTS` to extract:
- **Review target**: The first non-flag argument (file path, directory, or glob pattern). If none provided, use staged changes via `git diff --staged`.
- **--only <names>**: Comma-separated persona names to run. If omitted, run all personas.
- **--gilfoyle**: When present, activate Gilfoyle mode for all dispatched personas.
```

### Pattern 2: Explicit Parallel Subagent Dispatch
**What:** The skill prompt contains literal instructions to spawn each persona agent using the Task tool.
**When to use:** Always -- Claude does not auto-delegate to subagents (Pitfall 3).
**Why Task over Agent:** Task tool is designed for fire-and-forget parallel work. Agent tool is more interactive. For dispatching 14 read-only reviewers that each write output to a file, Task is the cleaner fit.

**Example prompt fragment:**
```markdown
## Dispatch

For each selected persona, use the Task tool to spawn a subagent:
- Set the agent name to the persona's kebab-case name (e.g., `theprimeagen`, `dhh`)
- Pass the review target and any flags in the task prompt
- All personas run in parallel -- dispatch all Task calls before waiting for results
```

### Pattern 3: File-Based Output Collection
**What:** Each persona writes its findings as JSON to `persona-reviews/{persona-name}.json` at the project root.
**When to use:** When collecting output from many subagents would exhaust the context window.
**Key detail:** Personas currently use `disallowedTools: Write, Edit, NotebookEdit`. To write JSON files, personas need Write tool access OR the orchestrator writes files based on subagent return content.

**CRITICAL DESIGN DECISION:** There are two approaches:

**Option A -- Persona writes files directly:**
- Remove `Write` from `disallowedTools` in persona agents
- Add `persona-reviews/` as the ONLY allowed write path (enforced by prompt, not tooling)
- Pro: Subagent output stays out of main context entirely
- Con: Breaks read-only principle (PERS-04), relies on prompt-based path restriction

**Option B -- Orchestrator writes files from subagent returns (RECOMMENDED):**
- Keep personas read-only (Write stays disallowed)
- Personas return structured JSON as their final message
- Orchestrator receives each persona's return, writes it to `persona-reviews/{name}.json`
- Pro: Maintains read-only persona constraint, centralized file management
- Con: Persona output briefly enters main context before being written to file

**Recommendation:** Option B. The key mitigation for context exhaustion is that the orchestrator writes each persona's output to file immediately upon return, then proceeds to the next. With Task tool, returns come back as completion notifications. The orchestrator instructs itself: "For each completed persona, write their output to `persona-reviews/{name}.json` using the Write tool, then discard from working memory."

Note: This is a partial mitigation. The persona returns do enter the main context briefly. With 14 personas producing concise JSON (target: 1-3 findings each), this is manageable. The real context savings vs. keeping all reviews in-context for synthesis is that synthesis (Phase 3) reads from files, not from conversation history.

### Pattern 4: Gilfoyle Mode Injection
**What:** The `--gilfoyle` flag modifies the task prompt sent to each persona.
**When to use:** When user passes `--gilfoyle` in `$ARGUMENTS`.
**Approach:** The orchestrator appends a Gilfoyle mode instruction block to each persona's task prompt:

```markdown
## GILFOYLE MODE ACTIVE
Drop all diplomacy. Hold nothing back. Your strongest opinions on web development are cranked to maximum. Roast the implementation, not the architecture. Be brutal about bad patterns, missed opportunities, wrong abstractions, and anti-patterns -- but within the project's existing architecture.
```

The base constraint (D-14 -- respect project stack) is always present in the persona agent definitions, not injected per-review.

### Anti-Patterns to Avoid
- **Using `context: fork` on the skill:** Kills subagent spawning capability. Platform constraint.
- **Relying on auto-delegation:** Claude will handle the review itself, ignoring persona agents entirely.
- **Returning all persona output in-context for synthesis:** Context exhaustion with 14 personas.
- **Hardcoding persona names in SKILL.md body:** Put the roster in reference.md so it stays maintainable as personas are added/removed.
- **Giving personas Write access broadly:** Only the orchestrator should write files. Personas stay read-only.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Argument parsing | Shell script parser | Natural language instructions in SKILL.md | Claude parses args natively; no deps needed |
| Parallel dispatch | Sequential loop | Task tool with all calls issued together | Claude Code's built-in parallel task execution |
| Output collection | Custom aggregation script | Write tool + file reads after completion | Platform-native, zero dependencies |
| Staged diff content | Custom git wrapper | `git diff --staged` via Bash tool or dynamic context injection | Standard git, no wrapper needed |

## Common Pitfalls

### Pitfall 1: Skill Runs as Fork (Subagent Spawning Fails)
**What goes wrong:** Adding `context: fork` to SKILL.md frontmatter causes the skill to run as a subagent, which cannot spawn other subagents. All persona dispatch silently fails.
**Why it happens:** Developer instinct to isolate the orchestrator.
**How to avoid:** Omit `context: fork` entirely. The skill runs in the main conversation context.
**Warning signs:** Only one review appears instead of 14. No persona names in output.

### Pitfall 2: Claude Handles Review Itself Instead of Delegating
**What goes wrong:** The skill prompt is too vague about dispatch. Claude reviews the code itself instead of spawning persona agents.
**Why it happens:** Claude prefers to handle tasks directly unless explicitly told to delegate.
**How to avoid:** The skill prompt must contain explicit, imperative instructions: "You MUST use the Task tool to dispatch each persona. Do NOT review the code yourself."
**Warning signs:** A single monolithic review with no persona attribution.

### Pitfall 3: Persona Output Schema Mismatch
**What goes wrong:** Personas produce markdown (their current format) instead of JSON. The orchestrator cannot parse or write valid JSON files.
**Why it happens:** Current persona agents (Phase 1) output structured markdown, not JSON.
**How to avoid:** Either (a) update persona agent prompts to output JSON when dispatched by the orchestrator, or (b) have the orchestrator handle markdown-to-JSON conversion. Option (a) is cleaner.
**Warning signs:** `persona-reviews/*.json` files contain markdown instead of valid JSON.

### Pitfall 4: Argument Flag Parsing Ambiguity
**What goes wrong:** A file named `--only` or a path containing spaces is misinterpreted as a flag.
**Why it happens:** `$ARGUMENTS` is a raw string, not a parsed argv.
**How to avoid:** Document that the review target comes first, flags come after. Persona names in `--only` are comma-separated with no spaces (or quoted). Keep examples in the skill prompt.
**Warning signs:** Wrong personas selected, wrong files reviewed.

### Pitfall 5: persona-reviews/ Directory Not Created
**What goes wrong:** Write tool fails because `persona-reviews/` does not exist at the project root.
**Why it happens:** First review run, directory never created.
**How to avoid:** Orchestrator must create the directory (via Bash `mkdir -p`) before dispatching personas or writing files.
**Warning signs:** Write tool errors on first run.

### Pitfall 6: Agent Name Mismatch Between Skill and Agent Files
**What goes wrong:** The skill dispatches `task agent="ThePrimeagen"` but the agent file defines `name: theprimeagen`. Case-sensitive mismatch causes dispatch failure.
**Why it happens:** Agent names are kebab-case lowercase, but persona display names are mixed case.
**How to avoid:** Maintain a mapping in reference.md. Always use the exact `name` field from agent frontmatter for dispatch. Use display names only in user-facing output.
**Warning signs:** "Agent not found" errors or Claude handling the task itself.

## Code Examples

### SKILL.md Frontmatter
```yaml
---
name: review
description: "Dispatch multi-persona code review against targeted files or changes"
argument-hint: "[file/dir/glob] [--only name1,name2] [--gilfoyle]"
---
```

Source: research/03-skills.md -- skills frontmatter reference

### Persona Roster Mapping (for reference.md)
```markdown
| Display Name | Agent Name | File |
|-------------|-----------|------|
| ThePrimeagen | theprimeagen | agents/theprimeagen.md |
| DHH | dhh | agents/dhh.md |
| Chris Coyier | chris-coyier | agents/chris-coyier.md |
| Dan Abramov | dan-abramov | agents/dan-abramov.md |
| Evan You | evan-you | agents/evan-you.md |
| Kent C. Dodds | kent-c-dodds | agents/kent-c-dodds.md |
| Lee Robinson | lee-robinson | agents/lee-robinson.md |
| Matt Mullenweg | matt-mullenweg | agents/matt-mullenweg.md |
| Matt Pocock | matt-pocock | agents/matt-pocock.md |
| Rich Harris | rich-harris | agents/rich-harris.md |
| Scott Tolinski | scott-tolinski | agents/scott-tolinski.md |
| Tanner Linsley | tanner-linsley | agents/tanner-linsley.md |
| Theo Browne | theo-browne | agents/theo-browne.md |
| Wes Bos | wes-bos | agents/wes-bos.md |
```

### JSON Output Schema (for persona-reviews/*.json)
```json
{
  "persona": "theprimeagen",
  "displayName": "ThePrimeagen",
  "gilfoyleMode": false,
  "target": "src/auth.ts",
  "findings": [
    {
      "severity": "critical",
      "confidence": 85,
      "file": "src/auth.ts",
      "line": 42,
      "issue": "Synchronous bcrypt call blocks the event loop",
      "recommendation": "Use bcrypt.hash() async variant",
      "reasoning": "This is a skill issue. You're blocking the entire event loop for password hashing. Every request queues behind this. Use the async API or better yet, use Argon2."
    }
  ],
  "summary": "1 critical, 0 warnings, 0 suggestions"
}
```

### Task Tool Dispatch Pattern
```markdown
For each selected persona, dispatch using the Task tool:

Task: Review code as {persona display name}
Agent: {persona agent name}
Prompt: |
  Review the following code target: {review target}

  {if gilfoyle mode}
  ## GILFOYLE MODE ACTIVE
  Drop all diplomacy. Hold nothing back. Roast the implementation, not the architecture.
  {end if}

  Return your findings as a JSON object with this schema:
  {json schema from reference.md}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Sequential subagent dispatch | Parallel Task tool dispatch | Claude Code current | All 14 personas run concurrently |
| In-context output collection | File-based JSON handoff | Project decision D-06/D-07 | Avoids context exhaustion |
| Generic persona archetypes | Real developer personas | Phase 1 D-01 | Authentic voice and perspective |

## Open Questions

1. **Task tool vs Agent tool for dispatch**
   - What we know: Both can dispatch subagents. Task tool is fire-and-forget, Agent tool is interactive.
   - What's unclear: Whether Task tool returns the subagent's final message to the main context (needed for Option B output collection).
   - Recommendation: Test with Task tool first. If returns are not accessible, use Agent tool with explicit "write your output and return a completion signal" instructions.

2. **Persona agent prompt updates for JSON output**
   - What we know: Current agents output structured markdown. D-06 requires JSON.
   - What's unclear: Whether to update the agent prompt globally (always output JSON) or have the orchestrator request JSON in the task prompt (override per-dispatch).
   - Recommendation: Per-dispatch override. The persona agent keeps its markdown format for direct invocation, but when dispatched by the orchestrator, the task prompt instructs JSON output. This preserves backward compatibility.

3. **Base constraint injection (D-14)**
   - What we know: "Personas MUST read the project's stack from CLAUDE.md / package.json and treat those choices as non-negotiable."
   - What's unclear: Whether this should be in each agent's `.md` file (permanent) or injected by the orchestrator per-review.
   - Recommendation: Add to each agent's `.md` file as a permanent instruction. This is always-active (D-14 says "ALWAYS active, not just Gilfoyle mode").

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Manual testing via Claude Code CLI |
| Config file | None -- plugin testing is interactive |
| Quick run command | `/persona:review src/test-file.ts --only theprimeagen` |
| Full suite command | `/persona:review src/test-file.ts` (all 14 personas) |

### Phase Requirements Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ORCH-01 | `/persona:review` invokes the skill | manual | Type `/persona:review` in Claude Code | Wave 0 |
| ORCH-02 | All 14 personas dispatch in parallel | manual | `/persona:review src/test.ts` -- verify 14 outputs | Wave 0 |
| ORCH-03 | File targeting works | manual | `/persona:review src/auth.ts --only theprimeagen` | Wave 0 |
| ORCH-04 | JSON files created in `persona-reviews/` | manual | `ls persona-reviews/` after review | Wave 0 |
| ORCH-05 | No `context: fork` in SKILL.md | manual (code review) | `grep "context: fork" skills/review/SKILL.md` returns empty | Wave 0 |

### Sampling Rate
- **Per task commit:** Verify SKILL.md has no `context: fork`, frontmatter is valid YAML
- **Per wave merge:** Run `/persona:review` with `--only` on a single persona to validate end-to-end
- **Phase gate:** Full 14-persona review on a test file

### Wave 0 Gaps
- [ ] `skills/review/SKILL.md` -- must be created (core deliverable)
- [ ] `skills/review/reference.md` -- must be created (persona roster + JSON schema)
- [ ] Test file for validation -- need a sample code file to review

## Sources

### Primary (HIGH confidence)
- `research/03-skills.md` -- Skills frontmatter, $ARGUMENTS, dynamic context injection, context: fork behavior
- `research/04-subagents.md` -- Subagent dispatch, Task/Agent tools, parallel execution, no-nesting constraint
- `research/02-plugins-reference.md` -- Plugin skill structure, agent field support
- `.planning/research/PITFALLS.md` -- Pitfalls 1, 3, 5, 9 directly relevant

### Secondary (MEDIUM confidence)
- Phase 1 CONTEXT.md -- Persona roster, output structure, tool restrictions
- CLAUDE.md Technology Stack section -- Orchestration skill conventions

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all components use documented Claude Code plugin primitives
- Architecture: HIGH - patterns derived from official docs and locked decisions
- Pitfalls: HIGH - documented in official sources and verified against project constraints

**Research date:** 2026-03-22
**Valid until:** 2026-04-22 (stable -- Claude Code plugin system is mature)
