# Architecture Patterns

**Domain:** Claude Code plugin with subagent orchestration for multi-persona code review
**Researched:** 2026-03-22

## Recommended Architecture

The plugin follows a **skill-driven orchestration** pattern where a user-invoked skill acts as the entry point, the main Claude Code agent dispatches persona subagents in parallel, and a synthesis step merges their outputs into a unified review.

### Why this shape

Claude Code's subagent system has one critical constraint: **subagents cannot spawn other subagents**. This means the orchestrator must live at the main agent level (via a skill), not inside a subagent. The skill instructs the main agent what to do; the main agent uses the built-in Agent tool to dispatch persona subagents.

```
User invokes /persona:review
        |
        v
+------------------+
|  Orchestrate     |  <-- SKILL.md: instructions for main agent
|  Skill           |      (reads file targets, dispatches personas)
+------------------+
        |
        | Main agent dispatches via Agent tool
        |
   +----+----+----+----+
   |    |    |    |    |
   v    v    v    v    v
 [P1] [P2] [P3] [P4] [P5]   <-- Persona subagents (agents/*.md)
   |    |    |    |    |          Each: read-only, own system prompt,
   |    |    |    |    |          project memory, specialized focus
   +----+----+----+----+
        |
        v
+------------------+
|  Synthesize      |  <-- Main agent merges persona outputs
|  (main agent)    |      using parse-output skill instructions
+------------------+
        |
        v
+------------------+
|  Present Review  |  <-- Formatted output to user
+------------------+
        |
        v (async, via hooks)
+------------------+
|  Memory Update   |  <-- Persona memory files updated
+------------------+
```

### Component Boundaries

| Component | Responsibility | Communicates With | Location |
|-----------|---------------|-------------------|----------|
| **Plugin Manifest** | Declares plugin identity, version, metadata | Claude Code plugin loader | `.claude-plugin/plugin.json` |
| **Orchestrate Skill** | Entry point; instructs main agent to read targets, dispatch all persona agents, collect results, synthesize | Main agent (via skill injection) | `skills/orchestrate/SKILL.md` |
| **Persona Agents** | Individual expert reviewers with distinct identities, priorities, review philosophies | Main agent (dispatched via Agent tool); project memory (read/write) | `agents/<persona-name>.md` |
| **Parse-Output Skill** | Instructions for how to merge and format multiple persona reviews into coherent output | Main agent (model-invocable, not user-invocable) | `skills/parse-output/SKILL.md` |
| **Hooks Config** | Tracks subagent lifecycle (SubagentStart/Stop) for progress reporting; optional memory triggers | Claude Code hook system | `hooks/hooks.json` |
| **Memory Store** | Per-persona project insights that persist across sessions | Persona agents (read/write via memory system) | `memory/MEMORY.md` (index) + `.claude/agent-memory/<name>/` (runtime) |
| **Scripts** | Helper scripts for hooks (progress tracking, memory management) | Hook system (invoked as command hooks) | `scripts/` |

### Data Flow

**Phase 1: Invocation**
1. User types `/persona:review <target>` (e.g., a file path, PR, or "staged changes")
2. Claude Code loads `skills/orchestrate/SKILL.md` into the main agent context
3. The skill uses `!` backtick syntax to dynamically inject context (e.g., `!git diff --staged` for staged changes)
4. `$ARGUMENTS` substitution provides the user's target specification

**Phase 2: Dispatch**
1. Main agent reads the orchestration instructions
2. Main agent uses the Agent tool to spawn each persona subagent defined in `agents/`
3. Claude Code dispatches subagents in parallel (native behavior when multiple Agent calls are made)
4. Each subagent receives: its persona system prompt, the code to review (via tools), and first 200 lines of its MEMORY.md
5. `SubagentStart` hooks fire for each persona (matched by agent name), enabling progress logging

**Phase 3: Review**
1. Each persona subagent independently reviews the code using read-only tools (Read, Grep, Glob)
2. Each applies its unique lens: security, performance, maintainability, etc.
3. Each produces structured output (findings, severity, suggestions) per its system prompt instructions
4. `SubagentStop` hooks fire as each completes, providing `last_assistant_message`

