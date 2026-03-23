# Persona Review Reference

Supporting reference for the `/persona:review` orchestration skill. Contains the persona roster, JSON output schema, and Gilfoyle mode block.

## Persona Roster

All 14 persona agents available for code review dispatch.

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

**Usage:** When dispatching via the Task tool, always use the **Agent Name** (kebab-case) as the agent identifier. Use **Display Name** only in user-facing output.

## JSON Output Schema

Each persona must return findings as a JSON object matching this schema. The orchestrator writes this JSON to `persona-reviews/{agent-name}.json`.

### Schema

```json
{
  "persona": "<agent-name>",
  "displayName": "<Display Name>",
  "gilfoyleMode": false,
  "target": "<review target path or 'staged changes'>",
  "findings": [
    {
      "severity": "<critical | warning | suggestion>",
      "confidence": 85,
      "file": "<file path>",
      "line": 42,
      "issue": "<concise description of the issue>",
      "recommendation": "<what to do instead>",
      "reasoning": "<why this matters -- in the persona's voice and perspective>"
    }
  ],
  "summary": "<N critical, N warnings, N suggestions>"
}
```

### Field Reference

| Field | Type | Required | Description |
|---|---|---|---|
| `persona` | string | yes | Agent name (kebab-case, matches agent file name) |
| `displayName` | string | yes | Human-readable persona name |
| `gilfoyleMode` | boolean | yes | Whether Gilfoyle mode was active for this review |
| `target` | string | yes | The review target (file path, directory, or "staged changes") |
| `findings` | array | yes | Array of finding objects (can be empty if no issues found) |
| `summary` | string | yes | Count string: "N critical, N warnings, N suggestions" |

### Finding Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `severity` | string | yes | One of: `critical`, `warning`, `suggestion` |
| `confidence` | integer | yes | 0-100 confidence score for this finding |
| `file` | string | yes | File path where the issue was found |
| `line` | integer | no | Line number (omit if not applicable) |
| `issue` | string | yes | Concise description of the issue |
| `recommendation` | string | yes | What to do instead |
| `reasoning` | string | yes | Why this matters -- written in the persona's voice |

### Severity Levels

- **critical** -- Bugs, security vulnerabilities, data loss risks, performance blockers. Must be fixed.
- **warning** -- Code smells, maintainability concerns, potential issues under certain conditions. Should be fixed.
- **suggestion** -- Style improvements, alternative approaches, nice-to-haves. Consider fixing.

### Complete Example

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
    },
    {
      "severity": "warning",
      "confidence": 70,
      "file": "src/auth.ts",
      "line": 15,
      "issue": "JWT secret loaded from process.env on every call",
      "recommendation": "Cache the secret at module level",
      "reasoning": "You're hitting process.env on every token verification. It's not catastrophically slow, but it's unnecessary work. Read it once, cache it. Blazingly simple."
    },
    {
      "severity": "suggestion",
      "confidence": 60,
      "file": "src/auth.ts",
      "issue": "No rate limiting on login endpoint",
      "recommendation": "Add rate limiting middleware",
      "reasoning": "Someone can just brute-force this all day. Not my primary concern as a performance guy, but even I know this is asking for trouble."
    }
  ],
  "summary": "1 critical, 1 warning, 1 suggestion"
}
```

## Gilfoyle Mode Block

When the `--gilfoyle` flag is active, append this block to each persona's task prompt:

```
## GILFOYLE MODE ACTIVE
Drop all diplomacy. Hold nothing back. Your strongest opinions on web development are cranked to maximum. Roast the implementation, not the architecture. Be brutal about bad patterns, missed opportunities, wrong abstractions, and anti-patterns -- but within the project's existing architecture.
```

When Gilfoyle mode is active, the persona should also set `"gilfoyleMode": true` in their JSON output.

## Synthesis Protocol

This protocol is referenced by both `/persona:review` (post-dispatch synthesis) and `/persona:parse-output` (standalone re-synthesis). Both invocations produce identical output.

### 1. Input Collection

1. Use Glob to find all `persona-reviews/*.json` files in the project root.
2. If `persona-reviews/` does not exist or is empty, output: "No persona reviews found. Run `/persona:review` first." and stop.
3. Read each JSON file using the Read tool.
4. If any JSON file is malformed (not valid JSON), skip it and note: "Skipped {filename}: invalid JSON"
5. Flatten all `findings` arrays from all persona JSON files into a single working list. Carry the `persona` and `displayName` from each file onto every finding so attribution is preserved.

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

**Example:** ThePrimeagen flags an issue at confidence 70, DHH flags the same at 75. Boosted confidence = min(99, 75 + 10) = 85. Attribution: "Flagged by: ThePrimeagen (70), DHH (75)"

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

### 7. Synthesis Output File

After presenting the synthesis in-context, also write the full synthesis output to `persona-reviews/SYNTHESIS.md` using the Write tool. This allows users to reference the synthesis later without re-running it.

The file should contain the same markdown output from Section 6 above, with an added header:

```markdown
<!-- Generated by /persona:review or /persona:parse-output -->
<!-- Re-run synthesis: /persona:parse-output -->

[full synthesis output from Section 6]
```
