# Domain Pitfalls

**Domain:** Claude Code multi-persona code review plugin (subagent orchestration)
**Researched:** 2026-03-22

## Critical Pitfalls

Mistakes that cause rewrites, architectural dead ends, or a non-functional plugin.

### Pitfall 1: Subagents Cannot Spawn Subagents

**What goes wrong:** You design a skill that spawns an "orchestrator" subagent, which in turn tries to spawn individual persona review subagents. This fails silently -- subagents cannot spawn other subagents. The entire orchestration layer collapses because the architecture assumed nesting.

**Why it happens:** Developers coming from traditional multi-agent frameworks (CrewAI, LangGraph) assume arbitrary nesting. Claude Code explicitly prohibits it: "Subagents cannot spawn other subagents."

**Consequences:** Complete architectural rewrite. The orchestration pattern must be fundamentally different from what most multi-agent tutorials teach.

**Prevention:** The orchestration skill must run in the **main conversation context** (no `context: fork` on the orchestrator itself), so the main agent can spawn multiple persona subagents in parallel. Alternatively, use a skill with `context: fork` that dispatches to a single agent type -- but then you lose parallel multi-persona dispatch. The correct pattern is: skill triggers main agent to spawn N persona subagents directly, not through an intermediary.

**Detection:** Test early with two persona agents. If only one review appears, the nesting constraint is blocking the second spawn.

**Phase:** Must be resolved in Phase 1 (core architecture). Getting this wrong invalidates everything built on top.

**Confidence:** HIGH -- directly stated in official Claude Code subagent docs.

---

### Pitfall 2: Plugin Agents Cannot Use hooks, mcpServers, or permissionMode

**What goes wrong:** You define persona agents in the plugin's `agents/` directory with `hooks:` frontmatter (e.g., to track SubagentStart/Stop for progress) or `permissionMode: plan` (to restrict write access). These fields are silently ignored. Personas run with default permissions and no lifecycle hooks.

**Why it happens:** The official docs state: "Plugin agents do NOT support: `hooks`, `mcpServers`, `permissionMode`." This is a security restriction -- plugins distributed via marketplace cannot escalate permissions or inject hooks through agents.

**Consequences:** Cannot implement per-persona permission scoping through agent definitions. Cannot attach hooks to individual persona agents for progress tracking. Must find alternative approaches for both needs.

**Prevention:**
- For progress tracking: Use plugin-level `hooks/hooks.json` with `SubagentStart` and `SubagentStop` matchers that match persona agent names.
- For permission control: Use `tools` and `disallowedTools` frontmatter (which ARE supported) to restrict what each persona can do. Set `disallowedTools: Write, Edit, Bash` on review-only personas.
- For permission mode: Accept that plugin agents inherit the session's permission mode. Document this for users.

**Detection:** Run `claude --debug` or `/debug` to see if agent frontmatter fields are being loaded. Silent ignoring is the symptom.

**Phase:** Phase 1 (agent definitions). Design around this from the start.

**Confidence:** HIGH -- explicitly documented in plugins reference.

---

### Pitfall 3: Main Agent Does Not Automatically Delegate to Subagents

**What goes wrong:** You create beautifully defined persona agents with descriptions like "Security-focused code reviewer" and expect Claude to automatically dispatch reviews to them. Instead, the main agent handles the entire review itself, ignoring subagents entirely.

**Why it happens:** Claude Code rarely summons subagents automatically. The main agent prefers to handle tasks directly unless explicitly instructed. Subagent descriptions alone are not enough to trigger delegation.

**Consequences:** The entire multi-persona concept fails silently -- users get a single review from the main agent instead of diverse persona feedback.

**Prevention:** The orchestration **must** be explicit. Use a skill (e.g., `/persona:review`) that contains explicit instructions to spawn each persona agent. Do not rely on implicit delegation. The skill prompt should literally say "Spawn the following agents in parallel: security-reviewer, performance-reviewer, architecture-reviewer..." with the Task tool or Agent tool.

**Detection:** If `/persona:review` produces a single monolithic review instead of multiple distinct persona sections, delegation is not happening.

**Phase:** Phase 1 (orchestration skill). This is the core mechanism -- if the skill does not explicitly orchestrate, nothing works.

**Confidence:** HIGH -- multiple community sources confirm this behavior; official docs note subagents must be explicitly invoked.

---

### Pitfall 4: Windows Hook Scripts Fail Silently

