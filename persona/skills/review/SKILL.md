---
name: review
description: "Dispatch multi-persona code review against targeted files or changes"
argument-hint: "[file/dir/glob] [--only name1,name2] [--gilfoyle] [--min-confidence N]"
---

# Multi-Persona Code Review

Dispatch persona agents in parallel to review code from diverse expert perspectives. Each persona reviews independently and returns structured JSON findings.

See `reference.md` in this skill directory for the complete persona roster, JSON output schema, and Gilfoyle mode block.

## Argument Parsing

Parse `$ARGUMENTS` to extract four components:

1. **Review target**: The non-flag portion of the arguments -- a file path, directory, or glob pattern. If no review target is provided (empty `$ARGUMENTS` or only flags), default to staged changes by running `git diff --staged` and using that output as the review content.

2. **--only filter**: If `--only <names>` is present, extract the comma-separated list of persona names. Names can be either display names or agent names. Map display names to agent names using the Persona Roster table in `reference.md`. Only the listed personas will be dispatched.

3. **--gilfoyle flag**: If `--gilfoyle` is present, Gilfoyle mode is active for all dispatched personas.

4. **--min-confidence filter**: If `--min-confidence N` is present, use N as the minimum confidence threshold for synthesis filtering (default: 30). Critical-severity findings are never filtered regardless of this setting.

### Parsing Examples

| `$ARGUMENTS` | Target | Personas | Gilfoyle | Min Confidence |
|---|---|---|---|---|
| `src/auth.ts` | src/auth.ts | All discovered | No | 30 (default) |
| `packages/convex/ --only "Matt Pocock,Theo Browne"` | packages/convex/ | matt-pocock, theo-browne | No | 30 (default) |
| `src/api/ --only theprimeagen,dhh --gilfoyle` | src/api/ | theprimeagen, dhh | Yes | 30 (default) |
| *(empty)* | Staged changes (`git diff --staged`) | All discovered | No | 30 (default) |
| `--gilfoyle` | Staged changes (`git diff --staged`) | All discovered | Yes | 30 (default) |
| `--only "Rich Harris"` | Staged changes (`git diff --staged`) | rich-harris | No | 30 (default) |
| `src/auth.ts --min-confidence 50` | src/auth.ts | All discovered | No | 50 |

## Pre-Dispatch Confirmation

Before dispatching personas, display a confirmation summary:

```
Personas: ThePrimeagen, DHH, Chris Coyier, Dan Abramov, ...
Target: src/auth.ts
Gilfoyle mode: no
```

Show the display names of all personas that will run. Show the review target (file path, directory, glob, or "staged changes"). Show whether Gilfoyle mode is active. Then proceed with dispatch -- no user approval gate needed.

## Setup

Before dispatching any personas, clear stale output and ensure the directory exists:

```bash
rm -f persona-reviews/*.json persona-reviews/SYNTHESIS.md
mkdir -p persona-reviews
```

This prevents JSON files from a prior run from contaminating synthesis.

## Dispatch

**CRITICAL: You MUST use the Task tool to dispatch each persona subagent. Do NOT review the code yourself. Do NOT skip delegation.**

### Agent Discovery

Before dispatching, dynamically discover available persona agents:

1. Use Glob to find all agent files at `${CLAUDE_SKILL_DIR}/../../agents/*.md` (this resolves to the plugin's agents directory regardless of the user's working directory).
2. Exclude `template.md` from the list (it is a scaffold, not a real persona).
3. For each remaining file, the **agent name** is the filename without the `.md` extension (e.g., `theprimeagen.md` -> `theprimeagen`).
4. To get the **display name** for user-facing output, resolve it in this order:
   - If the agent appears in the Persona Roster table in `reference.md`, use the **Display Name** column.
   - Otherwise, if the agent markdown contains a `# Claude Persona: ...` heading, use the heading text after the colon as the display name.
   - Otherwise, derive it from the agent name by converting kebab-case to title case (e.g., `theprimeagen` -> `ThePrimeagen`, `chris-coyier` -> `Chris Coyier`, `dhh` -> `DHH`).
   The YAML frontmatter `description` field is a summary/blurb, not the display name.
5. Store the discovered list as the available persona set for this run.

### --only Name Resolution

If `--only` is specified, resolve each provided name against the discovered agent list:
- If the name exactly matches an agent name (kebab-case), use it directly.
- If the name matches a display name from `reference.md`'s Persona Roster, map it to the corresponding agent name.
- If the name matches neither, print a warning: `"Warning: persona '{name}' not found in agents/ directory. Skipping."` and exclude it.

### Dispatching Agents

For each selected persona (all discovered agents if no `--only` filter, or the resolved subset):

1. Use the **Task tool** with the `agent` parameter set to the persona's **kebab-case agent name** as discovered from the agents/ directory (e.g., `theprimeagen`, `dhh`, `chris-coyier`).

2. The task prompt MUST include:
   - The review target label: the file path, directory, or glob pattern (or "staged changes" when reviewing a diff)
   - If reviewing staged changes, include the diff output as review content (but use "staged changes" as the target label, NOT the raw diff text)
   - Instruction to return findings as a JSON object matching the schema defined in `reference.md`
   - Instruction to set `gilfoyleMode` to `true` or `false` based on the `--gilfoyle` flag
   - If `--gilfoyle` is active, append the Gilfoyle mode block from `reference.md`

3. **Dispatch ALL selected personas in parallel.** Issue all Task tool calls before waiting for any results. Do NOT dispatch sequentially -- do NOT wait for one persona to finish before dispatching the next.

### Task Prompt Template

For each persona, construct a task prompt like this:

```
Review the following code target: {target label}

{If the target is a file/directory/glob, read the relevant files and review them.}
{If the target is "staged changes", the diff is provided below for you to review.}

{If staged changes: include the git diff --staged output here as review content}

Return your findings as a JSON object with this exact schema:

{
  "persona": "{agent-name}",
  "displayName": "{Display Name}",
  "gilfoyleMode": {true or false},
  "target": "{target label — e.g. 'src/auth.ts' or 'staged changes', NOT raw diff text}",
  "findings": [
    {
      "severity": "critical | warning | suggestion",
      "confidence": 0-100,
      "file": "path/to/file",
      "line": 42,
      "issue": "description",
      "recommendation": "what to do instead",
      "reasoning": "why this matters -- in your voice"
    }
  ],
  "summary": "N critical, N warnings, N suggestions"
}

The "line" field is optional -- omit it if not applicable.
Severity values: critical, warning, suggestion.
Confidence: integer 0-100.

Return ONLY the JSON object as your final response. No markdown wrapping, no extra commentary.

{If --gilfoyle is active, append the Gilfoyle mode block from reference.md here}
```

## Collection and Summary

After each persona task completes:

1. Parse the persona's returned content as JSON.
2. Write it to `persona-reviews/{agent-name}.json` using the **Write tool** (e.g., `persona-reviews/theprimeagen.json`).
3. Print a completion message: `"{Display Name} complete"` (e.g., "ThePrimeagen complete").

## Synthesis

After ALL personas have completed and their JSON files are written to `persona-reviews/`:

1. Parse `$ARGUMENTS` for `--min-confidence N` (default: 30)
2. Follow the **Synthesis Protocol** in `reference.md` to produce the unified review
3. Present the synthesized output to the user
4. Write synthesis output to `persona-reviews/SYNTHESIS.md`
