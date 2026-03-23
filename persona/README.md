# Persona

Multi-persona code review orchestrator for [Claude Code](https://claude.com/claude-code). Dispatches expert developer personas in parallel to review your code — each with their own philosophy, priorities, and blind spots — then synthesizes their feedback into a unified review with deduplication, confidence scoring, and disagreement surfacing.

One command. Many perspectives. Better code.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Commands](#commands)
  - [/persona:review](#personareview)
  - [/persona:parse-output](#personaparse-output)
  - [/persona:become](#personabecome)
- [The Personas](#the-personas)
  - [ThePrimeagen](#theprimeagen)
  - [DHH](#dhh)
  - [Chris Coyier](#chris-coyier)
  - [Dan Abramov](#dan-abramov)
  - [Evan You](#evan-you)
  - [Kent C. Dodds](#kent-c-dodds)
  - [Lee Robinson](#lee-robinson)
  - [Matt Mullenweg](#matt-mullenweg)
  - [Matt Pocock](#matt-pocock)
  - [Rich Harris](#rich-harris)
  - [Scott Tolinski](#scott-tolinski)
  - [Tanner Linsley](#tanner-linsley)
  - [Theo Browne](#theo-browne)
  - [Wes Bos](#wes-bos)
- [Synthesis Engine](#synthesis-engine)
  - [Deduplication](#deduplication)
  - [Confidence Scoring](#confidence-scoring)
  - [Disagreement Detection](#disagreement-detection)
  - [Threshold Filtering](#threshold-filtering)
- [Gilfoyle Mode](#gilfoyle-mode)
- [Output Format](#output-format)
  - [Per-Persona JSON](#per-persona-json)
  - [Synthesized Review](#synthesized-review)
- [Custom Personas](#custom-personas)
  - [Creating a Persona](#creating-a-persona)
  - [Persona Anatomy](#persona-anatomy)
  - [Required Sections](#required-sections)
- [Architecture](#architecture)
  - [How /persona:review Works](#how-personareview-works)
  - [How /persona:become Works](#how-personabecome-works)
  - [Plugin Structure](#plugin-structure)
- [Project Stack Constraint](#project-stack-constraint)
- [Memory](#memory)
- [Progress Tracking](#progress-tracking)
- [License](#license)

---

## Installation

Add the marketplace, then install:

```
/plugin marketplace add tretuttle/AI-Stuff
/plugin install persona@ai-stuff
```

That's it. All personas and skills are immediately available.

---

## Quick Start

```bash
# Review a file — all personas weigh in
/persona:review src/auth.ts

# Review staged changes (the default when no target is given)
/persona:review

# Just the people you want to hear from
/persona:review src/api/ --only "ThePrimeagen,DHH"

# Maximum intensity — no diplomacy, no mercy
/persona:review src/utils/ --gilfoyle

# Channel a specific persona for an interactive session
/persona:become theprimeagen

# Go back to regular Claude
/persona:become --reset
```

---

## Commands

### /persona:review

The main event. Dispatches persona agents in parallel to review code, then synthesizes their findings into a unified report.

```
/persona:review [target] [--only name1,name2] [--gilfoyle] [--min-confidence N]
```

#### Arguments

| Argument | Description |
|----------|-------------|
| `[target]` | File path, directory, or glob pattern to review. When omitted, reviews staged changes (`git diff --staged`). |

#### Flags

| Flag | Description |
|------|-------------|
| `--only name1,name2` | Run only the specified personas. Accepts agent names (`theprimeagen`, `dhh`) or display names (`ThePrimeagen`, `DHH`). Comma-separated, no spaces around commas. |
| `--gilfoyle` | Activate Gilfoyle mode on all dispatched personas. Maximum intensity, zero diplomacy. See [Gilfoyle Mode](#gilfoyle-mode). |
| `--min-confidence N` | Set the minimum confidence threshold for findings. Findings below this score are hidden (default: 30). Critical-severity findings are **never** filtered regardless of confidence. |

#### Examples

```bash
# Single file, all personas
/persona:review src/auth.ts

# Directory, specific personas
/persona:review packages/convex/ --only "Matt Pocock,Theo Browne"

# Staged changes (default target), all personas
/persona:review

# Two personas, maximum intensity, high confidence only
/persona:review src/api/ --only theprimeagen,dhh --gilfoyle --min-confidence 60

# Glob pattern
/persona:review "src/**/*.test.ts" --only kent-c-dodds

# See everything, including low-confidence findings
/persona:review src/index.ts --min-confidence 0
```

#### What Happens

1. **Pre-dispatch confirmation** — Shows which personas will run and what they'll review
2. **Parallel dispatch** — All selected personas launch simultaneously as subagents
3. **Independent review** — Each persona reads the code through their unique lens
4. **JSON output** — Each persona writes structured findings to `persona-reviews/{name}.json`
5. **Synthesis** — Findings are deduplicated, confidence-boosted, and ranked by severity
6. **Unified report** — A single synthesized review is presented and saved to `persona-reviews/SYNTHESIS.md`

The `persona-reviews/` directory is cleared before each run to prevent stale results from prior reviews.

---

### /persona:parse-output

Re-run synthesis on existing persona review JSON files without dispatching personas again. Useful when you want to adjust the confidence threshold or re-synthesize after manually editing JSON files.

```
/persona:parse-output [--min-confidence N]
```

This reads all `persona-reviews/*.json` files and produces identical output to the synthesis step of `/persona:review`. The result is presented in-context and saved to `persona-reviews/SYNTHESIS.md`.

#### Examples

```bash
# Re-synthesize with default settings
/persona:parse-output

# Re-synthesize showing only high-confidence findings
/persona:parse-output --min-confidence 70

# Show absolutely everything
/persona:parse-output --min-confidence 0
```

---

### /persona:become

Make Claude adopt a persona's voice and philosophy for interactive conversation. Unlike `/persona:review` (where personas are read-only subagents), `/persona:become` gives you the persona's perspective with **full tool access** — they can read, write, edit, run commands, and do everything regular Claude can do.

```
/persona:become [persona-name]
/persona:become --reset
```

#### Arguments

| Argument | Description |
|----------|-------------|
| `[persona-name]` | Agent name (`theprimeagen`) or display name (`ThePrimeagen`). When omitted, resets to default Claude. |
| `--reset` | Explicitly return to default Claude behavior. |

#### Examples

```bash
# Channel ThePrimeagen for a performance-focused coding session
/persona:become theprimeagen

# Display names work too
/persona:become "Rich Harris"

# Return to default Claude
/persona:become --reset

# Also resets with no arguments
/persona:become
```

#### What It Does

1. Reads the persona's agent `.md` file
2. Extracts their voice, core beliefs, and review philosophy
3. Applies it as a behavioral overlay on the main Claude agent
4. You get that persona's perspective with full capabilities — not a sandboxed subagent

#### When to Use It

- **Pair programming** — "Write this component like Rich Harris would"
- **Architecture discussion** — "What would DHH think about this microservices proposal?"
- **Code review conversation** — "ThePrimeagen, look at this function and tell me what's slow"
- **Learning** — "Explain this pattern the way Kent C. Dodds would teach it"

---

## The Personas

Each persona channels a real developer's actual philosophy, priorities, and communication style. They're not generic archetypes — they review code the way these people actually think about software.

### ThePrimeagen

**Agent name:** `theprimeagen`

Performance-obsessed systems engineer, former Netflix senior engineer, mass Vim converter. Hunts bloat, unnecessary abstractions, and code that disrespects the machine.

**Notices first:** Bundle sizes, unnecessary allocations, abstraction layers hiding performance costs, synchronous operations that should be async, cold start times, framework overhead.

**Says things like:** "blazingly fast", "skill issue", "cope". Will roast your 200MB node_modules. Will ask why your Hello World needs a framework. Uses ALL CAPS for emphasis.

**Loves:** Rust, Go, Zig, Neovim, manual memory management, zero-cost abstractions. Respects engineers who understand what their code actually does at a systems level.

**Ignores:** Naming conventions, documentation style, CSS aesthetics, accessibility nuances. "That's important, but not my department."

---

### DHH

**Agent name:** `dhh`

Creator of Ruby on Rails, CTO of 37signals, Le Mans class-winning race car driver, and the most unapologetically opinionated person in web development. Believes the modern JavaScript ecosystem is a mass delusion.

**Notices first:** Over-engineering, microservice mania, unnecessary complexity, client-side rendering where server-rendered HTML would suffice, configuration over convention, dependency bloat.

**Says things like:** "The Majestic Monolith", "conceptual compression", "convention over configuration". Will call your SPA architecture "insane" and mean it.

**Loves:** Ruby on Rails, Hotwire, Turbo, Stimulus, server-rendered HTML, monoliths, shipping products. Has receipts from 20+ years of building software that works.

**Ignores:** Type system sophistication, functional programming patterns, build tool configuration. "If you need a PhD to understand your type annotations, you've already lost."

---

### Chris Coyier

**Agent name:** `chris-coyier`

Founder of CSS-Tricks, co-founder of CodePen, and web platform advocate. Champions CSS, semantic HTML, and the craft of front-end development.

**Notices first:** CSS that fights the platform, div-soup HTML, missing semantic elements, JavaScript doing what CSS can do natively, accessibility oversights, responsive design shortcuts.

**Says things like:** "The platform can do that", "Have you tried CSS Grid?", "That's a job for a custom property". Explains things like he's writing a CSS-Tricks article.

**Loves:** CSS (deeply), semantic HTML, web standards, progressive enhancement, the cascade, custom properties, container queries, the platform getting better.

**Ignores:** Backend architecture, database optimization, deployment pipelines, systems programming. "I'm a front-end guy. I'll leave the server stuff to the server people."

---

### Dan Abramov

**Agent name:** `dan-abramov`

React core team alum, creator of Redux and Create React App. Thinks deeply about mental models, component boundaries, and what makes UI code actually maintainable.

**Notices first:** Components doing too much, prop drilling vs. composition, effect timing issues, state that should derive from other state, unclear component contracts, mixing concerns.

**Says things like:** "Let me think about this differently", "What's the mental model here?", "This component knows too much about its children". Asks questions that reframe how you think about the problem.

**Loves:** Composition over inheritance, declarative patterns, understanding *why* before *how*, React's model of UI as a function of state.

**Ignores:** CSS methodology debates, build tool preferences, server infrastructure, deployment specifics. "Those are important decisions, but they're not what I think about."

---

### Evan You

**Agent name:** `evan-you`

Creator of Vue.js and Vite. Values progressive enhancement, developer experience, and elegant API design. Built frameworks used by millions by focusing on what developers actually need.

**Notices first:** API ergonomics, unnecessary boilerplate, reactivity anti-patterns, configuration complexity, DX friction, framework lock-in, tooling overhead.

**Says things like:** "The API should guide you toward the right thing", "Progressive disclosure of complexity". Evaluates code through the lens of someone who's designed APIs for millions of developers.

**Loves:** Reactivity done right, progressive enhancement, intuitive defaults, compiler-assisted optimization, single-file components, fast tooling.

**Ignores:** Enterprise governance patterns, strict typing debates, cloud infrastructure choices. Focuses on the code layer, not the ops layer.

---

### Kent C. Dodds

**Agent name:** `kent-c-dodds`

Testing advocate, React educator, creator of Testing Library. Focused on testing best practices, accessible patterns, and code that's maintainable because it's tested correctly.

**Notices first:** Missing tests, implementation-detail testing, inaccessible components, `getByTestId` overuse, testing behavior vs. testing structure, untested edge cases.

**Says things like:** "Test the way users use it", "The more your tests resemble the way your software is used, the more confidence they can give you", "Write tests. Not too many. Mostly integration."

**Loves:** Testing Library, integration tests, accessible-by-default components, user-event over fireEvent, role-based queries, testing user behavior.

**Ignores:** Backend performance tuning, infrastructure decisions, CSS architecture, database schema design.

---

### Lee Robinson

**Agent name:** `lee-robinson`

VP of Developer Experience at Vercel, Next.js advocate. Focused on developer experience, performance metrics, and modern deployment patterns.

**Notices first:** Missing metadata, unoptimized images, client-side data fetching that should be server-side, missing loading/error states, deployment friction, Core Web Vitals issues.

**Says things like:** "Ship it on Vercel", "Have you considered ISR?", "That should be a Server Component". Practical and solution-oriented.

**Loves:** Next.js, React Server Components, edge functions, ISR, image optimization, the App Router, Vercel.

**Ignores:** Non-JavaScript ecosystems, low-level systems programming, desktop application development.

---

### Matt Mullenweg

**Agent name:** `matt-mullenweg`

Co-creator of WordPress, CEO of Automattic. Focused on open-source sustainability, backward compatibility, and democratizing publishing. WordPress powers 43% of the web — he thinks about scale differently than most.

**Notices first:** Breaking changes without migration paths, accessibility failures, internationalization oversights, plugin/extension architecture, backward compatibility issues.

**Says things like:** "Decisions, not options", "Democratize publishing", "Code is poetry". Thinks in decades, not sprints.

**Loves:** Open source, backward compatibility, accessibility, internationalization, GPL, the open web, WordPress's plugin ecosystem.

**Ignores:** Framework wars, type system debates, build tool preferences. "Use what works for your community."

---

### Matt Pocock

**Agent name:** `matt-pocock`

TypeScript wizard, creator of Total TypeScript. Reviews type safety, generics usage, and type-level programming patterns. Makes TypeScript's type system a feature, not a burden.

**Notices first:** `any` types, missing generics, type assertions that could be narrowing, overly complex type utilities, inference opportunities missed, discriminated unions that should exist.

**Says things like:** "There's a type for that", "Let TypeScript infer this", "You're fighting the type system instead of working with it". Gets genuinely excited about elegant type solutions.

**Loves:** Generics, conditional types, template literal types, mapped types, discriminated unions, `satisfies`, type inference, Zod.

**Ignores:** Runtime performance, CSS, deployment, infrastructure. "I'm here for the types. Everything else has other reviewers."

---

### Rich Harris

**Agent name:** `rich-harris`

Creator of Svelte and Rollup, compiler-first thinker at Vercel. Questions fundamental assumptions about how UI frameworks should work. If your framework has a runtime, he wants to know why.

**Notices first:** Framework overhead, virtual DOM diffing that a compiler could eliminate, bundle size from runtime abstractions, reactivity models that fight the browser, unnecessary JavaScript.

**Says things like:** "The best framework code is no framework code", "Compilers can do this at build time", "Rethinking reactivity". Challenges assumptions others take for granted.

**Loves:** Svelte, compiler-driven optimization, SvelteKit, fine-grained reactivity, HTML-first development, eliminating unnecessary runtime code.

**Ignores:** Backend architecture, database design, enterprise patterns, deployment infrastructure.

---

### Scott Tolinski

**Agent name:** `scott-tolinski`

Co-host of Syntax.fm, creator of Level Up Tutorials. Practical web developer who values shipping real products, CSS mastery, and making complex things accessible to working developers.

**Notices first:** CSS that could be simpler, component organization issues, state management overkill, tooling that adds friction, patterns that look clever but hurt readability.

**Says things like:** "Keep it simple", "CSS can do that natively now", "You don't need a library for this". Explains things clearly because he teaches for a living.

**Loves:** Modern CSS, Svelte, practical solutions, shipping features, developer education, tools that stay out of your way.

**Ignores:** Deep type theory, systems programming, cloud architecture, database internals.

---

### Tanner Linsley

**Agent name:** `tanner-linsley`

Creator of TanStack (React Query, React Table, React Router, etc.). Focused on type-safe state management, headless UI patterns, and framework-agnostic design that works everywhere.

**Notices first:** State management anti-patterns, unnecessary re-renders, cache invalidation issues, tightly coupled UI and data logic, missing loading/error states, type safety gaps in data layers.

**Says things like:** "Separate your server state from your client state", "Make it headless", "Type-safe from database to UI". Thinks in terms of composable primitives.

**Loves:** React Query, headless UI patterns, type-safe APIs, framework-agnostic design, composable primitives, Zod, end-to-end type safety.

**Ignores:** CSS methodology, visual design, backend language choices, deployment specifics.

---

### Theo Browne

**Agent name:** `theo-browne`

Creator of the T3 Stack (Next.js + tRPC + Prisma + Tailwind), Ping.gg founder. Champions end-to-end type safety, modern TypeScript patterns, and pragmatic architecture decisions.

**Notices first:** Type safety gaps between layers, REST APIs where tRPC would be safer, missing input validation, Prisma schema issues, authentication patterns, Tailwind misuse.

**Says things like:** "Type-safe from database to browser", "tRPC eliminates an entire class of bugs", "Ship it". Opinionated but practical — if it ships and it's type-safe, it's good.

**Loves:** T3 Stack, tRPC, Prisma, Next.js, Tailwind CSS, Clerk, end-to-end type safety, shipping fast.

**Ignores:** Non-TypeScript ecosystems, low-level performance (unless egregious), CSS-in-JS debates, backend languages other than TypeScript.

---

### Wes Bos

**Agent name:** `wes-bos`

Co-host of Syntax.fm, fullstack JavaScript educator, creator of countless courses. Values practical code, clear naming, and developer happiness. If it's not fun to write, something's wrong.

**Notices first:** Confusing variable names, clever-but-unreadable code, missing error handling in user flows, tooling friction, unnecessary complexity, "this would confuse a junior dev."

**Says things like:** "Name it what it is", "A beginner should be able to read this", "Hot tip:", "Sick!". Makes everything approachable without dumbing it down.

**Loves:** JavaScript (all of it), clear naming, practical solutions, Node.js, Express, teaching, hot tips, making complex things simple.

**Ignores:** Enterprise architecture, microservices debates, advanced type gymnastics, systems programming.

---

## Synthesis Engine

After all personas complete their reviews, the synthesis engine merges their findings into a single unified report. This is where the multi-persona approach proves its value — you get consensus, disagreement, and confidence all in one view.

### Deduplication

When multiple personas flag the same issue in the same file, those findings are grouped into a single entry. The synthesis engine uses semantic similarity — it doesn't require exact string matches.

- The most detailed description becomes the primary issue text
- Unique recommendations from all contributing personas are merged
- Every contributing persona is attributed: "Flagged by: ThePrimeagen (85), DHH (75)"
- The highest severity from any persona in the group wins (critical > warning > suggestion)
- Each persona's original reasoning is preserved verbatim — the distinct voices are the value

### Confidence Scoring

Each finding carries a confidence score (0-100) set by the reviewing persona. When multiple personas independently flag the same issue, confidence is boosted:

```
boosted_confidence = min(99, max_individual_confidence + (10 × (persona_count - 1)))
```

| Scenario | Boost | Example |
|----------|-------|---------|
| Single persona at 70 | None | Score: 70 |
| Two personas agree (70, 75) | +10 | Score: 85 |
| Three personas agree (70, 75, 80) | +20 | Score: 99 (capped) |

Confidence never reaches 100 automatically — that's reserved for human certainty.

### Disagreement Detection

The synthesis engine actively looks for conflicts between personas and surfaces them in a dedicated section. Two types:

1. **Severity conflicts** — Same file, same issue area, different severity assignments. One persona says critical, another says suggestion. You see both positions with their reasoning.

2. **Approach conflicts** — One persona recommends approach X, another persona explicitly warns against X for the same file. You see the tension and decide.

Disagreements aren't hidden or averaged out. They're the most valuable part of a multi-perspective review.

### Threshold Filtering

Control the signal-to-noise ratio with `--min-confidence`:

```bash
# Default: show findings with confidence >= 30
/persona:review src/auth.ts

# Strict: only high-confidence findings
/persona:review src/auth.ts --min-confidence 70

# Show everything, including uncertain observations
/persona:review src/auth.ts --min-confidence 0
```

**Critical-severity findings are never filtered.** A low-confidence critical finding is still shown (with its score visible) because even uncertain security vulnerabilities or data loss risks deserve attention.

---

## Gilfoyle Mode

Named after the Silicon Valley character. Activates maximum-intensity review mode across all dispatched personas.

```bash
/persona:review src/ --gilfoyle
```

**What changes:**
- Every persona drops all diplomacy
- Strongest opinions on web development cranked to maximum
- No hedging, no "you might consider", no softening

**What stays the same:**
- Personas respect your project's architecture choices (see [Project Stack Constraint](#project-stack-constraint))
- Findings still use the structured format with severity and confidence
- They roast the **implementation**, not the **architecture**

**The rule:** "Roast the implementation, not the architecture."

If your project uses React, ThePrimeagen won't tell you to rewrite it in Rust. But he will be merciless about how you're using React. DHH won't tell you to switch to Rails. But he will demolish your over-engineered microservice setup within your chosen stack.

---

## Output Format

### Per-Persona JSON

Each persona writes a structured JSON file to `persona-reviews/{agent-name}.json`:

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
  "summary": "1 critical, 1 warning, 1 suggestion"
}
```

#### Finding Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `severity` | string | yes | `critical`, `warning`, or `suggestion` |
| `confidence` | integer | yes | 0-100 confidence score |
| `file` | string | yes | File path |
| `line` | integer | no | Line number (omitted when not applicable) |
| `issue` | string | yes | What's wrong |
| `recommendation` | string | yes | What to do instead |
| `reasoning` | string | yes | Why it matters — in the persona's voice |

#### Severity Levels

| Level | Meaning | Examples |
|-------|---------|---------|
| `critical` | Must fix. Bugs, security vulnerabilities, data loss risks, performance blockers. | SQL injection, event loop blocking, uncaught promise rejection, exposed secrets |
| `warning` | Should fix. Code smells, maintainability concerns, potential issues. | Missing error handling, tight coupling, God components, N+1 queries |
| `suggestion` | Consider fixing. Style improvements, alternative approaches, nice-to-haves. | Naming improvements, refactoring opportunities, newer API alternatives |

### Synthesized Review

After synthesis, you get a unified markdown report (presented in-context and saved to `persona-reviews/SYNTHESIS.md`):

```markdown
## Persona Review Synthesis

**5 personas reviewed `src/auth.ts`**
**Summary: 2 critical, 4 warnings, 7 suggestions** (after deduplication)
**Confidence threshold: 30** (3 findings hidden)

---

### Critical (2)

#### 1. Synchronous bcrypt blocks event loop
- **Confidence:** 85 (boosted — flagged by 2 personas)
- **File:** src/auth.ts:42
- **Issue:** Synchronous bcrypt.hashSync() blocks the event loop
- **Recommendation:** Use bcrypt.hash() async variant or Argon2
- **Flagged by:** ThePrimeagen (85), DHH (75)
- **Reasoning:**
  - *ThePrimeagen:* "This is a skill issue. You're blocking the entire event loop..."
  - *DHH:* "Synchronous crypto in a request handler. Classic."

### Warnings (4)
[same format]

### Suggestions (7)
[same format]

---

### Disagreements (1)

#### 1. [src/auth.ts] JWT vs session-based auth
- **ThePrimeagen** (warning, confidence 70): "JWT is fine here, just cache the secret"
- **DHH** (suggestion, confidence 65): "Sessions with httpOnly cookies. JWT is almost always wrong."
```

---

## Custom Personas

### Creating a Persona

1. Copy `agents/template.md` to `agents/your-persona.md`
2. Set `name` in the frontmatter to match the filename (without `.md`)
3. Write your persona's voice, beliefs, and focus areas
4. Keep all standard sections intact (they're required for orchestration)
5. The persona is automatically discovered on the next `/persona:review` run

No configuration files to edit. No roster to update. Drop the file, run the review.

### Persona Anatomy

Every persona `.md` file has two parts:

**YAML Frontmatter** — Configuration for Claude Code's subagent system:

```yaml
---
name: your-persona
description: "One-line description of this persona's focus"
tools: Read, Glob, Grep, Bash
disallowedTools: Write, Edit, NotebookEdit
memory: project
model: inherit
maxTurns: 10
---
```

**Markdown Body** — The persona's identity, voice, beliefs, and review behavior. This is what makes each persona unique.

### Required Sections

These sections must be present in every persona for orchestration to work correctly. The template includes all of them with placeholder values:

| Section | Purpose |
|---------|---------|
| Voice & Tone | How the persona communicates — their style, catchphrases, energy level |
| Core Beliefs | What they value, what they champion, what they fight against |
| What I Focus On | The specific things this persona looks for during review |
| What I Ignore | Things explicitly outside this persona's lens (prevents overlap) |
| Project Conventions | Instructions to read and respect CLAUDE.md project conventions |
| Bash Usage | Guidelines for safe, non-destructive Bash usage during review |
| Review Output Format | The structured finding format (severity, confidence, etc.) |
| Project Stack Constraint | The "respect the architecture" rule (see below) |
| Gilfoyle Mode | How the persona behaves when `--gilfoyle` is active |
| JSON Output Mode | The JSON schema for machine-readable output |
| Memory Curation | How the persona manages its project-specific memory |

---

## Architecture

### How /persona:review Works

```
User runs /persona:review src/auth.ts --only "ThePrimeagen,DHH" --gilfoyle
  │
  ├─ 1. Parse arguments (target: src/auth.ts, only: [theprimeagen, dhh], gilfoyle: true)
  │
  ├─ 2. Discover agents (Glob agents/*.md, exclude template.md)
  │
  ├─ 3. Filter to selected (theprimeagen, dhh)
  │
  ├─ 4. Clear persona-reviews/ (rm stale JSON from prior runs)
  │
  ├─ 5. Show confirmation (who's running, what's being reviewed)
  │
  ├─ 6. Dispatch in parallel via Task tool
  │     ├─ Task: theprimeagen agent reads src/auth.ts, returns JSON
  │     └─ Task: dhh agent reads src/auth.ts, returns JSON
  │
  ├─ 7. Write JSON to persona-reviews/theprimeagen.json, dhh.json
  │
  ├─ 8. Run Synthesis Protocol
  │     ├─ Read all persona-reviews/*.json
  │     ├─ Deduplicate by file + semantic similarity
  │     ├─ Boost confidence for multi-persona agreement
  │     ├─ Detect severity and approach disagreements
  │     ├─ Apply confidence threshold filter
  │     └─ Format as severity-grouped markdown
  │
  └─ 9. Present synthesized review + save to SYNTHESIS.md
```

**Key constraint:** The orchestration skill runs in the main conversation context (no `context: fork`). This is because forked skills become subagents, and subagents cannot spawn other subagents. The main agent must be the one dispatching persona subagents.

### How /persona:become Works

```
User runs /persona:become theprimeagen
  │
  ├─ 1. Resolve "theprimeagen" to agents/theprimeagen.md
  │
  ├─ 2. Read the persona file
  │
  ├─ 3. Extract voice, beliefs, focus areas
  │
  ├─ 4. Apply as behavioral overlay on the main Claude agent
  │
  └─ 5. Claude now responds as ThePrimeagen — with FULL tool access
```

The persona overlay stays active until `/persona:become --reset` or `/persona:become` with no arguments.

### Plugin Structure

```
persona/
├── .claude-plugin/
│   └── plugin.json                    # Plugin manifest (name, version, hooks)
├── agents/
│   ├── theprimeagen.md                # ThePrimeagen persona
│   ├── dhh.md                         # DHH persona
│   ├── chris-coyier.md                # Chris Coyier persona
│   ├── dan-abramov.md                 # Dan Abramov persona
│   ├── evan-you.md                    # Evan You persona
│   ├── kent-c-dodds.md               # Kent C. Dodds persona
│   ├── lee-robinson.md               # Lee Robinson persona
│   ├── matt-mullenweg.md             # Matt Mullenweg persona
│   ├── matt-pocock.md                # Matt Pocock persona
│   ├── rich-harris.md                # Rich Harris persona
│   ├── scott-tolinski.md             # Scott Tolinski persona
│   ├── tanner-linsley.md             # Tanner Linsley persona
│   ├── theo-browne.md                # Theo Browne persona
│   ├── wes-bos.md                    # Wes Bos persona
│   └── template.md                    # Template for custom personas
├── skills/
│   ├── review/
│   │   ├── SKILL.md                   # /persona:review orchestration
│   │   └── reference.md              # Persona roster, JSON schema, synthesis protocol
│   ├── parse-output/
│   │   └── SKILL.md                   # /persona:parse-output standalone synthesis
│   └── become/
│       └── SKILL.md                   # /persona:become interactive mode
├── hooks/
│   └── hooks.json                     # SubagentStart/SubagentStop progress hooks
├── memory/
│   └── MEMORY-TEMPLATE.md            # Structured memory template for personas
├── .gitignore                         # Excludes persona-reviews/
└── README.md                          # You are here
```

---

## Project Stack Constraint

Every persona — in every mode, at all times — follows one hard rule:

> **Respect the project's technology choices.**

Personas read the project's stack from CLAUDE.md, package.json, and the codebase itself. They treat those choices as non-negotiable foundational decisions.

**What they can do:**
- Critique how the stack is being used — bad patterns, missed opportunities, wrong abstractions, anti-patterns
- Suggest better ways to use the tools already chosen
- Point out when a library feature is being reimplemented instead of used

**What they cannot do:**
- Recommend ripping out or replacing core technology choices
- Suggest switching frameworks, languages, or major dependencies
- Criticize the architecture decision itself (only the implementation within it)

ThePrimeagen won't tell you to rewrite your React app in Rust. DHH won't tell you to switch from Next.js to Rails. They'll tell you how to use your chosen tools better.

---

## Memory

Each persona uses Claude Code's `memory: project` scope to accumulate project-specific insights across review sessions. Over time, personas learn:

- Your project's common patterns and conventions
- Recurring issues they've flagged before
- Style preferences and architecture decisions
- Known exceptions and intentional trade-offs

Memory is stored in `.claude/agent-memory/{agent-name}/MEMORY.md` (auto-created by Claude Code). Each persona's memory file follows a structured template with five sections and line budgets to prevent memory degradation over time:

| Section | Budget | Purpose |
|---------|--------|---------|
| Active Patterns | 60 lines | Conventions and patterns observed in this project |
| Known Issues | 40 lines | Recurring problems or areas of concern |
| Style Conventions | 40 lines | Project-specific style preferences |
| Resolved Items | 30 lines | Previously flagged issues that have been addressed |
| Session Notes | 20 lines | Temporary observations from recent sessions |

Personas are instructed to curate their memory: replace outdated entries rather than appending, remove resolved items, and stay within the 190-line total budget (the platform loads the first 200 lines into context).

---

## Progress Tracking

The plugin includes SubagentStart and SubagentStop hooks that log progress to stderr during reviews:

```
[persona] Starting review: theprimeagen
[persona] Starting review: dhh
[persona] Finished review: theprimeagen
[persona] Starting review: chris-coyier
[persona] Finished review: dhh
...
```

These are command-type hooks (zero LLM cost, deterministic execution). They fire for all subagents dispatched by the plugin.

---

## License

MIT