**What goes wrong:** Hook scripts referenced via file paths in `hooks/hooks.json` fail on Windows. The plugin works on macOS/Linux but hangs or silently fails on Windows. The PROJECT.md shows the developer is on Windows 11.

**Why it happens:** Claude Code uses `/bin/bash` to execute hook commands. On Windows, file path resolution for script references breaks. Additionally, missing `async: true` on SessionStart hooks causes indefinite hangs on Windows because the Node.js event loop hasn't started when synchronous hooks execute during initialization.

**Consequences:** Plugin is unusable on Windows. Since the developer is building on Windows, this will be encountered immediately.

**Prevention:**
- Use inline commands in `hooks.json` rather than script file references where possible.
- When script files are necessary, use `bash "${CLAUDE_PLUGIN_ROOT}/scripts/my-script.sh"` with explicit bash invocation.
- Always add `"async": true` to SessionStart hooks.
- Test hooks on Windows early and often.
- Keep hook commands simple -- prefer `jq` piped commands over script files.

**Detection:** Hook commands that work locally with `--plugin-dir` but fail after marketplace install. Startup hangs with no error output.

**Phase:** Phase 1 (hooks setup). Must be validated on Windows from the first hook written.

**Confidence:** HIGH -- confirmed via GitHub issues #18610 (Windows path resolution) and #351 (async hangs).

---

### Pitfall 5: Context Window Exhaustion During Multi-Persona Review

**What goes wrong:** Each persona subagent reads the target code files into its own context, produces a review, and returns results to the main agent. With 3-5 personas reviewing even moderate code, the main agent's context fills with: the original code + persona 1 full review + persona 2 full review + ... + synthesis instructions. The 200k token window overflows, triggering compaction that loses review content.

**Why it happens:** Subagents return their full output to the parent context. With multiple parallel subagents, this multiplies. A single file review from one persona might be 2-5k tokens. Five personas reviewing multiple files can easily produce 30-50k tokens of review content alone, on top of the existing conversation context.

**Consequences:** Later persona reviews get compacted away before synthesis. The synthesized review is incomplete or incoherent. Users see truncated or missing perspectives.

**Prevention:**
- Instruct persona agents to be concise: "Limit your review to the 3 most important findings. Use bullet points, not paragraphs."
- Set `maxTurns` on persona agents to limit how much exploration they do (e.g., `maxTurns: 10`).
- Use `model: sonnet` or `model: haiku` for persona agents -- cheaper and naturally more concise.
- Consider having personas write findings to files (`.claude/reviews/persona-name.md`) rather than returning everything in-context, then have the synthesizer read those files.
- Set `effort: medium` or `effort: low` on persona agents to reduce verbosity.

**Detection:** Reviews from later personas appear truncated or missing. The synthesis step produces generic rather than specific feedback. `/compact` triggers mid-review.

**Phase:** Phase 2 (optimization). Get basic orchestration working first, then tune for context efficiency.

**Confidence:** MEDIUM -- based on community reports of context exhaustion with multi-subagent patterns; exact thresholds depend on review scope.

## Moderate Pitfalls

### Pitfall 6: Putting Plugin Directories Inside .claude-plugin/

**What goes wrong:** `agents/`, `skills/`, and `hooks/` directories are placed inside `.claude-plugin/` instead of at the plugin root. Nothing loads.

**Why it happens:** Intuitive but wrong assumption. The official docs explicitly warn: "Don't put commands/, agents/, skills/, or hooks/ inside the .claude-plugin/ directory. Only plugin.json goes inside .claude-plugin/."

**Prevention:** Follow the canonical structure:
```
persona/
  .claude-plugin/
    plugin.json          # ONLY this goes here
  agents/                # At plugin root
  skills/                # At plugin root
  hooks/                 # At plugin root
  scripts/               # At plugin root
```

**Phase:** Phase 1 (project scaffold). The existing scaffold in PROJECT.md already has this correct.

**Confidence:** HIGH -- explicitly documented warning.

---

### Pitfall 7: Memory (MEMORY.md) Degrades into Noise Over Time

**What goes wrong:** Persona agents with `memory: project` accumulate insights in their MEMORY.md files. Over many sessions, the memory becomes a junk drawer of contradictory notes, outdated observations, and irrelevant trivia. Since only the first 200 lines are loaded into context, critical insights get pushed below the cutoff by noise.

**Why it happens:** The agent decides what to write to memory based on its system prompt. Without explicit structure and curation instructions, the agent appends observations without pruning old ones.

