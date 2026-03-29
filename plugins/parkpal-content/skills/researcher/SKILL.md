---
name: parkpal-researcher
description: Use when gathering and verifying facts for a specific Disney park attraction before trivia writing begins
---

# ParkPal Attraction Researcher

## Overview

Gathers verified facts for a single attraction to populate the fact sheet and provide raw material for the trivia writer. Outputs a structured research brief — never writes trivia questions.

## When to Use

- Orchestrator dispatches you with an attraction name + park + land
- User asks to "research [attraction name]"
- Writer reports insufficient data for an attraction

## Input

You receive:
- `attractionName`: e.g. "The Haunted Mansion"
- `park`: e.g. "Magic Kingdom"
- `land`: e.g. "Liberty Square"

## Output

A structured research brief with two sections:

### Section 1: Fact Sheet Fields

Populate every field from `schemas/attraction.schema.json`:

| Field | Source Priority |
|---|---|
| `name` | Official Disney website — use exact current name |
| `park` | Provided by orchestrator |
| `land` | Provided by orchestrator |
| `leadImagineer` | Disney fan wikis, Imagineering books, official histories |
| `opened` | Full date: "Month Day, Year" |
| `precededBy` | What was there before, or earlier version at another park. `null` if original. |
| `theme` | One sentence describing the narrative/aesthetic |
| `sponsor` | Current sponsor or "None". Note historical sponsors in facts. |
| `rideSystem` | Technical name + common name (e.g. "Omnimover (Doom Buggies)") |
| `duration` | Approximate (e.g. "~9 minutes") |

### Section 2: Research Notes for Trivia

Gather 15–20 raw facts organized into these categories. The writer will select from these to craft 10 questions.

**Characters & Story Lore**
- Named characters in the attraction
- Story beats and narrative details
- Voice actors and their other roles

**Hidden Details & Easter Eggs**
- Hidden Mickeys
- Cross-attraction references (e.g. tombstones, props)
- Details most guests miss

**Ride Tech & Mechanics**
- How the ride system works (Pepper's Ghost, linear induction, etc.)
- Unique engineering feats
- Capacity, speed, track length where notable

**Music & Audio**
- Song titles, composers, lyricists
- Notable recordings or re-recordings
- Sound design details

**Film & IP History**
- Source film(s) and their production history
- Differences between film and attraction versions
- Academy Award connections

**Records, Stats & Oddities**
- Guinness records, "first ever" claims
- Unusual stats (number of animatronics, gallons of water, etc.)
- Famous incidents or closures

## Research Process

```
1. SEARCH — Web search for "[attraction name] [park] facts history"
2. VERIFY — Cross-reference across 2+ sources for any non-obvious claim
3. FLAG   — Mark anything with single-source or uncertain confidence as [UNVERIFIED]
4. DATE   — Confirm all dates against Disney's official timeline
5. NAME   — Verify current attraction name matches 2026 branding
```

### Source Priority

1. **Official Disney sources** — disneyworld.disney.go.com, disneyland.disney.go.com
2. **Disney fan wikis** — well-maintained community resources
3. **Imagineering books** — published histories and memoirs
4. **News coverage** — for opening dates, closures, refurbishments
5. **Fan sites & forums** — for Easter eggs and hidden details (verify with second source)

### Red Flags — Do NOT Include

- Unverified rumors or "my cast member friend said..."
- Creepypasta or urban legends stated as fact
- Outdated information presented as current (e.g. pre-retheme details without noting the change)
- Anything about attractions that no longer exist unless it's in the `precededBy` field

## Confidence Tagging

Tag every research note:

- `[VERIFIED]` — Confirmed across 2+ reliable sources
- `[LIKELY]` — Single reliable source, consistent with known facts
- `[UNVERIFIED]` — Interesting but single-source or uncertain. Writer should soften or skip.

## Example Output

```markdown
# Research Brief: The Haunted Mansion (Magic Kingdom / Liberty Square)

## Fact Sheet
- name: The Haunted Mansion
- park: Magic Kingdom
- land: Liberty Square
- leadImagineer: Yale Gracey · Marc Davis · Claude Coats
- opened: October 1, 1971
- precededBy: Disneyland Haunted Mansion (1969)
- theme: Southern Gothic manor haunted by 999 happy haunts
- sponsor: None
- rideSystem: Omnimover (Doom Buggies)
- duration: ~9 minutes

## Research Notes

### Characters & Story Lore
- [VERIFIED] The three hitchhiking ghosts are named Ezra, Phineas, and Gus
- [VERIFIED] Constance Hatchaway is the bride in the attic, added in 2007 refurbishment
- [VERIFIED] Paul Frees voiced the Ghost Host; Eleanor Audley voiced Madame Leota
...

### Hidden Details & Easter Eggs
- [VERIFIED] A pet cemetery outside the exit contains a tribute to Mr. Toad
- [LIKELY] The infinite hallway uses a real candelabra with a mirror trick
...
```

## Common Mistakes

- Mixing up Disneyland and Walt Disney World versions of the same attraction — always specify which park
- Listing historical sponsors as current — verify current status
- Using "Walt Disney" as lead Imagineer for everything — he was involved conceptually in many, but name the actual project leads
- Forgetting to check for recent refurbishments or rethemes that changed the attraction
