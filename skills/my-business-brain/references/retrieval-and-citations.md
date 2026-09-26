# Retrieval and citations

How the brain finds the right knowledge and proves every answer. Reading `INDEX.md` works for a small brain; once it holds more than a few dozen entries, or has documents in `sources/`, search it properly and check every citation before answering.

## 1. Search: hybrid retrieval

Two complementary signals, the same idea as production "hybrid search":

1. **Lexical recall (the script).** `scripts/brain_search.py <brain-folder> --q "<phrasing>" [--q "<another phrasing>"] --top 10` ranks entries and source-document sections with BM25, weighting titles and keys above values and tags, and values and tags above body text. It also searches `sources/` (Markdown and text files), split into section-sized chunks with line numbers.
2. **Semantic expansion and re-ranking (Claude).** Before searching, write 2–4 phrasings of the question: the user's words, synonyms, the business's own terms from the `glossary` domain and `_system/preferences.md`, and the likely `key` (e.g. `policy.refund.window-days`). The script fuses the phrasings with reciprocal rank fusion, so an entry found by any of them surfaces. Then read the top results and judge which actually answer the question: this is the re-ranking step.

The script's own re-ranking favours trust: active, high-confidence, in-date entries rank above drafts, disputed, low-confidence, overdue and archived ones. Results carry warning flags; carry them into the answer.

Useful options: `--audience external` when drafting anything that leaves the business (confidential entries are left out), `--domain pricing` to narrow, `--include-archive` for history questions ("what did we charge last year?"), `--no-sources` to search entries only, `--json` for structured output.

**If the search finds nothing,** try the business's own terms and broader phrasings before concluding the brain does not know. Log the miss in `_system/questions.md`.

## 2. Source documents: chunking

- Entries are already the ideal retrieval unit: one fact per entry, with a key. Keep it that way.
- Long documents the user wants kept go in `sources/`. Save a text or Markdown copy next to any PDF or Word file (for example `sources/supplier-x-agreement.md`), keeping headings and clause numbers, so it can be searched and cited to the line.
- The script splits source files at headings and clause or section markers, and into chunks of about 1,200 characters with a one-line overlap, and cites them as `sources/<file>#L<start>-L<end>`.
- A source chunk is evidence, not a stored fact. When a source answers a question the brain should know, offer to store it as an entry through the normal Remember flow.

## 3. Answer with citations, then verify them

1. Draft the answer from the retrieved entries and chunks. Put a citation after every factual sentence, exactly as the search prints it: `[[entry-id]]` or `[[sources/file.md#L40-L58]]`.
2. Mark anything you calculated rather than read (totals, days remaining, annual figures, derived dates) with `[calc]`, and show the working in the answer.
3. Run `scripts/cite_check.py <brain-folder> <draft.md>` (or pipe the draft with `-`). It confirms, sentence by sentence, that:
   - every cited entry or source range exists;
   - every number, amount, percentage and date appears in what the sentence cites;
   - every quoted phrase appears word for word;
   - cited entries are current (it warns on superseded, archived, disputed, draft, low-confidence and overdue entries);
   - no sentence states figures without a citation;
   - with `--audience external`, no confidential entry is cited and internal ones are flagged for the user to confirm.
4. **Fix every failure before answering**: correct the figure, cite the right entry, mark a genuine calculation with `[calc]`, or remove the claim. Carry every warning into the answer in plain words ("this was due for review in March").
5. Present the answer to the user with citations as entry titles and file names (the `[[id]]` markers are for checking; convert them to readable references unless the user prefers ids).

Where scripts cannot run, perform the same check by hand: reopen each cited entry and confirm each figure, date and quote is there.

## 4. What a good answer looks like

- Answer first, in one or two sentences.
- Every figure traceable to a named entry or source lines.
- Calculations shown.
- Flags stated: disputed, overdue, low confidence, historical.
- If sources conflict, both shown and the user asked which is current (then heal).
