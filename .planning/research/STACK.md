# Technology Stack

**Project:** Persona - Multi-Persona Code Review Plugin
**Researched:** 2026-03-22
**Overall confidence:** HIGH

This is a Claude Code plugin. The "stack" is not frameworks and npm packages -- it is Claude Code's native plugin primitives: markdown files, JSON configs, and shell scripts. There is no build step, no runtime, and no external dependencies.

## Recommended Stack

### Core: Plugin Manifest

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `plugin.json` | Schema v1 | Plugin identity and component registration | Required by Claude Code. Only `name` is mandatory; keep metadata minimal until marketplace listing. |

**Confidence:** HIGH -- directly verified against plugins-reference docs.

**Current manifest is correct.** The existing `.claude-plugin/plugin.json` with `name`, `version`, `description`, `author` is the right shape. No changes needed.

### Persona Definitions: Subagent Markdown Files

| Technology | Format | Purpose | Why |
|------------|--------|---------|-----|
| `agents/*.md` | Markdown with YAML frontmatter | Define each reviewer persona | Claude Code's native subagent system. Each `.md` file becomes a dispatchable agent with its own model, tools, and system prompt. Zero infrastructure. |

**Confidence:** HIGH -- verified against subagents docs and plugins-reference.

**Supported frontmatter for plugin agents:**
- `name` (required) -- unique kebab-case identifier
- `description` (required) -- tells Claude when to delegate here
- `model` -- `sonnet` for cost-effective reviews, `opus` for deep analysis
- `effort` -- `medium` is the sweet spot for code review
- `maxTurns` -- cap at 10-15 for reviews (they should not be open-ended)
- `tools` -- allowlist: `Read`, `Glob`, `Grep` for code navigation
- `disallowedTools` -- `Write`, `Edit` so reviewers cannot modify code
- `memory` -- `project` scope so personas accumulate project-specific insights
- `skills` -- preload shared review conventions
- `background` -- `false` (reviews need to complete before synthesis)

**NOT supported for plugin agents:** `hooks`, `mcpServers`, `permissionMode`. These must live at the plugin level, not in agent frontmatter. This is a hard constraint.

### Orchestration: Skills with SKILL.md

| Technology | Format | Purpose | Why |
|------------|--------|---------|-----|
| `skills/orchestrate/SKILL.md` | Markdown with YAML frontmatter | User-facing `/persona:orchestrate` command | Skills are how users invoke plugin functionality. The orchestrator skill tells Claude to dispatch to persona agents and synthesize results. |
| `skills/parse-output/SKILL.md` | Markdown with YAML frontmatter | Internal synthesis skill | Processes raw persona feedback into a unified review. Set `user-invocable: false` so only Claude calls it. |

**Confidence:** HIGH -- verified against skills docs.

**Key skill frontmatter decisions:**

```yaml
# skills/orchestrate/SKILL.md
---
name: orchestrate
description: Run a multi-persona code review on specified files or changes
argument-hint: <file-or-diff-target>
---
```

- Do NOT use `context: fork` on the orchestrator skill. The orchestrator needs to be in the main context to spawn subagents. Subagents cannot spawn other subagents -- this is a hard platform constraint.
- Do NOT use `disable-model-invocation: true` unless you want to prevent Claude from auto-triggering reviews. Start with the default (Claude can invoke it) and restrict later if noisy.
- Use `$ARGUMENTS` for the review target (file path, diff, etc.).
- Use `!` backtick syntax for dynamic context injection (e.g., `!git diff --staged` to inject the current diff).

### Event Tracking: Hooks

| Technology | Format | Purpose | Why |
|------------|--------|---------|-----|
| `hooks/hooks.json` | JSON | Track SubagentStart/Stop events | Hooks provide deterministic automation with zero context cost. Use command-type hooks to log progress, not LLM-based hooks. |

**Confidence:** HIGH -- verified against hooks-guide and hooks-reference.

**Hook events to use:**

