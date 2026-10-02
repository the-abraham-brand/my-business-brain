# Changelog

## 2.0.0 (2026-10-01)

The brain becomes your Chief of Staff. It has its own name and mandate, plans the work, hands it to a small team of specialist agents, keeps the business's promises, and learns how you like things done. It prepares; you approve. The design borrows the way a language model is built (ideas from MiniMind, Apache 2.0; no code copied): a vocabulary, a constitution, a router to experts, a fixed tool-call format, a quick-or-deliberate switch, adapters, preference learning, group-relative scoring, distillation and a guard against drift.

**Identity**
- At setup you name your Chief of Staff, and it writes a constitution: owner, voice, language, mandate, and what it may do alone, what needs your yes, and what it never does.
- It speaks as that identity in every session. The session brief now starts with its card.
- A drift guard checks its reports and your drafts: "I've sent it", "we guarantee a refund" and final legal or tax conclusions are caught.
- Only the owner can change the identity. Every change bumps the version and is logged.

**Orchestration**
- Four new specialist agents: researcher, analyst, drafter and clerk, alongside the reader, the checker and the topic expert.
- A router reads each request, recognises the business things in it through a new lexicon (the business's own words and abbreviations, in English and Arabic), picks the specialists, says which can run in parallel, and sets the depth and audience. It lists what needs your approval.
- Tasking memos brief each agent with the identity, the active lens, the reader's profile, the playbook, the facts its audience may see (confidential facts left out of team and external jobs), and a fixed report format.
- Every report is checked and scored: answer, sources, format, finished. Confidentiality breaches, unsupported or signal citations and identity drift lower the score. A specialist that keeps scoring low gets an independent check on its work.
- Quick by default; deliberate, with an independent checker the drafter waits for, for large sums, legal, tax, contract and people decisions, investors, the board or a bank, recommendations, and the CFO and people lenses.
- Options memos score two to four options on the same weighted criteria, recommend the one that beats the group, show the runner-up, and say what would change the answer.

**Chief of Staff rhythms**
- Commitments: promises both ways, with due dates read from plain English or Arabic ("by Thursday", "15 October", "غدا"). New promises are spotted as you type them, and in meeting notes and emails.
- Delegations: work handed to people or agents, with owners and dates, and a ready-to-send follow-up for anything overdue or blocked (sending needs your yes).
- Morning brief: the day's three priorities, what's coming up, who owes you what, and agent reports to review.
- Meeting prep: what the brain knows about them, promises both ways, dates, what you sent them before, decisions and leads, and a suggested agenda.
- The Sunday review adds promises and delegations, the agent scorecard and a refreshed playbook.

**Learning loop**
- Preference pairs: when you choose one draft over another, the brain records what made the difference. A difference that wins three times or more becomes a proposed rule, and you decide.
- Playbook: lessons, accepted preferences, agent watch-outs and recent decisions, condensed into one page every agent reads first.

**Lenses and people**
- Role lenses for CFO, operations, sales and people: the questions that role always asks, the specialists it leans on, and how it reports. The facts don't change.
- People profiles for colleagues: their audience (team by default), language, style and areas. Briefs written for them follow the profile and never include confidential facts.

**New command:** `/my-business-brain:chief`.

**Tests**
- 80 unit tests (14 new, including a stress test that throws odd, huge, Arabic and injected input at every new command) and 20 behaviour tests. The new behaviour tests check that the Chief of Staff holds an email for your approval instead of claiming it was sent, and that it leads the day with the overdue promise and the near notice deadline.

## 1.5.0 (2026-09-28)

This release gives the brain a research arm. It can keep an eye on the sources the business depends on, hear what people are saying without mistaking it for fact, keep recordings as sources, and use whatever research tools you have installed.

**Sentiment and leads**
- Posts, threads, forums, reviews and comments are never stored as facts. They're kept as signals: *sentiment* (what people are saying) or a *lead* (a claim to check at an official source).
- A lead can be confirmed once a proper source backs it, or dismissed. Open leads show up in the session brief, the health check and the Sunday review.
- The bulk-load planner and the watch list send social findings to signals automatically. The citation check fails a draft that cites a social source or a signal.
- Every source now has a tier: official, reputable, internal, recording, social or other. Recordings and other sources are capped at medium confidence. You can add or reclassify sources for your business.

**The watch list**
- Follow the pages and feeds you rely on: a tax authority's news page, a regulator's notices, a supplier's prices, an industry feed.
- Each check reports only what's new. When a new item mentions a figure that differs from one the brain holds, it names the fact and asks you to confirm at the source. The brain never changes a fact because a page changed.
- Plain web requests only: no sign-ins, no cookies, no browser. Hidden instructions in a page are flagged.

**The Sunday evening review**
- `/my-business-brain:review` runs the week's checks in one go: the watch list, the health check, what changed, past work affected, open leads, unsaved facts, the answers you rely on, the research toolkit and the dashboard. In the first week of a month it adds last month's journal.
- One step failing doesn't stop the rest. The report is saved in `_system/reviews/`.
- Setup and the health check offer to schedule it for Sunday evening in your time zone.

**Recordings as sources**
- Captions or transcripts (.vtt, .srt or text) from a webinar, podcast or call become a source document with one spoken line per line, so a fact is cited to the moment it was said.
- Rolling auto-captions are de-duplicated, private passages removed and instruction-like text flagged.
- If yt-dlp is installed, the brain can fetch published captions itself (captions only, never the video).
- Citations can now point at a single line (`#L42`) as well as a range.

**Uses what you have, installs nothing**
- At setup, in every health check and in every Sunday review, the brain looks for what's installed alongside it: research and document skills, converters like pandoc and pdftotext, and optional helpers like Agent Reach and yt-dlp. Every command checks this list before a job that could use a tool.
- It uses what it finds, tells you in one line what's missing, and never installs anything, signs in or reads cookies.

**Tests**
- 66 unit tests (10 new) and 18 behaviour tests. The new behaviour test checks that a claim from a LinkedIn post is kept as a lead and never replaces the sourced VAT rate.

**Smaller fixes**
- The watch list ignores years and day numbers when comparing figures, so "from 1 January 2027" isn't mistaken for a changed value.
- A source mentioning both the old and a new figure ("from 5% to 7.5%") is now flagged as a possible change.

## 1.4.0 (2026-09-26)

This release is about trust and reach. Your knowledge stays in your folder with a record of every change, anything off the record stays off the record, and what the brain knows is easier to use: briefings, a timeline, a monthly journal and a dashboard. Several ideas were adapted from claude-mem (Apache 2.0); no code was copied.

**Off the record**
- Wrap anything in `<private>...</private>` (or `<خاص>...</خاص>`), or say it's off the record, and it is used in the moment but never stored: not in facts, logs, briefings or the resume card.
- The scripts strip private passages before writing anything, and the health check flags any that reached a fact.

**Local storage and integrity**
- The brain keeps a fingerprint of every fact and source document. The health check reports anything edited, added or deleted outside the brain, so you can confirm or restore it.
- Change log lines now name the facts they touched, so the brain can tell its own changes from anyone else's.
- The README explains where your knowledge lives and how it is protected.

**Nothing slips through**
- When a message states a new business fact, the brain is reminded to offer to save it.
- When a session ends, facts you mentioned but never saved are listed, and the next session brief asks you about them. Facts the brain already holds, questions and private text are skipped. Works in English and Arabic.
- Long jobs keep a resume card with items done, items left and questions waiting. After a break, or when a long conversation is compacted, the brain continues from the card instead of from memory.

**Industry packs**
- Six ready-made packs: clinic, agency or consultancy, trading, law firm, real estate, restaurant.
- Each brings:
  - where facts belong;
  - which words make a fact confidential in that trade;
  - decision types for that trade;
  - the first questions to ask the owner;
  - what to watch.
- A pack builder makes a custom one with the owner and checks it before applying.

**Briefings and reports**
- Topic briefings: everything about a supplier, customer or product on one page, with sources. Choose the audience (you, your team, or outside), and facts that audience shouldn't see are left out.
- Onboarding packs for new team members.
- A new `topic-expert` helper answers follow-up questions from a briefing alone.
- Timeline: what was going on around a fact, a topic or a date, from changes, decisions, quotes and contract dates.
- Monthly journal: the business's story week by week, each week carrying forward what is still open.
- Dashboard: one page with the health score, deadlines, decisions, unsaved facts and recent changes. It works offline, handles Arabic right to left and follows light or dark mode. Values of confidential facts are masked.
- New command: `/my-business-brain:brief`. New setting: language of record (match, English, Arabic or both).

**Faster reading on big brains**
- Search can return a short index first, with the rough cost of reading everything, and fetch full facts only for the ones that matter.
- Fixed: plural searches such as "prices" now find "price".

**Fixes and hardening**
- Confidential now means "for the owner only". Briefings, handovers and staff messages use a new `team` audience in search and the citation check, so a contract fee can't slip into material for the team.
- When the owner confirms a change ("price list v4 is confirmed"), the brain applies it instead of asking again because an older document disagrees. It always says which past proposals and quotes used the old value.
- Two entries that disagree on the same fact are reported once, as a conflict, and no longer also as an "unstable fact".
- Hooks read UTF-8 input on Windows, so Arabic typed in a Windows console arrives intact.
- The Claude app upload limits (500-character plugin description, 1,024-character skill descriptions) are now checked by a test.
- The automated checks on GitHub skip the behaviour tests with a notice, not a failure, when no API key is set. They run on current Node 24 actions and a pinned Ubuntu.

**Tests**
- 56 unit tests and 17 behaviour tests. Two behaviour tests are new:
  - private text is never written into the brain (a guard);
  - a team briefing keeps a confidential contract fee out. Without the plugin, Claude included the AED 60,000 fee.

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
- Contract Clocks now puts Gulf deadlines at the right local time on Windows too, even without a time zone database.
- 44 unit tests (including Arabic search, figures and dates) and 15 behaviour tests. The new behaviour test checks that pay details in an Arabic HR note stay out of a public post.

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
