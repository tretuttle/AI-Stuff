# Phase 1: Plugin Foundation and Persona Agents - Research

**Researched:** 2026-03-22
**Domain:** Claude Code plugin system -- subagent definitions, plugin manifest, structured review output
**Confidence:** HIGH

## Summary

Phase 1 delivers a valid Claude Code plugin with 4 persona agents that can each independently review code through distinct philosophical lenses. The "stack" is Claude Code's native plugin primitives: YAML-frontmatter markdown files for agents, a JSON manifest, and shell scripts. There are no npm packages, no build step, and no external dependencies.

The project has a clean scaffold: `.claude-plugin/plugin.json` already exists with correct metadata, and empty `agents/`, `skills/`, `hooks/`, `scripts/`, and `memory/` directories are in place. The work is writing 4 agent markdown files with carefully crafted system prompts, verifying the plugin manifest, and confirming everything loads correctly via `claude --plugin-dir`.

**Primary recommendation:** Write 4 agent `.md` files in `agents/` with YAML frontmatter (`name`, `description`, `model: sonnet`, `tools: Read, Glob, Grep, Bash`, `disallowedTools: Write, Edit`, `memory: project`, `effort: medium`, `maxTurns: 10`) and detailed system prompts that encode both character voice and structured output format. Verify plugin loads with `claude --plugin-dir ./persona`.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** 4 persona agents: Security Hardener, The Architect, Readability Advocate, The Pragmatist
- **D-02:** Strong, memorable character voices -- not subtle professional variations. Feedback immediately attributable by voice alone.
- **D-03:** Character voice expressed through: what they notice first, how they frame issues, what they consider important, tolerance for tradeoffs. NOT through gimmicks, catchphrases, or roleplay.
- **D-04:** Each persona produces structured markdown findings with: Severity (critical/warning/suggestion), Confidence (0-100), File, Issue, Recommendation, Reasoning
- **D-05:** Each finding MUST include confidence score (0-100) for downstream filtering
- **D-06:** All persona agents are read-only: allowed tools are Glob, Grep, Read, and non-destructive Bash. No Edit, Write, or destructive operations.
- **D-07:** Persona agents use `memory: project` scope
- **D-08:** Persona prompts explicitly instruct agents to read and respect CLAUDE.md project conventions
- **D-09:** plugin.json includes name ("persona"), version ("0.1.0"), description, and author. Verify and update if needed.

### Claude's Discretion
- Agent file naming convention (e.g., `security-hardener.md` vs `the-security-hardener.md`)
- Exact wording of persona system prompts (as long as they embody the character and produce structured output)
- Whether to include a brief "persona bio" section in each agent file for user documentation

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope. Note: orchestration (Phase 2), synthesis (Phase 3), hooks (Phase 4), and memory learning (Phase 5) are explicitly out of scope for this phase.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PERS-01 | Plugin includes at least 3 distinct persona agents with unique names, philosophies, and review lenses | 4 agents defined in D-01; agent frontmatter format verified against subagent docs |
| PERS-02 | Each persona agent has a structured output contract (severity, file, explanation, recommendation) | Output format locked in D-04; implemented via system prompt instructions |
| PERS-03 | Each persona reviews through a fundamentally different lens | 4 complementary lenses defined: adversarial-security, structural-architecture, empathetic-readability, pragmatic-shipping |
| PERS-04 | Persona agents are read-only (Glob, Grep, Read, Bash non-destructive) | Use `tools` allowlist + `disallowedTools` in frontmatter; `hooks`/`permissionMode` NOT available for plugin agents |
| PERS-05 | Persona agents are aware of CLAUDE.md project conventions | System prompt includes explicit instruction to read CLAUDE.md before reviewing |
| PLUG-01 | Plugin has a valid plugin.json manifest with name, version, description, author | Existing manifest verified correct; only `name` is required, all other fields present |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

