---
name: parkpal-writer
description: Use when writing trivia questions and design facts from a verified research brief for a specific Disney park attraction
---

# ParkPal Trivia Writer

## Overview

Transforms a research brief into exactly 10 trivia questions and 5–8 design facts for a single attraction. Enforces the trivia firewall and difficulty curve. Never researches — only writes from provided research.

## When to Use

- Orchestrator passes you a completed research brief
- Reviewer rejects trivia and returns feedback for rewrite

## Input

A research brief from the researcher subagent containing:
- Fact sheet fields (populated)
- 15–20 categorized research notes with confidence tags

## Output

A complete attraction object matching `schemas/attraction.schema.json`.

## The Trivia Firewall — ABSOLUTE RULE

**NEVER write a trivia question whose answer is any of these fact sheet fields:**
- Park name
- Land name
- Lead Imagineer(s)
- Opening year or date
- Theme description
- Preceded by
- Sponsor
- Ride system name
- Duration

**Self-check before finalizing each question:** Could the guest answer this by reading the fact sheet card? If yes → DELETE and replace.

## Difficulty Curve

| Tier | Questions | Target Guest | Style |
|---|---|---|---|
| 🟢 Easy (Q1–Q3) | 3 | Casual visitor, rode it once | "Everyone knows this if they paid attention on the ride" |
| 🟠 Medium (Q4–Q7) | 4 | Return visitor, Disney fan | "You'd know this if you watched a YouTube video or read a blog" |
| 🔴 Hard (Q8–Q10) | 3 | Disney parks nerd | "Deep Imagineering lore, obscure film history, technical secrets" |

### Easy Questions Should...
- Reference something visible/audible during the ride
- Use character names, song titles, or iconic moments
- Have one obviously correct answer

### Medium Questions Should...
- Require behind-the-scenes knowledge
- Connect the attraction to film history or other attractions
- Have plausible distractors

### Hard Questions Should...
- Dive into Imagineering techniques, engineering, or production history
- Reference obscure cross-attraction Easter eggs
- Challenge even dedicated Disney fans
- Surprise the guest with the answer

## Writing Trivia Questions

### Answer Choices

- Always 4 choices: A, B, C, D
- Prefix format: `"A) Grim Grinning Ghosts"`
- Correct answer should NOT always be A or B — distribute across A/B/C/D
- Distractors should be plausible, not absurd
- Never use "All of the above" or "None of the above"
- Keep all 4 choices roughly the same length

### Fun Facts

Every question gets a `funFact` — a 1–2 sentence reward shown regardless of whether the guest answered correctly.

- Should add context the question itself didn't cover
- Should feel like "oh, cool!" not "here's a Wikipedia excerpt"
- Can connect to other attractions, films, or Imagineering history
- Never repeat information from the question or answer choices

### Confidence Handling

- `[VERIFIED]` research notes → use freely
- `[LIKELY]` notes → use but soften language ("reportedly", "is said to")
- `[UNVERIFIED]` notes → skip entirely for questions. May use in funFacts with hedging.

## Writing Design Facts

Select 5–8 of the most interesting research notes for the `facts` array. Prioritize:

1. Imagineering techniques and design decisions
2. Unique engineering or technical achievements
3. Historical context that shaped the attraction
4. Connections to Walt Disney or notable Imagineers
5. Surprising stats or records

Write each as a complete, self-contained sentence. Not a question — a declarative fact.

## Example Question

```json
{
  "difficulty": "medium",
  "question": "The ballroom ghost effect in The Haunted Mansion uses what classic theatrical illusion technique?",
  "answers": [
    "A) Pepper's Ghost",
    "B) Rear projection",
    "C) Holographic display",
    "D) Scrim lighting"
  ],
  "correct": "A",
  "funFact": "The technique dates back to 1862 London theater and uses angled glass to reflect animatronic figures hidden below the track into the scene — guests see 'ghosts' dancing in a room they can't physically enter."
}
```

## Pre-Submission Checklist

Before passing to reviewer:

- [ ] Exactly 10 questions (3 easy, 4 medium, 3 hard)
- [ ] No question answer overlaps with fact sheet fields (FIREWALL)
- [ ] Correct answers distributed across A/B/C/D (not all the same letter)
- [ ] Every question has a funFact
- [ ] No [UNVERIFIED] claims in questions (only hedged funFacts)
- [ ] All 4 answer choices per question are plausible and similar length
- [ ] 5–8 design facts in the `facts` array
- [ ] Complete JSON object matching schema

## Common Mistakes

- Writing a question about when the ride opened — FIREWALL VIOLATION
- Making all correct answers "A" — distribute evenly
- Fun facts that just restate the answer — add NEW information
- Distractors that are obviously wrong — make them plausible
- Questions that only a cast member could answer — hard should be hard, not impossible
- Skipping the self-check — always re-read each question against the firewall list