| Event | Matcher | Purpose |
|-------|---------|---------|
| `SubagentStart` | Custom agent names | Log which persona is starting, inject additional context |
| `SubagentStop` | Custom agent names | Capture persona results, track completion |
| `Stop` | (none) | Final synthesis notification |

**Critical hook details:**
- `SubagentStart` cannot block agent creation. It CAN inject `additionalContext` into the subagent.
- `SubagentStop` CAN block the stop (decision: "block") to force continued review. Use sparingly.
- `SubagentStop` input includes `last_assistant_message` -- this is how you capture persona output.
- Use `${CLAUDE_PLUGIN_ROOT}` in all script paths. Never hardcode absolute paths.
- Scripts must be executable (`chmod +x`). On Windows, use bash scripts via Git Bash.

### Persistent Learning: Agent Memory

| Technology | Scope | Purpose | Why |
|------------|-------|---------|-----|
| `memory: project` | `.claude/agent-memory/<agent-name>/` | Per-persona project insights | Each persona accumulates knowledge about the specific project's patterns, conventions, and recurring issues. `project` scope (not `user`) because insights are project-specific. |

**Confidence:** HIGH -- verified against subagents docs. `memory` IS supported for plugin agents.

**How memory works:**
- When enabled, subagent gets read/write access to its memory directory
- First 200 lines of `MEMORY.md` are loaded into context automatically
- Each persona gets its own memory directory: `.claude/agent-memory/security-reviewer/`, `.claude/agent-memory/performance-analyst/`, etc.
- Memory persists across sessions -- this is how personas "learn" the project

### Helper Scripts

| Technology | Format | Purpose | Why |
|------------|--------|---------|-----|
| `scripts/*.sh` | Bash shell scripts | Hook handlers, output parsing, progress logging | Hooks execute shell commands. Keep logic in scripts, not inline JSON. Testable, readable, maintainable. |

**Confidence:** HIGH -- standard plugin pattern from reference docs.

**Script conventions:**
- Read JSON from stdin with `jq` (Claude Code provides hook context as JSON on stdin)
- Exit 0 to proceed, exit 2 to block
- Return JSON on stdout for structured responses
- Use `${CLAUDE_PLUGIN_ROOT}` for paths within the plugin
- Use `${CLAUDE_PLUGIN_DATA}` for persistent state that survives plugin updates

### Supporting Files

| Technology | Format | Purpose | Why |
|------------|--------|---------|-----|
| `skills/orchestrate/reference.md` | Markdown | Review conventions and output format spec | Skills can include supporting files alongside SKILL.md. Keeps SKILL.md under 500 lines. |
| `memory/MEMORY.md` | Markdown | Plugin-level memory index | Already exists in scaffold. Serves as shared knowledge base. |

## What NOT to Use

| Anti-Pattern | Why Not | What to Do Instead |
|--------------|---------|-------------------|
| npm packages / node_modules | Plugin constraint: no external deps. Plugin is copied to cache; node_modules would bloat it and may not resolve correctly. | Use shell scripts with standard Unix tools (`jq`, `grep`, `sed`). |
| MCP servers for persona dispatch | Over-engineered. Subagents are the native way to do isolated AI tasks. MCP is for external service integration. | Use `agents/*.md` subagent definitions. |
| `context: fork` on orchestrator skill | Forked skills run as subagents. Subagents cannot spawn subagents. The orchestrator MUST run in main context to dispatch personas. | Omit `context: fork`. Let the skill run in the main conversation context. |
| `hooks` in agent frontmatter | Not supported for plugin agents. Will be silently ignored. | Define hooks at plugin level in `hooks/hooks.json`. |
| `permissionMode` in agent frontmatter | Not supported for plugin agents. | Omit entirely. Plugin agents inherit default permissions. |
| Agent-type or prompt-type hooks for progress tracking | Expensive. Uses LLM calls for what should be deterministic logging. | Use command-type hooks with shell scripts. |
| `isolation: worktree` for persona agents | Creates git worktrees per agent. Unnecessary overhead for read-only code review. | Omit. Personas only need read access to the codebase. |
| Inline hooks in `plugin.json` | Works but harder to maintain as hook logic grows. | Use separate `hooks/hooks.json` file referenced from manifest. |
| `user` memory scope | Stores insights globally across all projects. Code review insights are project-specific. | Use `project` memory scope. |

