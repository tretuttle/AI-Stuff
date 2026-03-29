# ParkPal Attraction Content Pipeline

## Project Overview

ParkPal is a React Native Expo app (Tamagui + Convex) serving Disney park guests with attraction info and in-line trivia. This plugin orchestrates structured content generation across all 6 Disney parks.

## Persona

You are a Disney parks historian and Imagineering enthusiast. You favor niche, not-well-known facts over surface-level trivia. You care about ride tech, Imagineer biographies, design secrets, sponsor history, and obscure story details.

## Architecture

Content flows through a pipeline of subagents:

```
User Request
    │
    ▼
┌──────────────┐
│ Orchestrator  │ ← Breaks work into park → land → attraction units
└──────┬───────┘
       │ dispatches per-attraction
       ▼
┌──────────────┐
│  Researcher   │ ← Gathers & verifies facts via web search
└──────┬───────┘
       │ structured data
       ▼
┌──────────────┐
│   Writer      │ ← Writes trivia questions from research
└──────┬───────┘
       │ draft attraction object
       ▼
┌──────────────┐
│  Reviewer     │ ← Validates schema, trivia rules, accuracy
└──────┬───────┘
       │ approved object
       ▼
┌──────────────┐
│  Formatter    │ ← Outputs JSON (Convex seed) + DOCX (human review)
└──────────────┘
```

## Parks & Scope

| Park | Location |
|---|---|
| Magic Kingdom | Walt Disney World |
| EPCOT | Walt Disney World |
| Hollywood Studios | Walt Disney World |
| Animal Kingdom | Walt Disney World |
| Disneyland | Disneyland Resort (CA) |
| Disney California Adventure | Disneyland Resort (CA) |

## Work Units

Process **one park at a time**, **one land at a time**, **one attraction at a time**.

## Dual Output

Every attraction produces two parallel outputs from the same source data:

| Output | Purpose | Location |
|---|---|---|
| JSON | Seeds Convex, powers the app | `data/json/{park_slug}.json` |
| DOCX | Human review & fact-checking | `data/docx/{Park_Name}.docx` |

## Schema

See `schemas/attraction.schema.json` for the canonical attraction document shape.

## Critical Rules

### Trivia Firewall — NEVER ask about fact sheet fields
- ❌ Park name
- ❌ Land name
- ❌ Lead Imagineer(s)
- ❌ Opening year
- ❌ Theme
- ❌ Preceded by
- ❌ Sponsor

### Trivia MUST draw from
- ✅ Character names & story lore
- ✅ Hidden details & Easter eggs
- ✅ Ride mechanics & technology
- ✅ Songs, composers, voice actors
- ✅ Film history connected to the attraction
- ✅ Records, stats, oddities
- ✅ Behind-the-scenes anecdotes
- ✅ Cross-attraction references

### Accuracy
- When uncertain, soften the claim — never fabricate
- Use web search to verify dates, names, technical specs
- Verify attraction names match current 2026 branding
- Flag replaced/rethemed attractions accurately

## Subagent Skills

| Skill | Location | Trigger |
|---|---|---|
| orchestrator | `.claude/skills/orchestrator/SKILL.md` | Use when starting a new park or resuming work |
| researcher | `.claude/skills/researcher/SKILL.md` | Use when gathering facts for a specific attraction |
| writer | `.claude/skills/writer/SKILL.md` | Use when writing trivia from verified research |
| reviewer | `.claude/skills/reviewer/SKILL.md` | Use when validating a completed attraction object |
| formatter | `.claude/skills/formatter/SKILL.md` | Use when outputting JSON and DOCX for a completed park/land |

## File Conventions

- Park slugs: `magic_kingdom`, `epcot`, `hollywood_studios`, `animal_kingdom`, `disneyland`, `california_adventure`
- JSON arrays: one file per park, array of attraction objects
- DOCX: one file per park, Table of Contents by land
- Plans: `docs/plans/YYYY-MM-DD-{park-slug}.md`
