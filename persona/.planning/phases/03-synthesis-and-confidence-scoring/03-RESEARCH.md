# Phase 3: Synthesis and Confidence Scoring - Research

**Researched:** 2026-03-22
**Domain:** Claude Code skill-based JSON synthesis and deduplication (prompt engineering, no external deps)
**Confidence:** HIGH

## Summary

Phase 3 builds two interconnected pieces: (1) a synthesis engine embedded in the `/persona:review` orchestration skill that runs automatically after all persona dispatches complete, and (2) a standalone `/persona:parse-output` skill that re-runs synthesis on existing `persona-reviews/*.json` files. Both produce identical severity-grouped, deduplicated, confidence-filtered markdown output.

The core challenge is deduplication and disagreement detection across up to 14 persona JSON files without external libraries. Since Claude Code plugins cannot use npm packages, all logic lives in skill prompt instructions -- Claude itself performs the semantic grouping, confidence boosting, and disagreement surfacing. This is a prompt engineering task, not a code engineering task.

**Primary recommendation:** Build synthesis as inline instructions in the skill markdown. Claude reads all 14 JSON files via `Read` tool, performs semantic deduplication in-context, and outputs structured markdown. No scripts, no shell-based JSON merging -- let the LLM do what it does best (semantic similarity and text synthesis).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Synthesis runs automatically at the end of `/persona:review` after all personas complete -- integrated into the orchestration flow.
- **D-02:** Also available as a standalone `/persona:parse-output` skill for re-running synthesis on existing persona-reviews files without re-dispatching personas.
- **D-03:** Both invocations produce identical output -- the standalone skill just skips the dispatch step.
- **D-04:** Deduplication by file + issue similarity -- findings about the same file with similar issue descriptions are grouped together, not exact string match.
- **D-05:** When multiple personas flag the same issue, it appears once in the output, attributed to all originating personas (e.g., "Flagged by: ThePrimeagen, DHH, Theo Browne").
- **D-06:** Confidence boosting: findings flagged by multiple personas get their confidence score boosted (demonstrates cross-persona agreement).
- **D-07:** Cross-persona disagreements are shown in a dedicated "Disagreements" section with both sides and their reasoning.
- **D-08:** Disagreements are detected when personas assign conflicting severity to the same file/issue area, or when one persona recommends an approach another explicitly cautions against.
- **D-09:** Severity-grouped markdown: critical findings first, then warnings, then suggestions.
- **D-10:** Summary header with finding counts (e.g., "3 critical, 7 warnings, 12 suggestions from 14 personas").
- **D-11:** Each finding shows: severity, confidence score, file, issue, recommendation, reasoning, and persona attribution.
- **D-12:** Confidence threshold filtering: findings below a configurable threshold (default: 30) are hidden. User can adjust via `--min-confidence N` flag.

### Claude's Discretion
- Exact similarity algorithm for deduplication (fuzzy string matching, semantic comparison, or simpler heuristic)
- How to detect disagreements algorithmically from JSON findings
- Whether to store synthesized output as a file or only display in-context
- How to structure the standalone parse-output skill (minimal wrapper around synthesis logic)

### Deferred Ideas (OUT OF SCOPE)
- **Chat with persona:** After seeing synthesis results, user can invoke a specific persona for follow-up conversation about their findings -- belongs in a future phase.
- **Output format options:** JSON and concise summary formats (from v2 requirements OUTF-01) -- deferred to v2.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SYNT-01 | User can parse and synthesize persona feedback into a unified review via `/persona:parse-output` skill | Standalone skill architecture (see Architecture Patterns) |
| SYNT-02 | Synthesis deduplicates findings that multiple personas flagged | Semantic deduplication via LLM grouping (see Deduplication Pattern) |
| SYNT-03 | Synthesis attributes each finding to the originating persona(s) | Multi-persona attribution in output format (see Output Format Pattern) |
| SYNT-04 | Synthesis ranks findings by severity (critical / warning / suggestion) | Severity-grouped output structure (see Output Format Pattern) |
| SYNT-05 | Synthesis surfaces cross-persona disagreements explicitly | Disagreement detection pattern (see Disagreement Detection) |
| CONF-01 | Each persona assigns a confidence score (0-100) to each finding | Already in JSON schema from Phase 2 -- `confidence` field exists in each finding |
| CONF-02 | Synthesis can filter findings below a configurable confidence threshold | `--min-confidence N` flag parsing + filter step (see Confidence Filtering) |
</phase_requirements>