CLAUDE.md contains project description and stack conventions but no additional actionable directives beyond what is captured in CONTEXT.md decisions. The GSD workflow enforcement section requires using GSD commands for file changes. No forbidden patterns or security requirements beyond what the plugin system itself constrains.

## Standard Stack

### Core

| Component | Format | Purpose | Why Standard |
|-----------|--------|---------|--------------|
| `plugin.json` | JSON (Schema v1) | Plugin identity and registration | Required by Claude Code. Only `name` is mandatory. |
| `agents/*.md` | Markdown + YAML frontmatter | Persona definitions | Native subagent system. Each `.md` becomes a dispatchable agent. |

### Agent Frontmatter Fields (Verified for Plugin Agents)

| Field | Value for This Phase | Required | Notes |
|-------|---------------------|----------|-------|
| `name` | kebab-case identifier | Yes | Must be unique across all agents |
| `description` | When Claude should delegate | Yes | Drives auto-delegation decisions |
| `model` | `sonnet` | No | Cost-effective for code review |
| `effort` | `medium` | No | Sweet spot for review depth |
| `maxTurns` | `10` | No | Prevents runaway exploration |
| `tools` | `Read, Glob, Grep, Bash` | No | Allowlist for read-only review |
| `disallowedTools` | `Write, Edit` | No | Enforces read-only constraint |
| `memory` | `project` | No | Per-persona project insights |
| `background` | `false` (or omit) | No | Reviews must complete before use |

**NOT supported for plugin agents (will be silently ignored):** `hooks`, `mcpServers`, `permissionMode`

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `tools` allowlist | `disallowedTools` only | Allowlist is safer -- explicitly permits only what's needed; denylist risks missing new tools |
| `model: sonnet` | `model: haiku` | Haiku is cheaper but may miss subtle issues; sonnet is the recommended balance |
| `model: sonnet` | `model: opus` | Opus is deeper but expensive for 4 parallel agents; save for v2 tiered analysis |
| `memory: project` | `memory: local` | Local is gitignored/private; project shares via VCS, better for team use |

## Architecture Patterns

### Plugin Directory Structure (Phase 1 Deliverables)

```
persona/
  .claude-plugin/
    plugin.json                    # Plugin manifest (exists, verify)
  agents/
    security-hardener.md           # Persona: adversarial security lens
    the-architect.md               # Persona: structural/design lens
    readability-advocate.md        # Persona: newcomer-empathy lens
    the-pragmatist.md              # Persona: shipping/simplicity lens
  skills/                          # Empty for Phase 1 (Phase 2)
    orchestrate/
    parse-output/
  hooks/                           # Empty for Phase 1 (Phase 4)
  scripts/                         # Empty for Phase 1 (Phase 4)
  memory/
    MEMORY.md                      # Exists (placeholder)
```

Note: `skills/`, `hooks/`, and `scripts/` directories exist from scaffold but are populated in later phases. Phase 1 focuses exclusively on `agents/` and `plugin.json`.

### Pattern 1: Agent File Structure

**What:** Each persona agent is a single markdown file with YAML frontmatter and a system prompt body.
**When to use:** Every persona agent follows this pattern.
**Example:**

```markdown
---
name: security-hardener
description: Adversarial security reviewer that hunts for vulnerabilities, injection points, auth gaps, and data exposure in code
model: sonnet
effort: medium
maxTurns: 10
tools: Read, Glob, Grep, Bash
disallowedTools: Write, Edit
memory: project
---

[System prompt body goes here - character voice + review instructions + output format]
```

Source: research/04-subagents.md, research/02-plugins-reference.md

### Pattern 2: Structured Output via System Prompt

**What:** The output contract (severity, confidence, file, issue, recommendation, reasoning) is enforced through system prompt instructions, not through code or tooling.
**When to use:** Every persona agent's system prompt must include the output format specification.
**Example output format (from D-04):**

