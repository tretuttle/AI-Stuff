<!-- PROJECT SHIELDS -->
<div align="center">

[![Claude Code Plugin][claude-shield]][claude-url]
[![License: MIT][license-shield]][license-url]
[![GitHub Pull Requests][pr-shield]][pr-url]
[![GitHub Issues][issues-shield]][issues-url]
[![GitHub Stars][stars-shield]][stars-url]

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

<p>
  <a href="https://github.com/tretuttle/AI-Stuff">
    <img src="https://readme-typing-svg.demolab.com/?lines=ThePrimeagen+reviews+your+code;DHH+reviews+your+code;Rich+Harris+reviews+your+code;Dan+Abramov+reviews+your+code;All+of+them+review+your+code;In+parallel.&font=Fira+Code&center=true&width=440&height=45&duration=2500&pause=800&color=B794F4&vCenter=true" alt="Typing SVG">
  </a>
</p>

**Multi-persona code review orchestrator for [Claude Code](https://claude.com/claude-code)**

</div>

---

## Why

A single reviewer catches what they know to look for. A performance engineer spots the blocking call but misses the accessibility gap. A testing advocate flags missing coverage but doesn't notice the bundle size doubled.

Persona gives you multiple expert perspectives in one command — each with their own philosophy, priorities, and blind spots. When they agree, confidence goes up. When they disagree, you see both sides. No duplicate noise.

## Features

- **Multiple expert perspectives** — ThePrimeagen, DHH, Rich Harris, Dan Abramov, and more review your code simultaneously, each through their unique lens
- **Unified findings** — Duplicates are merged, agreement boosts confidence, disagreements are surfaced with both positions
- **Confidence scoring** — Every finding carries a 0-100 score so you can filter noise with `--min-confidence`
- **Gilfoyle mode** — Maximum intensity reviews with all diplomacy dropped
- **Interactive persona mode** — `/persona:become` lets you pair-program or discuss architecture as any persona
- **Extensible** — Drop a new `.md` file in `agents/` and it's automatically available
- **Project memory** — Personas accumulate project-specific insights across sessions

---

## Getting Started

### Prerequisites

- [Claude Code](https://claude.com/claude-code) with plugin marketplace support

### Install

```
/plugin marketplace add tretuttle/AI-Stuff
/plugin install persona@ai-stuff
```

### First Review

```bash
/persona:review src/auth.ts
```

You'll see which personas are running, progress as each finishes, and a synthesized review grouped by severity.

---

## Demo

```
/persona:review src/auth.ts
```

```
Personas: ThePrimeagen, DHH, Chris Coyier, Dan Abramov, Evan You, ...
Target: src/auth.ts

[persona] Starting review: theprimeagen
[persona] Starting review: dhh
[persona] Finished review: theprimeagen
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

### Interactive Persona Mode

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

```
/persona:review [target] [--only name1,name2] [--gilfoyle] [--min-confidence N]
```

| Argument / Flag | Description |
|-----------------|-------------|
| `[target]` | File path, directory, or glob. Defaults to staged changes. |
| `--only name1,name2` | Run only specified personas. |
| `--gilfoyle` | Maximum intensity mode. |
| `--min-confidence N` | Hide findings below this score (default: 30). Critical findings are never hidden. |

**Examples:**

| Command | What it does |
|---------|-------------|
| `/persona:review src/auth.ts` | All personas review a file |
| `/persona:review` | All personas review staged changes |
| `/persona:review --only "Rich Harris"` | Single persona |
| `/persona:review src/api/ --only theprimeagen,dhh --gilfoyle` | Two personas, max intensity |
| `/persona:review src/auth.ts --min-confidence 60` | High-confidence only |

### /persona:parse-output

Re-run synthesis on existing persona review JSON without dispatching personas again. Useful for adjusting confidence thresholds after a review.

```bash
/persona:parse-output                      # Re-synthesize with defaults
/persona:parse-output --min-confidence 70  # Only high-confidence
```

### /persona:become

Adopt a persona's voice for interactive conversation — with full tool access (read, write, edit, run commands).

```bash
/persona:become theprimeagen       # Channel ThePrimeagen
/persona:become "Rich Harris"      # Display names work too
/persona:become --reset            # Return to default Claude
```

---

## The Personas

Personas are inspired by these developers' public writing, talks, and recurring opinions.

| Persona | Focus | Philosophy |
|---------|-------|------------|
| **[ThePrimeagen](docs/PERSONAS.md#theprimeagen)** | Performance, allocations, framework overhead | "blazingly fast" — everything should be zero-cost |
| **[DHH](docs/PERSONAS.md#dhh)** | Over-engineering, complexity, dependency bloat | The Majestic Monolith — ship products, not abstractions |
| **[Chris Coyier](docs/PERSONAS.md#chris-coyier)** | CSS, semantic HTML, web standards | The platform can do that |
| **[Dan Abramov](docs/PERSONAS.md#dan-abramov)** | Component design, composition, mental models | Understand *why* before *how* |
| **[Evan You](docs/PERSONAS.md#evan-you)** | API ergonomics, DX, reactivity | Progressive disclosure of complexity |
| **[Kent C. Dodds](docs/PERSONAS.md#kent-c-dodds)** | Testing, accessibility, user-centric queries | Test the way users use it |
| **[Lee Robinson](docs/PERSONAS.md#lee-robinson)** | Server components, Core Web Vitals, metadata | That should be a Server Component |
| **[Matt Mullenweg](docs/PERSONAS.md#matt-mullenweg)** | Backward compat, a11y, i18n, open source | Decisions, not options |
| **[Matt Pocock](docs/PERSONAS.md#matt-pocock)** | Type safety, generics, inference | There's a type for that |
| **[Rich Harris](docs/PERSONAS.md#rich-harris)** | Compiler optimization, bundle size, reactivity | The best framework code is no framework code |
| **[Scott Tolinski](docs/PERSONAS.md#scott-tolinski)** | Modern CSS, simplicity, practical solutions | You don't need a library for this |
| **[Tanner Linsley](docs/PERSONAS.md#tanner-linsley)** | State management, caching, headless patterns | Separate server state from client state |
| **[Theo Browne](docs/PERSONAS.md#theo-browne)** | End-to-end type safety, tRPC, validation | Type-safe from database to browser |
| **[Wes Bos](docs/PERSONAS.md#wes-bos)** | Readability, naming, practical JS | A beginner should be able to read this |

[Full persona profiles &#8594;](docs/PERSONAS.md) &#124; [Create your own &#8594;](docs/CUSTOM-PERSONAS.md)

---

## Limitations

- **Token cost scales with persona count.** Each persona is a separate subagent with its own context. Use `--only` to control costs.
- **Requires Claude Code** with plugin marketplace support. This is not a standalone tool.
- **Memory accumulates over time.** Persona memory files in `.claude/agent-memory/` may need occasional cleanup.
- **Personas are read-only in review mode.** They cannot modify your code. `/persona:become` gives full tool access.

---

## FAQ

**How many personas can I run at once?**
All of them. Use `--only` to narrow down for faster results or focused feedback.

**Does this cost more than a regular Claude Code session?**
Yes. Each persona is a separate subagent. Use `--only` to control costs.

**Can personas modify my code?**
In `/persona:review`, no — Write and Edit are disallowed. In `/persona:become`, yes.

**Can I use this with languages other than JavaScript/TypeScript?**
Yes. The personas' philosophical lenses apply universally.

**How does memory work across projects?**
`project` scope — each project gets its own memory per persona.

**What's the difference between /persona:review and /persona:become?**
Review dispatches read-only subagents that return structured findings. Become makes Claude adopt a persona's voice with full capabilities.

---

## Reference

- [Full persona profiles](docs/PERSONAS.md)
- [Synthesis engine and output format](docs/SYNTHESIS.md)
- [Custom persona creation guide](docs/CUSTOM-PERSONAS.md)
- [Architecture and plugin structure](docs/ARCHITECTURE.md)

---

## Acknowledgments

- [Claude Code](https://claude.com/claude-code) by Anthropic — the plugin platform that makes this possible
- [ThePrimeagen](https://www.youtube.com/@ThePrimeagen), [DHH](https://dhh.dk/), [Rich Harris](https://github.com/Rich-Harris), [Dan Abramov](https://github.com/gaearon), [Evan You](https://github.com/yyx990803), [Kent C. Dodds](https://kentcdodds.com/), [Lee Robinson](https://leerob.io/), [Matt Mullenweg](https://ma.tt/), [Matt Pocock](https://www.mattpocock.com/), [Chris Coyier](https://chriscoyier.net/), [Scott Tolinski](https://scotttolinski.com/), [Tanner Linsley](https://tanstack.com/), [Theo Browne](https://t3.gg/), [Wes Bos](https://wesbos.com/) — the developers whose philosophies inspire these personas
- [Silicon Valley](https://en.wikipedia.org/wiki/Silicon_Valley_(TV_series)) — for Gilfoyle

*Persona is a fan project. The personas are inspired by these developers' public teachings, talks, and writing. It is not endorsed by or affiliated with any of the individuals named above.*

---

## Feedback

Found a bug? Have a persona request? [Open an issue](https://github.com/tretuttle/AI-Stuff/issues) — include which persona and what they said (or should have said).

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
[issues-shield]: https://img.shields.io/github/issues/tretuttle/AI-Stuff
[issues-url]: https://github.com/tretuttle/AI-Stuff/issues
[stars-shield]: https://img.shields.io/github/stars/tretuttle/AI-Stuff?style=social
[stars-url]: https://github.com/tretuttle/AI-Stuff/stargazers
