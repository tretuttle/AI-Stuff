# Persona Review Reference

Supporting reference for the `/persona:review` orchestration skill. Contains the persona roster, review output format, and synthesis protocol.

## Persona Roster (Documentation Reference)

The built-in persona agents shipped with this plugin. This table is a documentation reference for display-name-to-agent-name mapping (used by `--only` flag resolution). **Dispatch does not read from this table** -- agents are discovered dynamically from the `agents/` directory at runtime.

| Display Name | Agent Name | File |
|---|---|---|
| ThePrimeagen | theprimeagen | agents/theprimeagen.md |
| DHH | dhh | agents/dhh.md |
| Chris Coyier | chris-coyier | agents/chris-coyier.md |
| Dan Abramov | dan-abramov | agents/dan-abramov.md |
| Evan You | evan-you | agents/evan-you.md |
| Kent C. Dodds | kent-c-dodds | agents/kent-c-dodds.md |
| Lee Robinson | lee-robinson | agents/lee-robinson.md |
| Matt Mullenweg | matt-mullenweg | agents/matt-mullenweg.md |
| Matt Pocock | matt-pocock | agents/matt-pocock.md |
| Rich Harris | rich-harris | agents/rich-harris.md |
| Scott Tolinski | scott-tolinski | agents/scott-tolinski.md |
| Tanner Linsley | tanner-linsley | agents/tanner-linsley.md |
| Theo Browne | theo-browne | agents/theo-browne.md |
| Wes Bos | wes-bos | agents/wes-bos.md |

**Adding custom personas:** Drop a new `.md` file in the `agents/` directory following the format in `agents/template.md`. The persona will be automatically discovered on the next `/persona:review` run -- no need to edit this table. Add an entry here only if you want `--only` to support a friendly display name for the custom persona.

## Dispatch Instructions

When the review skill dispatches a persona subagent, it injects these operational instructions alongside the persona's own identity. These do NOT live in the persona files -- they're injected at dispatch time by the orchestrator.

### Review Output Format

Structure your findings as follows. Stay in character -- your voice and perspective ARE the value.

```markdown
## [Persona Name] Review

### Finding 1
- **Severity:** critical | warning | suggestion
- **Confidence:** [0-100]
- **File:** [path]
- **Issue:** [what you noticed]
- **Recommendation:** [what you would do instead]
- **Reasoning:** [why this matters -- in your voice, from your perspective]
```

### Severity Levels

- **critical** -- Bugs, security vulnerabilities, data loss risks, performance blockers. Must be fixed.
- **warning** -- Code smells, maintainability concerns, potential issues under certain conditions. Should be fixed.
- **suggestion** -- Style improvements, alternative approaches, nice-to-haves. Consider fixing.

### Bash Safety

You have access to Bash for gathering information only. Use it for: `git log`, `git diff`, `find`, `wc`, `du`, checking file sizes, running read-only commands. NEVER use Bash to modify files, delete files, create files, or run destructive git commands. You are a reviewer, not an editor.

### Memory Curation

You have persistent project memory at `.claude/agent-memory/{your-agent-name}/MEMORY.md`. The first 200 lines are auto-loaded into your context each session.

**After each review**, update your MEMORY.md with project-specific insights:

Organize memory into these sections (stay under 190 lines total):
- **Active Patterns** (max 60 lines) -- recurring code patterns in this project
- **Known Issues** (max 40 lines) -- issues seen across reviews; remove when fixed
- **Style Conventions** (max 40 lines) -- project-specific style choices
- **Architecture Notes** (max 30 lines) -- key architectural decisions and constraints
- **Curation Log** (max 20 lines) -- what you changed and when

Rules:
- Before adding an insight, check if it contradicts or supersedes an existing entry. If so, REPLACE the old entry -- do not append.
- Keep each entry to 1-3 concise lines.
- If a pattern has not been reinforced in recent reviews, consider pruning it.
- Never exceed 190 lines total. If you must add and are at the limit, remove the least relevant entry first.
- Focus on insights that will change your FUTURE reviews, not summaries of past reviews.

## Synthesis Protocol

After all persona subagents complete their reviews, the orchestrator synthesizes findings into a unified report.

### 1. Input Collection

Collect the findings from all persona subagent responses. Each persona returns its findings in the Review Output Format above.

### 2. Deduplication

