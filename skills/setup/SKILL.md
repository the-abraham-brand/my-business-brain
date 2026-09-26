---
name: setup
description: My Business Brain setup. Creates the business knowledge bank (the brain folder, its profile, system files and index) in a folder the user chooses, then offers to load the first documents. Use when the user runs /my-business-brain:setup, or asks to set up, start or create their business brain or business knowledge base.
---

# /my-business-brain:setup

Create the brain and get the first knowledge into it.

1. Load the `my-business-brain` skill from this plugin (via the Skill tool). If it cannot be loaded, read `../my-business-brain/SKILL.md` and `../my-business-brain/references/knowledge-model.md` directly.
2. **Choose the folder.** Use the folder the user names or has connected. If a `BRAIN.md` already exists there, stop and say the brain is already set up; offer a health check instead. With no writable folder, explain that the brain needs a folder (in the desktop app, a connected folder) and offer to build the files for them to save.
3. **Read the plugin settings first** (brain folder `${user_config.brain_folder}`, calendar `${user_config.calendar}`, currency `${user_config.currency}`, time zone `${user_config.timezone}`, weekend `${user_config.weekend}`, capture mode `${user_config.capture_mode}`); tell the user they can change them any time in the plugin's settings. Then **ask in one message** only for what is still unknown: business name and what it does; where it operates (country, city) and its currency; the owner or main contact; how the brain should capture facts from conversation (ask first, or remember automatically). Also ask which calendar they use (Google, Outlook, Apple, or another), for Contract Clocks.
4. **Create the structure** from `knowledge-model.md`: `business-brain/` with `entries/<domain>/` for the starting domains, `contracts/calendar/`, `analytics/`, `sources/`, `_system/archive/`.
5. **Write the starting files:**
   - `BRAIN.md`: business profile (name, what it does, location, currency, fiscal year, owner), the domain list, and a short "How this brain works" note (one fact per entry, sources, supersede don't delete, where decisions wait).
   - `_system/preferences.md`: capture mode, currency, time zone, weekend days, date format, preferred calendar and its reminders (7 days, 3 days, 24 hours).
   - Label the company entries' sensitivity (`public` for what is published, otherwise `internal`).
   - Empty `_system/changelog.md` (with a "Brain created" line), `decisions-needed.md`, `lessons.md`, `questions.md`.
   - Company entries for the profile facts, each with `source_type: user-stated` and `source: <user> (setup, <date>)`.
6. Run `scripts/brain_index.py` and `scripts/brain_health.py` on the new brain (from the core skill folder).
7. **Suggest the first load**, in order of value: price list, contracts, policies and terms, product or service descriptions, key customers and suppliers, SOPs. Offer to process any documents the user attaches right away (`/my-business-brain:learn`).
8. After the first load, propose 5 to 10 **golden questions** the business relies on (headline prices, refund and payment terms, key contract dates, VAT rate) and add the ones the user agrees to with `scripts/golden.py add` (`references/knowledge-regression.md`). Save a first snapshot: `scripts/brain_diff.py snapshot <brain>`.
9. Offer two scheduled tasks, created only if the user says yes: a weekly health check, and a monthly brain review with the next 90 days of contract dates.
