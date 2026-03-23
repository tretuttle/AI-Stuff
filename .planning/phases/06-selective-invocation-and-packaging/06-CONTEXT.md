# Phase 6: Selective Invocation and Packaging - Context

**Gathered:** 2026-03-22
**Status:** Ready for planning
**Mode:** Auto-generated (packaging/documentation phase)

<domain>
## Phase Boundary

Package the plugin for marketplace distribution: template persona for custom personas, README documentation, and marketplace readiness. Note: SELC-01 (--only flag) and SELC-02 (default all) were already implemented in Phase 2 — this phase handles the remaining packaging requirements.

</domain>

<decisions>
## Implementation Decisions

### Already Completed (from Phase 2)
- **SELC-01:** `--only` flag implemented in `/persona:review` skill (Phase 2, D-01/D-02)
- **SELC-02:** Default behavior runs all 14 personas when no `--only` flag (Phase 2, D-01)

### Remaining Work
- **PLUG-02:** Plugin must be installable via `/plugin install persona@ai-stuff` from tretuttle/AI-Stuff marketplace
- **PLUG-03:** Template persona `.md` file for custom persona creation
- **PLUG-04:** README documenting usage, persona descriptions, custom persona contract

### Claude's Discretion
All implementation choices at Claude's discretion. Key notes:
- Template persona should follow the established agent structure (frontmatter + voice + beliefs + focus/ignore + conventions + review output + stack constraint + gilfoyle + JSON output + memory curation)
- README should be concise and practical — install, usage examples, persona list, custom persona instructions
- Marketplace readiness may just require proper plugin.json fields and directory structure

</decisions>

<canonical_refs>
## Canonical References

### Plugin System
- `research/01-create-plugins.md` — Plugin creation, directory structure
- `research/02-plugins-reference.md` — Plugin manifest fields for marketplace
- `research/06-plugin-marketplaces.md` — Marketplace installation and distribution

### Existing Assets
- `.claude-plugin/plugin.json` — Current plugin manifest
- `agents/*.md` — 14 existing persona agents (template should match this structure)
- `skills/review/reference.md` — Persona roster and JSON schema

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- All 14 agent files have consistent structure — template can be derived from any one
- plugin.json already has name, version, description, author
- skills/review/reference.md has persona roster table

### Integration Points
- README.md at plugin root
- Template persona at agents/template.md or similar
- plugin.json may need additional marketplace fields

</code_context>

<specifics>
## Specific Ideas

No specific requirements beyond what's in ROADMAP success criteria.

</specifics>

<deferred>
## Deferred Ideas

None.

</deferred>

---

*Phase: 06-selective-invocation-and-packaging*
*Context gathered: 2026-03-22*
