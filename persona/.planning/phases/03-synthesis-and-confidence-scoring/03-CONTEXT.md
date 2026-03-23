# Phase 3: Synthesis and Confidence Scoring - Context

**Gathered:** 2026-03-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver a synthesis system that reads persona JSON output files from `persona-reviews/`, merges duplicate findings, ranks by severity and confidence, surfaces cross-persona disagreements, and presents a unified review. Available both as automatic post-review step in `/persona:review` and as standalone `/persona:parse-output` skill.

</domain>

<decisions>
## Implementation Decisions

### Synthesis Invocation
- **D-01:** Synthesis runs automatically at the end of `/persona:review` after all personas complete — integrated into the orchestration flow.
- **D-02:** Also available as a standalone `/persona:parse-output` skill for re-running synthesis on existing persona-reviews files without re-dispatching personas.
- **D-03:** Both invocations produce identical output — the standalone skill just skips the dispatch step.

### Deduplication Logic
- **D-04:** Deduplication by file + issue similarity — findings about the same file with similar issue descriptions are grouped together, not exact string match.
- **D-05:** When multiple personas flag the same issue, it appears once in the output, attributed to all originating personas (e.g., "Flagged by: ThePrimeagen, DHH, Theo Browne").
- **D-06:** Confidence boosting: findings flagged by multiple personas get their confidence score boosted (demonstrates cross-persona agreement).

### Disagreement Surfacing
- **D-07:** Cross-persona disagreements are shown in a dedicated "Disagreements" section with both sides and their reasoning.
- **D-08:** Disagreements are detected when personas assign conflicting severity to the same file/issue area, or when one persona recommends an approach another explicitly cautions against.

### Output Format
- **D-09:** Severity-grouped markdown: critical findings first, then warnings, then suggestions.
- **D-10:** Summary header with finding counts (e.g., "3 critical, 7 warnings, 12 suggestions from 14 personas").
- **D-11:** Each finding shows: severity, confidence score, file, issue, recommendation, reasoning, and persona attribution.
- **D-12:** Confidence threshold filtering: findings below a configurable threshold (default: 30) are hidden. User can adjust via `--min-confidence N` flag.

### Claude's Discretion
- Exact similarity algorithm for deduplication (fuzzy string matching, semantic comparison, or simpler heuristic)
- How to detect disagreements algorithmically from JSON findings
- Whether to store synthesized output as a file or only display in-context
- How to structure the standalone parse-output skill (minimal wrapper around synthesis logic)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Plugin System
- `research/03-skills.md` — Skills frontmatter, user-invocable vs internal skills
- `research/02-plugins-reference.md` — Plugin reference

### Orchestration (Phase 2)
- `skills/review/SKILL.md` — Current orchestration skill that synthesis integrates with
- `skills/review/reference.md` — JSON output schema that synthesis consumes, persona roster

### Phase 2 Context
- `.planning/phases/02-orchestration-skill/02-CONTEXT.md` — File-based output decisions (D-06, D-07, D-08)

### Pitfalls
- `.planning/research/PITFALLS.md` — Context window exhaustion (Pitfall 5), relevant for synthesis reading 14 JSON files

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `skills/review/reference.md` — JSON output schema defining the structure synthesis will consume
- `skills/review/SKILL.md` — Orchestration skill that synthesis integrates with (post-dispatch step)
- `persona-reviews/` — Directory where persona JSON output lives (gitignored)

### Established Patterns
- Skills use `$ARGUMENTS` for user input
- Plugin skills are namespaced: `/persona:parse-output`
- `user-invocable: false` for internal-only skills

### Integration Points
- Synthesis reads from `persona-reviews/{persona-name}.json` (created by Phase 2 orchestrator)
- Synthesis output is presented in-context after `/persona:review` completes
- Standalone `/persona:parse-output` reads same files independently

</code_context>

<specifics>
## Specific Ideas

- The parse-output skill should be marked `user-invocable: true` so users can re-synthesize without re-running reviews
- Confidence threshold default of 30 is low enough to show most findings but filters out very uncertain observations
- The disagreement section adds unique value — it's where the multi-persona approach proves its worth

</specifics>

<deferred>
## Deferred Ideas

- **Chat with persona:** After seeing synthesis results, user can invoke a specific persona for follow-up conversation about their findings (e.g., ask DHH "why is this critical?"). This is a new interactive capability beyond synthesis — belongs in a future phase or Phase 6 enhancement.
- **Output format options:** JSON and concise summary formats (from v2 requirements OUTF-01) — deferred to v2.

</deferred>

---

*Phase: 03-synthesis-and-confidence-scoring*
*Context gathered: 2026-03-22*
