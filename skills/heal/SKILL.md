---
name: heal
description: My Business Brain full health check. Scans the whole brain for conflicts, duplicates, overlaps, stale and unsourced entries, broken links, supersede errors and contract deadlines; fixes housekeeping automatically and brings the user each decision with a recommended answer and a health score. Use when the user runs /my-business-brain:heal, or asks to check, clean up, audit or fix their business brain.
---

# /my-business-brain:heal

Keep the brain trustworthy.

1. Load the `my-business-brain` skill from this plugin (via the Skill tool). If it cannot be loaded, read `../my-business-brain/SKILL.md` and `../my-business-brain/references/self-healing.md` directly.
2. Run `scripts/brain_health.py <brain-folder>` from the core skill folder (it also replays the golden questions, lists outputs built on changed facts, flags unstable facts and saves a daily snapshot), then `scripts/brain_index.py <brain-folder>`, `scripts/decide.py stats <brain-folder> --write` `scripts/brain_diff.py diff <brain-folder>` `scripts/dashboard.py <brain-folder>` and `scripts/toolkit.py <brain-folder> detect` (refresh what the brain can use) (`references/knowledge-regression.md`, `references/decision-gates.md`). Where scripts cannot run, perform the same checks by reading the entries.
3. Apply the automatic fixes (index, register, formatting, id and folder mismatches, archiving superseded entries) and log them.
4. Review what the script cannot judge (use `scripts/brain_search.py` to find related entries): statements in different entries that contradict each other without sharing a key, and overlaps worth merging. Re-vet stale official information.
5. Write open items to `_system/decisions-needed.md`, grouped and High first; within a group, most urgent first (the `urgency` and `stakes` scores).
6. Report: **Brain health score** and trend, **Fixed automatically** (one line), **Needs your decision** (each with a recommendation and a one-word answer the user can give), **Knowledge regressions** (golden questions answering differently: accept or restore), **Outdated past outputs** (who received the old value, with an offer to draft follow-ups), **What changed this week** (the diff, in a few lines), **Changed outside the brain** (files edited, added or deleted without a record: confirm or restore each), **Mentioned but not saved** (from `_system/unsaved-facts.md`), **Decision accuracy** (any decision type whose bar was raised or whose confidence is being corrected, in plain words such as "domain calls said 95% sure but were right 80% of the time; I now ask when unsure", and any proposed rule), and the next contract deadlines.
7. Apply the user's answers: supersede, merge, confirm or archive; record each in the changelog and any repeated mistake as a lesson.
8. Mention that the dashboard is at `_system/dashboard.html` (offer to open it). At the start of a month, offer the journal for the month just ended (`references/briefings-and-journal.md`).
9. Run `scripts/lexicon.py <brain-folder> build` and `scripts/distill.py <brain-folder>` so the lexicon and playbook match the healed brain. Mention overdue promises and delegations (`commitments.py list --overdue`, `delegations.py list --overdue`) and any agent whose work now gets an independent check (`delegate.py scorecard`).
10. Mention open leads in one line (`scripts/signals.py <brain> list --open --kind lead`). If there is no Sunday evening review scheduled (`/my-business-brain:review`), offer one once.
