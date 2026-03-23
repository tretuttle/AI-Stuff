# Persona

Multi-persona code review orchestrator for Claude Code. Get feedback from 14 distinct expert perspectives -- each with their own philosophy, priorities, and blind spots.

## Installation

```
/plugin install persona@ai-stuff
```

## Quick Start

```
# Review a specific file
/persona:review src/auth.ts

# Review staged changes (default target)
/persona:review

# Select specific personas with maximum intensity
/persona:review src/api/ --only theprimeagen,dhh --gilfoyle
```

## Usage

```
/persona:review [target] [--only name1,name2] [--gilfoyle] [--min-confidence N]
```

| Flag | Description |
|------|-------------|
| `[target]` | File, directory, or glob to review. Defaults to staged changes if omitted. |
| `--only name1,name2` | Run only specified personas. Accepts agent names (`theprimeagen`) or display names (`ThePrimeagen`). |
| `--gilfoyle` | Activate maximum-intensity review mode. All diplomacy dropped, strongest opinions cranked to maximum. |
| `--min-confidence N` | Filter findings below confidence threshold (default: 30). Critical findings are never filtered. |

### Examples

| Command | What it does |
|---------|-------------|
| `/persona:review src/auth.ts` | Review a specific file with all 14 personas |
| `/persona:review` | Review staged changes with all 14 personas |
| `/persona:review --staged` | Same as above -- review staged changes |
| `/persona:review --only "Rich Harris"` | Review staged changes with just Rich Harris |
| `/persona:review packages/convex/ --only "Matt Pocock,Theo Browne"` | Review a directory with two specific personas |
| `/persona:review src/api/ --only theprimeagen,dhh --gilfoyle` | Two personas, maximum intensity |
| `/persona:review src/auth.ts --min-confidence 50` | Only show findings with 50+ confidence |

## Personas

| Persona | Agent Name | Focus |
|---------|-----------|-------|
| ThePrimeagen | `theprimeagen` | Performance-obsessed systems engineer who hunts bloat, unnecessary abstractions, and code that disrespects the machine |
| DHH | `dhh` | Rails creator and monolith advocate who challenges complexity worship, microservice mania, and the JavaScript industrial complex |
| Chris Coyier | `chris-coyier` | CSS-Tricks founder and web platform advocate who champions CSS, semantic HTML, and front-end craft |
| Dan Abramov | `dan-abramov` | React core team alum who thinks deeply about mental models, component boundaries, and the nature of UI |
| Evan You | `evan-you` | Vue.js and Vite creator who values progressive enhancement, developer experience, and elegant API design |
| Kent C. Dodds | `kent-c-dodds` | Testing advocate and React educator focused on testing best practices, accessible patterns, and maintainable code |
| Lee Robinson | `lee-robinson` | Next.js advocate and Vercel VP focused on developer experience, performance, and modern deployment |
| Matt Mullenweg | `matt-mullenweg` | WordPress co-creator focused on open-source sustainability, backward compatibility, and democratizing publishing |
| Matt Pocock | `matt-pocock` | TypeScript wizard who reviews type safety, generics usage, and type-level programming patterns |
| Rich Harris | `rich-harris` | Svelte creator and compiler-first thinker who questions reactivity paradigms and framework overhead |
| Scott Tolinski | `scott-tolinski` | Web dev educator and practitioner who values practical solutions, CSS mastery, and shipping real products |
| Tanner Linsley | `tanner-linsley` | TanStack creator focused on type-safe state management, headless UI patterns, and framework-agnostic design |
| Theo Browne | `theo-browne` | T3 stack champion focused on end-to-end type safety, modern TypeScript patterns, and pragmatic architecture |
| Wes Bos | `wes-bos` | Fullstack JavaScript educator who values practical code, clear naming, and developer happiness |

## Output

After a review completes, you get:

- **Individual persona JSON files** in `persona-reviews/` -- one per persona with structured findings
- **Synthesized review** in `persona-reviews/SYNTHESIS.md` -- deduplicated, confidence-boosted, ranked by severity
- Findings are **deduplicated** when multiple personas flag the same issue
- Confidence is **boosted** when multiple personas agree (up to +10 per additional persona)
- Cross-persona **disagreements** are surfaced explicitly so you see where experts differ

## Custom Personas

Create your own personas to extend the review panel:

1. Copy `agents/template.md` to `agents/your-persona-name.md`
2. Fill in the frontmatter fields (`name`, `description`)
3. Write your persona's voice, beliefs, and focus areas in the body
4. Keep the standard sections unchanged: Project Conventions, Bash Usage, Review Output Format, Project Stack Constraint, Gilfoyle Mode, JSON Output Mode, Memory Curation
5. The persona will be automatically available in the next review

**Requirements:**
- The `name` field in frontmatter must be kebab-case and match the filename (without `.md`)
- The `persona` field in the JSON Output Mode section must also match the agent name
- Personas are read-only reviewers -- they cannot modify code (Write and Edit tools are disallowed)

## How It Works

The orchestrator dispatches all selected personas in parallel as Claude Code subagents. Each persona reads the code through its unique philosophical lens and returns structured JSON findings. The synthesis engine deduplicates findings, boosts confidence when multiple personas agree, surfaces disagreements, and produces a unified review. Personas also accumulate project-specific insights via memory, so their feedback sharpens over time.

## License

MIT
