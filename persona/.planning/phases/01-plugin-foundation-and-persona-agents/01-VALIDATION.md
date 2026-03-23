---
phase: 1
slug: plugin-foundation-and-persona-agents
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-22
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Manual verification (markdown plugin — no runtime test framework) |
| **Config file** | none |
| **Quick run command** | `cat .claude-plugin/plugin.json \| node -e "JSON.parse(require('fs').readFileSync(0,'utf8'))"` |
| **Full suite command** | `bash -c 'for f in agents/*.md; do head -1 "$f"; done'` |
| **Estimated runtime** | ~1 second |

---

## Sampling Rate

- **After every task commit:** Validate JSON and frontmatter syntax
- **After every plan wave:** Verify all agent files exist with required frontmatter fields
- **Before `/gsd:verify-work`:** Full suite must confirm all agents present and structured
- **Max feedback latency:** 2 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01 | 01 | 1 | PLUG-01 | manual | `node -e "JSON.parse(require('fs').readFileSync('.claude-plugin/plugin.json','utf8'))"` | ✅ | ⬜ pending |
| 02-01 | 02 | 1 | PERS-01, PERS-03 | manual | `ls agents/*.md \| wc -l` | ❌ W0 | ⬜ pending |
| 02-02 | 02 | 1 | PERS-02 | manual | `grep -l "Severity:" agents/*.md` | ❌ W0 | ⬜ pending |
| 02-03 | 02 | 1 | PERS-04 | manual | `grep -l "disallowedTools:" agents/*.md` | ❌ W0 | ⬜ pending |
| 02-04 | 02 | 1 | PERS-05 | manual | `grep -l "CLAUDE.md" agents/*.md` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] No test framework needed — validation is structural (file existence, frontmatter fields, JSON validity)

*Existing infrastructure covers all phase requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Persona voice distinctiveness | PERS-01, PERS-03 | Subjective quality — requires reading agent prompts | Read each agent .md and verify distinct philosophy, priorities, and review lens |
| Structured output compliance | PERS-02 | Output format is prompt-enforced, not schema-enforced | Invoke each persona manually and verify output contains severity/confidence/file/issue/recommendation/reasoning |
| CLAUDE.md awareness | PERS-05 | Behavioral — requires runtime invocation | Invoke persona in a project with CLAUDE.md and verify it references conventions |

---

## Validation Sign-Off

- [ ] All tasks have automated verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 2s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