```markdown
## [Persona Name] Review

### Finding 1
- **Severity:** critical | warning | suggestion
- **Confidence:** [0-100]
- **File:** [path]
- **Issue:** [what's wrong]
- **Recommendation:** [what to do instead]
- **Reasoning:** [why this matters from this persona's perspective]
```

### Pattern 3: CLAUDE.md Awareness

**What:** Each persona's system prompt includes an explicit instruction to read the target project's CLAUDE.md before reviewing, so findings respect project conventions.
**When to use:** Required by PERS-05 and D-08.
**Implementation:** Add to each system prompt: "Before reviewing, read CLAUDE.md in the project root (if it exists) to understand project conventions, coding standards, and constraints. Do not flag issues that are consistent with documented project conventions."

### Pattern 4: "What I Ignore" Boundaries

**What:** Each persona explicitly declares what is outside its review lens to prevent overlapping findings.
**When to use:** All persona system prompts (from Specifics section of CONTEXT.md).
**Purpose:** Maximizes productive disagreement by keeping personas in their lanes. Security Hardener ignores code style. Readability Advocate ignores performance. The Pragmatist ignores theoretical security risks. The Architect ignores naming conventions.

### Anti-Patterns to Avoid

- **Gimmicky voice:** Do NOT use catchphrases, emoji, roleplay personas, or forced personality quirks. Voice comes from priorities, framing, and tolerance for tradeoffs (D-03).
- **Overlapping lenses:** Do NOT have all 4 personas comment on the same things. Each should have a clear "what I ignore" section.
- **Over-long system prompts:** Keep prompts focused. The 200-line memory limit means context is precious. Aim for 50-100 lines per system prompt.
- **Using `context: fork` for orchestration:** This would make the orchestrator a subagent, which cannot spawn persona subagents. (Out of scope for Phase 1 but noted for awareness.)
- **Including `hooks` or `permissionMode` in agent frontmatter:** Silently ignored for plugin agents. Wastes developer time debugging.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Agent dispatch | Custom script-based agent spawning | `agents/*.md` subagent definitions | Native Claude Code mechanism; auto-discovered |
| Tool restriction | Prompt-based "please don't edit files" | `tools`/`disallowedTools` frontmatter | Enforced at platform level, not honor system |
| Memory persistence | Custom file-based memory system | `memory: project` frontmatter | Built-in MEMORY.md with auto-load of first 200 lines |
| Plugin registration | Manual path configuration | `plugin.json` in `.claude-plugin/` | Auto-discovered by Claude Code plugin system |
| Skill namespacing | Custom command routing | Skills in `skills/` directory | Automatic `/persona:<skill>` namespacing |

**Key insight:** Claude Code's plugin system handles discovery, registration, namespacing, tool restriction, and memory. The entire "infrastructure" for Phase 1 is writing the right YAML frontmatter and system prompts. Do not build anything the platform provides.

## Common Pitfalls

### Pitfall 1: Plugin Agents Silently Ignore hooks/permissionMode

**What goes wrong:** Adding `hooks:` or `permissionMode:` to agent frontmatter. Fields are silently ignored. Agent runs with default permissions and no lifecycle hooks.
**Why it happens:** These fields ARE valid for standalone agents (`.claude/agents/`) but NOT for plugin agents.
**How to avoid:** Only use the supported fields listed in the Standard Stack table above. For tool restriction, use `tools`/`disallowedTools` exclusively.
**Warning signs:** Agent appears to load but hooks never fire; permission behavior doesn't match expectation.

### Pitfall 2: Directories Inside .claude-plugin/

**What goes wrong:** Placing `agents/`, `skills/`, `hooks/` inside `.claude-plugin/` instead of at the plugin root. Nothing loads.
**Why it happens:** Intuitive but wrong. Only `plugin.json` goes inside `.claude-plugin/`.
**How to avoid:** Verify the scaffold has directories at the plugin root level (it does -- already confirmed).
**Warning signs:** Plugin loads but no agents or skills appear.

