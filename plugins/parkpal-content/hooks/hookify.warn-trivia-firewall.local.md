---
name: warn-trivia-firewall
enabled: true
event: file
conditions:
  - field: file_path
    operator: regex_match
    pattern: data/json/.*\.json$
  - field: new_text
    operator: regex_match
    pattern: (leadImagineer|"opened"|"precededBy"|"sponsor"|"rideSystem"|"duration")
---

⚠️ **Trivia Firewall Check Required**

You're writing to a park JSON file. Before saving, verify:

**No trivia question's correct answer matches ANY of these fact sheet values:**
- Park name
- Land name
- Lead Imagineer(s)
- Opening year/date
- Theme
- Preceded by
- Sponsor

Read each question's `correct` letter, find the matching answer choice, and compare it against the fact sheet fields for that attraction. If there's a match, that question is a **FIREWALL VIOLATION** and must be replaced.

This is the most common content error in this project. Check every single question.
