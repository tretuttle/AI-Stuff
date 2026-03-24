# Architecture

## Commands

Persona has three skills. One guided entry point, two power-user shortcuts.

| Command | Purpose |
|---------|---------|
| `/persona:run` | Guided workflow — walks you through review or chat. Also accepts direct args. |
| `/persona:review` | Power-user shortcut — straight to multi-persona review. |
| `/persona:call` | Power-user shortcut — straight to interactive persona chat. |

## How /persona:run Routes

```
/persona:run [args]
  |
  +- No args? → Guided mode (ask what the user wants)
  +- Starts with "review"? → Review mode
  +- Matches a persona name? → Chat mode
  +- Looks like a file path? → Review mode (inferred)
  +- "--reset"? → Reset chat mode
```

## How Review Works

```
/persona:review src/auth.ts --only "ThePrimeagen,DHH"
  |
  +- Parse arguments (target, --only, --min-confidence)
  +- Discover agents (Glob agents/*.md, exclude template.md)
  +- Filter to selected personas
  +- Clear persona-reviews/ (remove stale results)
  +- Show confirmation
  +- Dispatch all in parallel via Task tool
  |    +- theprimeagen reads code, returns findings
  |    +- dhh reads code, returns findings
  +- Run Synthesis Protocol (dedup, boost, disagree, filter)
  +- Present unified review + save SYNTHESIS.md
```

**Key constraint:** The skill runs in the main conversation context (no `context: fork`) because the main agent must spawn persona subagents, and subagents cannot spawn other subagents.

## How Chat Works

```
/persona:call theprimeagen
  |
  +- Resolve name to agents/theprimeagen.md
  +- Read persona file
  +- Strip YAML frontmatter
  +- Apply as behavioral overlay (full tool access retained)
  +- Claude responds as ThePrimeagen until reset
```

## Persona Design

Personas are **principle-based and stack-agnostic**. They don't recommend specific tools — they apply transferable beliefs to whatever codebase they're invoked in.

Each persona file contains:
- **Voice & Tone** — personality, catchphrases, communication style
- **Core Beliefs** — principles that apply to any language/framework
- **How to Respond** — how to apply those principles to the code in front of them

Personas are always at full intensity. No diplomatic mode. The personality IS the product.

## Plugin Structure

```
persona/
+-- .claude-plugin/
|   +-- plugin.json              # Manifest (name, version)
+-- agents/
|   +-- theprimeagen.md          # ThePrimeagen
|   +-- dhh.md                   # DHH
|   +-- chris-coyier.md          # Chris Coyier
|   +-- dan-abramov.md           # Dan Abramov
|   +-- evan-you.md              # Evan You
|   +-- kent-c-dodds.md          # Kent C. Dodds
|   +-- lee-robinson.md          # Lee Robinson
|   +-- matt-mullenweg.md        # Matt Mullenweg
|   +-- matt-pocock.md           # Matt Pocock
|   +-- rich-harris.md           # Rich Harris
|   +-- scott-tolinski.md        # Scott Tolinski
|   +-- tanner-linsley.md        # Tanner Linsley
|   +-- theo-browne.md           # Theo Browne
|   +-- wes-bos.md               # Wes Bos
|   +-- template.md              # Template for custom personas
+-- skills/
|   +-- run/
|   |   +-- SKILL.md             # /persona:run (guided entry point)
|   +-- review/
|   |   +-- SKILL.md             # /persona:review (power-user shortcut)
|   |   +-- reference.md         # Roster, output format, synthesis protocol
|   +-- call/
|       +-- SKILL.md             # /persona:call (power-user shortcut)
+-- hooks/
|   +-- hooks.json               # SubagentStart/SubagentStop
+-- docs/
|   +-- SYNTHESIS.md             # Synthesis engine details + output format
|   +-- CUSTOM-PERSONAS.md       # Custom persona creation guide
|   +-- ARCHITECTURE.md          # This file
+-- memory/
|   +-- MEMORY-TEMPLATE.md       # Structured memory template
+-- .gitignore                   # Excludes persona-reviews/
+-- README.md                    # Quickstart + overview
```

## Memory System

Each persona uses `memory: project` to accumulate project-specific insights across sessions.

| Section | Budget | Purpose |
|---------|--------|---------|
| Active Patterns | 60 lines | Project conventions and patterns |
| Known Issues | 40 lines | Recurring problems |
| Style Conventions | 40 lines | Project style preferences |
| Architecture Notes | 30 lines | Key architectural decisions and constraints |
| Curation Log | 20 lines | What changed and when |

Memory is stored in `.claude/agent-memory/{agent-name}/MEMORY.md`. Personas curate their memory — replacing outdated entries rather than appending — to stay within a 190-line budget.

## Progress Tracking

SubagentStart/SubagentStop hooks log review progress:

```
[persona] Starting review: theprimeagen
[persona] Starting review: dhh
[persona] Finished review: theprimeagen
[persona] Finished review: dhh
```

Command-type hooks — zero LLM cost, deterministic execution.