**Phase 4: Synthesis**
1. Main agent collects all persona outputs (returned from Agent tool calls)
2. Main agent follows parse-output skill instructions to: deduplicate findings, resolve contradictions, rank by severity, format output
3. Unified review is presented to the user

**Phase 5: Memory Update**
1. Each persona subagent writes insights to its memory directory during its turn (enabled by `memory: project`)
2. Over time, personas accumulate project-specific knowledge (code patterns, past issues, team conventions)

## Patterns to Follow

### Pattern 1: Skill as Orchestration Script
**What:** The orchestrate skill does not use `context: fork` -- it runs in the main agent context so it can dispatch subagents.
**When:** Any time you need a skill that spawns multiple subagents.
**Why:** `context: fork` would run the skill as a subagent, and subagents cannot spawn other subagents. The skill must inject instructions into the main agent.

```markdown
---
name: review
description: Run multi-persona code review on specified targets
---

# Multi-Persona Code Review

## Current diff context
!`git diff --staged 2>/dev/null || echo "No staged changes"`

## Instructions
1. Read the target files: $ARGUMENTS
2. Dispatch each persona agent to review the code
3. Collect all persona outputs
4. Synthesize into a unified review using the parse-output skill
```

### Pattern 2: Read-Only Persona Agents
**What:** Persona subagents get only read-only tools (Read, Grep, Glob, Bash for read commands) plus memory write access.
**When:** Always, for review agents that should never modify code.
**Why:** Review agents should observe and report, not change code. Prevents accidental mutations.

```markdown
---
name: security-sentinel
description: Reviews code for security vulnerabilities, injection risks, auth issues
tools: Read, Grep, Glob
model: sonnet
memory: project
maxTurns: 15
effort: high
---

You are Security Sentinel...
```

### Pattern 3: Structured Output Contract
**What:** All persona agents produce output in a consistent structure so synthesis is reliable.
**When:** Always -- the parse-output skill depends on predictable format.
**Why:** Without a contract, synthesis becomes fragile string parsing instead of reliable pattern matching.

Each persona system prompt should mandate output format:
```
## Findings
### [SEVERITY: critical/high/medium/low] Finding Title
- **File:** path/to/file.ts:42
- **Issue:** Description
- **Suggestion:** How to fix
- **Rationale:** Why this matters from this persona's perspective
```

### Pattern 4: Dynamic Context via Backtick Injection
**What:** Use `!` backtick syntax in SKILL.md to inject live data (git diff, file lists) before the skill is processed.
**When:** The orchestrate skill needs current repo state.
**Why:** Avoids requiring the agent to run extra tool calls; context is pre-loaded.

### Pattern 5: SubagentStop Hooks for Progress
**What:** Use SubagentStop hooks matched on persona agent names to log progress.
**When:** Optional but recommended for UX -- lets users see which personas have completed.
**Why:** Multi-persona review takes time; progress feedback prevents the user from thinking it stalled.

```json
{
  "hooks": {
    "SubagentStop": [{
      "matcher": "security-sentinel|performance-hawk|maintainability-sage",
      "hooks": [{
        "type": "command",
        "command": "echo \"Persona review complete\" >&2"
      }]
    }]
  }
}
```

## Anti-Patterns to Avoid

### Anti-Pattern 1: Orchestrator as a Subagent
**What:** Making the orchestrate skill use `context: fork` or putting orchestration logic in an agent definition.
**Why bad:** Subagents cannot spawn other subagents. The orchestrator would be unable to dispatch persona agents.
**Instead:** Keep the orchestrate skill running in main agent context (no `context: fork`).

### Anti-Pattern 2: Plugin-Level Hooks on Agents
**What:** Trying to define `hooks` or `mcpServers` in agent frontmatter within a plugin.
**Why bad:** Plugin agents do NOT support `hooks`, `mcpServers`, or `permissionMode` fields. These are silently ignored.
**Instead:** Define hooks at the plugin level in `hooks/hooks.json` with matchers for specific agent names.

