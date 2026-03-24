---
name: run
description: "Multi-persona code review and interactive persona chat. Use when the user mentions personas, code review with multiple perspectives, calling a specific developer by name (ThePrimeagen, DHH, Rich Harris, etc.), or wants expert opinions on their code. Trigger on: 'persona', 'review my code', 'what would Prime think', 'call DHH', 'ask Rich Harris', or any developer name from the roster."
argument-hint: "[review <target>] [<persona-name>] [--only name1,name2] [--min-confidence N] [--reset]"
---

# Persona

One command. Two modes. Guided when you need it, direct when you don't.

## Quick Routing

If `$ARGUMENTS` is provided, route directly:

| Pattern | Mode | Example |
|---------|------|---------|
| Starts with `review` | **Review mode** | `/persona:run review src/auth.ts` |
| Matches a persona name | **Chat mode** | `/persona:run theprimeagen` |
| `--reset` | **Reset chat mode** | `/persona:run --reset` |
| Has a file path but no `review` keyword | **Review mode** (infer) | `/persona:run src/auth.ts` |
| Empty or unrecognized | **Guided mode** | `/persona:run` |

To determine if an argument matches a persona name: discover all agents at `${CLAUDE_SKILL_DIR}/../../agents/*.md` (exclude `template.md`), extract agent names (filename without `.md`). Also check display names from the Persona Roster in `${CLAUDE_SKILL_DIR}/../review/reference.md`. If the first non-flag argument matches any agent name or display name (case-insensitive), route to Chat mode.

To determine if an argument is a file path: check if it contains `/`, `\`, or `.` (like `src/auth.ts`, `./api/`, `*.tsx`). If so, route to Review mode.

## Guided Mode

When no arguments are provided or routing is ambiguous, guide the user:

```
Welcome to Persona. What would you like to do?

1. **Review code** — Multiple expert personas review your code in parallel
2. **Chat as a persona** — Channel a specific developer's voice and philosophy
3. **List personas** — See who's available

>
```

Wait for the user's response. Based on their choice:

- **1 or "review"** → Ask: "What should I review? (file path, directory, or leave blank for staged changes)" Then proceed to Review mode.
- **2 or "chat"** → Ask: "Which persona? Here are the available ones:" then list discovered personas with display names. Proceed to Chat mode with their choice.
- **3 or "list"** → Discover and display all personas with a one-line description from each agent's YAML `description` field. Then ask what they'd like to do.

## Review Mode

Dispatch persona agents in parallel to review code from diverse expert perspectives.

See `${CLAUDE_SKILL_DIR}/../review/reference.md` for the persona roster, output format, and synthesis protocol.

### Arguments

Parse the remaining arguments (after stripping the `review` keyword if present):

1. **Review target**: File path, directory, or glob pattern. If none, default to staged changes via `git diff --staged`.
2. **--only name1,name2**: Only dispatch these personas. Accepts agent names or display names.
3. **--min-confidence N**: Minimum confidence threshold for synthesis filtering (default: 30). Critical findings are never filtered.

### Flow

1. **Discover agents**: Glob `${CLAUDE_SKILL_DIR}/../../agents/*.md`, exclude `template.md`. Agent name = filename without `.md`.

2. **Resolve display names**: Check Persona Roster in reference.md, or extract from `# Claude Persona: {Name}` heading, or convert kebab-case to title case.

3. **Resolve --only filter**: Match provided names against agent names and display names. Warn and skip unrecognized names.

4. **Show confirmation**:
   ```
   Personas: ThePrimeagen, DHH, Chris Coyier, ...
   Target: src/auth.ts
   ```

5. **Clean up**: `rm -f persona-reviews/*.json persona-reviews/SYNTHESIS.md && mkdir -p persona-reviews`

6. **Dispatch ALL selected personas in parallel using the Task tool.** Do NOT review code yourself. Do NOT dispatch sequentially.

   For each persona, use the Task tool with `agent` set to the agent's kebab-case name. The task prompt must include:
   - The review target (file path or "staged changes")
   - If staged changes, include the diff output
   - Instruction to return findings as structured markdown per the Review Output Format in reference.md
   - The persona's agent name and display name

7. **Collect results**: As each persona completes, note completion.

8. **Synthesize**: Follow the Synthesis Protocol in reference.md (dedup, confidence boost, disagreement detection, threshold filtering). Present the unified review and write to `persona-reviews/SYNTHESIS.md`.

## Chat Mode

Overlay a persona's voice onto the main agent for interactive conversation.

### Name Resolution

1. Clean input: trim whitespace, remove surrounding quotes.
2. Try exact agent name match against discovered agents.
3. Try display name match from Persona Roster in reference.md (case-insensitive).
4. Try kebab-case conversion of input.
5. If no match: list available personas and stop.

### Activation

1. Read the persona file from `${CLAUDE_SKILL_DIR}/../../agents/{agent-name}.md`.
2. Extract display name from `# Claude Persona: {Name}` heading (or derive from agent name).
3. Strip YAML frontmatter.
4. Inject the persona overlay:

---

## Persona Mode Active: {Display Name}

You are now channeling **{Display Name}**. The following persona definition describes your voice, beliefs, priorities, and focus. Adopt this identity fully for all subsequent responses until the user runs `/persona:run --reset`.

**IMPORTANT:** You retain ALL your normal tools and capabilities (Read, Write, Edit, Bash, Glob, Grep, Task, etc.). You are NOT restricted to read-only operations. You are the main agent with a persona overlay — act with that persona's voice and philosophy while having full power to help the user.

{full contents of the persona .md file, with YAML frontmatter stripped}

---

You are now {Display Name}. Respond in character. Your first response should acknowledge the persona activation briefly (1 sentence in character) and ask how you can help.

### Reset

When `--reset` is the argument (or the user says "reset"):

1. Drop any persona voice from previous activations. Respond as default Claude.
2. Tell the user: "Persona mode cleared. Back to regular Claude."
3. Stop processing.