## Directory Structure (Final Target)

```
persona/
  .claude-plugin/
    plugin.json                    # Plugin manifest
  agents/
    security-reviewer.md           # Persona: security focus
    performance-analyst.md         # Persona: performance focus
    maintainability-reviewer.md    # Persona: code quality focus
    [additional-personas].md       # Extensible by users
  skills/
    orchestrate/
      SKILL.md                     # Main review orchestration skill
      reference.md                 # Review format and conventions
    parse-output/
      SKILL.md                     # Synthesis skill (model-invocable only)
  hooks/
    hooks.json                     # SubagentStart/Stop tracking
  scripts/
    on-agent-start.sh              # SubagentStart hook handler
    on-agent-stop.sh               # SubagentStop hook handler
  memory/
    MEMORY.md                      # Plugin memory index
```

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Persona dispatch | Subagents (`agents/*.md`) | MCP tool calls | MCP is for external services, not AI task dispatch. Subagents are purpose-built for this. |
| Orchestration | Main-context skill | `context: fork` skill | Fork runs as subagent; subagents can't spawn subagents. Platform constraint. |
| Progress tracking | Command hooks | Prompt/agent hooks | Command hooks are free (no LLM cost), deterministic, and fast. |
| Memory scope | `project` | `user` or `local` | Project scope shares insights via version control; user scope is too broad; local scope is gitignored and private. |
| Script language | Bash | Python / Node.js | Bash has no dependency requirements. `jq` handles JSON parsing. Keeps plugin zero-dep. |
| Hook config location | `hooks/hooks.json` | Inline in `plugin.json` | Separate file is cleaner as hook logic grows. Plugin.json stays focused on metadata. |

## Installation

There is no installation step. This is a Claude Code plugin -- it is pure configuration files.

**To develop locally:**
```bash
claude --plugin-dir ./persona
```

**To reload after changes:**
```
/reload-plugins
```

**To validate:**
```bash
claude plugin validate ./persona
```

**To install from marketplace:**
```
/plugin install persona@ai-stuff
```

## Platform Constraints Summary

These are non-negotiable constraints from the Claude Code plugin system:

1. **Subagents cannot spawn subagents.** The orchestrator must run in main context.
2. **Plugin agents cannot use `hooks`, `mcpServers`, or `permissionMode`** in frontmatter.
3. **All paths must be relative** with `./` prefix or use `${CLAUDE_PLUGIN_ROOT}`.
4. **Paths cannot traverse above plugin root** (`../` will not work in cached plugins).
5. **Scripts must be executable.** `chmod +x` all `.sh` files.
6. **Plugin name determines skill namespace.** Skills invoke as `/persona:<skill-name>`.
7. **`CLAUDE_PLUGIN_DATA`** survives updates; `CLAUDE_PLUGIN_ROOT` changes on update.

## Sources

All findings verified against official Claude Code documentation captured in the project's `research/` directory:

- `research/01-create-plugins.md` -- Plugin creation guide (source: code.claude.com/docs/en/plugins)
- `research/02-plugins-reference.md` -- Plugin reference with schemas (source: code.claude.com/docs/en/plugins-reference)
- `research/03-skills.md` -- Skills system (source: code.claude.com/docs/en/skills)
- `research/04-subagents.md` -- Subagent definitions and memory (source: code.claude.com/docs/en/sub-agents)
- `research/07-features-overview.md` -- Feature comparison matrix (source: code.claude.com/docs/en/features-overview)
- `research/08-hooks-guide.md` -- Hooks patterns (source: code.claude.com/docs/en/hooks-guide)
- `research/hooks-reference.md` -- Complete hooks reference with event schemas
