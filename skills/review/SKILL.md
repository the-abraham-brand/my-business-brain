---
name: review
description: My Business Brain Sunday evening review and updates pack. Checks the watch list for changes at official pages, supplier prices and industry feeds, then runs the health check, the week's changes, past work affected by changed facts, open sentiment and leads, unsaved facts, golden answers, the research toolkit and the dashboard, in one short report. Use when the user runs /my-business-brain:review, asks for the weekly or Sunday review, asks what changed this week, or wants to watch a page or feed for changes.
---

# /my-business-brain:review

Set the week up in five minutes.

1. Load the `my-business-brain` skill from this plugin (via the Skill tool). If it cannot be loaded, read `../my-business-brain/SKILL.md` and `../my-business-brain/references/research-and-watch.md` directly.
2. Find the brain (the folder with `BRAIN.md`). If there is none, offer `/my-business-brain:setup` first.
3. **Watch list.** If the user wants a page or feed followed, add it: `scripts/watch.py <brain> add URL --name "..." [--entries ID,...] [--keywords "..."]`. If the list is empty and the brain holds official facts (VAT, licence fees, filing dates) or supplier prices, suggest two or three sources worth watching, from the most authoritative source for each (`references/trusted-sources.md`), and add the ones the user agrees to.
4. **Run the review:** `scripts/weekly_review.py <brain>` (from the core skill folder), with `--lang` set to the language of record. It runs the watch check, health, the week's changes, impact, signals, unsaved facts, golden answers, the toolkit check and the dashboard, and saves `_system/reviews/<date>.md`. Where scripts cannot run, do the same checks by hand in that order.
5. **Report answer first**, in the language of record (`${user_config.language}`):
   - One headline line: the health score, how many possible fact changes, open leads, and anything drifting.
   - **Needs your decision**: each "may affect what the brain knows" item, with the entry it touches. Offer to check it at the official source now (vet it; the brain never changes a fact because a page changed), then supersede and report the impact if it holds.
   - **Leads and sentiment**: say they are not facts. For each lead, offer to confirm (then `signals.py <brain> confirm ID --entry ENTRY`) or dismiss it.
   - **This week**: what the brain learned and changed, past work affected, unsaved facts and golden answers, a line each.
   - **Toolkit**: only if something changed, or a missing helper would have made this week's work easier (the user installs it; the brain never does).
6. Offer to open the dashboard. In the first week of a month, mention the journal for the month just ended.
7. If no Sunday review is scheduled, offer once to schedule it for Sunday evening in the owner's time zone (`${user_config.timezone}`, ask if unknown), or the evening before their first working day if their weekend differs. Create it only if they say yes.
