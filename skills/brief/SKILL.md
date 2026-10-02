---
name: brief
description: My Business Brain briefings and reports. Builds a cited briefing on one topic (a supplier, customer, product line or pricing), an onboarding pack for a new team member, a timeline of what happened around a fact or date, the monthly business journal, or the one-page dashboard. Use when the user runs /my-business-brain:brief, or asks "what do we know about…", "brief me on…", "what happened with…", for an onboarding pack, a monthly summary or journal, or the brain dashboard.
---

# /my-business-brain:brief

Turn what the brain knows into something a person can read in two minutes.

1. Load the `my-business-brain` skill from this plugin (via the Skill tool). If it cannot be loaded, read `../my-business-brain/SKILL.md` and `../my-business-brain/references/briefings-and-journal.md` directly.
2. Work out which one the user wants, and for whom:
   - **Topic briefing:** `scripts/briefing.py <brain> --topic "..." [--q "other phrasing"] --audience owner|team|external --write`.
   - **Onboarding pack:** `scripts/briefing.py <brain> --onboarding [--domain ...] --audience team --write`.
   - **Timeline:** `scripts/timeline.py <brain> --entry ID | --key K | --topic "..." | --around YYYY-MM-DD`.
   - **Monthly journal:** `scripts/journal.py <brain> --month YYYY-MM --write`.
   - **Meeting prep:** `scripts/meeting_prep.py <brain> --with "..." [--topic "..."] [--audience team] --write`.
   - **Dashboard:** `scripts/dashboard.py <brain>`, then offer to open `_system/dashboard.html`.

   If the audience isn't clear, ask. Anything for staff is `team`, anything leaving the business is `external`, and only the owner sees confidential facts.
   For a topic briefing, add open sentiment and leads on the same topic (`scripts/signals.py <brain> list --open`) in a separate part headed as unconfirmed, owner audience only.
3. Replace the placeholder lines in a briefing or journal with a short plain-language summary, written only from the facts listed, in the language of record (`${user_config.language}`). Keep every `[[id]]` citation. Never add facts that aren't listed.
4. For several follow-up questions on one topic, hand them to the `topic-expert` agent with the briefing's path. It answers from the briefing only, so a team or external briefing never leaks withheld facts.
5. Before sharing, run `scripts/cite_check.py <brain> <file> --audience team` (or `external` for outsiders) and fix every failure. Log it with `--log` if it is sent.
