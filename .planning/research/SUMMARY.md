# Project Research Summary

**Project:** Persona - Multi-Persona Code Review Plugin
**Domain:** Claude Code plugin with subagent orchestration
**Researched:** 2026-03-22
**Confidence:** HIGH

## Executive Summary

Persona is a Claude Code plugin that dispatches multiple named, opinionated AI reviewer personas to analyze code in parallel, then synthesizes their findings into a unified review. This is not a traditional software project -- there is no build step, no runtime, no external dependencies. The entire "stack" is Claude Code's native plugin primitives: markdown files for agent definitions and skills, JSON for hooks, and bash scripts for automation. Experts build plugins like this by leveraging subagents for isolated AI tasks, skills for user-facing entry points, and hooks for lifecycle automation. The key architectural insight is that all orchestration must happen at the main agent level because subagents cannot spawn other subagents.

The recommended approach is a skill-driven orchestration pattern: a user invokes `/persona:review`, which loads a skill into the main Claude Code agent context. The main agent then dispatches 3-4 persona subagents in parallel using the native Agent tool. Each persona reviews code through a distinct philosophical lens (security, performance, maintainability) using read-only tools, produces structured findings, and returns results to the main agent. A synthesis step deduplicates, resolves contradictions, and presents a unified review. Persona memory (`memory: project`) lets each reviewer accumulate project-specific insights over time -- a differentiator no competitor in the Claude Code ecosystem offers.

The primary risks are: (1) the no-nesting constraint silently breaking orchestration if the skill uses `context: fork`, (2) Windows-specific hook failures since the developer is on Windows 11, (3) context window exhaustion when multiple persona outputs flood the main agent, and (4) the main agent ignoring subagents unless the orchestration skill contains explicit dispatch instructions. All four are well-understood and preventable with the patterns documented in this research.

## Key Findings

### Recommended Stack

The plugin is pure configuration -- no npm packages, no build tools, no external services. Every component maps to a Claude Code primitive.

**Core technologies:**
- `plugin.json` manifest: plugin identity and component registration -- required by Claude Code, already exists
- `agents/*.md` subagent definitions: one markdown file per persona with YAML frontmatter -- the native way to define isolated AI tasks
- `skills/orchestrate/SKILL.md`: user-facing entry point for `/persona:review` -- must run in main context (no `context: fork`) to dispatch subagents
- `skills/parse-output/SKILL.md`: internal synthesis instructions -- model-invocable only, not user-facing
- `hooks/hooks.json`: SubagentStart/Stop event tracking for progress reporting -- plugin-level, not per-agent
- `scripts/*.sh`: bash hook handlers using `jq` for JSON processing -- zero external dependencies
- `memory: project` scope on persona agents: per-persona project insights that persist across sessions

**Critical version/platform notes:**
- Plugin agents do NOT support `hooks`, `mcpServers`, or `permissionMode` in frontmatter (silently ignored)
- All paths must use `${CLAUDE_PLUGIN_ROOT}` or `${CLAUDE_PLUGIN_DATA}` -- no path traversal above plugin root
- Scripts must be executable (`chmod +x`) and invoked via explicit `bash` on Windows

### Expected Features

