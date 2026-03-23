---
name: parse-output
description: "Synthesize existing persona review output into a unified, deduplicated review with confidence scoring"
argument-hint: "[--min-confidence N]"
---

# Synthesize Persona Reviews

Read all persona review JSON files from `persona-reviews/` and produce a unified, deduplicated review following the Synthesis Protocol.

## Arguments

Parse `$ARGUMENTS` for:
- `--min-confidence N`: Minimum confidence threshold for filtering findings (default: 30). Critical-severity findings are never filtered.

## Steps

1. Check that `persona-reviews/` directory exists at the project root
2. Use Glob to find all `persona-reviews/*.json` files
3. If no JSON files found, tell the user: "No persona reviews found. Run `/persona:review` first."
4. Read each JSON file using the Read tool
5. Follow the **Synthesis Protocol** in `skills/review/reference.md` to:
   - Deduplicate findings by file + semantic similarity
   - Apply confidence boosting for multi-persona agreement
   - Detect and surface cross-persona disagreements
   - Filter findings below the confidence threshold (except critical)
   - Format output as severity-grouped markdown
6. Present the synthesized review to the user
7. Write the synthesis output to `persona-reviews/SYNTHESIS.md`
