# Orchestration: parallel readers and an independent checker

For big jobs the brain works as a small team: a **coordinator** (the main conversation) that owns the brain, **readers** that extract knowledge in parallel, and an independent **checker** for high-stakes results. The plugin ships both as agents:

- **`brain-reader`** (`my-business-brain:brain-reader`): tools limited to Read, Glob and Grep. It cannot write, run commands or use the web, so a poisoned document cannot make it act. It returns candidate facts as JSON in its reply; the coordinator saves that JSON to a file for the planner.
- **`brain-checker`** (`my-business-brain:brain-checker`): Read, Glob, Grep, WebSearch and WebFetch; no writing. It is never shown the draft finding.

Where plugin agents are not available, use general sub-agents with the same briefs, or do the steps one after another. The rules are identical either way.

## Roles

| Role | Does | Never does |
|---|---|---|
| **Coordinator** | Splits the work, briefs readers, merges results, resolves conflicts with the user, writes to the brain, reports | Delegates the decision on a conflict, or lets anyone else write to the brain |
| **Reader** | Reads its assigned documents and returns candidate facts as JSON | Writes to the brain, decides conflicts, invents missing values |
| **Checker** | Re-checks a finding from scratch with only the question and the evidence | Sees the author's reasoning or conclusion before forming its own |

## Bulk load (many documents at once)

Use when the user adds more than about five documents, or one very long one (a policy manual, a year of contracts).

1. **Plan.** List the documents; group them into batches of 3–5 by type (contracts, price lists, policies…). One `brain-reader` per batch, up to about five in parallel.
2. **Brief each reader** with: the documents, the brain's domain list and existing keys for those domains (from `INDEX.md` or `brain_search.py --domain`), the business's glossary, and this output contract:
   - Return a JSON list of candidates, one fact per item, with `title`, `type`, `domain`, `key` (reuse existing keys where the fact is the same thing), `value`, `source` (document name and version), `location` (page, clause, table), `quote` (the exact wording), `confidence`, and optional `body`, `related`, `tags`, and `extra` (contract fields: `counterparty`, `start_date`, `end_date`, `notice_deadline`, `auto_renewal`).
   - Extract only what the document states. No inference beyond simple unit normalisation. Anything unclear is returned with `confidence: low` and a note in `body`.
   - Do not write any files except the JSON output.
3. **Merge and plan.** Save each reader's JSON reply to a file and run `scripts/ingest_plan.py <brain-folder> reader1.json reader2.json …`. It classifies every candidate against the brain and against the rest of the batch: `new`, `refresh`, `conflict` (with the brain, or between two documents in the batch), `overlap`, `duplicate`, `invalid`, `quarantine` (the candidate contains text that tries to instruct an AI; see `security-and-privacy.md`), and `confirm` (the reader's `certainty` is below the auto-apply threshold: pass `--auto <setting>`; show these to the user before writing).
4. **Review the plan** (coordinator): spot-check a sample of `new` items against their quotes; send `invalid` items back to their reader; vet official information (`trusted-sources.md`).
5. **Apply.** Run again with `--write`: new entries are created with review dates by type, conflicts go to `_system/decisions-needed.md` grouped by key, and the changelog records the load. Apply refreshes; propose merges or links for overlaps.
6. **Contracts** found in the load go through Contract Clocks (confirm dates with the user before any calendar event).
7. **Heal and report.** Rebuild the index, run the health check, and report: added, refreshed, conflicts needing a decision (with a recommendation each), overlaps proposed, items returned.

## Independent checker (maker-checker)

Use a fresh `brain-checker` whenever a result could cost money, create legal exposure or drive a significant decision:

- official information before it is stored (tax, fees, licences, regulations, deadlines);
- a conflict resolution the user asks the brain to recommend;
- an analysis whose recommendation changes pricing, spend, headcount or a contract;
- contract dates before they go on a calendar, when the contract is complex.

**How:** give the checker only the question, the jurisdiction and date, and the evidence to consult (or the task of finding it under the trust test in `trusted-sources.md`). Do not share the draft finding. Ask for its own answer, sources and confidence. Then compare:

- **Agree:** store or report, noting that it was independently checked.
- **Disagree:** do not pick one. Show the user both findings with their sources, say which is more authoritative and why, and let the user decide. Record the outcome as a lesson if it reveals a pattern.

Without sub-agents, do the check as a separate pass: re-derive the answer from the sources without looking at the first draft, then compare.

## Escalation ladder

Every action falls on one rung. Climb, never skip.

| Rung | Examples | What happens |
|---|---|---|
| **1. Do it** | Rebuild the index, fix formatting, add a new uncontested fact with a source | Done automatically, logged |
| **2. Propose** | Merge overlaps, refresh a stale entry, store a vetted official rule | Shown to the user with a recommendation; applied on confirmation |
| **3. Must ask** | Any conflict, any change to a price, policy or contract fact, any calendar event | Nothing changes until the user answers; waits in `_system/decisions-needed.md` |
| **4. Stop and advise** | Legal disputes, tax positions, signing or terminating contracts, large financial commitments | The brain informs; it recommends a professional (lawyer, accountant, licensed adviser) and takes no action |

When a reader or checker is unsure, the item moves up a rung, never down.
