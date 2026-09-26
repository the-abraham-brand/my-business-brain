# Briefings, timeline, journal and dashboard

Reports that turn the brain into something a person reads in two minutes. All of them cite the entries they use, leave out anything marked private, and are written in the language of record (setting `language`: match, english, arabic or both).

## Topic briefings

`scripts/briefing.py <brain> --topic "Supplier X" [--q "hosting contract"] --audience owner|team|external --write`

It gathers:
- every fact about the topic, grouped by area, with linked entries one step away;
- earlier values kept in the archive;
- proposals, quotes and emails that used these facts;
- contract dates coming up;
- decisions waiting.

It is saved in `_system/briefings/`.

**Audiences:**
- `owner` sees everything.
- `team` sees public and internal facts; confidential ones are withheld and counted.
- `external` sees public facts only, and never the answer log.

Choose the audience before building; don't build an owner briefing and trim it by hand.

**Finishing it:** replace the "In short" placeholder with two or three sentences that answer what the reader needs. Use only the facts listed and keep the citations.

**Follow-up questions:** for several questions on one topic, give the `topic-expert` agent the briefing's path and the questions. It answers from the briefing alone and says what's missing, so it can't leak what the audience wasn't meant to see.

## Onboarding pack

`scripts/briefing.py <brain> --onboarding --audience team [--domain products --domain policies] --write`

This gives a new team member everything they're allowed to know, area by area. Write a short welcome summary on top: what the business does, what it sells, the policies they'll be asked about most. Offer to add the glossary from an applied industry pack.

## Timeline

`scripts/timeline.py <brain> --entry ID | --key K | --topic "..." | --around YYYY-MM-DD [--days 14]`

This answers "what was going on around this?". It merges into one dated list:
- the changelog;
- entries recorded and verified, and archived values;
- decisions and corrections;
- outputs that went out;
- contract dates.

Future dates are shown after a "today" line. Use it to explain why a price changed, who was quoted what before a change, or what happened in a given fortnight. The timeline is for the owner: it may show confidential values, so never paste it into anything external.

## Monthly journal

`scripts/journal.py <brain> --month YYYY-MM --write` → `_system/journal/YYYY-MM.md`

Each week lists:
- **What changed** (from snapshots and the changelog);
- **What went out**;
- **Decisions that needed a person**;
- **Still open from earlier weeks** and **Newly open**.

The "still open" lists carry each week into the next, so the journal reads as one continuing story.

**Finishing it:**
1. Write one short paragraph at the top of each week that follows on from the previous week. Mention what was resolved and what is still dragging on.
2. Write a two or three sentence summary of the month at the top.
3. Use only the listed facts, and keep citations where the facts have them.
4. A quiet week gets one line, not padding.

Offer the journal at the start of each month, or as a scheduled task.

## Dashboard

`scripts/dashboard.py <brain> [--lang english|arabic|both]` → `_system/dashboard.html`

One self-contained page:
- the health score;
- contract dates in the next 90 days;
- decisions waiting;
- facts mentioned but not saved;
- outputs sent with an old value;
- key answers that changed;
- any unfinished job;
- this week's changes;
- the top issues.

It needs no internet and shows no confidential values. Arabic displays right to left, and it follows the device's light or dark mode. The full health check refreshes it; offer to open it after each health check.
