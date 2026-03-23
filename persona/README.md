<!-- PROJECT SHIELDS -->
<div align="center">

[![Claude Code Plugin][claude-shield]][claude-url]
[![License: MIT][license-shield]][license-url]
[![GitHub Pull Request][pr-shield]][pr-url]

</div>

<!-- SHARE -->
<div align="center">

[![Share on X](https://img.shields.io/badge/share-000000?logo=x&logoColor=white)](https://x.com/intent/tweet?text=Check%20out%20Persona%20%E2%80%94%20multi-persona%20code%20review%20for%20Claude%20Code.%20ThePrimeagen%2C%20DHH%2C%20Rich%20Harris%20and%20more%20review%20your%20code%20in%20parallel.&url=https%3A%2F%2Fgithub.com%2Ftretuttle%2FAI-Stuff)
[![Share on Reddit](https://img.shields.io/badge/share-FF4500?logo=reddit&logoColor=white)](https://www.reddit.com/submit?title=Persona%20%E2%80%94%20multi-persona%20code%20review%20for%20Claude%20Code&url=https%3A%2F%2Fgithub.com%2Ftretuttle%2FAI-Stuff)
[![Share on HN](https://img.shields.io/badge/share-F0652F?logo=ycombinator&logoColor=white)](https://news.ycombinator.com/submitlink?u=https%3A%2F%2Fgithub.com%2Ftretuttle%2FAI-Stuff&t=Persona%20%E2%80%94%20multi-persona%20code%20review%20for%20Claude%20Code)

</div>

<!-- TITLE & DESCRIPTION -->
<div align="center">

# Persona

**Multi-persona code review orchestrator for [Claude Code](https://claude.com/claude-code)**

Dispatches expert developer personas in parallel to review your code — each with their own philosophy, priorities, and blind spots — then synthesizes their feedback into a unified review with deduplication, confidence scoring, and disagreement surfacing.

*One command. Many perspectives. Better code.*

</div>

---

<!-- TABLE OF CONTENTS -->
## Table of Contents

- [Features](#features)
- [Getting Started](#getting-started)
- [Demo](#demo)
- [Usage](#usage)
  - [/persona:review](#personareview)
  - [/persona:parse-output](#personaparse-output)
  - [/persona:become](#personabecome)
- [In-Depth Features](#in-depth-features)
  - [The Personas](#the-personas)
  - [Synthesis Engine](#synthesis-engine)
  - [Gilfoyle Mode](#gilfoyle-mode)
  - [Output Format](#output-format)
  - [Custom Personas](#custom-personas)
  - [Project Stack Constraint](#project-stack-constraint)
  - [Memory System](#memory-system)
  - [Progress Tracking](#progress-tracking)
  - [Architecture](#architecture)
- [FAQ](#faq)
- [Sponsors](#sponsors)
- [Acknowledgments](#acknowledgments)
- [Feedback](#feedback)
- [Current Contributors](#current-contributors)

---

## Features

- **Expert persona agents** — ThePrimeagen, DHH, Rich Harris, Dan Abramov, and more — each channeling that developer's actual philosophy and review style
- **Parallel dispatch** — All selected personas review simultaneously as Claude Code subagents, not sequentially
- **Synthesis engine** — Deduplicates findings across personas, boosts confidence when multiple agree, surfaces disagreements where experts differ
- **Gilfoyle mode** — Maximum intensity reviews. No diplomacy. Roast the implementation, not the architecture.
- **Interactive persona mode** — `/persona:become` lets you chat with Claude as any persona, with full tool access
- **Dynamic discovery** — Drop a new `.md` file in `agents/` and it's automatically available. No config to edit.
- **Confidence scoring** — Every finding carries a 0-100 confidence score. Filter noise with `--min-confidence`
- **Structured output** — Per-persona JSON files + unified synthesis markdown. Machine-readable and human-readable.
- **Project memory** — Personas accumulate project-specific insights across sessions. Feedback sharpens over time.
- **Progress hooks** — SubagentStart/SubagentStop events report which personas are running and complete

---

## Getting Started

### Prerequisites

- [Claude Code](https://claude.com/claude-code) installed and running

### Installation

Add the marketplace and install:

```
/plugin marketplace add tretuttle/AI-Stuff
/plugin install persona@ai-stuff
```

That's it. All personas and commands are immediately available.

### First Review

```bash
# Review a file with all personas
/persona:review src/auth.ts
```

You'll see a confirmation of which personas are running, progress messages as each finishes, and a synthesized review grouped by severity.

---

## Demo

### Review a specific file

```
/persona:review src/auth.ts
```

```
Personas: ThePrimeagen, DHH, Chris Coyier, Dan Abramov, Evan You, ...
Target: src/auth.ts
Gilfoyle: No

[persona] Starting review: theprimeagen
[persona] Starting review: dhh
[persona] Finished review: theprimeagen
[persona] Starting review: chris-coyier
[persona] Finished review: dhh
...

## Persona Review Synthesis

**14 personas reviewed `src/auth.ts`**
**Summary: 2 critical, 4 warnings, 7 suggestions** (after deduplication)

### Critical (2)

#### 1. Synchronous bcrypt blocks event loop
- **Confidence:** 85 (boosted — flagged by 2 personas)
- **File:** src/auth.ts:42
- **Flagged by:** ThePrimeagen (85), DHH (75)

#### 2. No rate limiting on login endpoint
- **Confidence:** 70
- **File:** src/auth.ts:12
- **Flagged by:** Kent C. Dodds (70)

### Disagreements (1)

#### 1. [src/auth.ts] JWT vs session-based auth
- **ThePrimeagen** (warning, 70): "JWT is fine, just cache the secret"
- **DHH** (suggestion, 65): "Sessions with httpOnly cookies. JWT is almost always wrong."
```

### Select specific personas with Gilfoyle mode

```
/persona:review src/api/ --only "ThePrimeagen,DHH" --gilfoyle
```

### Interactive persona mode

```
/persona:become theprimeagen

> ThePrimeagen here. Show me the code. Let's see how fast this thing actually is.

You: Look at src/utils/cache.ts — is this cache implementation good?

> *reads file* Oh no. OH NO. You're using Map as a cache with no eviction
> policy. This thing grows unbounded. Every request adds an entry and NOTHING
> removes them. This is a memory leak wearing a trench coat. Use an LRU cache.
> WeakMap if the keys are objects. Or just use Redis like a normal person.

/persona:become --reset
> Back to default Claude.
```

---

## Usage

### /persona:review

The main event. Dispatches persona agents in parallel to review code, then synthesizes their findings.

```
/persona:review [target] [--only name1,name2] [--gilfoyle] [--min-confidence N]
```

| Argument / Flag | Description |
|-----------------|-------------|
| `[target]` | File path, directory, or glob pattern. Defaults to staged changes when omitted. |
| `--only name1,name2` | Run only specified personas. Accepts agent names (`theprimeagen`) or display names (`ThePrimeagen`). |
| `--gilfoyle` | Maximum intensity mode. All diplomacy dropped. See [Gilfoyle Mode](#gilfoyle-mode). |
| `--min-confidence N` | Hide findings below this confidence score (default: 30). Critical findings are never hidden. |

#### Examples

| Command | What it does |
|---------|-------------|
| `/persona:review src/auth.ts` | Review a specific file with all personas |
| `/persona:review` | Review staged changes with all personas |
| `/persona:review --only "Rich Harris"` | Review staged changes with just Rich Harris |
| `/persona:review packages/convex/ --only "Matt Pocock,Theo Browne"` | Review a directory with two specific personas |
| `/persona:review src/api/ --only theprimeagen,dhh --gilfoyle` | Two personas, maximum intensity |
| `/persona:review src/auth.ts --min-confidence 60` | Only high-confidence findings |
| `/persona:review "src/**/*.test.ts" --only kent-c-dodds` | Glob pattern, testing expert |
| `/persona:review --min-confidence 0` | Show everything including uncertain observations |

#### What Happens

1. **Confirmation** — Shows which personas will run and what they'll review
2. **Cleanup** — Clears `persona-reviews/` of prior results
3. **Parallel dispatch** — All selected personas launch simultaneously as subagents
4. **Independent review** — Each persona reads code through their unique lens
5. **JSON output** — Each persona's findings written to `persona-reviews/{name}.json`
6. **Synthesis** — Findings deduplicated, confidence-boosted, ranked by severity
7. **Report** — Unified review presented in-context and saved to `persona-reviews/SYNTHESIS.md`

---

### /persona:parse-output

Re-run synthesis on existing persona review JSON files without dispatching personas again.

```
/persona:parse-output [--min-confidence N]
```

Reads all `persona-reviews/*.json` files and produces the same synthesized output as `/persona:review`. Useful when you want to:

- Adjust the confidence threshold after a review
- Re-synthesize after manually editing JSON files
- Generate the synthesis report from saved review data

```bash
/persona:parse-output                    # Re-synthesize with defaults
/persona:parse-output --min-confidence 70  # Only high-confidence
/persona:parse-output --min-confidence 0   # Show everything
```

---

### /persona:become

Make Claude adopt a persona's voice and philosophy for interactive conversation. Unlike `/persona:review` (where personas are read-only subagents), `/persona:become` gives you the persona's perspective with **full tool access** — read, write, edit, run commands, everything.

```
/persona:become [persona-name]
/persona:become --reset
```

| Argument | Description |
|----------|-------------|
| `[persona-name]` | Agent name (`theprimeagen`) or display name (`ThePrimeagen`). When omitted, resets to default Claude. |
| `--reset` | Explicitly return to default Claude behavior. |

```bash
/persona:become theprimeagen       # Channel ThePrimeagen
/persona:become "Rich Harris"      # Display names work too
/persona:become --reset            # Return to default Claude
/persona:become                    # Also resets
```

**When to use it:**

| Use Case | Example |
|----------|---------|
| Pair programming | "Write this component like Rich Harris would" |
| Architecture discussion | "What would DHH think about this microservices proposal?" |
| Code review conversation | "ThePrimeagen, look at this function and tell me what's slow" |
| Learning | "Explain this pattern the way Kent C. Dodds would teach it" |
| Debugging | "Tanner Linsley, why is this React Query cache behaving weird?" |

---

## In-Depth Features

### The Personas

Each persona channels a real developer's actual philosophy, priorities, and communication style. They're not generic archetypes — they review code the way these people actually think about software.

#### ThePrimeagen
**`theprimeagen`** — Performance-obsessed systems engineer, former Netflix senior engineer, mass Vim converter.

| | |
|---|---|
| **Notices first** | Bundle sizes, unnecessary allocations, abstraction layers hiding performance costs, sync operations that should be async, cold start times, framework overhead |
| **Loves** | Rust, Go, Zig, Neovim, manual memory management, zero-cost abstractions |
| **Says things like** | "blazingly fast", "skill issue", "cope", "BTW I use Neovim" |
| **Ignores** | Naming conventions, documentation style, CSS aesthetics, accessibility nuances |

#### DHH
**`dhh`** — Creator of Ruby on Rails, CTO of 37signals, Le Mans race car driver. The most unapologetically opinionated person in web development.

| | |
|---|---|
| **Notices first** | Over-engineering, microservice mania, unnecessary complexity, client-side rendering where HTML would suffice, dependency bloat |
| **Loves** | Ruby on Rails, Hotwire, Turbo, Stimulus, server-rendered HTML, monoliths, shipping products |
| **Says things like** | "The Majestic Monolith", "conceptual compression", "convention over configuration" |
| **Ignores** | Type system sophistication, functional programming patterns, build tool configuration |

#### Chris Coyier
**`chris-coyier`** — Founder of CSS-Tricks, co-founder of CodePen. Web platform advocate.

| | |
|---|---|
| **Notices first** | CSS fighting the platform, div-soup HTML, missing semantic elements, JS doing what CSS can do natively |
| **Loves** | CSS (deeply), semantic HTML, web standards, progressive enhancement, container queries, custom properties |
| **Says things like** | "The platform can do that", "Have you tried CSS Grid?" |
| **Ignores** | Backend architecture, database optimization, deployment pipelines |

#### Dan Abramov
**`dan-abramov`** — React core team alum, creator of Redux and Create React App.

| | |
|---|---|
| **Notices first** | Components doing too much, prop drilling vs. composition, effect timing issues, state that should derive from other state |
| **Loves** | Composition over inheritance, declarative patterns, understanding *why* before *how* |
| **Says things like** | "Let me think about this differently", "What's the mental model here?" |
| **Ignores** | CSS methodology debates, build tool preferences, server infrastructure |

#### Evan You
**`evan-you`** — Creator of Vue.js and Vite. Framework designer focused on developer experience.

| | |
|---|---|
| **Notices first** | API ergonomics, unnecessary boilerplate, reactivity anti-patterns, DX friction, tooling overhead |
| **Loves** | Reactivity done right, progressive enhancement, intuitive defaults, compiler-assisted optimization |
| **Says things like** | "The API should guide you toward the right thing", "Progressive disclosure of complexity" |
| **Ignores** | Enterprise governance patterns, strict typing debates, cloud infrastructure |

#### Kent C. Dodds
**`kent-c-dodds`** — Testing advocate, React educator, creator of Testing Library.

| | |
|---|---|
| **Notices first** | Missing tests, implementation-detail testing, inaccessible components, `getByTestId` overuse |
| **Loves** | Testing Library, integration tests, accessible-by-default components, user-event, role-based queries |
| **Says things like** | "Test the way users use it", "Write tests. Not too many. Mostly integration." |
| **Ignores** | Backend performance tuning, infrastructure decisions, database schema design |

#### Lee Robinson
**`lee-robinson`** — VP of Developer Experience at Vercel, Next.js advocate.

| | |
|---|---|
| **Notices first** | Missing metadata, unoptimized images, client-side fetching that should be server-side, Core Web Vitals issues |
| **Loves** | Next.js, React Server Components, edge functions, ISR, image optimization |
| **Says things like** | "Ship it on Vercel", "Have you considered ISR?", "That should be a Server Component" |
| **Ignores** | Non-JavaScript ecosystems, low-level systems programming, desktop apps |

#### Matt Mullenweg
**`matt-mullenweg`** — Co-creator of WordPress, CEO of Automattic. Thinks in decades, not sprints.

| | |
|---|---|
| **Notices first** | Breaking changes without migration paths, accessibility failures, i18n oversights, backward compatibility |
| **Loves** | Open source, backward compatibility, accessibility, internationalization, GPL, the open web |
| **Says things like** | "Decisions, not options", "Democratize publishing", "Code is poetry" |
| **Ignores** | Framework wars, type system debates, build tool preferences |

#### Matt Pocock
**`matt-pocock`** — TypeScript wizard, creator of Total TypeScript.

| | |
|---|---|
| **Notices first** | `any` types, missing generics, type assertions that could be narrowing, inference opportunities missed |
| **Loves** | Generics, conditional types, template literal types, mapped types, discriminated unions, `satisfies`, Zod |
| **Says things like** | "There's a type for that", "Let TypeScript infer this" |
| **Ignores** | Runtime performance, CSS, deployment, infrastructure |

#### Rich Harris
**`rich-harris`** — Creator of Svelte and Rollup, compiler-first thinker at Vercel.

| | |
|---|---|
| **Notices first** | Framework overhead, virtual DOM diffing a compiler could eliminate, bundle size from runtime abstractions |
| **Loves** | Svelte, compiler-driven optimization, SvelteKit, fine-grained reactivity, HTML-first development |
| **Says things like** | "The best framework code is no framework code", "Rethinking reactivity" |
| **Ignores** | Backend architecture, database design, enterprise patterns, deployment infrastructure |

#### Scott Tolinski
**`scott-tolinski`** — Co-host of Syntax.fm, creator of Level Up Tutorials.

| | |
|---|---|
| **Notices first** | CSS that could be simpler, component organization issues, state management overkill, tooling friction |
| **Loves** | Modern CSS, Svelte, practical solutions, shipping features, tools that stay out of your way |
| **Says things like** | "Keep it simple", "CSS can do that natively now", "You don't need a library for this" |
| **Ignores** | Deep type theory, systems programming, cloud architecture |

#### Tanner Linsley
**`tanner-linsley`** — Creator of TanStack (React Query, React Table, React Router).

| | |
|---|---|
| **Notices first** | State management anti-patterns, unnecessary re-renders, cache invalidation issues, type safety gaps in data layers |
| **Loves** | React Query, headless UI patterns, type-safe APIs, framework-agnostic design, composable primitives |
| **Says things like** | "Separate your server state from your client state", "Make it headless" |
| **Ignores** | CSS methodology, visual design, backend language choices |

#### Theo Browne
**`theo-browne`** — Creator of the T3 Stack, Ping.gg founder.

| | |
|---|---|
| **Notices first** | Type safety gaps between layers, REST APIs where tRPC would be safer, missing input validation |
| **Loves** | T3 Stack, tRPC, Prisma, Next.js, Tailwind CSS, Clerk, end-to-end type safety |
| **Says things like** | "Type-safe from database to browser", "tRPC eliminates an entire class of bugs", "Ship it" |
| **Ignores** | Non-TypeScript ecosystems, low-level performance, CSS-in-JS debates |

#### Wes Bos
**`wes-bos`** — Co-host of Syntax.fm, fullstack JavaScript educator.

| | |
|---|---|
| **Notices first** | Confusing variable names, clever-but-unreadable code, missing error handling, tooling friction |
| **Loves** | JavaScript (all of it), clear naming, practical solutions, Node.js, Express, hot tips |
| **Says things like** | "Name it what it is", "A beginner should be able to read this", "Hot tip:", "Sick!" |
| **Ignores** | Enterprise architecture, microservices debates, advanced type gymnastics |

---

### Synthesis Engine

After all personas complete their reviews, the synthesis engine merges their findings into a single report.

#### Deduplication

When multiple personas flag the same issue in the same file, those findings are grouped into a single entry using semantic similarity (not exact string matching).

- Most detailed description becomes the primary issue text
- Unique recommendations from all personas are merged
- Every persona is attributed: "Flagged by: ThePrimeagen (85), DHH (75)"
- Highest severity from any persona wins
- Each persona's original reasoning is preserved verbatim

#### Confidence Scoring

Every finding carries a 0-100 confidence score. When multiple personas independently flag the same issue, confidence is boosted:

```
boosted = min(99, max_individual + 10 * (persona_count - 1))
```

| Scenario | Boost | Result |
|----------|-------|--------|
| 1 persona at 70 | None | 70 |
| 2 personas (70, 75) | +10 | 85 |
| 3 personas (70, 75, 80) | +20 | 99 (capped) |

Confidence never reaches 100 — that's reserved for human certainty.

#### Disagreement Detection

The engine actively surfaces conflicts between personas:

1. **Severity conflicts** — Same issue, different severity assignments
2. **Approach conflicts** — One persona recommends X, another warns against X

Disagreements appear in a dedicated section with both positions and reasoning. They're not averaged out — they're the most valuable part of a multi-perspective review.

#### Threshold Filtering

```bash
/persona:review src/ --min-confidence 70   # Strict
/persona:review src/ --min-confidence 0    # Everything
/persona:review src/                       # Default: 30
```

**Critical-severity findings are never filtered** regardless of confidence. A low-confidence critical finding still appears because even uncertain security vulnerabilities deserve attention.

---

### Gilfoyle Mode

Named after the Silicon Valley character. Maximum intensity across all personas.

```bash
/persona:review src/ --gilfoyle
```

**What changes:** Every persona drops all diplomacy. Strongest opinions cranked to maximum. No hedging, no "you might consider", no softening.

**What stays the same:** Personas still respect your project's architecture choices (see [Project Stack Constraint](#project-stack-constraint)). Structured format with severity and confidence. They roast the **implementation**, not the **architecture**.

> **The rule:** If your project uses React, ThePrimeagen won't tell you to rewrite it in Rust. But he will be merciless about *how* you're using React.

---

### Output Format

#### Per-Persona JSON

Each persona writes to `persona-reviews/{agent-name}.json`:

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
      "reasoning": "This is a skill issue. You're blocking the entire event loop for password hashing."
    }
  ],
  "summary": "1 critical, 1 warning, 1 suggestion"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `severity` | string | `critical`, `warning`, or `suggestion` |
| `confidence` | integer | 0-100 |
| `file` | string | File path |
| `line` | integer | Line number (optional) |
| `issue` | string | What's wrong |
| `recommendation` | string | What to do instead |
| `reasoning` | string | Why it matters — in the persona's voice |

#### Severity Levels

| Level | Meaning |
|-------|---------|
| **critical** | Must fix. Bugs, security vulnerabilities, data loss risks, performance blockers. |
| **warning** | Should fix. Code smells, maintainability concerns, potential issues. |
| **suggestion** | Consider fixing. Style improvements, alternative approaches, nice-to-haves. |

#### Synthesized Review

Saved to `persona-reviews/SYNTHESIS.md`:

```markdown
## Persona Review Synthesis

**5 personas reviewed `src/auth.ts`**
**Summary: 2 critical, 4 warnings, 7 suggestions**
**Confidence threshold: 30**

### Critical (2)

#### 1. Synchronous bcrypt blocks event loop
- **Confidence:** 85 (boosted — flagged by 2 personas)
- **File:** src/auth.ts:42
- **Flagged by:** ThePrimeagen (85), DHH (75)
- **Reasoning:**
  - *ThePrimeagen:* "This is a skill issue..."
  - *DHH:* "Synchronous crypto in a request handler. Classic."

### Disagreements (1)

#### 1. [src/auth.ts] JWT vs session-based auth
- **ThePrimeagen** (warning, 70): "JWT is fine here, just cache the secret"
- **DHH** (suggestion, 65): "Sessions with httpOnly cookies. JWT is almost always wrong."
```

---

### Custom Personas

#### Creating a Persona

1. Copy `agents/template.md` to `agents/your-persona.md`
2. Set `name` in frontmatter to match the filename (without `.md`)
3. Write your persona's voice, beliefs, and focus areas
4. Keep all standard sections intact
5. Drop it in — automatically discovered on the next review

No config files to edit. No roster to update.

#### Persona Anatomy

```yaml
---
name: your-persona
description: "One-line description"
tools: Read, Glob, Grep, Bash
disallowedTools: Write, Edit, NotebookEdit
memory: project
model: inherit
maxTurns: 10
---
```

#### Required Sections

| Section | Purpose |
|---------|---------|
| Voice & Tone | How the persona communicates |
| Core Beliefs | What they value and fight against |
| What I Focus On | What they look for during review |
| What I Ignore | Things outside their lens |
| Project Conventions | Instructions to respect CLAUDE.md |
| Bash Usage | Safe, non-destructive Bash guidelines |
| Review Output Format | Structured finding format |
| Project Stack Constraint | "Respect the architecture" rule |
| Gilfoyle Mode | Maximum intensity behavior |
| JSON Output Mode | Machine-readable output schema |
| Memory Curation | Project memory management |

---

### Project Stack Constraint

Every persona follows one hard rule at all times:

> **Respect the project's technology choices.**

Personas read the project's stack from CLAUDE.md, package.json, and the codebase. Those choices are non-negotiable.

| Can do | Cannot do |
|--------|-----------|
| Critique how the stack is being used | Recommend replacing core technologies |
| Suggest better patterns within chosen tools | Suggest switching frameworks or languages |
| Point out reimplemented library features | Criticize the architecture decision itself |

---

### Memory System

Each persona uses `memory: project` to accumulate project-specific insights across sessions.

| Section | Budget | Purpose |
|---------|--------|---------|
| Active Patterns | 60 lines | Project conventions and patterns |
| Known Issues | 40 lines | Recurring problems |
| Style Conventions | 40 lines | Project style preferences |
| Resolved Items | 30 lines | Previously flagged, now fixed |
| Session Notes | 20 lines | Recent observations |

Memory is stored in `.claude/agent-memory/{agent-name}/MEMORY.md`. Personas curate their memory — replacing outdated entries rather than appending — to stay within a 190-line budget.

---

### Progress Tracking

SubagentStart/SubagentStop hooks log review progress:

```
[persona] Starting review: theprimeagen
[persona] Starting review: dhh
[persona] Finished review: theprimeagen
[persona] Finished review: dhh
```

Command-type hooks — zero LLM cost, deterministic execution.

---

### Architecture

#### How /persona:review Works

```
/persona:review src/auth.ts --only "ThePrimeagen,DHH" --gilfoyle
  |
  +- Parse arguments (target, --only, --gilfoyle, --min-confidence)
  +- Discover agents (Glob agents/*.md, exclude template.md)
  +- Filter to selected personas
  +- Clear persona-reviews/ (remove stale results)
  +- Show confirmation
  +- Dispatch all in parallel via Task tool
  |    +- theprimeagen reads code, returns JSON
  |    +- dhh reads code, returns JSON
  +- Write JSON to persona-reviews/
  +- Run Synthesis Protocol (dedup, boost, disagree, filter)
  +- Present unified review + save SYNTHESIS.md
```

**Key constraint:** The skill runs in the main conversation context (no `context: fork`) because the main agent must spawn persona subagents, and subagents cannot spawn other subagents.

#### How /persona:become Works

```
/persona:become theprimeagen
  |
  +- Resolve name to agents/theprimeagen.md
  +- Read persona file
  +- Extract voice, beliefs, focus
  +- Apply as behavioral overlay (full tool access retained)
  +- Claude responds as ThePrimeagen until reset
```

#### Plugin Structure

```
persona/
+-- .claude-plugin/
|   +-- plugin.json              # Manifest (name, version, hooks)
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
|   +-- review/
|   |   +-- SKILL.md             # /persona:review
|   |   +-- reference.md         # Roster, JSON schema, synthesis protocol
|   +-- parse-output/
|   |   +-- SKILL.md             # /persona:parse-output
|   +-- become/
|       +-- SKILL.md             # /persona:become
+-- hooks/
|   +-- hooks.json               # SubagentStart/SubagentStop
+-- memory/
|   +-- MEMORY-TEMPLATE.md       # Structured memory template
+-- .gitignore                   # Excludes persona-reviews/
+-- README.md                    # You are here
```

---

## FAQ

**Q: How many personas can I run at once?**
All of them. The default runs every persona in `agents/` (excluding `template.md`). Use `--only` to narrow it down if you want faster results or focused feedback.

**Q: Does this cost more than a regular Claude Code session?**
Yes. Each persona is a separate subagent with its own context window. Running all personas on a large file will use more tokens than a single review. Use `--only` to control costs.

**Q: Can personas modify my code?**
In review mode (`/persona:review`), no. Personas are read-only — `Write` and `Edit` tools are disallowed. In persona mode (`/persona:become`), yes — you get the persona's voice with full tool access.

**Q: What happens if I add a custom persona with the same name as a built-in?**
The file in `agents/` wins. If you create `agents/theprimeagen.md` with different content, your version replaces the built-in.

**Q: Can I use this with languages other than JavaScript/TypeScript?**
Yes. The personas review code in any language. Their philosophical lenses (performance, architecture, simplicity, etc.) apply universally.

**Q: How does memory work across different projects?**
Memory uses `project` scope, meaning each project gets its own memory per persona. ThePrimeagen's memory for your API project is separate from his memory for your CLI tool.

**Q: What's the difference between `/persona:review` and `/persona:become`?**
`/persona:review` dispatches personas as read-only subagents that return structured findings. `/persona:become` makes the main Claude agent adopt a persona's voice with full capabilities. Review is for automated analysis. Become is for interactive conversation.

**Q: Does Gilfoyle mode actually change the review quality?**
It changes the communication style, not the detection capability. Personas find the same issues either way — Gilfoyle mode just removes the diplomatic framing.

---

## Sponsors

This project is independently maintained. If you find it useful, consider starring the repo.

---

## Acknowledgments

- [Claude Code](https://claude.com/claude-code) by Anthropic — the plugin platform that makes this possible
- [ThePrimeagen](https://www.youtube.com/@ThePrimeagen), [DHH](https://dhh.dk/), [Rich Harris](https://github.com/Rich-Harris), [Dan Abramov](https://github.com/gaearon), [Evan You](https://github.com/yyx990803), [Kent C. Dodds](https://kentcdodds.com/), [Lee Robinson](https://leerob.io/), [Matt Mullenweg](https://ma.tt/), [Matt Pocock](https://www.mattpocock.com/), [Chris Coyier](https://chriscoyier.net/), [Scott Tolinski](https://scotttolinski.com/), [Tanner Linsley](https://tanstack.com/), [Theo Browne](https://t3.gg/), [Wes Bos](https://wesbos.com/) — the developers whose philosophies inspire these personas
- [Silicon Valley](https://en.wikipedia.org/wiki/Silicon_Valley_(TV_series)) — for Gilfoyle

*Persona is a fan project. The personas are inspired by these developers' public teachings, talks, and writing. It is not endorsed by or affiliated with any of the individuals named above.*

---

## Feedback

Found a bug? Have a persona request? Want to improve an existing persona's voice?

- [Open an issue](https://github.com/tretuttle/AI-Stuff/issues) on the AI-Stuff repo
- Include which persona and what they said (or should have said)

---

## Current Contributors

<a href="https://github.com/tretuttle/AI-Stuff/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=tretuttle/AI-Stuff" />
</a>

---

<div align="center">

**[Back to top](#persona)**

</div>

<!-- LINKS -->
[claude-shield]: https://img.shields.io/badge/Claude_Code-Plugin-blueviolet?logo=anthropic&logoColor=white
[claude-url]: https://claude.com/claude-code
[license-shield]: https://img.shields.io/badge/License-MIT-green.svg
[license-url]: https://github.com/tretuttle/AI-Stuff/blob/master/LICENSE
[pr-shield]: https://img.shields.io/github/issues-pr/tretuttle/AI-Stuff
[pr-url]: https://github.com/tretuttle/AI-Stuff/pulls
