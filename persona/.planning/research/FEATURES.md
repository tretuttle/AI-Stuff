# Feature Landscape

**Domain:** Multi-persona code review orchestration (Claude Code plugin)
**Researched:** 2026-03-22

## Table Stakes

Features users expect from a multi-persona code review plugin. Missing any of these and the plugin feels broken or incomplete compared to the official code-review plugin and competing tools.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Parallel persona dispatch | Anthropic's official code-review plugin runs 4 agents in parallel; sequential would feel slow | Medium | Use `context: fork` + `background: true` on subagents. Claude Code handles parallel execution natively. |
| At least 3 distinct personas | Fewer than 3 defeats "multi-persona" premise. Competitors use 4-5. | Low | Markdown subagent files in `agents/`. Low effort per persona but high effort to make them genuinely distinct. |
| Unified synthesis of findings | Every multi-agent review tool aggregates results. Raw dumps of per-persona output are unusable. | Medium | The `parse-output` skill handles this. Must deduplicate, resolve contradictions, and prioritize. |
| Skill-based invocation (`/persona:review`) | Claude Code plugins use namespaced skills. Users expect a single command entry point. | Low | `skills/orchestrate/SKILL.md` with `$ARGUMENTS` for target specification. |
| File/diff targeting | Users need to review specific files, staged changes, or PR diffs -- not the entire repo | Low | Use `!`git diff`` or `$ARGUMENTS` for dynamic context injection in the orchestration skill. |
| Structured output format | Findings need severity, location, and explanation. Wall-of-text reviews are worthless. | Low | Define output schema in persona prompts: severity (critical/warning/suggestion), file, line range, explanation. |
| Confidence/severity scoring | Official plugin uses 0-100 scoring with threshold filtering (default 80). This is now expected. | Medium | Each persona scores its own findings. Synthesis step can apply threshold filtering. |
| CLAUDE.md awareness | Official plugin dedicates 2 of 4 agents to CLAUDE.md compliance. Project conventions matter. | Low | Personas naturally have access to CLAUDE.md via Claude Code's context system. Explicitly instruct personas to reference it. |

## Differentiators

Features that set Persona apart from the official code-review plugin and generic subagent collections. These are the reasons someone installs this plugin instead of (or alongside) the official one.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Named character personas with genuine philosophies | Official plugin uses anonymous "Agent #1-4" by function. Persona gives each reviewer a name, worldview, and voice -- making feedback memorable and attributable ("The Architect flagged this coupling issue again"). | Medium | The core differentiator. Each persona `.md` needs a distinct identity, not just a different checklist. Philosophy drives what they notice and how they frame it. |
| Persistent persona memory (`memory: project`) | Personas accumulate project-specific insights over time. "The Security Reviewer remembers you fixed a similar XSS pattern in auth.ts last month." No competitor in the Claude Code ecosystem does this. | Low | Built into Claude Code's subagent system. Set `memory: project` in frontmatter. Memory improves over sessions without any custom code. |
| Cross-persona disagreement surfacing | When personas disagree (Architect says "abstract this" while Pragmatist says "keep it simple"), surface the tension explicitly rather than hiding it. Real review teams have productive disagreements. | Medium | Synthesis skill must detect contradictory findings and present both sides with reasoning, not just pick a winner. |
| Persona-specific review lenses | Each persona reviews through a fundamentally different lens, not just a different checklist. A "Security Hardener" thinks adversarially. A "Junior Developer Advocate" asks "would a new team member understand this?" | Low | Prompt engineering in agent `.md` files. Low technical complexity but high design quality required. |
| User-extensible persona system | Drop a `.md` file in `agents/` and you have a new reviewer. No config files, no registration. Claude Code's agent discovery handles it. | Low | Already how the plugin system works. Document the contract clearly (required frontmatter fields, output format expectations). |
| Selective persona invocation | Run only specific personas for focused reviews: `/persona:review --security` or `/persona:review --architect,perf` | Medium | Parse `$ARGUMENTS` for persona selection flags. Default to all personas if none specified. |
| Review history diffing | "Last review flagged 5 issues. This review flags 2. Here's what improved and what's new." Tracks progress across reviews via memory. | High | Requires storing previous review results in persona memory and comparing. Defer to v2. |

## Anti-Features

