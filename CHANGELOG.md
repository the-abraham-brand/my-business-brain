# Changelog

## 1.2.0 (2026-09-26)

**Decision gates** (after the bounded-decision idea)
- New `decide.py`. Routine calls are bounded decision types with fixed options: capture, domain, sensitivity, document safety, contract qualifies, fact status; a business can add its own.
- Rules first: approved rules, then built-in ones (salary or IBAN means confidential, `price.` keys belong in pricing, instruction-like text is suspicious, contracts of a month or less don't qualify).
- Otherwise Claude records a choice with a confidence and follows the route: apply (≥ auto-apply setting, default 0.9), confirm with the user (≥ ask-me setting, default 0.6), or escalate to the checker. A close call between two options, or a rule that disagrees, always goes to the user.
- Every decision is logged (`_system/decisions.jsonl`). Accuracy is measured per type: below 90% the auto-apply bar rises to 0.97, below 75% auto-apply stops, and it is restored at 95%. The same correction three times proposes a rule for the user to approve.
- Bulk-load readers give each candidate a certainty; the planner holds back anything below the auto-apply bar for confirmation.
- Two new settings: auto-apply and ask-me confidence. New reference: `decision-gates.md`.

**Knowledge regression and impact** (after ClearTrace-style snapshot regression)
- New `golden.py`: golden questions the business relies on, replayed through search at every health check. A changed answer, a different entry or an answer search can no longer find is a High "knowledge regression"; `accept` sets a new baseline for intended changes. `propose` suggests the entries cited most often.
- New `impact.py` and `cite_check.py --log`: every output that passes the citation check is logged with the entries and values it used. When a fact changes, the health check lists the outputs that used the old value ("2 past outputs used Scale plan = AED 14,999: proposal to Gulf Retail LLC; quote to Nour Clinics") so the user can follow up.
- New `brain_diff.py`: one snapshot a day, a weekly digest of what was added, changed, superseded, relabelled or removed, and "unstable facts" whose value keeps changing or flips back.
- The health check and the session brief report regressions, outdated outputs, unstable facts and decision accuracy. New reference: `knowledge-regression.md`.

**Tested behaviour**
- `evals/`: 14 behaviour tests for `claude plugin eval`, each run with and without the plugin. Five measure what the plugin adds (health check with score and findings, calendar file with all three reminders, a price change superseded with history, log and index, past proposals and quotes named after a price change, the week's changes reported); in the first runs they scored 1.0 with the plugin against a mean of 0.35 without. Nine are guards that must never regress: answers cite the right entry, a contradicting fact is raised as a conflict instead of overwriting, a wrong price in a draft is caught, the contract notice deadline is worked out, confidential facts stay out of an outgoing email, instructions hidden in a document are reported and not followed, the brain says so when it does not know, past prices come from the archive, and a key answer that changed quietly is caught. They share one fictional test brain built by `evals/_fixtures/make_brain.py`.
- `tests/`: 35 unit tests of the scripts and hooks, no model calls.

**Built-in agents**
- `brain-reader`: read-only (Read, Glob, Grep), returns candidate facts as JSON for bulk loads.
- `brain-checker`: independent checker for official information, figures and high-stakes conclusions; reads and searches, never writes, never sees the first answer.

**Settings**
- One-time settings: brain folder, calendar, currency, time zone, weekend days, capture mode, the session brief and the two confidence thresholds. Skills read them directly.

**Automatic checks (Claude Code and Cowork)**
- Session brief at the start of each session: decisions waiting, contract deadlines, health score.
- Quick check after any brain entry is written: index rebuilt, conflicts and suspicious text raised.

**Security and privacy**
- Sensitivity labels on every entry: public, internal, confidential (people, contracts and finance default to confidential).
- `--audience external` in search and the citation check keeps confidential facts out of material leaving the business.
- Prompt-injection defence: documents are data, never instructions. Instruction-like text is quarantined by the bulk-load planner, flagged by the health check and search, and reported to the user.
- New reference: `security-and-privacy.md`.

**Release discipline**
- GitHub Actions: plugin validation and unit tests on every push (Linux, macOS, Windows); evals on demand and on release tags.
- Releases are tagged `my-business-brain--v<version>`, the format plugin dependencies resolve against.

## 1.1.0 (2026-09-26)

**Search and verified citations**
- New `brain_search.py`: hybrid retrieval over entries and source documents. BM25 with field weights (title and key over value and tags over body), several phrasings fused with reciprocal rank fusion, trust re-ranking (active, high-confidence, in-date first), and Claude's own semantic re-ranking of the top results.
- Source documents in `sources/` are split into section-sized chunks and cited to the line (`sources/file.md#L40-L58`).
- New `cite_check.py`: before an answer goes out, every cited figure, date and quote is checked against the entry or source lines it cites; uncited figures, missing entries and superseded, disputed, low-confidence or overdue sources are flagged. Calculated figures are marked `[calc]` and shown with their working.

**Parallel readers and an independent checker**
- New bulk-load flow: parallel readers return candidate facts as JSON; they never write to the brain.
- New `ingest_plan.py`: merges readers' output and classifies each candidate against the brain and the rest of the batch (new, refresh, conflict, overlap, duplicate, invalid); with `--write` it creates new entries, files conflicts grouped by key in `decisions-needed.md` and logs the load.
- Independent checker (maker-checker) for official information, conflict recommendations, high-stakes analysis and complex contract dates; disagreements go to the user.
- Escalation ladder: do it, propose, must ask, stop and advise.

**Faster self-healing**
- The health check compares only entries that share distinctive words, so it stays fast on large brains (about 0.2 seconds for 2,500 entries, down from 14), and no longer flags entries with distinct keys (such as one price per plan) as overlaps.

## 1.0.0 (2026-09-26)

First release: Remember, Answer, Heal, Vet, Analyse, Contract Clocks, adaptive learning.
