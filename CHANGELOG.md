# Changelog

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
