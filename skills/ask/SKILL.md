---
name: ask
description: My Business Brain answer. Answers a question about the user's own business from the brain, answer first, citing the entries used, flagging stale or disputed entries and conflicts, and saying plainly when the brain does not know. Use when the user runs /my-business-brain:ask, or asks what the business charges, agreed, decided, uses, owes, or how a policy or procedure works.
---

# /my-business-brain:ask

Answer from what the business knows, with the receipts.

1. Load the `my-business-brain` skill from this plugin (via the Skill tool). If it cannot be loaded, read `../my-business-brain/SKILL.md` directly. Follow **Answering a question**.
2. Search `INDEX.md`, then the entries (including `_system/archive/` for history questions such as "what did we charge last year?"). Apply relevant lessons and preferences.
3. Lead with the answer in one or two sentences. Then the supporting detail, then the sources: entry titles and file names, with their dates.
4. Flag anything past its review date, marked disputed, or low confidence. If two entries conflict, show both and ask which is current.
5. If the brain does not know, say so. Give a general-knowledge answer only if clearly labelled, and offer to store the confirmed answer. If the question depends on official rules, vet them first.
6. Log the question in `_system/questions.md`; if it has come up before unanswered, suggest documenting it.
