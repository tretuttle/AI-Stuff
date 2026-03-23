# Synthesis Engine

After all personas complete their reviews, the synthesis engine merges their findings into a single report.

## Deduplication

When multiple personas flag the same issue in the same file, those findings are grouped into a single entry using semantic similarity (not exact string matching).

- Most detailed description becomes the primary issue text
- Unique recommendations from all personas are merged
- Every persona is attributed: "Flagged by: ThePrimeagen (85), DHH (75)"
- Highest severity from any persona wins
- Each persona's original reasoning is preserved verbatim

## Confidence Scoring

Every finding carries a 0-100 confidence score. When multiple personas independently flag the same issue, confidence is boosted:

```
boosted = min(99, max_individual + 10 * (persona_count - 1))
```

| Scenario | Boost | Result |
|----------|-------|--------|
| 1 persona at 70 | None | 70 |
| 2 personas (70, 75) | +10 | 85 |
| 3 personas (70, 75, 80) | +20 | 99 (capped) |

Confidence never reaches 100 — that's reserved for human certainty.

## Disagreement Detection

The engine actively surfaces conflicts between personas:

1. **Severity conflicts** — Same issue, different severity assignments
2. **Approach conflicts** — One persona recommends X, another warns against X

Disagreements appear in a dedicated section with both positions and reasoning. They're not averaged out — they're the most valuable part of a multi-perspective review.

## Threshold Filtering

```bash
/persona:review src/ --min-confidence 70   # Strict
/persona:review src/ --min-confidence 0    # Everything
/persona:review src/                       # Default: 30
```

**Critical-severity findings are never filtered** regardless of confidence. A low-confidence critical finding still appears because even uncertain security vulnerabilities deserve attention.

---

## Output Format

### Per-Persona JSON

Each persona writes to `persona-reviews/{agent-name}.json`:

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
      "reasoning": "This is a skill issue. You're blocking the entire event loop for password hashing."
    }
  ],
  "summary": "1 critical, 1 warning, 1 suggestion"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `severity` | string | `critical`, `warning`, or `suggestion` |
| `confidence` | integer | 0-100 |
| `file` | string | File path |
| `line` | integer | Line number (optional) |
| `issue` | string | What's wrong |
| `recommendation` | string | What to do instead |
| `reasoning` | string | Why it matters — in the persona's voice |

### Severity Levels

| Level | Meaning |
|-------|---------|
| **critical** | Must fix. Bugs, security vulnerabilities, data loss risks, performance blockers. |
| **warning** | Should fix. Code smells, maintainability concerns, potential issues. |
| **suggestion** | Consider fixing. Style improvements, alternative approaches, nice-to-haves. |

### Synthesized Review

Saved to `persona-reviews/SYNTHESIS.md`:

```markdown
## Persona Review Synthesis

**5 personas reviewed `src/auth.ts`**
**Summary: 2 critical, 4 warnings, 7 suggestions**
**Confidence threshold: 30**

### Critical (2)

#### 1. Synchronous bcrypt blocks event loop
- **Confidence:** 85 (boosted — flagged by 2 personas)
- **File:** src/auth.ts:42
- **Flagged by:** ThePrimeagen (85), DHH (75)
- **Reasoning:**
  - *ThePrimeagen:* "This is a skill issue..."
  - *DHH:* "Synchronous crypto in a request handler. Classic."

### Disagreements (1)

#### 1. [src/auth.ts] JWT vs session-based auth
- **ThePrimeagen** (warning, 70): "JWT is fine here, just cache the secret"
- **DHH** (suggestion, 65): "Sessions with httpOnly cookies. JWT is almost always wrong."
```
