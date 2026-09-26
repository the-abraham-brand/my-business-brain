# Changelog

## 1.3.0 (2026-09-26)

This release is about judgement and language. The brain now makes its small everyday calls more carefully, keeps score of how often it gets them right, and handles Arabic properly throughout.

**Smarter everyday calls** (inspired by the "System 1" decision models Laya and Jev)
- Every routine call is now one of three kinds:
  - a choice from a fixed list, with a short description of each option;
  - a score on a scale, such as urgency from 0 to 3;
  - a yes/no question answered with a probability.
- Three new built-in calls:
  - how urgent something is (worked out from its due date when there is one);
  - how much is at stake;
  - whether something is official information that must be checked at the source.
- When something new arrives, all the small questions about it are asked together in one go. Anything a rule can settle comes pre-answered, and anything that needs you is gathered into a single question.
- Answers that don't fit the options are refused, and close calls between two options always come to you.
- If you add your own decision types, they're checked for common mistakes. Examples: too many options, yes/no hidden inside a list, or questions phrased in the negative.

**It keeps score, and adjusts**
- For every kind of call, the brain now tracks how often it was right, how well its confidence matched reality, and (for scores) how far off it was.
- Once it has 20 checked calls of a kind, it corrects its own confidence to match its track record. In testing, a judge that claimed 95% certainty but was right 70% of the time was treated as 70% sure, so it asked instead of acting.

**Arabic, built in**
- Search reads Arabic and copes with spelling variations and attached words, so استرداد finds الاسترداد.
- Arabic-Indic numbers (٣٢٬٠٠٠) and Arabic month names are understood, so wrong figures in Arabic drafts are caught and the same price in different numerals isn't flagged as a clash.
- Salaries, bank details, IDs and similar are recognised as confidential in Arabic, and instructions hidden in Arabic documents are caught.
- It replies in the language you write in and stores each fact in the language it came in.
- On Arabic, or any language it hasn't yet proven itself on, it asks before acting until it has 20 checked calls in that language.
- Arabic text displays and saves correctly on every platform, including Windows.

**Also**
- The README and plugin description have been rewritten in plain language, with a section on Arabic.
- 43 unit tests (including Arabic search, figures and dates) and 15 behaviour tests. The new behaviour test checks that pay details in an Arabic HR note stay out of a public post.

## 1.2.0 (2026-09-26)

This release made the brain careful about its own decisions and alert to knowledge going wrong over time. It also gained helper agents, settings, automatic checks and proper privacy and security.

**Careful everyday calls**
- The small calls the brain makes all day have fixed options to choose from:
  - is this worth remembering;
  - which area it belongs to;
  - how sensitive it is;
  - is this document safe;
  - does this contract need tracking;
  - is this new, an update, a clash or a duplicate.
- Clear cases are settled by rules first. Examples: a salary or IBAN is confidential, and a contract of a month or less doesn't need tracking.
- Otherwise the brain says how sure it is. Very sure, it goes ahead (0.9 by default). Fairly sure, it asks you (0.6 by default). Less sure than that, it gets a second opinion. A close call, or a rule that disagrees, always comes to you.
- Every call is logged and scored against your corrections. If a kind of call keeps being corrected, the brain holds back and asks more often. Correct the same thing three times and it suggests a rule you can approve.
- Two new settings let you choose how sure it must be before acting and before asking.

**Catching knowledge that goes wrong**
- Key questions: the answers you rely on most are re-checked at every health check, and a quiet change is flagged as high priority.
- Impact alerts: every answer, proposal and quote that passes the source check is logged with the facts it used. When a fact changes, you're told who received the old version, for example "2 past outputs used Scale plan = AED 14,999: proposal to Gulf Retail LLC; quote to Nour Clinics".
- Weekly changes: a daily snapshot feeds a weekly summary of what was added, changed or retired, and facts that keep flipping back and forth are flagged.

**Helper agents**
- `brain-reader` reads documents during bulk loads and can only read, so a bad document can't make it do anything.
- `brain-checker` double-checks official information and big conclusions without seeing the first answer.

**Settings and automatic checks**
- One-time settings: brain folder, calendar, currency, time zone, weekend days, whether to remember things automatically, the session brief, and the two confidence levels.
- In Claude Code and Cowork, a short brief at the start of each session (what's waiting, deadlines, health score), and a quick check every time an entry changes.

**Privacy and security**
- Every entry is public, internal or confidential. People, contracts and finance are confidential unless marked otherwise.
- Anything going outside the business is checked so confidential facts stay in.
- Documents are information, never instructions. Text that tries to instruct an AI is set aside, flagged and shown to you.

**Testing and releases**
- 35 unit tests and 14 behaviour tests, each behaviour test run with and without the plugin. The five that measure what the plugin adds all scored 1.0 with it, against an average of 0.35 without.
- Automatic checks on GitHub for every change on Linux, macOS and Windows, with the behaviour tests run for each release.
- Releases are tagged `my-business-brain--v<version>`.

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