**Consequences:** Persona feedback stops improving over time. Worse, stale memory causes personas to give advice based on old code patterns that no longer exist.

**Prevention:**
- Define explicit MEMORY.md structure in the persona system prompt: sections for "Active Patterns," "Known Issues," "Style Conventions," with max line counts per section.
- Include curation instructions: "Before adding a new insight, check if it contradicts or supersedes an existing one. Remove the old entry."
- Use `memory: project` (not `user`) so memory is project-scoped and doesn't leak across codebases.
- Consider a periodic "memory reset" skill that clears and re-derives memory from recent reviews.

**Detection:** Compare persona feedback quality after 5 sessions vs. 50 sessions. If quality plateaus or declines, memory is degrading.

**Phase:** Phase 3 (memory/learning). Start without memory, add it once the core review loop is solid.

**Confidence:** MEDIUM -- community observations about memory quality; the 200-line limit is documented officially.

---

### Pitfall 8: Skill Namespacing Confusion

**What goes wrong:** Users expect `/review` but must type `/persona:review`. Or the skill name conflicts with another plugin's skill.

**Why it happens:** Plugin skills are automatically namespaced with the plugin name: `/<plugin-name>:<skill-name>`. This is different from standalone `.claude/skills/` which use bare names.

**Consequences:** User friction. Documentation says "run /review" but the actual command is `/persona:review`.

**Prevention:**
- Choose short, clear skill names since the plugin name is already a prefix.
- Document the full namespaced command in all user-facing instructions.
- Pick a plugin name that reads well as a namespace: `/persona:review` reads better than `/multi-persona-code-reviewer:review`.

**Phase:** Phase 1 (plugin manifest). The plugin name "persona" is already good -- short and clear.

**Confidence:** HIGH -- documented plugin behavior.

---

### Pitfall 9: Parallel Subagent File Conflicts

**What goes wrong:** Multiple persona subagents running in parallel attempt to write review output to the same file, or read/write overlapping project files simultaneously, causing race conditions or corrupted output.

**Why it happens:** Parallel subagents share the same filesystem. Without `isolation: worktree`, they operate in the same working directory. If the orchestration skill tells all personas to "write your review to .claude/reviews/output.md," they will clobber each other.

**Consequences:** Missing review content, garbled output files, non-deterministic results.

**Prevention:**
- Each persona writes to a persona-specific file: `.claude/reviews/{persona-name}.md`.
- Use `disallowedTools: Write, Edit` on persona agents if they should only analyze and return findings in-context rather than writing files.
- If personas need to modify code (future feature), use `isolation: worktree` to give each its own git worktree. Note: worktree isolation adds overhead and complexity.

**Detection:** Run the same review twice. If results differ significantly or files are truncated, parallel writes are conflicting.

**Phase:** Phase 1 (agent definitions). Restrict tools from the start; add file writing as a controlled feature later.

**Confidence:** MEDIUM -- follows from parallel execution fundamentals; confirmed by community reports of parallel agent conflicts.

---

### Pitfall 10: Marketplace Plugin Path Traversal Restriction

**What goes wrong:** Plugin references files outside its own directory (e.g., `../shared-utils/helper.sh`). Works locally with `--plugin-dir`, breaks after marketplace installation.

**Why it happens:** Marketplace plugins are copied to `~/.claude/plugins/cache`. Paths that traverse outside the plugin root won't resolve because the directory structure changes. The docs warn: "Paths that traverse outside the plugin root (like ../shared-utils) won't work."

**Consequences:** Plugin works in development, breaks in production (marketplace install). Extremely frustrating to debug because the error only appears for end users.

**Prevention:**
- All script and resource references must use `${CLAUDE_PLUGIN_ROOT}` for paths within the plugin.
- All persistent data must use `${CLAUDE_PLUGIN_DATA}` for files that survive updates.
- Never use relative paths that go above the plugin root.
- Always test via marketplace install (or simulate the cache path) before distribution.

**Detection:** `--plugin-dir` works but `/plugin install` does not. Path-related errors in `claude --debug` output.

**Phase:** Phase 1 (scaffold). Use correct path variables from the first script written.

**Confidence:** HIGH -- documented in plugins reference, confirmed by common issues table.

## Minor Pitfalls

### Pitfall 11: Forgetting /reload-plugins During Development

**What goes wrong:** You edit a SKILL.md or agent definition, test it, and see no change. You spend time debugging the wrong thing.

**Why it happens:** Plugin content is cached at load time. Changes require `/reload-plugins` to take effect.