### Pitfall 3: Bash Tool Without disallowedTools Guard

**What goes wrong:** Including `Bash` in the `tools` allowlist without also disallowing `Write` and `Edit`. A persona could theoretically use Bash to run destructive commands (e.g., `rm`, `git checkout`).
**Why it happens:** D-06 says "non-destructive Bash" but the platform has no "non-destructive Bash" mode.
**How to avoid:** Include `Bash` in `tools` (needed for `git diff`, `git log`, etc.) but add explicit system prompt instructions: "Never use Bash to modify files, delete files, or run destructive git commands. Bash is only for reading information (git log, git diff, find, etc.)." Also set `disallowedTools: Write, Edit` to block the obvious write paths.
**Warning signs:** Persona produces "I've fixed the issue" in its output instead of "I recommend fixing..."

### Pitfall 4: Agent Name Collisions

**What goes wrong:** Two agent files have the same `name:` field in frontmatter. One silently shadows the other.
**Why it happens:** Using similar naming patterns (e.g., `reviewer` appearing in multiple names).
**How to avoid:** Use distinct, descriptive names: `security-hardener`, `the-architect`, `readability-advocate`, `the-pragmatist`. Verify uniqueness across all agents.
**Warning signs:** Fewer agents appear than expected when listing available agents.

### Pitfall 5: Forgetting /reload-plugins During Development

**What goes wrong:** Editing agent files and seeing no change when testing.
**Why it happens:** Plugin content is cached at load time.
**How to avoid:** After every edit: `/reload-plugins`, then test.
**Warning signs:** Changes to system prompts or frontmatter don't take effect.

## Code Examples

### Agent File: Security Hardener (structural template)

```markdown
---
name: security-hardener
description: Adversarial security reviewer that hunts for vulnerabilities, injection points, auth gaps, and data exposure in code
model: sonnet
effort: medium
maxTurns: 10
tools: Read, Glob, Grep, Bash
disallowedTools: Write, Edit
memory: project
---

[System prompt with: identity, philosophy, what-I-notice-first, what-I-ignore,
 CLAUDE.md awareness instruction, output format, conciseness directive]
```

Source: research/02-plugins-reference.md (agent frontmatter), research/04-subagents.md (supported fields)

### Plugin Manifest: Existing (verified correct)

```json
{
  "name": "persona",
  "version": "0.1.0",
  "description": "Multi-persona code review orchestrator -- get feedback from diverse expert perspectives",
  "author": {
    "name": "Trent Tuttle"
  }
}
```

Source: `.claude-plugin/plugin.json` (existing file, verified against plugins-reference schema)

### Testing Command

