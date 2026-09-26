---
name: heal
description: My Business Brain full health check. Scans the whole brain for conflicts, duplicates, overlaps, stale and unsourced entries, broken links, supersede errors and contract deadlines; fixes housekeeping automatically and brings the user each decision with a recommended answer and a health score. Use when the user runs /my-business-brain:heal, or asks to check, clean up, audit or fix their business brain.
---

# /my-business-brain:heal

Keep the brain trustworthy.

1. Load the `my-business-brain` skill from this plugin (via the Skill tool). If it cannot be loaded, read `../my-business-brain/SKILL.md` and `../my-business-brain/references/self-healing.md` directly.
2. Run `scripts/brain_health.py <brain-folder>` from the core skill folder, then `scripts/brain_index.py <brain-folder>`. Where scripts cannot run, perform the same checks by reading the entries.
3. Apply the automatic fixes (index, register, formatting, id and folder mismatches, archiving superseded entries) and log them.
4. Review what the script cannot judge: statements in different entries that contradict each other without sharing a key, and overlaps worth merging. Re-vet stale official information.
5. Write open items to `_system/decisions-needed.md`, grouped and High first.
6. Report: **Brain health score** and trend, **Fixed automatically** (one line), **Needs your decision** (each with a recommendation and a one-word answer the user can give), and the next contract deadlines.
7. Apply the user's answers: supersede, merge, confirm or archive; record each in the changelog and any repeated mistake as a lesson.
8. If there is no weekly check scheduled, offer one once.
