# ParkPal Content Plugin

A Claude Code plugin that orchestrates Disney park attraction content generation through a pipeline of specialized subagents.

## What This Does

Generates structured attraction data for all 6 Disney parks — fact sheets + 10 trivia questions per attraction — in two parallel formats:

- **JSON** → Seeds your Convex database
- **DOCX** → Human-readable review docs

## Architecture

```
Orchestrator → Researcher → Writer → Reviewer → Formatter
                                        ↑           │
                                        └── reject ──┘
```

Five subagent skills, each with a single responsibility:

| Agent | Job | Input | Output |
|---|---|---|---|
| **Orchestrator** | Break work into units, track progress | Park name | Dispatches per-attraction |
| **Researcher** | Gather & verify facts via web search | Attraction + park + land | Research brief |
| **Writer** | Author trivia from research | Research brief | Attraction JSON object |
| **Reviewer** | Validate schema, firewall, accuracy | Draft object | APPROVED or REJECTED |
| **Formatter** | Generate JSON + DOCX files | Approved objects | Files in `data/` |

## Setup

1. Copy this directory into your project or `~/.claude/skills/`
2. The `CLAUDE.md` at root provides project-level context
3. Skills in `.claude/skills/` are auto-discovered by Claude Code
4. Hookify rules in `.claude/` enforce the trivia firewall and schema validation

## Usage

```
> Let's start Magic Kingdom

# Orchestrator builds the roster, creates a plan, and starts dispatching

> Continue

# Resumes from where it left off — checks data/json/ for progress

> Export what we have so far

# Formatter outputs current progress as draft JSON + DOCX
```

## Key Files

```
parkpal-content-plugin/
├── CLAUDE.md                          # Master project instructions
├── .claude/
│   ├── settings.json                  # Permissions
│   ├── skills/
│   │   ├── orchestrator/SKILL.md      # Pipeline coordinator
│   │   ├── researcher/SKILL.md        # Fact gatherer
│   │   ├── writer/SKILL.md            # Trivia author
│   │   ├── reviewer/SKILL.md          # Quality gate
│   │   └── formatter/SKILL.md         # JSON + DOCX output
│   ├── hookify.warn-trivia-firewall.local.md
│   └── hookify.require-schema-validation.local.md
├── schemas/
│   ├── attraction.schema.json         # Canonical schema
│   ├── convex-schema.ts               # Convex table definition (reference)
│   └── seed-attractions.ts            # Convex seed mutation (reference)
├── scripts/
│   └── validate.js                    # JSON validation CLI tool
├── data/
│   ├── json/                          # Park JSON files (Convex seed data)
│   └── docx/                          # Park Word docs (human review)
└── docs/
    └── plans/                         # Progress plans per park
```

## The Trivia Firewall

The single most important rule: **no trivia question's answer can match any fact sheet field**. This is enforced at three levels:

1. **Writer skill** — self-check instructions before submission
2. **Reviewer skill** — explicit firewall validation step
3. **Hookify rule** — triggers a warning on every JSON file write
4. **Validation script** — `node scripts/validate.js` catches violations programmatically

## Convex Integration

The `schemas/` directory contains reference files for your ParkPal Convex project:

1. Copy `convex-schema.ts` into your Convex `schema.ts`
2. Copy `seed-attractions.ts` into your Convex `convex/` directory
3. After generating JSON: `npx convex run seedAttractions:seed --file data/json/magic_kingdom.json`

## Validation

```bash
node scripts/validate.js data/json/magic_kingdom.json
```

Checks schema compliance, trivia firewall, difficulty distribution, and answer letter balance.
