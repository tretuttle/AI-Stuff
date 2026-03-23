---
phase: 01-plugin-foundation-and-persona-agents
plan: 02
subsystem: persona-agents
tags: [personas, system-prompts, subagents]
dependency_graph:
  requires: []
  provides: [chris-coyier-persona, evan-you-persona, kent-c-dodds-persona, lee-robinson-persona, matt-mullenweg-persona]
  affects: [orchestration, synthesis]
tech_stack:
  added: []
  patterns: [7-section-persona-structure, structured-review-output]
key_files:
  created: []
  modified:
    - agents/chris-coyier.md
    - agents/evan-you.md
    - agents/kent-c-dodds.md
    - agents/lee-robinson.md
    - agents/matt-mullenweg.md
decisions:
  - All 5 personas follow consistent 8-section structure (Voice & Tone, Core Beliefs, What I Focus On, What I Ignore, Project Conventions, Bash Usage, Review Output Format, plus identity intro)
  - What I Focus On and What I Ignore sections are distinct per persona with zero overlap between focus and ignore within each agent
metrics:
  duration: 3min
  completed: "2026-03-23T00:47:49Z"
  tasks_completed: 5
  tasks_total: 5
  files_modified: 5
requirements: [PERS-01, PERS-03]
---

# Phase 01 Plan 02: Write System Prompts for 5 Persona Agents Summary

Complete system prompt sections added to 5 persona agents (Chris Coyier, Evan You, Kent C. Dodds, Lee Robinson, Matt Mullenweg) with distinct review philosophies, What I Focus On/Ignore sections, and standardized Project Conventions/Bash Usage/Review Output Format.

## What Was Done

All 5 agents already had rich identity introductions, Voice & Tone, and Core Beliefs sections from prior work. This plan added the missing structured review sections required by the persona agent standard:

| Task | Agent | Commit | Key Changes |
|------|-------|--------|-------------|
| 1 | Chris Coyier | 74a1c55 | CSS quality, HTML semantics, web platform, progressive enhancement, responsive design, SVG |
| 2 | Evan You | 19e6f2e | API design, reactivity patterns, build tooling, DX, framework integration |
| 3 | Kent C. Dodds | c909527 | Test quality, accessibility, component patterns, error handling, colocation |
| 4 | Lee Robinson | d8ba37b | Next.js patterns, Web Vitals, deployment, SEO/metadata, modern web patterns |
| 5 | Matt Mullenweg | d7aa841 | Backward compat, extensibility/hooks, open source health, data portability, long-term maintainability |

## Sections Added to Each Agent

1. **What I Focus On** -- 6-7 bullet points per persona, each reflecting the real developer's actual review priorities
2. **What I Ignore** -- 5-6 bullet points per persona, explicitly scoping what each reviewer won't comment on
3. **Project Conventions** -- Standard section instructing agents to read and respect `CLAUDE.md`
4. **Bash Usage** -- Standard section allowing read-only Bash with explicit "NEVER use Bash to modify files" constraint

## Verification Results

- All 5 agents have all 8 required sections (Voice & Tone, Core Beliefs, What I Focus On, What I Ignore, Project Conventions, Bash Usage, Review Output Format, identity intro)
- All 5 agents reference `CLAUDE.md` in Project Conventions
- All 5 agents contain "NEVER use Bash to modify files" in Bash Usage
- All 5 agents have persona-specific keywords (CSS-Tricks, CodePen, Vue, Vite, Testing Library, Next.js, Vercel, WordPress, Automattic)
- All 5 agents have 100+ total lines (80+ body content after frontmatter)
- No two agents have identical What I Focus On sections -- each reflects a distinct review lens

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing functionality] Preserved existing rich content instead of replacing**
- **Found during:** All tasks
- **Issue:** The plan said "replace the contents" but the existing agent files already had high-quality, extensive Core Beliefs and identity content (60-80 lines of well-written persona material). Replacing would have lost valuable content.
- **Fix:** Kept existing frontmatter AND existing body content intact. Only replaced the "How to Respond" section with the required "What I Focus On", "What I Ignore", "Project Conventions", and "Bash Usage" sections.
- **Files modified:** All 5 agent files
- **Impact:** Positive -- agents retain richer persona content while gaining the required structured sections.

## Known Stubs

None -- all sections contain substantive content.

## Self-Check: PASSED

- [x] agents/chris-coyier.md exists and has all sections (110 lines)
- [x] agents/evan-you.md exists and has all sections (117 lines)
- [x] agents/kent-c-dodds.md exists and has all sections (106 lines)
- [x] agents/lee-robinson.md exists and has all sections (104 lines)
- [x] agents/matt-mullenweg.md exists and has all sections (115 lines)
- [x] Commit 74a1c55 exists
- [x] Commit 19e6f2e exists
- [x] Commit c909527 exists
- [x] Commit d8ba37b exists
- [x] Commit d7aa841 exists
