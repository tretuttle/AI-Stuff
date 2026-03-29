---
name: require-schema-validation
enabled: true
event: stop
pattern: .*
---

Before stopping, verify:

- [ ] All attraction objects in `data/json/` pass schema validation against `schemas/attraction.schema.json`
- [ ] Every trivia array has exactly 10 items (3 easy, 4 medium, 3 hard)
- [ ] The DOCX in `data/docx/` was regenerated from the latest JSON
- [ ] The plan in `docs/plans/` is updated with checkmarks for completed attractions
- [ ] Progress was reported to the user

Run: `node scripts/validate.js data/json/{park_slug}.json` if the validation script exists.
