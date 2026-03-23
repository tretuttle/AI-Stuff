<!-- GSD:project-start source:PROJECT.md -->
## Project

**Persona**

A Claude Code plugin that orchestrates multi-persona code reviews. It dispatches code to multiple AI subagents — each with a distinct expert identity, philosophy, and priorities — collects their feedback in parallel, and synthesizes a unified review. Personas accumulate project-specific insights via memory, so feedback sharpens over time.

**Core Value:** Diverse expert perspectives on code that a single reviewer would miss — each persona has its own philosophy, priorities, and blind spots.

### Constraints

- **Plugin format**: Must conform to Claude Code plugin conventions (plugin.json, agents/, skills/, hooks/)
- **Subagent system**: Persona agents must be `.md` subagent definitions that Claude Code can dispatch
- **No external deps**: Plugin should work with just Claude Code — no npm packages or external services
- **Marketplace compatible**: Must be installable via `/plugin install persona@ai-stuff`
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

## Recommended Stack
### Core: Plugin Manifest
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `plugin.json` | Schema v1 | Plugin identity and component registration | Required by Claude Code. Only `name` is mandatory; keep metadata minimal until marketplace listing. |
### Persona Definitions: Subagent Markdown Files
| Technology | Format | Purpose | Why |
|------------|--------|---------|-----|
| `agents/*.md` | Markdown with YAML frontmatter | Define each reviewer persona | Claude Code's native subagent system. Each `.md` file becomes a dispatchable agent with its own model, tools, and system prompt. Zero infrastructure. |
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
### Orchestration: Skills with SKILL.md
| Technology | Format | Purpose | Why |
|------------|--------|---------|-----|
| `skills/orchestrate/SKILL.md` | Markdown with YAML frontmatter | User-facing `/persona:orchestrate` command | Skills are how users invoke plugin functionality. The orchestrator skill tells Claude to dispatch to persona agents and synthesize results. |
| `skills/parse-output/SKILL.md` | Markdown with YAML frontmatter | Internal synthesis skill | Processes raw persona feedback into a unified review. Set `user-invocable: false` so only Claude calls it. |
# skills/orchestrate/SKILL.md
- Do NOT use `context: fork` on the orchestrator skill. The orchestrator needs to be in the main context to spawn subagents. Subagents cannot spawn other subagents -- this is a hard platform constraint.
- Do NOT use `disable-model-invocation: true` unless you want to prevent Claude from auto-triggering reviews. Start with the default (Claude can invoke it) and restrict later if noisy.
- Use `$ARGUMENTS` for the review target (file path, diff, etc.).
- Use `!` backtick syntax for dynamic context injection (e.g., `!git diff --staged` to inject the current diff).
### Event Tracking: Hooks
| Technology | Format | Purpose | Why |
|------------|--------|---------|-----|
| `hooks/hooks.json` | JSON | Track SubagentStart/Stop events | Hooks provide deterministic automation with zero context cost. Use command-type hooks to log progress, not LLM-based hooks. |
| Event | Matcher | Purpose |
|-------|---------|---------|
| `SubagentStart` | Custom agent names | Log which persona is starting, inject additional context |
| `SubagentStop` | Custom agent names | Capture persona results, track completion |
| `Stop` | (none) | Final synthesis notification |
- `SubagentStart` cannot block agent creation. It CAN inject `additionalContext` into the subagent.
- `SubagentStop` CAN block the stop (decision: "block") to force continued review. Use sparingly.
- `SubagentStop` input includes `last_assistant_message` -- this is how you capture persona output.
- Use `${CLAUDE_PLUGIN_ROOT}` in all script paths. Never hardcode absolute paths.
- Scripts must be executable (`chmod +x`). On Windows, use bash scripts via Git Bash.
### Persistent Learning: Agent Memory
| Technology | Scope | Purpose | Why |
|------------|-------|---------|-----|
| `memory: project` | `.claude/agent-memory/<agent-name>/` | Per-persona project insights | Each persona accumulates knowledge about the specific project's patterns, conventions, and recurring issues. `project` scope (not `user`) because insights are project-specific. |
- When enabled, subagent gets read/write access to its memory directory
- First 200 lines of `MEMORY.md` are loaded into context automatically
- Each persona gets its own memory directory: `.claude/agent-memory/security-reviewer/`, `.claude/agent-memory/performance-analyst/`, etc.
- Memory persists across sessions -- this is how personas "learn" the project
### Helper Scripts
| Technology | Format | Purpose | Why |
|------------|--------|---------|-----|
| `scripts/*.sh` | Bash shell scripts | Hook handlers, output parsing, progress logging | Hooks execute shell commands. Keep logic in scripts, not inline JSON. Testable, readable, maintainable. |
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
## Platform Constraints Summary
## Sources
- `research/01-create-plugins.md` -- Plugin creation guide (source: code.claude.com/docs/en/plugins)
- `research/02-plugins-reference.md` -- Plugin reference with schemas (source: code.claude.com/docs/en/plugins-reference)
- `research/03-skills.md` -- Skills system (source: code.claude.com/docs/en/skills)
- `research/04-subagents.md` -- Subagent definitions and memory (source: code.claude.com/docs/en/sub-agents)
- `research/07-features-overview.md` -- Feature comparison matrix (source: code.claude.com/docs/en/features-overview)
- `research/08-hooks-guide.md` -- Hooks patterns (source: code.claude.com/docs/en/hooks-guide)
- `research/hooks-reference.md` -- Complete hooks reference with event schemas
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd:profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
