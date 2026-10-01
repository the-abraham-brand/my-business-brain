---
name: ask
description: My Business Brain answer. Answers a question about the user's own business from the brain, answer first, citing the entries used, flagging stale or disputed entries and conflicts, and saying plainly when the brain does not know. Uses ranked hybrid search over entries and source documents, and checks every cited figure, date and quote against its entry before answering. Use when the user runs /my-business-brain:ask, or asks what the business charges, agreed, decided, uses, owes, or how a policy or procedure works.
---

# /my-business-brain:ask

Answer from what the business knows, with the receipts.

1. Load the `my-business-brain` skill from this plugin (via the Skill tool). If it cannot be loaded, read `../my-business-brain/SKILL.md` directly. Follow **Answering a question**.
2. Search with `scripts/brain_search.py` (from the core skill folder) using 2–4 phrasings of the question, including the business's own terms (on a large brain, `--brief` first, then `scripts/brain_get.py` for the entries that matter); add `--include-archive` for history questions such as "what did we charge last year?". Read the top results and keep the ones that truly answer it. Apply relevant lessons and preferences.
3. Draft answer first, with a citation after every factual sentence (`[[entry-id]]` or `[[sources/file.md#Lx-Ly]]`) and `[calc]` on calculated figures, then run `scripts/cite_check.py` on the draft (with `--audience external` if the answer will be sent outside the business) and fix every failure. When the answer is sent or acted on, add `--log "<the question>" --kind answer` (or email, proposal, quote, report) and `--recipient` so later changes to those facts raise an impact alert.
4. Present the verified answer: the answer in one or two sentences, the supporting detail, then the sources as entry titles and file names with their dates. Flag anything past its review date, disputed, low confidence or historical. If two entries conflict, show both and ask which is current.
5. If the brain does not know, say so. Give a general-knowledge answer only if clearly labelled, and offer to store the confirmed answer. If the question depends on official rules, vet them first. When it needs outside information, use the research tools the toolkit lists (`scripts/toolkit.py <brain> show`) and install nothing; if a missing helper would have made it easier, say so in one line. Anything found on social or community sources is a lead or sentiment (`scripts/signals.py`), reported as "not confirmed" and never cited as support.
6. Log the question in `_system/questions.md`; if it has come up before unanswered, suggest documenting it.