Group findings that describe the SAME issue in the SAME file. Two findings are "the same issue" if:
- They reference the same file (exact path match)
- They describe semantically similar problems (e.g., "missing error handling" and "no try-catch around async call" about the same function)

Do NOT group findings that happen to be in the same file but describe different issues.
When in doubt, keep findings separate rather than merging them.

For each deduplicated group:
- **Primary description:** Use the most detailed `issue` description from any contributing persona as the primary issue text.
- **Combined recommendations:** Merge unique `recommendation` values from all contributing personas. Do not repeat duplicates.
- **Attribution:** List all contributing personas with their individual confidence scores: "Flagged by: ThePrimeagen (85), DHH (75)"
- **Severity:** Use the highest severity assigned by any persona in the group (critical > warning > suggestion).
- **Preserve reasoning:** Include each persona's original `reasoning` verbatim. Do NOT merge reasoning into a bland average -- the distinct voices are the value of multi-persona review.

### 3. Confidence Boosting

After deduplication, apply confidence boosting to findings flagged by multiple personas.

**Formula:** `boosted_confidence = min(99, max_individual_confidence + (10 * (persona_count - 1)))`

- Single persona: original confidence (no boost)
- Two personas agree: +10 boost to the highest individual score
- Three personas agree: +20 boost
- Capped at 99 (never assign 100 automatically)

Show the boosted score as the finding's primary confidence. Include individual scores in the persona attribution line.

### 4. Disagreement Detection

After deduplication, scan findings for cross-persona disagreements. Two types of disagreement exist:

1. **Severity conflict:** Two or more personas flag the same file + issue area but assign different severities (e.g., one says `critical`, another says `suggestion`).
2. **Approach conflict:** One persona recommends approach X for a file, while another persona explicitly cautions against approach X for the same file.

Each disagreement appears in the dedicated `### Disagreements` section of the output. For each disagreement, show:
- The file and issue area
- Each persona's position with their severity, confidence, and a direct quote of their reasoning

Disagreements are separate from the main findings list. A finding involved in a disagreement still appears in its severity group (using the highest severity from the group), AND the disagreement is surfaced separately.

### 5. Confidence Threshold Filtering

Parse `--min-confidence N` from skill arguments:
- If present: use the specified integer as the minimum confidence threshold
- If absent: default to 30

After deduplication and confidence boosting, apply the threshold:
- **NEVER filter critical-severity findings regardless of confidence.** A low-confidence critical finding is still shown, with its confidence score visible so the user can judge.
- Filter `warning` and `suggestion` findings whose boosted confidence is below the threshold.
- Track the count of filtered findings.

At the bottom of the output, show: "{N} findings hidden below confidence threshold of {threshold}. Use `--min-confidence 0` to see all."

If no findings were hidden, omit this line.

### 6. Output Format

Present the synthesized review using this exact template:

```markdown
## Persona Review Synthesis

**{N} personas reviewed `{target}`**
**Summary: {N} critical, {N} warnings, {N} suggestions** (after deduplication)
**Confidence threshold: {threshold}** ({N} findings hidden)

---

### Critical ({count})

#### 1. {issue title}
- **Confidence:** {score} {if boosted: "(boosted -- flagged by N personas)"}
- **File:** {file}:{line}
- **Issue:** {description}
- **Recommendation:** {combined recommendations}
- **Flagged by:** {Persona1} ({score1}), {Persona2} ({score2})
- **Reasoning:**
  - *{Persona1}:* "{reasoning}"
  - *{Persona2}:* "{reasoning}"

### Warnings ({count})
[same format as Critical]

### Suggestions ({count})
[same format as Critical]

---

### Disagreements ({count})

#### 1. [{file}] {issue area}
- **{Persona1}** ({severity}, confidence {score}): "{reasoning}"
- **{Persona2}** ({severity}, confidence {score}): "{reasoning}"

---

*{N} findings hidden below confidence threshold of {threshold}. Use `--min-confidence 0` to see all.*
```

**Formatting rules:**
- Number findings within each severity section (1, 2, 3...).
- Sort findings within each severity group by confidence descending (highest confidence first).
- If a finding has no line number, show only the file path (no colon suffix).
- If no disagreements exist, omit the Disagreements section entirely.
- If no findings were hidden, omit the footer line about hidden findings.
- The `{target}` in the header is the review target (file path, directory, or "staged changes").
- Counts in the Summary line reflect post-deduplication, post-filtering totals.
