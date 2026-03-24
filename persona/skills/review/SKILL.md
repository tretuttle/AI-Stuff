---
name: review
description: "Dispatch multi-persona code review against targeted files or changes. Use when the user wants expert opinions on their code from multiple perspectives, mentions persona review, or wants ThePrimeagen/DHH/Rich Harris/etc to look at their code."
argument-hint: "[file/dir/glob] [--only name1,name2] [--min-confidence N]"
---

# Multi-Persona Code Review

Dispatch persona agents in parallel to review code from diverse expert perspectives. Each persona reviews independently through their unique philosophical lens, then findings are synthesized into a unified report.

## Argument Parsing

Parse `$ARGUMENTS` to extract:

1. **Review target**: The non-flag portion — a file path, directory, or glob pattern. If empty, default to staged changes via `git diff --staged`.

2. **--only filter**: Comma-separated persona names (agent names or display names). Only these personas run.

3. **--min-confidence N**: Minimum confidence threshold for synthesis filtering (default: 30). Critical findings are never filtered.

### Examples

| `$ARGUMENTS` | Target | Personas | Min Confidence |
|---|---|---|---|
| `src/auth.ts` | src/auth.ts | All | 30 |
| `--only "ThePrimeagen,DHH"` | Staged changes | theprimeagen, dhh | 30 |
| `src/api/ --only theprimeagen --min-confidence 60` | src/api/ | theprimeagen | 60 |
| *(empty)* | Staged changes | All | 30 |

## Agent Discovery

1. Glob `${CLAUDE_SKILL_DIR}/../../agents/*.md` to find all persona files.
2. Exclude `template.md`.
3. Agent name = filename without `.md` (e.g., `theprimeagen.md` → `theprimeagen`).
4. Display name: check Persona Roster in `${CLAUDE_SKILL_DIR}/reference.md`, or extract from `# Claude Persona: {Name}` heading, or convert kebab-case to title case.

## --only Resolution

Match each name against discovered agents:
- Exact agent name match → use directly
- Display name match from Persona Roster → map to agent name
- No match → warn and skip

## Pre-Dispatch

Show confirmation, then proceed immediately (no approval gate):

```
Personas: ThePrimeagen, DHH, Chris Coyier, ...
Target: src/auth.ts
```

Clean stale output:

```bash
rm -f persona-reviews/*.json persona-reviews/SYNTHESIS.md
mkdir -p persona-reviews
```

## Dispatch

**CRITICAL: Use the Agent tool to dispatch each persona. Do NOT review the code yourself. Do NOT skip delegation. Do NOT read agent files yourself — the Agent tool loads the persona automatically when you set `subagent_type` to the agent name.**

For each selected persona, dispatch using the Agent tool:

- Set `subagent_type` to the persona's agent name (e.g., `theprimeagen`, `dhh`, `chris-coyier`)
- Set `description` to a short label like `"ThePrimeagen reviews src/auth.ts"`

The prompt to each persona should be simple and direct:

```
Review this code: {target}

{If file/directory/glob: "Read the files and review them through your lens."}
{If staged changes: include the git diff --staged output}

Give me your findings. For each issue you find, tell me:
- Severity (critical, warning, or suggestion)
- Confidence (0-100)
- File and line
- What's wrong
- What to do instead
- Why it matters — in YOUR voice

Be yourself. Write the way you actually talk.
```

**Dispatch ALL personas in parallel.** Issue all Agent tool calls in a single message. Do NOT dispatch sequentially.

## Collection

As each persona finishes, note their completion. The Agent tool returns their findings directly — no JSON parsing needed, no files to write during collection.

## Synthesis

After ALL personas complete:

1. Follow the **Synthesis Protocol** in `${CLAUDE_SKILL_DIR}/reference.md`:
   - Deduplicate findings across personas (same file + semantically similar issue)
   - Boost confidence when multiple personas agree
   - Surface disagreements where personas conflict
   - Filter by `--min-confidence` threshold (critical findings never filtered)
2. Present the synthesized review to the user
3. Write synthesis to `persona-reviews/SYNTHESIS.md`
