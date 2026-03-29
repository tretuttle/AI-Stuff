---
name: parkpal-formatter
description: Use when outputting approved attraction objects as JSON seed files for Convex and DOCX documents for human review
---

# ParkPal Content Formatter

## Overview

Takes approved attraction objects and produces two parallel outputs: a JSON file that seeds Convex and a DOCX file for human review and fact-checking. Handles incremental updates — appending to existing files as attractions are completed.

## When to Use

- Orchestrator signals a land is complete and ready for output
- User requests a progress export mid-park
- All attractions for a park are approved and need final packaging

## Input

An array of approved attraction objects matching `schemas/attraction.schema.json`.

## Outputs

### JSON — `data/json/{park_slug}.json`

A single JSON file per park containing an array of all attraction objects, ordered by land (in park walking order) then by attraction name within each land.

```json
[
  { "park": "Magic Kingdom", "land": "Main Street, U.S.A.", "name": "Walt Disney World Railroad", ... },
  { "park": "Magic Kingdom", "land": "Main Street, U.S.A.", "name": "Main Street Vehicles", ... },
  { "park": "Magic Kingdom", "land": "Adventureland", "name": "Jungle Cruise", ... },
  ...
]
```

**Park slugs:**
- `magic_kingdom`
- `epcot`
- `hollywood_studios`
- `animal_kingdom`
- `disneyland`
- `california_adventure`

**Land ordering (Magic Kingdom walking order):**
1. Main Street, U.S.A.
2. Adventureland
3. Frontierland
4. Liberty Square
5. Fantasyland
6. Tomorrowland

### DOCX — `data/docx/{Park_Name}.docx`

**Use the docx skill at `/mnt/skills/public/docx/SKILL.md` for document generation.**

One Word document per park containing all attractions organized by land.

#### Document Structure

```
Title Page: "{Park Name} — Attraction Guide"
Table of Contents (by land)

For each land:
  Land Header (styled as Heading 1)
  
  For each attraction in the land:
    Attraction Name (Heading 2)
    
    Fact Sheet Table:
    ┌──────────────┬─────────────────────────────┐
    │ Park         │ Magic Kingdom               │
    │ Land         │ Liberty Square               │
    │ Lead Imagineer│ Yale Gracey · Marc Davis    │
    │ Opened       │ October 1, 1971             │
    │ Preceded By  │ Disneyland Haunted Mansion   │
    │ Theme        │ Southern Gothic manor...     │
    │ Sponsor      │ None                        │
    │ Ride System  │ Omnimover (Doom Buggies)    │
    │ Duration     │ ~9 minutes                  │
    └──────────────┴─────────────────────────────┘
    
    Imagineering & Design Notes (Heading 3)
    • Bullet point for each fact
    
    Trivia Questions (Heading 3)
    
    🟢 EASY
    Q1. [question]
        A) ...  B) ...  C) ...  D) ...
        💡 Fun Fact: ...
    
    🟠 MEDIUM
    Q4. [question]
        ...
    
    🔴 HARD
    Q8. [question]
        ...
    
    Answer Key:
    ┌────┬─────────┐
    │ Q1 │ A       │
    │ Q2 │ C       │
    │ ...│ ...     │
    └────┴─────────┘
    
    Page Break
```

## Incremental Updates

### Appending to existing JSON

```javascript
// Read existing file
const existing = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
// Append new attractions
const updated = [...existing, ...newAttractions];
// Re-sort by land order then name
const sorted = sortByLandOrder(updated, parkSlug);
// Write back
fs.writeFileSync(jsonPath, JSON.stringify(sorted, null, 2));
```

### Appending to existing DOCX

For DOCX, regenerate the full document from the JSON source each time. The JSON file is the source of truth — the DOCX is always a full rebuild from JSON.

## Validation Before Output

Before writing either file:

```
□ Every object in the array passes schema validation
□ No duplicate attraction names within the park
□ Land names are consistent (no "Adventureland" vs "Adventure Land" mismatches)
□ Attractions are sorted by land order, then alphabetically within land
□ JSON is valid (parseable)
□ DOCX generates without errors
```

## Progress Export

If the user requests output before a park is complete:

- JSON: Output what's done so far with a `_meta` comment noting completeness
- DOCX: Generate with a "DRAFT — {N} of {M} attractions" watermark on the title page
- Report which lands/attractions are still pending

## Common Mistakes

- Not regenerating DOCX from JSON — always rebuild from the JSON source
- Inconsistent land names between attractions — normalize before output
- Forgetting the page break between attractions in DOCX — each attraction starts fresh
- Not sorting by land walking order — guests expect geographic flow