```bash
# Load plugin for local testing
claude --plugin-dir ./persona

# After making changes
/reload-plugins

# Verify agents are available (in Claude Code session)
# Ask: "What agents are available?"
# Or attempt to delegate: "Use the security-hardener agent to review src/index.ts"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `commands/` directory for skills | `skills/` directory with SKILL.md | Claude Code 1.0.33+ | Skills support frontmatter, arguments, dynamic context |
| Inline hooks in plugin.json | Separate `hooks/hooks.json` | Still both work | Separate file is cleaner for maintenance |
| No plugin agents support for `memory` | `memory` supported for plugin agents | Current | Enables persistent per-persona learning |

**Deprecated/outdated:**
- Nothing relevant to Phase 1 is deprecated. The plugin system is current.

## Open Questions

1. **Bash tool safety for read-only personas**
   - What we know: `disallowedTools` blocks `Write` and `Edit`, but `Bash` can still run destructive commands
   - What's unclear: Whether Claude Code has a "read-only Bash" mode or if this is purely prompt-enforced
   - Recommendation: Use prompt instructions to restrict Bash to read-only commands. Accept the risk that prompt enforcement is softer than tool-level enforcement. This is a known tradeoff.

2. **Agent auto-delegation behavior**
   - What we know: Claude rarely auto-delegates to subagents without explicit instructions (Pitfall 3 in PITFALLS.md)
   - What's unclear: How well agent `description` fields influence delegation in practice
   - Recommendation: For Phase 1, test agents by explicitly asking Claude to use them. Orchestration skill (Phase 2) will handle explicit dispatch. Write good descriptions anyway for future auto-delegation.

3. **Character voice quality**
   - What we know: D-02 requires "immediately attributable by voice alone"
   - What's unclear: How much character voice survives when the model follows structured output format
   - Recommendation: Put character identity and philosophy BEFORE output format instructions in the system prompt. The "Reasoning" field in each finding is where character voice shows most -- emphasize this in prompts.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Claude Code | Plugin loading | Yes | 2.1.81 | -- |
| Bash (Git Bash) | Agent Bash tool, future hook scripts | Yes | 5.2.37 | -- |
| jq | Future hook scripts (Phase 4) | **No** | -- | Use bash string parsing or node inline scripts |

**Missing dependencies with no fallback:**
- None for Phase 1 (agents and plugin.json require only Claude Code)

**Missing dependencies with fallback:**
- `jq` is not installed. This does not block Phase 1 (no hooks yet). For Phase 4 hook scripts, either install jq or use alternative JSON parsing (bash built-ins, node -e). Flag for Phase 4 planning.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Manual validation via Claude Code CLI |
| Config file | None needed -- plugin system is the test harness |
| Quick run command | `claude --plugin-dir ./persona` then test agent delegation |
| Full suite command | Load plugin, invoke each agent, verify output format |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PLUG-01 | Plugin manifest is valid | smoke | `claude plugin validate ./persona` (if available) or load with `--plugin-dir` | N/A -- manual |
| PERS-01 | 4 distinct persona agents load | smoke | Load plugin, ask "list available agents" | N/A -- manual |
| PERS-02 | Structured output with severity/confidence/file/issue/recommendation/reasoning | integration | Invoke each agent on a sample file, verify output contains all fields | N/A -- manual |
| PERS-03 | Each reviews through different lens | integration | Run all 4 on same file, compare focus areas | N/A -- manual |
| PERS-04 | Agents are read-only (no Write/Edit) | unit | Check each agent's frontmatter has `disallowedTools: Write, Edit` | N/A -- file inspection |
| PERS-05 | Agents aware of CLAUDE.md | integration | Invoke agent in project with CLAUDE.md, verify it references conventions | N/A -- manual |

### Sampling Rate
- **Per task commit:** Load plugin with `claude --plugin-dir ./persona`, verify agent loads
- **Per wave merge:** Invoke all 4 agents on a sample code file
- **Phase gate:** Full manual test of all 6 requirements

### Wave 0 Gaps
- None -- this is a plugin with markdown files, not a codebase with a test framework. Validation is done through the Claude Code plugin loading system itself. No test infrastructure to create.

## Sources

### Primary (HIGH confidence)
- `research/01-create-plugins.md` -- plugin creation, directory structure, testing workflow
- `research/02-plugins-reference.md` -- complete manifest schema, supported frontmatter, unsupported fields for plugin agents
- `research/04-subagents.md` -- frontmatter fields, memory scopes, delegation patterns
- `.planning/research/PITFALLS.md` -- 13 domain pitfalls with prevention strategies
- `.planning/research/STACK.md` -- full stack recommendations with verified sources

### Secondary (MEDIUM confidence)
- None needed -- all findings verified against official docs captured in research/

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- verified against official Claude Code docs (captured in research/)
- Architecture: HIGH -- plugin structure is well-documented with explicit constraints
- Pitfalls: HIGH -- documented in official sources and cross-verified in PITFALLS.md

**Research date:** 2026-03-22
**Valid until:** 2026-04-22 (plugin system is stable; 30-day window appropriate)
