---
name: parkpal-reviewer
description: Use when validating a completed attraction object against the schema, trivia rules, and accuracy standards before it enters the final dataset
---

# ParkPal Content Reviewer

## Overview

Quality gate between the writer and the formatter. Validates every attraction object against the schema, the trivia firewall, difficulty distribution, and factual accuracy. Returns APPROVED or REJECTED with specific feedback.

## When to Use

- Writer submits a completed attraction object
- After a rewrite triggered by a previous rejection

## Input

A complete attraction JSON object from the writer.

## Output

One of:

**APPROVED** — Object passes all checks. Forward to formatter.

**REJECTED** — Object fails one or more checks. Return to writer with:
- Which checks failed
- Specific items that need fixing
- Suggested corrections where possible

## Review Checklist

Run every check. Stop at first REJECT-worthy failure only if it's structural (schema violation). For content issues, collect all problems and return them together.

### 1. Schema Validation

```
□ All required fields present
□ park is one of the 6 valid enum values
□ opened is in "Month Day, Year" format
□ precededBy is string or null
□ facts array has 5–8 items
□ trivia array has exactly 10 items
□ Each trivia item has: difficulty, question, answers (4), correct (A/B/C/D), funFact
□ Difficulty values are only "easy", "medium", or "hard"
□ correct values are only "A", "B", "C", or "D"
□ Answer strings start with "A) ", "B) ", "C) ", "D) "
```

**REJECT if any schema field is missing or malformed.**

### 2. Trivia Firewall

For each of the 10 questions, check: could the answer be found on the fact sheet?

```
□ No question asks about the park name
□ No question asks about the land name
□ No question asks about lead Imagineer(s)
□ No question asks about opening year or date
□ No question asks about the theme
□ No question asks about what preceded the attraction
□ No question asks about the sponsor
□ No question asks about the ride system name (as a direct answer)
□ No question asks about the duration
```

**How to detect violations:**
- Read the `correct` answer letter, find the matching choice
- Compare that answer to every fact sheet field value
- If the correct answer IS a fact sheet value → FIREWALL VIOLATION

**Also check indirect violations:**
- "In what year did this attraction welcome its first guests?" → opening year, even if phrased differently
- "Who designed this attraction?" → lead Imagineer
- "What land is this in?" → land name

**REJECT if any firewall violation found. Cite the specific question and which field it violates.**

### 3. Difficulty Distribution

```
□ Q1–Q3 are difficulty: "easy"
□ Q4–Q7 are difficulty: "medium"
□ Q8–Q10 are difficulty: "hard"
□ Easy questions reference ride-visible/ride-audible details
□ Hard questions require behind-the-scenes or historical knowledge
```

**REJECT if distribution is wrong or difficulty labels don't match content.**

### 4. Answer Distribution

```
□ Correct answers are not all the same letter
□ No more than 3 correct answers share the same letter
□ All 4 choices per question are plausible (no joke answers)
□ All 4 choices per question are roughly the same length
```

**REJECT if all correct answers are the same letter. WARN (but approve) for minor imbalance.**

### 5. Fun Fact Quality

```
□ Every question has a non-empty funFact
□ No funFact merely restates the question or correct answer
□ Fun facts add genuinely new information
□ No [UNVERIFIED] claims stated as fact (hedging is acceptable)
```

**REJECT if funFact is missing or is just a restatement.**

### 6. Factual Accuracy Spot Check

Pick 3 claims at random from facts + trivia. Verify via web search:

```
□ Dates mentioned in trivia match known records
□ Names (characters, Imagineers, voice actors) are spelled correctly
□ Technical claims (ride speeds, animatronic counts) are in the right ballpark
□ Current branding matches 2026 reality (no outdated names)
```

**REJECT if a factual error is found. WARN if spelling is off but the claim is correct.**

### 7. Tone & Voice

```
□ Questions read naturally — not like a textbook
□ Fun facts feel conversational — "oh, cool!" not "Wikipedia says..."
□ No condescending language ("Did you know that...")
□ Difficulty feels appropriate for the target guest persona
```

**WARN only — never reject purely on tone unless it's egregious.**

## Rejection Format

```markdown
## REJECTED: {Attraction Name}

### Failures
1. **FIREWALL VIOLATION** — Q3 asks about opening year ("When did guests first board Doom Buggies?"). The correct answer "1971" matches the fact sheet `opened` field.
2. **SCHEMA** — `precededBy` is missing (should be string or null).
3. **ACCURACY** — Q7 funFact states "Paul Frees also voiced Ludwig Von Drake" — verify this claim.

### Suggested Fixes
1. Replace Q3 with a question about the pet cemetery Easter eggs or the stretching room portraits.
2. Add `"precededBy": "Disneyland Haunted Mansion (1969)"` to the object.
3. Web search Paul Frees filmography to confirm or correct the Ludwig Von Drake claim.
```

## Approval Format

```markdown
## APPROVED: {Attraction Name}

All checks passed. 10/10 trivia, schema valid, firewall clean.

### Notes (optional)
- Q8 is borderline medium/hard — consider if this is intentional
- funFact on Q2 could be punchier
```

## Common Mistakes

- Approving firewall violations because the question is "interesting" — the firewall is absolute
- Rejecting on tone alone — tone is a WARN, not a REJECT
- Not spot-checking facts — always verify at least 3 claims
- Accepting "approximately" dates when the exact date is known — if research says "October 1, 1971", the fact sheet should too