Features to explicitly NOT build. Each would dilute the plugin's focus or create maintenance burden without proportional value.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Custom persona creation UI/wizard | PROJECT.md explicitly scopes this out. Users who want custom personas can write `.md` files -- that is the UI. A wizard adds complexity for marginal convenience. | Document the persona file contract clearly with examples. Provide a template persona `.md` that users copy and modify. |
| Real-time streaming of persona feedback | PROJECT.md scopes this out. Streaming partial reviews creates anxiety and partial context. Let reviews complete, then present unified results. | Show a brief progress indicator via hooks (SubagentStart/Stop) so users know work is happening. |
| GitHub PR comment integration | The official code-review plugin already does this with `--comment`. Reimplementing it duplicates effort and competes directly where Anthropic has the advantage. | Output to terminal. Users who want PR comments can pipe output or use the official plugin for that workflow. |
| Multi-LLM persona diversity | Using GPT-4 for one persona and Claude for another sounds clever but adds API key management, billing complexity, and external dependencies. The constraint is "no external deps." | All personas use Claude models. Vary the model tier (haiku for quick-scan personas, sonnet/opus for deep-analysis) to get genuine behavioral diversity within the Claude family. |
| Automated CI/CD integration | Running persona reviews in CI requires authentication, token management, and headless Claude Code -- all complex. The official plugin already targets this use case. | Focus on developer-initiated reviews during development. Let the official plugin handle CI/CD. |
| Per-line inline annotation format | Mapping findings to exact line numbers with inline diff annotations is fragile and breaks with code changes. The official plugin handles this with full SHA links. | Report findings at file + function/section level with enough context to locate the issue. More robust than line numbers. |
| Persona "voting" or democratic consensus | Counting votes (3/5 personas agree) reduces nuanced expert opinions to a popularity contest. A security concern is critical even if 4 other personas don't flag it. | Present all unique findings with persona attribution. Let the synthesis highlight severity and confidence without vote-counting. |

## Feature Dependencies

```
Persona agent definitions (.md files)
  --> Orchestration skill (dispatches to personas)
    --> Synthesis/parse-output skill (aggregates results)
      --> Confidence scoring (filters noise)

Persona agent definitions (.md files)
  --> memory: project (accumulates insights)
    --> Review history diffing (v2, compares across sessions)

Orchestration skill
  --> Selective persona invocation (argument parsing)
  --> File/diff targeting (dynamic context injection)

SubagentStart/Stop hooks
  --> Progress tracking (which personas are running/done)
```

## MVP Recommendation

**Phase 1 -- Prioritize:**
1. 3-4 distinct persona agent definitions with genuine character and philosophy (table stakes + core differentiator)
2. Orchestration skill that dispatches to all personas in parallel with file/diff targeting (table stakes)
3. Synthesis skill that deduplicates, attributes findings to personas, and structures output with severity (table stakes)
4. Confidence scoring with configurable threshold (table stakes)
5. SubagentStart/Stop hooks for progress indication (table stakes)

**Phase 2 -- Add depth:**
6. Persistent persona memory via `memory: project` (differentiator, low complexity)
7. Cross-persona disagreement surfacing in synthesis (differentiator, medium complexity)
8. Selective persona invocation via arguments (differentiator, medium complexity)
9. CLAUDE.md compliance as explicit review dimension across all personas (table stakes refinement)

**Defer to v2:**
- Review history diffing (high complexity, depends on memory maturity)
- Additional persona packs (community contribution opportunity)

**Rationale:** The MVP must prove the core value proposition -- that named, opinionated personas with distinct philosophies produce better reviews than anonymous function-based agents. Memory and selective invocation deepen that value but aren't required to demonstrate it.

## Competitive Positioning

| Competitor | What They Do | Persona's Advantage |
|------------|-------------|---------------------|
| Official code-review plugin | 4 anonymous function-based agents (compliance, bugs, history). 89K+ installs. | Named personas with philosophies create memorable, attributable feedback. Not a replacement -- complementary. |
| Claude Buddy | 12 general-purpose personas that auto-activate by context. | Persona is focused exclusively on code review depth, not general development assistance. Deeper expertise per persona. |
| CodeRabbit / Greptile | SaaS code review with full codebase indexing. | Zero external dependencies, runs locally, project memory improves over time, fully extensible via `.md` files. |
| Calimero ai-code-reviewer | Multi-model orchestration with consensus scoring. | No external API dependencies. Persona diversity comes from character/philosophy, not model diversity. |
| awesome-claude-code-subagents | Collection of individual subagents (code-reviewer, architect-reviewer). | Orchestrated ensemble with synthesis, not individual agents used ad-hoc. |

## Sources

- [Anthropic official code-review plugin](https://github.com/anthropics/claude-code/blob/main/plugins/code-review/README.md) - PRIMARY competitive reference
- [VoltAgent awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents) - Subagent patterns
- [Claude Buddy - 12 AI Personas](https://claude-buddy.dev/) - Closest persona-based competitor
- [Calimero ai-code-reviewer](https://github.com/calimero-network/ai-code-reviewer) - Multi-agent orchestration patterns
- [Composio top Claude Code plugins 2026](https://composio.dev/content/top-claude-code-plugins) - Marketplace landscape
- [Greptile vs CodeRabbit comparison](https://www.greptile.com/greptile-vs-coderabbit) - SaaS code review feature baseline
- [State of AI Code Review 2025](https://www.devtoolsacademy.com/blog/state-of-ai-code-review-tools-2025/) - Industry context