**Prevention:** Build the habit: edit, `/reload-plugins`, test. Consider a development workflow note.

**Phase:** All phases (development workflow).

**Confidence:** HIGH -- documented behavior.

---

### Pitfall 12: Matcher Case Sensitivity

**What goes wrong:** A hook with `matcher: "bash"` never fires for Bash tool calls. Or `matcher: "write"` misses Write tool calls.

**Why it happens:** Matchers are case-sensitive and tool names are PascalCase. `Bash`, `Write`, `Edit`, `Read` -- not `bash`, `write`, `edit`, `read`.

**Prevention:** Always use PascalCase for tool matchers. For SubagentStart/Stop matchers, use the exact agent name as defined in its frontmatter.

**Phase:** Phase 1 (hooks). Easy to get wrong on the first attempt.

**Confidence:** HIGH -- documented behavior.

---

### Pitfall 13: Treating Persona Subagents as Code Executors

**What goes wrong:** Persona agents are designed to write code fixes, apply patches, or make changes to the codebase as part of their review. This burns tokens, causes parallel write conflicts, and fundamentally misunderstands the subagent pattern.

**Why it happens:** Developers want an "end-to-end" experience where personas not only identify issues but fix them. Community sources consistently recommend against this for subagents.

**Prevention:** Personas should be read-only analysts. Use `disallowedTools: Write, Edit, Bash` or explicit `tools: Read, Glob, Grep` allowlists. The synthesizer or main agent can optionally propose fixes based on persona findings, but personas themselves should only report.

**Phase:** Phase 1 (agent definitions). Set the right tool boundaries from the start.

**Confidence:** HIGH -- strong community consensus that subagents work best as information collectors, not executors.

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|---|---|---|
| Phase 1: Core Architecture | No-nesting constraint breaks orchestration design | Design orchestration at main-agent level, not subagent level |
| Phase 1: Agent Definitions | Plugin agents silently ignore hooks/permissionMode | Use tools/disallowedTools for access control; plugin-level hooks.json for events |
| Phase 1: Orchestration Skill | Main agent ignores subagents without explicit dispatch | Skill must contain literal spawn instructions, not hints |
| Phase 1: Hooks | Windows path resolution and async hangs | Inline commands, explicit bash invocation, async: true on SessionStart |
| Phase 1: Scaffold | Wrong directory nesting, path traversal | Follow canonical structure, use ${CLAUDE_PLUGIN_ROOT} everywhere |
| Phase 2: Context Tuning | Multi-persona output floods context window | Concise prompts, maxTurns limits, consider file-based output |
| Phase 2: Synthesis | Synthesizer loses persona nuance | Structured output format (JSON or markdown sections) from personas |
| Phase 3: Memory | MEMORY.md degrades to noise | Structured templates, curation instructions, periodic cleanup |
| Phase 3: Marketplace | Works locally, fails after install | Test via marketplace install path, not just --plugin-dir |

## Sources

- [Claude Code Plugins Reference](https://code.claude.com/docs/en/plugins-reference) -- plugin agent limitations, path restrictions, directory structure (HIGH confidence)
- [Claude Code Subagents Docs](https://code.claude.com/docs/en/sub-agents) -- no-nesting constraint, memory scopes, frontmatter fields (HIGH confidence)
- [Claude Code Skills Docs](https://code.claude.com/docs/en/skills) -- context: fork, skill frontmatter, namespacing (HIGH confidence)
- [Claude Code Hooks Guide](https://code.claude.com/docs/en/hooks-guide) -- hook types, matchers, input/output format (HIGH confidence)
- [Claude Code Hooks Reference](https://code.claude.com/docs/en/hooks) -- event lifecycle, matcher patterns, handler fields (HIGH confidence)
- [Subagents: Common Mistakes & Best Practices](https://claudekit.cc/blog/vc-04-subagents-from-basic-to-deep-dive-i-misunderstood) -- delegation misconceptions, context exhaustion, tool pollution (MEDIUM confidence)
- [GitHub Issue #18610](https://github.com/anthropics/claude-code/issues/18610) -- Windows plugin hook path resolution failure (HIGH confidence)
- [GitHub Issue #351](https://github.com/anthropics/claude-plugins-official/issues/351) -- Windows async hook hang (HIGH confidence)
- [GitHub Issue #18547](https://github.com/anthropics/claude-code/issues/18547) -- Plugin hooks not firing in VSCode (MEDIUM confidence)