**Must have (table stakes):**
- Parallel persona dispatch (Anthropic's official plugin does this; sequential would feel slow)
- At least 3 distinct personas with genuine philosophical differences
- Unified synthesis of findings with deduplication and contradiction resolution
- Skill-based invocation (`/persona:review <target>`)
- File/diff targeting via `$ARGUMENTS` and dynamic context injection
- Structured output format with severity, location, explanation per finding
- Confidence/severity scoring (official plugin uses 0-100 with threshold filtering)
- CLAUDE.md awareness across all personas

**Should have (differentiators):**
- Named character personas with philosophies, not anonymous function agents -- the core differentiator
- Persistent persona memory that improves reviews over time
- Cross-persona disagreement surfacing (present tensions, don't hide them)
- User-extensible persona system (drop a `.md` file, get a new reviewer)
- Selective persona invocation (`/persona:review --security`)

**Defer (v2+):**
- Review history diffing across sessions (high complexity, depends on memory maturity)
- Additional persona packs (community contribution opportunity)
- GitHub PR comment integration (official plugin already handles this)
- CI/CD integration (official plugin's territory)

### Architecture Approach

The architecture is a four-phase pipeline: invocation (skill loads, context injected), dispatch (main agent spawns persona subagents in parallel), review (each persona analyzes code independently with read-only tools), and synthesis (main agent merges outputs using parse-output skill instructions). All orchestration lives at the main agent level. Subagents are isolated, read-only analysts that produce structured findings. Hooks provide lifecycle tracking without LLM cost.

**Major components:**
1. **Orchestrate Skill** -- entry point; instructs main agent to dispatch personas and synthesize results
2. **Persona Agents** -- independent expert reviewers with distinct identities, read-only tools, and project memory
3. **Parse-Output Skill** -- synthesis instructions for deduplication, contradiction resolution, severity ranking
4. **Hooks System** -- SubagentStart/Stop tracking for progress reporting via command-type hooks
5. **Memory Store** -- per-persona `.claude/agent-memory/<name>/` directories for persistent project insights

### Critical Pitfalls

1. **Subagents cannot spawn subagents** -- The orchestrator skill must NOT use `context: fork`. It must run in main agent context to dispatch persona subagents. Getting this wrong requires a complete architectural rewrite.
2. **Main agent ignores subagents without explicit instructions** -- The orchestration skill must literally name each persona and instruct the main agent to spawn them. Descriptions alone do not trigger delegation.
3. **Plugin agent frontmatter silently ignores hooks/permissionMode** -- Use `tools`/`disallowedTools` for access control; use plugin-level `hooks/hooks.json` with matchers for lifecycle events.
4. **Windows hook scripts fail silently** -- Use inline commands or explicit `bash "${CLAUDE_PLUGIN_ROOT}/scripts/..."` invocation. Add `async: true` to SessionStart hooks. The developer is on Windows 11; this will be encountered immediately.
5. **Context window exhaustion during multi-persona review** -- Instruct personas to be concise (top 3-5 findings only), set `maxTurns: 10-15`, use `effort: medium`, consider file-based output for large reviews.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Foundation and Core Agents

**Rationale:** Agents are self-contained and independently testable. The plugin manifest already exists. Persona definitions must come first because everything downstream depends on them.
**Delivers:** 3-4 fully defined persona agents with distinct identities, philosophies, structured output contracts, and read-only tool restrictions. Validated plugin directory structure.
**Addresses:** Table stakes (3+ personas, structured output), core differentiator (named character personas)
**Avoids:** Pitfall 6 (directory nesting), Pitfall 10 (path traversal), Pitfall 13 (personas as code executors), Pitfall 2 (unsupported frontmatter)

### Phase 2: Orchestration Skill

**Rationale:** The orchestration skill is the glue -- it needs agents from Phase 1 to dispatch. Cannot be tested without persona definitions.
**Delivers:** Working `/persona:review` command that dispatches all personas in parallel with file/diff targeting via `$ARGUMENTS` and dynamic context injection.
**Addresses:** Table stakes (skill invocation, file/diff targeting, parallel dispatch)
**Avoids:** Pitfall 1 (no-nesting -- no `context: fork`), Pitfall 3 (explicit dispatch instructions, not hints)

### Phase 3: Synthesis and Output

**Rationale:** The parse-output skill needs real multi-persona output to test against. Depends on orchestration producing results.
**Delivers:** Unified review output with deduplication, persona attribution, severity ranking, confidence scoring, and cross-persona disagreement surfacing.
**Addresses:** Table stakes (unified synthesis, confidence scoring), differentiator (disagreement surfacing)
**Avoids:** Pitfall 5 (context exhaustion -- concise persona output, structured format)

### Phase 4: Hooks and Progress

**Rationale:** Hooks are enhancements, not core flow. The review works without them. Must be validated on Windows from the first hook written.
**Delivers:** SubagentStart/Stop progress tracking, user-visible feedback during reviews.
**Addresses:** Table stakes (progress indication)
**Avoids:** Pitfall 4 (Windows hook failures -- inline commands, explicit bash, async: true)

### Phase 5: Memory and Learning

**Rationale:** Memory deepens the value proposition but is not required for the core review experience. Adding it last means the review loop is already solid.
**Delivers:** Persistent persona memory with structured MEMORY.md templates, curation instructions, and improving review quality over sessions.
**Addresses:** Differentiator (persistent memory), table stakes refinement (CLAUDE.md compliance)
**Avoids:** Pitfall 7 (memory degradation -- structured templates, curation rules, 200-line awareness)

### Phase 6: Polish and Extensibility

**Rationale:** Quality-of-life features that round out the product. Selective invocation requires the full system to be working.
**Delivers:** Selective persona invocation via arguments, user documentation for custom persona creation, template persona file, marketplace readiness.
**Addresses:** Differentiator (selective invocation, user-extensible system)

### Phase Ordering Rationale

- Agents before orchestration because agents are independently testable and the orchestrator depends on them
- Orchestration before synthesis because synthesis needs real multi-persona output to process
- Hooks after core flow because the review works without progress tracking
- Memory last because it is an enhancement that requires a stable review loop to add value
- Each phase produces a testable increment: Phase 1 = individual persona reviews, Phase 2 = multi-persona dispatch, Phase 3 = unified output, Phase 4 = UX polish, Phase 5 = learning

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 2 (Orchestration):** The interaction between skill instructions and main agent dispatch behavior is nuanced. Need to validate exact prompt patterns that reliably trigger parallel Agent tool calls. Test on Windows immediately.
- **Phase 3 (Synthesis):** Deduplication and contradiction detection across persona outputs is non-trivial. May need iterative prompt engineering.
- **Phase 5 (Memory):** The 200-line MEMORY.md limit and curation strategy need experimentation to get right.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Agents):** Well-documented subagent definition format. Markdown files with YAML frontmatter. Follow the reference.
- **Phase 4 (Hooks):** Hooks reference provides complete schemas. Main risk is Windows compatibility, which is a testing concern not a research concern.
- **Phase 6 (Polish):** Standard argument parsing and documentation work.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All technologies verified against official Claude Code docs. Zero ambiguity -- the stack IS the plugin primitives. |
| Features | HIGH | Competitive analysis covers official plugin, 5+ competitors. Table stakes and differentiators clearly identified. |
| Architecture | HIGH | Architecture directly follows from platform constraints (no-nesting, plugin agent limitations). One correct pattern. |
| Pitfalls | HIGH | Critical pitfalls sourced from official docs and confirmed GitHub issues. Context exhaustion is MEDIUM (thresholds vary). |

**Overall confidence:** HIGH

### Gaps to Address

- **Parallel dispatch reliability:** How consistently does the main agent spawn all personas in parallel vs. sequentially? May need prompt tuning during Phase 2.
- **Context window thresholds:** Exact token budget for N personas reviewing M files is unknown. Need empirical testing in Phase 3 to determine if file-based output is necessary.
- **Windows hook behavior:** Known issues exist but workarounds are documented. Must validate every hook on Windows during Phase 4 development.
- **Memory curation effectiveness:** No proven pattern for keeping MEMORY.md under 200 useful lines over many sessions. Phase 5 will require experimentation.
- **Marketplace install testing:** Local development (`--plugin-dir`) may mask issues that only appear after marketplace install. Need a marketplace test strategy before release.

## Sources

### Primary (HIGH confidence)
- Claude Code Plugin Creation Guide (code.claude.com/docs/en/plugins)
- Claude Code Plugins Reference (code.claude.com/docs/en/plugins-reference)
- Claude Code Skills Documentation (code.claude.com/docs/en/skills)
- Claude Code Subagents Documentation (code.claude.com/docs/en/sub-agents)
- Claude Code Hooks Guide (code.claude.com/docs/en/hooks-guide)
- Claude Code Hooks Reference (code.claude.com/docs/en/hooks-reference)
- Claude Code Features Overview (code.claude.com/docs/en/features-overview)

### Secondary (MEDIUM confidence)
- Anthropic official code-review plugin (github.com/anthropics/claude-code) -- competitive baseline
- VoltAgent awesome-claude-code-subagents -- subagent patterns
- Claude Buddy -- persona-based competitor reference
- Claudekit subagent best practices blog -- common mistakes
- GitHub Issues #18610, #351 -- Windows-specific hook failures

### Tertiary (LOW confidence)
- Calimero ai-code-reviewer -- multi-agent orchestration patterns (different platform)
- State of AI Code Review 2025 -- industry context (general, not Claude-specific)

---
*Research completed: 2026-03-22*
*Ready for roadmap: yes*
