---
name: contract-clocks
description: Contract Clocks from My Business Brain. Extracts the key dates from any contract with a term longer than one month (end, auto-renewal, notice deadline, breaks, price reviews, payments, milestones), shows them for confirmation, and adds them to the user's preferred calendar (Google, Outlook, Apple or any open-source/CalDAV calendar via .ics) with reminders 7 days, 3 days and 24 hours before. Use when the user runs /my-business-brain:contract-clocks, shares a contract, lease, subscription or agreement, or asks when a contract renews, ends or needs notice.
---

# /my-business-brain:contract-clocks

Never miss a renewal, notice deadline or expiry.

1. Load the `my-business-brain` skill from this plugin (via the Skill tool). If it cannot be loaded, read `../my-business-brain/references/contract-clocks.md` directly.
2. Read the whole contract. Qualify it: term longer than one month, or auto-renewing. Otherwise say so and stop (offer to store it anyway).
3. Extract the dates and terms with clause references, and compute derived dates with `scripts/contract_dates.py` (from the core skill folder). Flag weekends and ask about public holidays in the contract's jurisdiction.
4. Show the date table with the **notice deadline** first and highlighted. Ask the user to confirm or correct. Never add unconfirmed dates.
5. Use the preferred calendar from `_system/preferences.md`, or ask once and save it:
   - Google Calendar connector: create events with popup reminders at 10,080, 4,320 and 1,440 minutes, after a clear yes.
   - Outlook connector: main event with a 24-hour reminder plus reminder events 7 and 3 days before, or the .ics file.
   - Apple, Thunderbird, Nextcloud, Proton, any CalDAV, or no connector: build an `.ics` with `scripts/make_ics.py` (three alarms per event) and send it to import.
6. Record the contract entry and register in the brain (when one exists), with the calendar status. Without a brain, still deliver the dates and the calendar file.
7. Remind the user that this tracks dates, not legal meaning; unclear terms go to a lawyer.
