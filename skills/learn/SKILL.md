---
name: learn
description: My Business Brain remember/ingest. Adds business knowledge from documents, messages, notes or what the user says, splitting it into one-fact entries, checking each against the brain for duplicates, overlaps and conflicts, vetting official information, and running Contract Clocks on contracts. Use when the user runs /my-business-brain:learn, or says remember this, add this to the brain, save this for the business, or uploads business documents to be stored.
---

# /my-business-brain:learn

Put new knowledge into the brain without creating duplicates or silent contradictions.

1. Load the `my-business-brain` skill from this plugin (via the Skill tool). If it cannot be loaded, read `../my-business-brain/SKILL.md` and its `references/` folder directly. Follow **Remember** in `references/knowledge-model.md`.
2. Find the brain (the folder with `BRAIN.md`). If there is none, offer `/my-business-brain:setup` first.
3. Read everything provided: attachments, pasted text, or what the user said. Read `_system/lessons.md` and `_system/preferences.md` first.
4. Split the material into atomic items; give each a type, domain and `key`.
5. Check each item against the brain: same key and value → refresh; same key, different value → conflict, not overwritten, added to `_system/decisions-needed.md`; similar → propose merge or link; new → write the entry.
6. Vet official information (laws, fees, rates, deadlines) with `references/trusted-sources.md` before storing it.
7. For contracts, run Contract Clocks (`references/contract-clocks.md`), including the date table for the user to confirm and the calendar offer.
8. Update the changelog, run the quick health check and rebuild the index.
9. Report in a short list: **Added** (count and titles), **Updated**, **Needs your decision** (each conflict with the recommended answer).