## Standard Stack

### Core
| Technology | Format | Purpose | Why Standard |
|------------|--------|---------|--------------|
| `skills/parse-output/SKILL.md` | Markdown with YAML frontmatter | Standalone synthesis skill | Claude Code native skill system. User-invocable via `/persona:parse-output`. |
| `skills/review/SKILL.md` | Existing skill (modification) | Add post-dispatch synthesis step | Synthesis integrates into the existing orchestration flow. |
| `skills/review/reference.md` | Existing file (modification) | Add synthesis output format spec | Keep synthesis format spec alongside the JSON input schema it consumes. |

### Supporting
| Technology | Format | Purpose | When to Use |
|------------|--------|---------|-------------|
| `Read` tool | Built-in | Read persona-reviews/*.json files | Synthesis reads all JSON files before processing |
| `Glob` tool | Built-in | Discover persona-reviews/*.json files | Find which persona output files exist |
| `Bash` tool | Built-in | Optional: list files in persona-reviews/ | Fallback for file discovery |

### What NOT to Use
| Anti-Pattern | Why Not | What to Do Instead |
|--------------|---------|-------------------|
| Shell scripts for JSON merging | No external deps constraint; `jq` may not be available on all systems | Let Claude read JSON files and synthesize in-context |
| npm packages for deduplication | Plugin constraint: no external deps | LLM-based semantic similarity in prompt instructions |
| Separate synthesis subagent | Subagents cannot spawn subagents; synthesis must run in main context | Inline synthesis instructions in the skill |
| `context: fork` on parse-output skill | Would create a subagent that cannot access persona-reviews/ easily | Run in main context like the review skill |

## Architecture Patterns

### Recommended Skill Structure
```
skills/
  review/
    SKILL.md           # Modified: add synthesis step after dispatch
    reference.md       # Modified: add synthesis output format spec
  parse-output/
    SKILL.md           # NEW: standalone synthesis skill
```

### Pattern 1: Dual-Invocation Synthesis (Core Architecture)

**What:** Synthesis logic appears in two places but produces identical output. The review skill has synthesis as its final step; the parse-output skill has synthesis as its ONLY step.

**When to use:** Always -- this is the locked decision (D-01, D-02, D-03).

**How it works:**

1. **In `/persona:review` (SKILL.md modification):** After the "Collection and Summary" section, add a "Synthesis" section with full synthesis instructions. This replaces the current simple severity listing with the full deduplicated, confidence-filtered output.

2. **In `/persona:parse-output` (new SKILL.md):** Contains the same synthesis instructions but starts by reading existing `persona-reviews/*.json` files. No dispatch step.

**Key constraint:** The synthesis instructions should be written once in `reference.md` and referenced from both skills, to avoid duplication drift. Both skills say "Follow the Synthesis Protocol in reference.md."

**Example structure for parse-output/SKILL.md:**
```yaml
---
name: parse-output
description: "Synthesize existing persona review output into a unified, deduplicated review"
argument-hint: "[--min-confidence N]"
---
```

### Pattern 2: LLM-Based Semantic Deduplication

**What:** Claude reads all persona JSON findings, groups similar findings by file + issue semantics (not exact string match), and produces a single entry per unique issue with multi-persona attribution.

**When to use:** For SYNT-02 (deduplication) and D-04 (similarity-based grouping).

**How it works:**

The synthesis prompt instructs Claude to:
1. Load all `persona-reviews/*.json` files
2. Flatten all findings into a single list
3. Group findings that describe the same issue in the same file (semantic similarity, not string match)
4. For each group: take the most detailed description, combine recommendations, list all contributing personas, apply confidence boosting
5. Sort groups by severity then confidence

**Why LLM-based:** The constraint is no external dependencies. String similarity algorithms (Levenshtein, Jaccard) would need code. But Claude is already in-context reading these findings -- semantic grouping is exactly what LLMs excel at. A 14-persona review might produce 70-140 findings (1-5 per persona x 14). This fits easily in context.

**Prompt instruction example:**
```
Group findings that describe the SAME issue in the SAME file. Two findings are "the same issue" if:
- They reference the same file (exact path match)
- They describe semantically similar problems (e.g., "missing error handling" and "no try-catch around async call" about the same function)

Do NOT group findings that happen to be in the same file but describe different issues.
```

### Pattern 3: Confidence Boosting Formula

**What:** When N personas independently flag the same issue, the synthesized confidence score increases.

**When to use:** For D-06 (confidence boosting).

**Recommended formula:**
```
boosted_confidence = min(99, max_individual_confidence + (10 * (persona_count - 1)))
```

- Single persona: original confidence (no boost)
- Two personas agree: +10 boost
- Three personas agree: +20 boost
- Capped at 99 (never auto-100)

**Example:** ThePrimeagen flags an issue at confidence 70, DHH flags the same at 75. Boosted confidence = min(99, 75 + 10) = 85. Attribution: "Flagged by: ThePrimeagen (70), DHH (75)"

### Pattern 4: Disagreement Detection

**What:** Identify cases where personas disagree on severity or approach for the same file/area.

**When to use:** For SYNT-05 and D-07/D-08.

**Detection rules (for prompt instructions):**
1. **Severity conflict:** Two personas flag the same file+issue area but assign different severities (e.g., one says `critical`, another says `suggestion`).
2. **Approach conflict:** One persona recommends X for a file, another persona explicitly cautions against X for the same file.

**Output format for disagreements:**
```markdown
### Disagreements

#### [file.ts] Error Handling Strategy
- **ThePrimeagen** (critical, confidence 85): "Use Result types, exceptions are lazy"
- **Kent C. Dodds** (suggestion, confidence 60): "ErrorBoundary pattern is fine here, it's the React way"
```

### Pattern 5: Confidence Threshold Filtering

**What:** Parse `--min-confidence N` from skill arguments and exclude findings below the threshold.

**When to use:** For CONF-02 and D-12.

**How it works in the skill prompt:**
```
Parse $ARGUMENTS for --min-confidence flag:
- If present: use the specified integer as the minimum confidence threshold
- If absent: default to 30

After deduplication and boosting, exclude any finding whose final confidence score
is below the threshold. Show a note at the bottom: "N findings hidden (below confidence threshold of {threshold})"
```

### Anti-Patterns to Avoid
- **Separate synthesis script:** Don't try to merge JSON in bash. Let Claude do it in-context. The plugin has no external deps, and the semantic grouping requires language understanding.
- **Over-engineering deduplication:** Don't specify exact similarity thresholds or string matching algorithms. Claude's semantic understanding is the algorithm. Keep instructions behavioral, not algorithmic.
- **Duplicating synthesis instructions:** Don't copy-paste the same synthesis logic into both SKILL.md files. Put the protocol in `reference.md` and reference it from both skills.
- **Running synthesis as a subagent:** The review skill runs in main context. Synthesis is the final step of that skill. Do NOT fork it into a subagent -- that would break the flow and create unnecessary context separation.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON parsing | Shell scripts with jq | Claude's `Read` tool + in-context processing | No external deps constraint; Claude natively understands JSON |
| Semantic similarity | Custom string matching algorithm | LLM semantic understanding via prompt instructions | Claude IS the similarity engine -- just describe what "same issue" means |
| Findings aggregation | Database or data structure | In-context list processing | 70-140 findings from 14 personas fits easily in context |
| Markdown formatting | Template engine | Prompt instructions with exact output format | Claude follows format instructions precisely |

**Key insight:** This entire phase is prompt engineering. The "synthesis engine" is Claude itself, guided by detailed instructions in skill markdown files. There is no code to write -- only carefully structured instructions.

## Common Pitfalls

### Pitfall 1: Context Window Pressure from 14 JSON Files
**What goes wrong:** Reading 14 persona JSON files (each potentially 2-5KB) adds 28-70KB of raw text to context before synthesis even begins. Combined with the existing conversation context from dispatch, this could trigger compaction.
**Why it happens:** The review skill already has dispatch context (persona prompts, completion messages). Adding all JSON file contents on top pushes total context usage high.
**How to avoid:** The review skill already writes JSON to files (Phase 2 design). For the integrated synthesis path, Claude reads the files AFTER dispatch is complete. The synthesis prompt should instruct Claude to read files one at a time and build a working summary, not load all 14 simultaneously. For the standalone parse-output skill, context is clean -- no prior dispatch overhead.
**Warning signs:** Compaction messages during synthesis. Missing persona attributions in output (compacted away).

### Pitfall 2: Deduplication Hallucination
**What goes wrong:** Claude over-groups findings, merging genuinely different issues because they happen to be in the same file. Or under-groups, treating the same issue described differently as separate findings.
**Why it happens:** Semantic similarity is subjective. Without clear grouping criteria in the prompt, Claude may be too aggressive or too conservative.
**How to avoid:** Provide explicit grouping criteria: "same file AND same function/area AND same category of concern." Include examples of what SHOULD and SHOULD NOT be grouped. Add a "when in doubt, keep separate" bias.
**Warning signs:** Synthesized output has significantly fewer findings than expected. Or: no deduplication occurs at all (every finding unique).

### Pitfall 3: Losing Persona Voice in Synthesis
**What goes wrong:** The synthesized output reads like generic code review feedback. The unique perspectives and reasoning of each persona are lost in the merge.
**Why it happens:** When deduplicating, the natural instinct is to create a "neutral" merged description. But the value of multi-persona review IS the different perspectives.
**How to avoid:** For deduplicated findings, include the original reasoning from EACH contributing persona. "ThePrimeagen says: [reasoning]. DHH says: [reasoning]." Don't synthesize the reasoning into a bland average.
**Warning signs:** User can't tell which persona contributed what. Reasoning section reads like it could come from any reviewer.

### Pitfall 4: Confidence Threshold Silently Hiding Important Findings
**What goes wrong:** A persona flags a genuine critical issue but with confidence 25 (below the default 30 threshold). The finding is silently filtered out.
**Why it happens:** Personas may assign low confidence to findings outside their expertise area. A security issue flagged by a CSS-focused persona might have low confidence but still be valid.
**How to avoid:** Never filter critical-severity findings regardless of confidence. The threshold only applies to warning and suggestion severity. Show a clear message about hidden findings count so users know to lower the threshold if needed.
**Warning signs:** Users report missing findings they expected to see.

### Pitfall 5: Parse-Output Skill Fails on Empty or Partial Reviews
**What goes wrong:** User invokes `/persona:parse-output` but `persona-reviews/` doesn't exist, is empty, or has partial results (some personas failed).
**Why it happens:** Parse-output runs independently of dispatch. Files may not exist, be malformed, or be from a partial run.
**How to avoid:** Add validation at the start of synthesis: check that persona-reviews/ exists, list available files, handle zero-file case gracefully ("No persona reviews found. Run /persona:review first."), handle malformed JSON gracefully (skip and note).
**Warning signs:** Error messages about missing files or JSON parse failures.

## Code Examples

### Synthesis Output Format (for reference.md)

```markdown
## Persona Review Synthesis

**14 personas reviewed `src/auth.ts`**
**Summary: 3 critical, 7 warnings, 12 suggestions** (after deduplication)
**Confidence threshold: 30** (4 findings hidden)

---

### Critical (3)

#### 1. Synchronous bcrypt blocks event loop
- **Confidence:** 92 (boosted -- flagged by 3 personas)
- **File:** src/auth.ts:42
- **Issue:** Synchronous bcrypt.hashSync() call blocks the Node.js event loop during password hashing
- **Recommendation:** Use bcrypt.hash() async variant or switch to Argon2
- **Flagged by:** ThePrimeagen (85), Dan Abramov (80), Theo Browne (75)
- **Reasoning:**
  - *ThePrimeagen:* "This is a skill issue. You're blocking the entire event loop for password hashing."
  - *Dan Abramov:* "Every concurrent request queues behind this synchronous call. This doesn't compose."
  - *Theo Browne:* "Ship-blocking. Your API will time out under load."

#### 2. JWT secret in plaintext config
- **Confidence:** 78
- **File:** src/auth.ts:8
- **Issue:** JWT signing secret is hardcoded in the configuration file
- **Recommendation:** Use environment variables or a secrets manager
- **Flagged by:** Lee Robinson (78)
- **Reasoning:**
  - *Lee Robinson:* "This secret will end up in version control. Use process.env at minimum."

---

### Warnings (7)
[... similar format ...]

### Suggestions (12)
[... similar format ...]

---

### Disagreements (2)

#### 1. [src/auth.ts] Error Handling Approach
- **ThePrimeagen** (critical, confidence 85): "Exceptions are control flow abuse. Use Result types."
- **Kent C. Dodds** (suggestion, confidence 60): "ErrorBoundary catches this at the component level. The try-catch is fine for server code."

#### 2. [src/auth.ts:15] JWT Secret Caching
- **ThePrimeagen** (warning, confidence 70): "Cache the secret at module level. Hitting process.env on every call is wasteful."
- **Dan Abramov** (suggestion, confidence 45): "process.env reads are fast enough. Premature optimization."

---

*4 findings hidden below confidence threshold of 30. Use `--min-confidence 0` to see all.*
```

### Parse-Output SKILL.md Structure

```yaml
---
name: parse-output
description: "Synthesize existing persona review output into a unified, deduplicated review with confidence scoring"
argument-hint: "[--min-confidence N]"
---

# Synthesize Persona Reviews

Read all persona review JSON files from `persona-reviews/` and produce a unified,
deduplicated review following the Synthesis Protocol in the review skill's `reference.md`.

## Arguments

Parse `$ARGUMENTS` for:
- `--min-confidence N`: Minimum confidence threshold (default: 30)

## Steps

1. Check that `persona-reviews/` directory exists
2. List all `.json` files in `persona-reviews/`
3. If no files found, tell the user: "No persona reviews found. Run /persona:review first."
4. Read each JSON file
5. Follow the **Synthesis Protocol** in `skills/review/reference.md`
6. Output the synthesized review
```

### Review SKILL.md Modification (Synthesis Step Addition)

The existing "Collection and Summary" section in `skills/review/SKILL.md` currently ends with a simple severity listing. Replace that with:

```markdown
## Synthesis

After ALL personas have completed and their JSON files are written to `persona-reviews/`:

1. Read all JSON files from `persona-reviews/`
2. Parse `$ARGUMENTS` for `--min-confidence N` (default: 30)
3. Follow the **Synthesis Protocol** in `reference.md` to produce the unified review
4. Present the synthesized output to the user
```

## State of the Art

| Old Approach (Phase 2 current) | New Approach (Phase 3) | Impact |
|-------------------------------|------------------------|--------|
| Simple severity count listing after dispatch | Full deduplication + confidence + disagreement synthesis | Users get actionable, deduplicated review instead of raw listing |
| No confidence filtering | Configurable threshold filtering | Users control signal-to-noise ratio |
| No disagreement surfacing | Explicit disagreement section | Multi-persona value proposition proven |
| No standalone re-synthesis | `/persona:parse-output` skill | Users can re-synthesize without re-running reviews |

## Open Questions

1. **Should synthesized output be saved to a file?**
   - What we know: Persona raw JSON is saved to `persona-reviews/`. Synthesis is presented in-context.
   - What's unclear: Should synthesis output also be written to a file (e.g., `persona-reviews/SYNTHESIS.md`) for later reference?
   - Recommendation: Write to `persona-reviews/SYNTHESIS.md` so users can reference it later and re-read without re-running synthesis. This is a Claude's Discretion item -- recommend YES.

2. **How to handle the synthesis instructions appearing in two skills?**
   - What we know: Both `/persona:review` and `/persona:parse-output` need identical synthesis behavior.
   - What's unclear: Best way to share instructions without duplication.
   - Recommendation: Put the full Synthesis Protocol in `skills/review/reference.md` (which already has the JSON schema). Both skills reference it: "Follow the Synthesis Protocol in the review skill's reference.md." The parse-output skill can use dynamic context injection or just instruct Claude to read the file.

3. **Critical findings below confidence threshold**
   - What we know: Default threshold is 30 (D-12). Some critical findings might have low confidence.
   - What's unclear: Should critical-severity findings be exempt from threshold filtering?
   - Recommendation: YES -- never filter critical findings regardless of confidence. Show them with a note like "(low confidence)" but do not hide them.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Manual validation (no automated test framework -- this is a Claude Code plugin, not a codebase with unit tests) |
| Config file | N/A |
| Quick run command | `/persona:parse-output` with sample persona-reviews/ data |
| Full suite command | `/persona:review src/` end-to-end review + synthesis |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SYNT-01 | `/persona:parse-output` skill invocable and produces output | manual | Invoke `/persona:parse-output` after creating sample JSON files | Wave 0: create sample JSON |
| SYNT-02 | Duplicate findings from multiple personas merged into one entry | manual | Create 2 persona JSONs with overlapping findings, run parse-output | Wave 0: create test data |
| SYNT-03 | Each finding shows originating persona(s) | manual | Verify "Flagged by:" attribution in output | N/A |
| SYNT-04 | Findings ranked by severity (critical > warning > suggestion) | manual | Verify output section ordering | N/A |
| SYNT-05 | Disagreements surfaced in dedicated section | manual | Create 2 persona JSONs with conflicting severities, verify disagreement section | Wave 0: create test data |
| CONF-01 | Confidence scores present in persona output (0-100) | manual | Check existing persona JSON files for confidence field | Already in schema |
| CONF-02 | `--min-confidence` flag filters findings below threshold | manual | Run parse-output with --min-confidence 80, verify low-confidence findings hidden | N/A |

### Sampling Rate
- **Per task commit:** Manual review of skill markdown for instruction clarity
- **Per wave merge:** Test with sample persona-reviews/ data
- **Phase gate:** End-to-end `/persona:review` with synthesis on a real file

### Wave 0 Gaps
- [ ] `persona-reviews/sample-theprimeagen.json` -- sample test data for synthesis testing
- [ ] `persona-reviews/sample-dhh.json` -- second persona with overlapping + conflicting findings
- [ ] Verify CONF-01: confirm persona agents already include `confidence` field in JSON output (should be done from Phase 2)

## Project Constraints (from CLAUDE.md)

- **No external deps:** Plugin works with just Claude Code -- no npm packages. Synthesis must be LLM-based, not library-based.
- **Plugin format:** Must conform to Claude Code plugin conventions (skills in `skills/` directory with SKILL.md).
- **Subagent system:** Persona agents are `.md` subagent definitions. Synthesis is NOT a subagent -- it runs in main context.
- **No `context: fork` on orchestrator or synthesis:** Main agent must stay in main context to complete the flow.
- **`user-invocable: true` for parse-output:** So users can invoke `/persona:parse-output` directly.
- **`${CLAUDE_SKILL_DIR}` for cross-referencing:** Parse-output skill can reference review skill's reference.md.
- **Bash scripts must work on Windows:** Any helper scripts (if needed) must use inline bash commands, not script file references.

## Sources

### Primary (HIGH confidence)
- `skills/review/reference.md` -- JSON output schema that synthesis consumes (existing project file)
- `skills/review/SKILL.md` -- Current orchestration skill with dispatch and collection steps (existing project file)
- `research/03-skills.md` -- Skills frontmatter, string substitutions, dynamic context injection
- `.planning/phases/03-synthesis-and-confidence-scoring/03-CONTEXT.md` -- User decisions and locked constraints

### Secondary (MEDIUM confidence)
- `.planning/research/PITFALLS.md` -- Pitfall 5 (context window exhaustion) directly relevant to synthesis reading 14 files
- `.planning/phases/02-orchestration-skill/02-CONTEXT.md` -- File-based output decisions establishing persona-reviews/ pattern

### Tertiary (LOW confidence)
- Confidence boosting formula (min(99, max + 10*(n-1))) is a reasonable heuristic but not derived from any source -- planner can adjust

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - This is entirely Claude Code native (skills, Read tool, in-context processing). No novel technology.
- Architecture: HIGH - Pattern follows established skill conventions from Phase 2. Dual-invocation via shared reference.md is clean.
- Pitfalls: HIGH - Context exhaustion and deduplication quality are well-understood risks with clear mitigations.
- Deduplication approach: MEDIUM - LLM-based semantic grouping is the right approach given constraints, but quality depends on prompt instruction specificity.

**Research date:** 2026-03-22
**Valid until:** 2026-04-22 (stable -- Claude Code plugin conventions unlikely to change rapidly)
