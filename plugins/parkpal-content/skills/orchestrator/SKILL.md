---
name: parkpal-orchestrator
description: Use when starting content generation for a new park, resuming interrupted work, or managing the overall attraction content pipeline across parks and lands
---

# ParkPal Content Orchestrator

## Overview

Coordinates the full content pipeline for Disney park attractions. Breaks work into park → land → attraction units and dispatches subagents for each phase: research, write, review, format.

## When to Use

- User says "let's do [park name]" or "start [park]"
- User says "continue" or "resume" or "what's left"
- User says "do all of [land]" or "next land"
- Beginning of any content generation session

## Workflow

```
1. INVENTORY — Build the attraction roster for the target park
2. TRACK    — Check data/json/{park_slug}.json for already-completed attractions
3. PLAN     — Create a plan in docs/plans/ listing remaining attractions by land
4. DISPATCH — For each attraction, run the pipeline:
               research → write → review (loop if rejected) → collect
5. FORMAT   — Once a land is complete, call formatter to output JSON + DOCX
6. REPORT   — Show progress summary after each land
```

### Step 1: Build Attraction Roster

For the target park, enumerate every current attraction (as of 2026) organized by land. Include:
- Rides (dark rides, coasters, flat rides, water rides)
- Shows (theater, 4D, walk-through)
- Interactive experiences (shooting galleries, scavenger hunts)
- Transport attractions (railroad, boats, PeopleMover)

Exclude:
- Meet & greets (character dining, photo ops)
- Shops and restaurants
- Seasonal overlays (treat as notes on the base attraction)
- Closed/demolished attractions (unless recently replaced — then note in `precededBy`)

### Step 2: Check Progress

```bash
# Check what's already been written
cat data/json/{park_slug}.json 2>/dev/null | jq '.[].name' 2>/dev/null
```

Compare against the full roster. Report: "X of Y attractions complete. Remaining: [list]"

### Step 3: Create Plan

Save to `docs/plans/YYYY-MM-DD-{park-slug}.md`:

```markdown
# {Park Name} Content Plan

**Status:** {X}/{Y} complete
**Remaining by land:**

## {Land Name}
- [ ] Attraction 1
- [ ] Attraction 2

## {Land Name}
- [ ] Attraction 3
```

### Step 4: Dispatch Pipeline

For each attraction, in land order:

1. **Research** — Dispatch researcher subagent with attraction name + park + land
2. **Write** — Pass research to writer subagent to produce trivia
3. **Review** — Pass complete object to reviewer subagent
   - If REJECTED: log rejection reason, re-dispatch writer with feedback
   - If APPROVED: append to the park's working data
4. **Checkpoint** — After every 3 attractions, save intermediate JSON

### Step 5: Format on Land Completion

When all attractions in a land are done:
- Call formatter to append to the park JSON file
- Call formatter to append to the park DOCX file
- Update the plan with checkmarks

### Step 6: Progress Report

After each land:

```
✅ {Land Name} complete ({N} attractions)
   Remaining: {M} attractions across {L} lands
   Next up: {Next Land Name}
```

## Resuming Interrupted Work

If the user returns mid-park:
1. Read `data/json/{park_slug}.json` to find completed attractions
2. Read `docs/plans/` for the latest plan
3. Report status and ask: "Continue from {next attraction}?"

## Park Rosters Reference

### Magic Kingdom
- **Main Street, U.S.A.:** Walt Disney World Railroad, Main Street Vehicles
- **Adventureland:** Jungle Cruise, Pirates of the Caribbean, Walt Disney's Enchanted Tiki Room, The Magic Carpets of Aladdin, A Pirate's Adventure: Treasures of the Seven Seas
- **Frontierland:** Big Thunder Mountain Railroad, Tiana's Bayou Adventure, Tom Sawyer Island, Country Bear Jamboree, Frontierland Shootin' Arcade
- **Liberty Square:** The Haunted Mansion, Liberty Belle Riverboat, The Hall of Presidents
- **Fantasyland:** Seven Dwarfs Mine Train, Peter Pan's Flight, "it's a small world", The Many Adventures of Winnie the Pooh, Under the Sea – Journey of The Little Mermaid, Dumbo the Flying Elephant, The Barnstormer, Mickey's PhilharMagic, Prince Charming Regal Carrousel, Mad Tea Party, Enchanted Tales with Belle
- **Tomorrowland:** Space Mountain, TRON Lightcycle / Run, Buzz Lightyear's Space Ranger Spin, Tomorrowland Speedway, Walt Disney's Carousel of Progress, Tomorrowland Transit Authority PeopleMover, Astro Orbiter

### EPCOT
*(To be enumerated when this park is targeted)*

### Hollywood Studios
*(To be enumerated when this park is targeted)*

### Animal Kingdom
*(To be enumerated when this park is targeted)*

### Disneyland
*(To be enumerated when this park is targeted)*

### Disney California Adventure
*(To be enumerated when this park is targeted)*

## Common Mistakes

- Starting a new park before finishing the current one — always complete all lands first
- Skipping the progress check on resume — always read existing JSON before dispatching
- Not checkpointing — save intermediate JSON every 3 attractions to avoid data loss
- Mixing up current vs. historical attraction names — always use 2026 branding