### Anti-Pattern 3: Unstructured Persona Output
**What:** Letting each persona free-form its review output.
**Why bad:** The synthesis step becomes unreliable. Different formats mean the main agent has to guess structure.
**Instead:** Enforce a strict output contract in each persona's system prompt.

### Anti-Pattern 4: Using Memory for Inter-Agent Communication
**What:** Having one persona write to memory expecting another persona to read it in the same session.
**Why bad:** Memory is loaded at subagent start (first 200 lines of MEMORY.md). Writes during a session are not visible to sibling agents running in parallel.
**Instead:** All synthesis happens at the main agent level after all subagents complete.

### Anti-Pattern 5: Heavyweight Persona Count
**What:** Defining 10+ personas for every review.
**Why bad:** Each subagent is a full Claude invocation. Cost and latency scale linearly with persona count. Diminishing returns on review quality past 4-5 perspectives.
**Instead:** Start with 3-4 well-differentiated personas. Let users selectively invoke subsets.

## Component Build Order

Build order is driven by two constraints: (1) you cannot test downstream components without upstream ones, and (2) the plugin manifest must exist first for Claude Code to recognize the plugin.

```
Phase 1: Foundation
  plugin.json (exists) --> persona agent definitions (at least 2)

Phase 2: Core Loop
  orchestrate skill --> (depends on agents from Phase 1)

Phase 3: Synthesis
  parse-output skill --> (depends on orchestrate producing output)

Phase 4: Polish
  hooks config --> (depends on agents being named/finalized)
  memory setup --> (depends on agents having memory: project)
  scripts/ helpers --> (depends on hooks config)
```

**Rationale:**
- **Agents first** because they are self-contained and independently testable (you can invoke them directly with `claude --agent <name>`)
- **Orchestrate skill second** because it is the glue -- it needs agents to dispatch
- **Parse-output third** because it needs real multi-persona output to test against
- **Hooks and memory last** because they are enhancements, not core flow -- the review works without them

## Scalability Considerations

| Concern | 2-3 Personas | 5-6 Personas | 10+ Personas |
|---------|-------------|-------------|-------------|
| **Latency** | Acceptable (parallel dispatch) | Noticeable but manageable | Likely frustrating; consider subset selection |
| **Cost** | Low (each is one subagent call) | Moderate | High; recommend user opt-in per persona |
| **Context window** | No issue | Synthesis output grows; still fits | May hit context limits on main agent during synthesis |
| **Memory conflicts** | Unlikely | Low risk | Higher risk of conflicting memory entries across personas |

**Recommendation:** Ship with 3-4 personas. Design the system to support more, but default to a curated set. The orchestrate skill should accept optional persona selection (e.g., `/persona:review --only security,performance src/auth.ts`).

## Key Architectural Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Orchestration location | Main agent via skill (not forked) | Subagents cannot spawn subagents |
| Agent dispatch | Native Agent tool, parallel | Built-in Claude Code behavior; no custom infra |
| Persona output format | Structured markdown contract | Reliable synthesis requires predictable input |
| Hook placement | Plugin-level `hooks/hooks.json` | Plugin agents cannot define their own hooks |
| Memory scope | `memory: project` per persona | Insights are project-specific; accumulate over time |
| Tool access for personas | Read-only (Read, Grep, Glob) | Review agents should not modify code |
| Synthesis location | Main agent after all subagents complete | Only main agent has access to all outputs |

## Sources

- Claude Code Plugin Reference: https://code.claude.com/docs/en/plugins-reference (HIGH confidence -- official docs)
- Claude Code Subagents: https://code.claude.com/docs/en/sub-agents (HIGH confidence -- official docs)
- Claude Code Skills: https://code.claude.com/docs/en/skills (HIGH confidence -- official docs)
- Claude Code Hooks Guide: https://code.claude.com/docs/en/hooks-guide (HIGH confidence -- official docs)
- Hooks Reference (SubagentStart/Stop schemas): https://code.claude.com/docs/en/hooks-reference (HIGH confidence -- official docs)
