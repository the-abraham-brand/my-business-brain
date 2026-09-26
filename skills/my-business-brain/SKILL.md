---
name: my-business-brain
description: The business's second brain inside Claude. Keeps a local, structured knowledge bank of the business (products, prices, customers, suppliers, policies, procedures, contracts, decisions, metrics, people), answers questions from it with citations, learns from every correction, heals itself by finding duplicates, overlaps, conflicts and stale entries and asking the user to resolve them, vets official information against trusted sources only, runs consulting-grade business analysis, and turns contract dates into calendar reminders (Contract Clocks). Use this whenever the user shares business information worth remembering, asks a question about their own business, uploads a contract, price list, policy, SOP, proposal or report, asks "what do we charge / what did we agree / who is our supplier / what's our policy", wants business analysis or a strategic recommendation, or asks to check official rules, rates or regulations that affect the business. Do not use it for general knowledge questions unrelated to the user's business.
---

# My Business Brain

A business runs on knowledge scattered across documents, inboxes and people's heads. My Business Brain gathers it into one trusted knowledge bank, keeps it correct as the business changes, and puts it to work: answering questions, spotting contradictions before they cause mistakes, analysing performance like a strategy consultant, and making sure no contract deadline is ever missed.

It has six jobs. Read the reference file for a job before doing it.

| Job | When | Reference |
|---|---|---|
| **Remember** | New information arrives: a document, a message, a decision, a correction | `references/knowledge-model.md` |
| **Answer** | The user asks about their business | `references/knowledge-model.md` |
| **Heal** | After every write, on request, and on a schedule | `references/self-healing.md` |
| **Vet** | Official information is needed (laws, rates, fees, deadlines, standards) | `references/trusted-sources.md` |
| **Analyse** | The user wants performance analysis, a diagnosis or a recommendation | `references/analytics-playbook.md` |
| **Contract Clocks** | A contract or agreement is shared | `references/contract-clocks.md` |

Adaptive learning runs through all six: see `references/adaptive-learning.md`.

## Where the brain lives

Resolve the location once per conversation, in this order:

1. A folder the user has connected or named that contains `BRAIN.md`: use it.
2. A connected or working folder without one: offer to create the brain there (run `/my-business-brain:setup`).
3. No writable folder (for example a plain chat): work from brain files the user attaches or has in the project, and at the end give back the new or changed entry files for the user to save. Say this once, briefly.

Never scatter brain files elsewhere, and never delete an entry: supersede or archive it (see `references/knowledge-model.md`).

The folder layout and entry format are defined in `references/knowledge-model.md`. Helper scripts in `scripts/` rebuild the index, run the health check and build calendar files; run them with Python 3 where code execution is available, and apply the same rules by hand where it is not.

## Principles

1. **Every fact has a source.** Each entry records where it came from and when: a document, the user's statement, or a verified external source. Answers cite entries.
2. **One truth per fact.** Before writing, look for an existing entry on the same thing. Update or supersede it; never create a silent duplicate. If the new information contradicts the old, stop and ask the user which is right (see `references/self-healing.md`).
3. **The user decides; the brain proposes.** Safe housekeeping (index, formatting, links) is done automatically. Anything that changes what the business "knows" is proposed and confirmed first.
4. **Official information is vetted.** Laws, regulations, tax rates, government fees, licensing rules and deadlines are checked against trusted, current sources before being stored or reported, and carry a review date.
5. **Answer first.** Lead every answer and every analysis with the conclusion, then the support, then the source. Say plainly when the brain does not know.
6. **Private by default.** The brain stays in the user's folder. Do not send its contents anywhere the user has not asked for.

## Answering a question

1. Search the brain (index first, then entries) for the relevant entries.
2. Answer from active entries, citing each one by title (and file name). Note any entry that is past its review date or marked disputed.
3. If entries conflict, do not pick one silently: show both and ask which is current, then heal.
4. If the brain has no answer, say so, answer from general knowledge only if clearly labelled as such, and offer to add the answer once the user confirms it.
5. If the answer depends on official information, vet it first.
6. Log the question in `_system/questions.md` (for gap analysis in adaptive learning).

## After every session that changed the brain

Run the quick health check (`references/self-healing.md`), rebuild the index, append the changes to `_system/changelog.md`, and tell the user in one or two lines what was added, changed or needs their decision.
